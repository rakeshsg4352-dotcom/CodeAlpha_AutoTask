"""
Comprehensive automated test suite for AutoTask system.
Tests authentication, services, views, SSRF filters, file operations, and permissions.
"""

import os
import shutil
import tempfile
import socket
from pathlib import Path
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import AutomationTask, AutomationConfiguration, AutomationActivity
from .services import (
    move_jpg_files,
    extract_email_addresses,
    scrape_webpage_title,
    validate_url_for_ssrf,
    resolve_safe_workspace_path
)


class BaseTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_password = 'TestPassword123!'
        self.user = User.objects.create_user(
            username='tester',
            email='tester@example.com',
            password=self.user_password
        )
        self.other_user = User.objects.create_user(
            username='other_tester',
            email='other@example.com',
            password=self.user_password
        )
        self.admin_user = User.objects.create_superuser(
            username='admintester',
            email='admin@example.com',
            password=self.user_password
        )

        # Temporary workspace directory for isolated file testing
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir, ignore_errors=True)

        self.config = AutomationConfiguration.objects.create(
            configuration_name='Test Workspace',
            approved_workspace=self.temp_dir,
            is_active=True
        )

    def login_tester(self):
        self.client.login(username='tester', password=self.user_password)


# ==============================================================================
# 1. AUTHENTICATION & REGISTRATION TESTS
# ==============================================================================

class AuthenticationTests(BaseTestCase):
    def test_user_registration_success(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePassword123',
            'confirm_password': 'SecurePassword123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_registration_password_mismatch(self):
        response = self.client.post(reverse('register'), {
            'username': 'mismatchuser',
            'email': 'mismatch@example.com',
            'password': 'Password123',
            'confirm_password': 'DifferentPassword456'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='mismatchuser').exists())

    def test_user_login_and_logout(self):
        response = self.client.post(reverse('login'), {
            'username': 'tester',
            'password': self.user_password
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.id)

        # Logout
        logout_resp = self.client.get(reverse('logout'))
        self.assertEqual(logout_resp.status_code, 302)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_unauthenticated_redirect(self):
        # Protected dashboard view redirects to login
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)


# ==============================================================================
# 2. JPG FILE ORGANIZER TESTS
# ==============================================================================

class MoveJpgTests(BaseTestCase):
    def test_move_jpg_success(self):
        # Setup source and dest directories inside approved workspace
        src = Path(self.temp_dir) / 'source'
        src.mkdir()
        dest = Path(self.temp_dir) / 'dest'

        # Create sample files
        (src / 'img1.jpg').write_text('dummy1')
        (src / 'img2.jpeg').write_text('dummy2')
        (src / 'notes.txt').write_text('ignore this')

        result = move_jpg_files('source', 'dest')
        self.assertEqual(result['moved_count'], 2)
        self.assertTrue((dest / 'img1.jpg').exists())
        self.assertTrue((dest / 'img2.jpeg').exists())
        self.assertTrue((src / 'notes.txt').exists())  # Non-jpg left intact

    def test_move_jpg_duplicate_handling(self):
        src = Path(self.temp_dir) / 'source'
        dest = Path(self.temp_dir) / 'dest'
        src.mkdir()
        dest.mkdir()

        # Destination already has photo.jpg
        (dest / 'photo.jpg').write_text('original')
        (src / 'photo.jpg').write_text('new')

        result = move_jpg_files('source', 'dest')
        self.assertEqual(result['moved_count'], 1)
        # Should have preserved original and created photo_1.jpg
        self.assertEqual((dest / 'photo.jpg').read_text(), 'original')
        self.assertTrue((dest / 'photo_1.jpg').exists())
        self.assertEqual((dest / 'photo_1.jpg').read_text(), 'new')

    def test_nonexistent_source_folder(self):
        with self.assertRaises(FileNotFoundError):
            move_jpg_files('does_not_exist', 'dest')

    def test_directory_traversal_rejection(self):
        with self.assertRaises(PermissionError):
            resolve_safe_workspace_path('../outside_workspace')


# ==============================================================================
# 3. EMAIL ADDRESS EXTRACTOR TESTS
# ==============================================================================

class ExtractEmailsTests(BaseTestCase):
    def test_extract_emails_success_and_deduplication(self):
        content = (
            "Contact support@example.com for help.\n"
            "Sales: sales@example.org.\n"
            "Duplicate support: support@example.com.\n"
            "Admin contact is admin@example.com."
        ).encode('utf-8')

        uploaded = SimpleUploadedFile("sample.txt", content, content_type="text/plain")
        result = extract_email_addresses(uploaded, self.user.id)

        self.assertEqual(result['unique_count'], 3)
        self.assertEqual(result['emails'], [
            'support@example.com',
            'sales@example.org',
            'admin@example.com'
        ])
        self.assertTrue(Path(result['output_filename']).suffix, '.txt')

    def test_empty_txt_file_rejection(self):
        empty_file = SimpleUploadedFile("empty.txt", b"", content_type="text/plain")
        with self.assertRaises(ValueError):
            extract_email_addresses(empty_file, self.user.id)

    def test_no_emails_found(self):
        no_email_file = SimpleUploadedFile("no_emails.txt", b"Hello world, there are no addresses here.", content_type="text/plain")
        with self.assertRaises(ValueError):
            extract_email_addresses(no_email_file, self.user.id)


# ==============================================================================
# 4. WEBPAGE TITLE SCRAPER & SSRF TESTS
# ==============================================================================

class ScrapeTitleTests(BaseTestCase):
    @patch('requests.Session.get')
    @patch('socket.getaddrinfo')
    def test_scrape_title_success(self, mock_dns, mock_get):
        # Mock public IP resolution
        mock_dns.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 80))]

        # Mock HTML response
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.encoding = 'utf-8'
        mock_resp.headers = {}
        mock_resp.iter_content.return_value = [b"<html><head><title>Example Domain</title></head><body><h1>Hello</h1></body></html>"]
        mock_get.return_value = mock_resp

        result = scrape_webpage_title("https://example.com", self.user.id)
        self.assertEqual(result['title'], "Example Domain")
        self.assertEqual(result['http_status'], 200)

    def test_ssrf_blocks_localhost(self):
        with self.assertRaises(PermissionError):
            validate_url_for_ssrf("http://localhost:8000/admin")

    def test_ssrf_blocks_loopback_ip(self):
        with self.assertRaises(PermissionError):
            validate_url_for_ssrf("http://127.0.0.1/status")

    @patch('socket.getaddrinfo')
    def test_ssrf_blocks_private_network_ips(self, mock_dns):
        # 192.168.1.1
        mock_dns.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('192.168.1.1', 80))]
        with self.assertRaises(PermissionError):
            validate_url_for_ssrf("http://my-internal-router.corp")

    def test_ssrf_blocks_unsupported_schemes(self):
        with self.assertRaises(ValueError):
            validate_url_for_ssrf("file:///etc/passwd")
        with self.assertRaises(ValueError):
            validate_url_for_ssrf("ftp://example.com/file")


# ==============================================================================
# 5. TASK HISTORY, DOWNLOADS & AUTHORIZATION
# ==============================================================================

class TaskHistoryAndDownloadTests(BaseTestCase):
    def test_user_data_isolation(self):
        # Create tasks for user1 and user2
        task1 = AutomationTask.objects.create(
            user=self.user,
            task_type='MOVE_JPG',
            task_name='User1 Task',
            input_summary='Input 1',
            status='SUCCESS'
        )
        task2 = AutomationTask.objects.create(
            user=self.other_user,
            task_type='MOVE_JPG',
            task_name='User2 Task',
            input_summary='Input 2',
            status='SUCCESS'
        )

        # Log in as user 1
        self.login_tester()

        # User 1 history should only display task1
        resp = self.client.get(reverse('history'))
        self.assertContains(resp, 'User1 Task')
        self.assertNotContains(resp, 'User2 Task')

        # User 1 attempting to view User 2's task details should be forbidden (403)
        detail_resp = self.client.get(reverse('task_details', args=[task2.id]))
        self.assertEqual(detail_resp.status_code, 403)

    def test_admin_dashboard_permission_check(self):
        self.login_tester()
        # Ordinary user cannot access admin dashboard
        resp = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(resp.status_code, 302)  # Redirects

        # Superuser can access admin dashboard
        self.client.login(username='admintester', password=self.user_password)
        admin_resp = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(admin_resp.status_code, 200)
