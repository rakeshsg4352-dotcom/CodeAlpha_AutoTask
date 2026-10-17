"""
Service layer for AutoTask automation tasks.
Implements business logic for:
1. JPG File Organizer
2. Email Address Extractor
3. Webpage Title Scraper (with SSRF protection)
"""

import os
import re
import socket
import ipaddress
import shutil
from pathlib import Path
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import requests
from django.conf import settings
from django.utils import timezone
from .models import AutomationTask, AutomationConfiguration, AutomationActivity


# ==============================================================================
# WORKSPACE & SECURITY HELPERS
# ==============================================================================

def get_active_workspace_path() -> Path:
    """
    Retrieves the administrator-approved workspace directory path.
    Falls back to settings.APPROVED_WORKSPACE_ROOT if no active configuration exists.
    """
    config = AutomationConfiguration.objects.filter(is_active=True).first()
    if config and config.approved_workspace:
        workspace = Path(config.approved_workspace).resolve()
    else:
        workspace = Path(settings.APPROVED_WORKSPACE_ROOT).resolve()

    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


def resolve_safe_workspace_path(relative_subfolder: str) -> Path:
    """
    Validates and resolves a user-submitted folder path against the approved workspace.
    Guarantees that the resulting path is strictly contained within the approved workspace,
    preventing arbitrary server filesystem access and directory traversal attacks.
    """
    workspace_root = get_active_workspace_path()

    # Clean the input relative path
    cleaned_input = relative_subfolder.strip().replace('\\', '/')
    # Strip any leading slashes to prevent root-relative escaping
    cleaned_input = cleaned_input.lstrip('/')

    if not cleaned_input:
        target_path = workspace_root
    else:
        target_path = (workspace_root / cleaned_input).resolve()

    # Check whether the resolved path starts with the workspace root path
    try:
        common = os.path.commonpath([str(workspace_root), str(target_path)])
    except ValueError:
        # Happens on Windows if paths are on different drives
        raise PermissionError("Access denied: Target folder resides outside the approved workspace drive.")

    if common != str(workspace_root):
        raise PermissionError(
            "Access denied: Path traversal detected. Operations are strictly restricted to the approved workspace."
        )

    return target_path


# ==============================================================================
# TASK 1: MOVE JPG FILES SERVICE
# ==============================================================================

def move_jpg_files(source_subfolder: str, dest_subfolder: str) -> dict:
    """
    Moves all JPG and JPEG files from source folder to destination folder within
    the approved workspace. Safely handles duplicate filenames by appending counter.
    """
    source_dir = resolve_safe_workspace_path(source_subfolder)
    dest_dir = resolve_safe_workspace_path(dest_subfolder)

    if not source_dir.exists():
        raise FileNotFoundError(
            f"Source folder '{source_subfolder}' does not exist inside the approved workspace."
        )

    if not source_dir.is_dir():
        raise NotADirectoryError(
            f"Source path '{source_subfolder}' is not a directory."
        )

    # Ensure destination directory exists
    dest_dir.mkdir(parents=True, exist_ok=True)

    if source_dir == dest_dir:
        raise ValueError("Source and destination folders cannot be the same directory.")

    moved_files = []
    skipped_count = 0

    # Scan for matching image files
    for entry in os.scandir(source_dir):
        if entry.is_file():
            ext = os.path.splitext(entry.name)[1].lower()
            if ext in ('.jpg', '.jpeg'):
                orig_name = entry.name
                target_dest_file = dest_dir / orig_name

                # Safe collision handling: append counter if destination file already exists
                if target_dest_file.exists():
                    stem, file_ext = os.path.splitext(orig_name)
                    counter = 1
                    while target_dest_file.exists():
                        target_dest_file = dest_dir / f"{stem}_{counter}{file_ext}"
                        counter += 1

                # Move file safely
                shutil.move(entry.path, str(target_dest_file))
                moved_files.append({
                    'original': orig_name,
                    'destination_name': target_dest_file.name
                })

    return {
        'moved_count': len(moved_files),
        'moved_files': moved_files,
        'source_folder': source_subfolder,
        'dest_folder': dest_subfolder,
        'source_abs_display': f"[Workspace]/{source_subfolder}",
        'dest_abs_display': f"[Workspace]/{dest_subfolder}",
    }


# ==============================================================================
# TASK 2: EXTRACT EMAIL ADDRESSES SERVICE
# ==============================================================================

def extract_email_addresses(uploaded_file, user_id: int) -> dict:
    """
    Extracts email addresses from an uploaded TXT file.
    Deduplicates emails preserving original order and saves output into a TXT file.
    """
    # Read file content safely
    raw_content = uploaded_file.read()
    try:
        text_content = raw_content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            text_content = raw_content.decode('latin-1')
        except Exception as exc:
            raise ValueError(f"Unable to decode text file. Ensure it is a valid plain text document: {exc}")

    if not text_content.strip():
        raise ValueError("The uploaded text file is completely empty.")

    # Regular expression for matching email addresses
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    raw_matches = re.findall(email_pattern, text_content)

    # Clean matches (strip trailing punctuation like dots or commas)
    cleaned_emails = []
    for email in raw_matches:
        cleaned = email.rstrip('.,;:')
        if cleaned and '.' in cleaned.split('@')[-1]:
            cleaned_emails.append(cleaned)

    # Deduplicate while preserving original order
    unique_emails = list(dict.fromkeys(cleaned_emails))

    if not unique_emails:
        raise ValueError("No valid email addresses were found in the uploaded text file.")

    # Save output to generated media directory
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    out_filename = f"extracted_emails_user{user_id}_{timestamp}.txt"
    gen_dir = Path(settings.MEDIA_ROOT) / 'generated'
    gen_dir.mkdir(parents=True, exist_ok=True)

    output_path = gen_dir / out_filename
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# AutoTask - Extracted Email Addresses\n")
        f.write(f"# Source File: {uploaded_file.name}\n")
        f.write(f"# Extracted At: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Total Unique Emails: {len(unique_emails)}\n")
        f.write("# " + "=" * 50 + "\n\n")
        for email in unique_emails:
            f.write(f"{email}\n")

    return {
        'total_found': len(raw_matches),
        'unique_count': len(unique_emails),
        'emails': unique_emails,
        'output_filename': out_filename,
        'output_relative_path': f"generated/{out_filename}",
        'source_filename': uploaded_file.name
    }


# ==============================================================================
# TASK 3: SCRAPE WEBPAGE TITLE SERVICE (WITH SSRF PROTECTION)
# ==============================================================================

def validate_url_for_ssrf(url: str) -> None:
    """
    Enforces strict Server-Side Request Forgery (SSRF) protections.
    Blocks:
    - Schemes other than http/https
    - Loopback addresses (127.0.0.0/8, ::1)
    - Private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
    - Cloud metadata addresses (e.g. 169.254.169.254)
    - Link-local, reserved, multicast addresses
    - Localhost aliases
    """
    parsed = urlparse(url)

    if parsed.scheme.lower() not in ('http', 'https'):
        raise ValueError(f"Unsupported URL scheme '{parsed.scheme}'. Only HTTP and HTTPS are permitted.")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("Invalid URL: Hostname cannot be empty.")

    lower_host = hostname.lower()
    blocked_hosts = {'localhost', '127.0.0.1', '::1', '0.0.0.0', 'local', 'internal'}
    if lower_host in blocked_hosts or lower_host.endswith('.localhost') or lower_host.endswith('.local'):
        raise PermissionError(f"Security Alert: Requests to '{hostname}' (localhost/internal) are strictly forbidden.")

    # Resolve hostname to IP addresses via DNS
    try:
        addr_info = socket.getaddrinfo(hostname, None)
    except socket.gaierror as e:
        raise ValueError(f"DNS Resolution failed for host '{hostname}': {e}")

    for entry in addr_info:
        ip_str = entry[4][0]
        try:
            ip_obj = ipaddress.ip_address(ip_str)
        except ValueError:
            continue

        if (ip_obj.is_private or
            ip_obj.is_loopback or
            ip_obj.is_reserved or
            ip_obj.is_link_local or
            ip_obj.is_multicast):
            raise PermissionError(
                f"Security Alert: URL resolves to restricted/private IP address ({ip_str}). Request blocked to prevent SSRF."
            )


def scrape_webpage_title(target_url: str, user_id: int) -> dict:
    """
    Fetches a public webpage and extracts its <title> tag using BeautifulSoup.
    Implements timeout, size limits, redirect SSRF re-validation, and saves output to a TXT file.
    """
    current_url = target_url.strip()
    session = requests.Session()
    headers = {
        'User-Agent': 'AutoTask-Bot/1.0 (+http://localhost/academic-project; Academic Web Automation)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }

    # Follow up to 3 redirects manually to re-validate SSRF on each redirect hop
    max_redirects = 3
    final_response = None

    for _ in range(max_redirects + 1):
        validate_url_for_ssrf(current_url)

        try:
            resp = session.get(
                current_url,
                headers=headers,
                timeout=5.0,
                allow_redirects=False,
                stream=True
            )
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Connection timed out while attempting to reach {current_url} (timeout limit: 5s).")
        except requests.exceptions.SSLError as ssl_err:
            raise ConnectionError(f"SSL/TLS Certificate verification failed: {ssl_err}")
        except requests.exceptions.RequestException as req_err:
            raise ConnectionError(f"Failed to connect to destination server: {req_err}")

        # Check for redirect
        if resp.status_code in (301, 302, 303, 307, 308):
            location = resp.headers.get('Location')
            if not location:
                break
            current_url = urljoin(current_url, location)
            continue
        else:
            final_response = resp
            break

    if final_response is None:
        raise ConnectionError("Too many redirects or failed redirect resolution.")

    if final_response.status_code >= 400:
        raise ConnectionError(
            f"Server returned HTTP error status {final_response.status_code} ({final_response.reason})."
        )

    # Read up to 1 MB to prevent decompression bombs or memory exhaustion
    max_bytes = 1 * 1024 * 1024
    content_chunks = []
    bytes_read = 0

    for chunk in final_response.iter_content(chunk_size=8192):
        bytes_read += len(chunk)
        content_chunks.append(chunk)
        if bytes_read >= max_bytes:
            break

    html_bytes = b"".join(content_chunks)
    encoding = final_response.encoding or 'utf-8'
    try:
        html_text = html_bytes.decode(encoding, errors='replace')
    except Exception:
        html_text = html_bytes.decode('utf-8', errors='replace')

    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(html_text, 'html.parser')

    title_text = None
    if soup.title and soup.title.string:
        title_text = soup.title.string.strip()
    elif soup.find('meta', property='og:title'):
        title_text = soup.find('meta', property='og:title').get('content', '').strip()

    if not title_text:
        title_text = "Untitled Webpage (No <title> or <meta og:title> tag found)"

    # Clean whitespace in title
    title_text = re.sub(r'\s+', ' ', title_text)

    # Save title to output file
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    out_filename = f"scraped_title_user{user_id}_{timestamp}.txt"
    gen_dir = Path(settings.MEDIA_ROOT) / 'generated'
    gen_dir.mkdir(parents=True, exist_ok=True)

    output_path = gen_dir / out_filename
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# AutoTask - Scraped Webpage Title Result\n")
        f.write(f"# Requested URL: {target_url}\n")
        f.write(f"# Final URL: {current_url}\n")
        f.write(f"# Scraped At: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# HTTP Status: {final_response.status_code}\n")
        f.write("# " + "=" * 50 + "\n\n")
        f.write(f"Title: {title_text}\n")

    return {
        'title': title_text,
        'requested_url': target_url,
        'final_url': current_url,
        'http_status': final_response.status_code,
        'output_filename': out_filename,
        'output_relative_path': f"generated/{out_filename}"
    }


# ==============================================================================
# COMMON TASK EXECUTION AND AUDIT WRAPPER
# ==============================================================================

def execute_automation_task(user, task_type: str, task_name: str, input_summary: str, runner_func, *args, **kwargs):
    """
    Executes an automation function within an audited transaction wrapper.
    Creates an AutomationTask record, updates timestamps, handles errors cleanly,
    and records an audit log entry in AutomationActivity.
    """
    started_at = timezone.now()
    task = AutomationTask.objects.create(
        user=user,
        task_type=task_type,
        task_name=task_name,
        input_summary=input_summary,
        status='RUNNING',
        started_at=started_at
    )

    AutomationActivity.objects.create(
        user=user,
        automation_task=task,
        action='TASK_EXECUTE',
        details=f"Task #{task.id} ({task_name}) initiated by {user.username}."
    )

    try:
        result_data = runner_func(*args, **kwargs)

        task.status = 'SUCCESS'
        task.completed_at = timezone.now()

        # Build appropriate result summary based on task type
        if task_type == 'MOVE_JPG':
            task.result_summary = (
                f"Successfully moved {result_data['moved_count']} image(s) from "
                f"'{result_data['source_folder']}' to '{result_data['dest_folder']}'."
            )
        elif task_type == 'EXTRACT_EMAILS':
            task.result_summary = (
                f"Extracted {result_data['unique_count']} unique email address(es) "
                f"from '{result_data['source_filename']}'."
            )
            task.output_file = result_data.get('output_relative_path')
        elif task_type == 'SCRAPE_TITLE':
            task.result_summary = f"Scraped title: \"{result_data['title']}\" (HTTP {result_data['http_status']})."
            task.output_file = result_data.get('output_relative_path')

        task.save()

        AutomationActivity.objects.create(
            user=user,
            automation_task=task,
            action='TASK_SUCCESS',
            details=f"Task #{task.id} finished successfully. {task.result_summary}"
        )

        return task, result_data, None

    except Exception as exc:
        task.status = 'FAILED'
        task.error_message = str(exc)
        task.completed_at = timezone.now()
        task.save()

        AutomationActivity.objects.create(
            user=user,
            automation_task=task,
            action='TASK_FAILED',
            details=f"Task #{task.id} failed: {str(exc)}"
        )

        return task, None, str(exc)
