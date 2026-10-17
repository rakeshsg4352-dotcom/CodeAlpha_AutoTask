from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os


class AutomationTask(models.Model):
    """
    Records an execution of an automation script.
    """
    TASK_TYPE_CHOICES = [
        ('MOVE_JPG', 'JPG File Organizer'),
        ('EXTRACT_EMAILS', 'Email Address Extractor'),
        ('SCRAPE_TITLE', 'Webpage Title Scraper'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tasks',
        help_text='The user who initiated this automation task.'
    )
    task_type = models.CharField(
        max_length=50,
        choices=TASK_TYPE_CHOICES,
        db_index=True,
        help_text='Type of automation task.'
    )
    task_name = models.CharField(
        max_length=150,
        help_text='Descriptive title of the automation task.'
    )
    input_summary = models.TextField(
        help_text='Sanitized summary of the inputs supplied to the automation.'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        db_index=True,
        help_text='Current execution status.'
    )
    result_summary = models.TextField(
        blank=True,
        default='',
        help_text='Summary of execution outcomes, counters, or extracted data.'
    )
    output_file = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Relative filename or path to generated output file.'
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text='Error details if execution failed.'
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when execution began.'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when execution completed.'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text='Timestamp when record was created.'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['task_type']),
        ]
        verbose_name = 'Automation Task'
        verbose_name_plural = 'Automation Tasks'

    def __str__(self):
        return f"[{self.get_status_display()}] {self.task_name} (#{self.id}) - {self.user.username}"

    @property
    def duration_seconds(self):
        """Calculates duration of task execution in seconds."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return round(delta.total_seconds(), 2)
        return None

    @property
    def output_filename(self):
        """Returns just the basename of the output file."""
        if self.output_file:
            return os.path.basename(self.output_file)
        return None

    @property
    def status_badge_class(self):
        """Returns CSS badge class for status styling."""
        mapping = {
            'SUCCESS': 'badge-success',
            'FAILED': 'badge-danger',
            'RUNNING': 'badge-warning',
            'PENDING': 'badge-secondary',
        }
        return mapping.get(self.status, 'badge-secondary')


class AutomationConfiguration(models.Model):
    """
    Administrative configuration for approved filesystem workspaces and policies.
    """
    configuration_name = models.CharField(
        max_length=100,
        unique=True,
        help_text='Unique identifier for this workspace configuration.'
    )
    approved_workspace = models.CharField(
        max_length=500,
        help_text='Absolute or relative path to the allowed workspace directory.'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Designates whether this configuration is currently active.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Automation Configuration'
        verbose_name_plural = 'Automation Configurations'

    def __str__(self):
        status = 'Active' if self.is_active else 'Inactive'
        return f"{self.configuration_name} ({status}): {self.approved_workspace}"


class AutomationActivity(models.Model):
    """
    Audit log of system activities, task executions, and security events.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities',
        help_text='User associated with this activity.'
    )
    automation_task = models.ForeignKey(
        AutomationTask,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='activities',
        help_text='Associated automation task, if applicable.'
    )
    action = models.CharField(
        max_length=100,
        help_text='Action key (e.g., TASK_EXECUTE, FILE_DOWNLOAD, LOGIN).'
    )
    details = models.TextField(
        blank=True,
        help_text='Detailed log description of the activity.'
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text='When this activity occurred.'
    )

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Automation Activity'
        verbose_name_plural = 'Automation Activities'

    def __str__(self):
        username = self.user.username if self.user else 'System/Anonymous'
        return f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {username} - {self.action}"
