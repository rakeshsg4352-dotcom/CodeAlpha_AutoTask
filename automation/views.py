"""
Views for AutoTask - Python Automation System.
Handles web dashboard, task execution endpoints, history, analytics, and authentication.
"""

import os
from pathlib import Path
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, FileResponse, Http404, HttpResponseForbidden
from django.core.paginator import Paginator
from django.conf import settings
from django.utils import timezone

from .models import AutomationTask, AutomationConfiguration, AutomationActivity
from .forms import (
    UserRegistrationForm,
    UserLoginForm,
    MoveJpgForm,
    ExtractEmailsForm,
    ScrapeTitleForm
)
from .services import (
    move_jpg_files,
    extract_email_addresses,
    scrape_webpage_title,
    execute_automation_task,
    get_active_workspace_path
)


# ==============================================================================
# 1. HOME / DASHBOARD VIEW
# ==============================================================================

@login_required
def dashboard_view(request):
    """
    Renders the main dashboard displaying metrics, recent tasks, and automation cards.
    """
    user_tasks = AutomationTask.objects.filter(user=request.user)
    
    total_tasks = user_tasks.count()
    successful_tasks = user_tasks.filter(status='SUCCESS').count()
    failed_tasks = user_tasks.filter(status='FAILED').count()
    success_rate = round((successful_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0

    # Retrieve last execution status for each task type
    last_move_jpg = user_tasks.filter(task_type='MOVE_JPG').first()
    last_extract_emails = user_tasks.filter(task_type='EXTRACT_EMAILS').first()
    last_scrape_title = user_tasks.filter(task_type='SCRAPE_TITLE').first()

    # Recent activities and recent executions
    recent_tasks = user_tasks[:6]
    recent_activities = AutomationActivity.objects.filter(user=request.user)[:8]

    context = {
        'total_tasks': total_tasks,
        'successful_tasks': successful_tasks,
        'failed_tasks': failed_tasks,
        'success_rate': success_rate,
        'recent_tasks': recent_tasks,
        'recent_activities': recent_activities,
        'last_move_jpg': last_move_jpg,
        'last_extract_emails': last_extract_emails,
        'last_scrape_title': last_scrape_title,
    }
    return render(request, 'dashboard.html', context)


# ==============================================================================
# 2. AUTOMATION TASKS CATALOG VIEW
# ==============================================================================

@login_required
def tasks_view(request):
    """
    Renders the catalog of all available automation tools with requirements and actions.
    """
    user_tasks = AutomationTask.objects.filter(user=request.user)
    context = {
        'last_move_jpg': user_tasks.filter(task_type='MOVE_JPG').first(),
        'last_extract_emails': user_tasks.filter(task_type='EXTRACT_EMAILS').first(),
        'last_scrape_title': user_tasks.filter(task_type='SCRAPE_TITLE').first(),
    }
    return render(request, 'tasks.html', context)


# ==============================================================================
# 3. TASK 1: MOVE JPG FILES VIEW
# ==============================================================================

@login_required
def move_jpg_view(request):
    """
    Handles JPG file organization automation with safe workspace validation.
    Supports both traditional POST submissions and AJAX requests.
    """
    workspace_root = get_active_workspace_path()
    
    # List existing subdirectories in approved workspace for user reference
    available_folders = []
    try:
        for entry in os.scandir(workspace_root):
            if entry.is_dir():
                available_folders.append(entry.name)
    except Exception:
        pass

    if request.method == 'POST':
        form = MoveJpgForm(request.POST)
        if form.is_valid():
            source = form.cleaned_data['source_folder']
            dest = form.cleaned_data['dest_folder']

            task, result, err = execute_automation_task(
                request.user,
                task_type='MOVE_JPG',
                task_name='JPG File Organizer',
                input_summary=f"Source: {source} | Destination: {dest}",
                runner_func=move_jpg_files,
                source_subfolder=source,
                dest_subfolder=dest
            )

            is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '')

            if err:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': err, 'task_id': task.id}, status=400)
                messages.error(request, f"Task Failed: {err}")
            else:
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'task_id': task.id,
                        'moved_count': result['moved_count'],
                        'moved_files': result['moved_files'],
                        'source_folder': result['source_folder'],
                        'dest_folder': result['dest_folder'],
                        'message': f"Successfully moved {result['moved_count']} image(s)!"
                    })
                messages.success(request, f"Success: Moved {result['moved_count']} image(s) into '{dest}'.")
                return redirect('task_details', task_id=task.id)
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                errors = "; ".join([f"{f}: {e[0]}" for f, e in form.errors.items()])
                return JsonResponse({'success': False, 'error': errors}, status=400)
    else:
        form = MoveJpgForm()

    context = {
        'form': form,
        'workspace_path': str(workspace_root),
        'available_folders': available_folders,
    }
    return render(request, 'move_jpg.html', context)


# ==============================================================================
# 4. TASK 2: EXTRACT EMAIL ADDRESSES VIEW
# ==============================================================================

@login_required
def extract_emails_view(request):
    """
    Handles TXT file upload and email address extraction automation.
    Supports both traditional POST submissions and AJAX requests.
    """
    if request.method == 'POST':
        form = ExtractEmailsForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data['file']

            task, result, err = execute_automation_task(
                request.user,
                task_type='EXTRACT_EMAILS',
                task_name='Email Address Extractor',
                input_summary=f"Uploaded File: {uploaded_file.name} ({uploaded_file.size} bytes)",
                runner_func=extract_email_addresses,
                uploaded_file=uploaded_file,
                user_id=request.user.id
            )

            is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '')

            if err:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': err, 'task_id': task.id}, status=400)
                messages.error(request, f"Extraction Failed: {err}")
            else:
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'task_id': task.id,
                        'total_found': result['total_found'],
                        'unique_count': result['unique_count'],
                        'emails': result['emails'],
                        'download_url': f"/history/{task.id}/download/",
                        'message': f"Extracted {result['unique_count']} unique email address(es)."
                    })
                messages.success(request, f"Extracted {result['unique_count']} unique email(s).")
                return redirect('task_details', task_id=task.id)
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                errors = "; ".join([f"{f}: {e[0]}" for f, e in form.errors.items()])
                return JsonResponse({'success': False, 'error': errors}, status=400)
    else:
        form = ExtractEmailsForm()

    return render(request, 'extract_emails.html', {'form': form})


# ==============================================================================
# 5. TASK 3: SCRAPE WEBPAGE TITLE VIEW
# ==============================================================================

@login_required
def scrape_title_view(request):
    """
    Handles public webpage fetching and <title> tag scraping with SSRF prevention.
    Supports both traditional POST submissions and AJAX requests.
    """
    if request.method == 'POST':
        form = ScrapeTitleForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']

            task, result, err = execute_automation_task(
                request.user,
                task_type='SCRAPE_TITLE',
                task_name='Webpage Title Scraper',
                input_summary=f"Target URL: {url}",
                runner_func=scrape_webpage_title,
                target_url=url,
                user_id=request.user.id
            )

            is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '')

            if err:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': err, 'task_id': task.id}, status=400)
                messages.error(request, f"Scraping Failed: {err}")
            else:
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'task_id': task.id,
                        'title': result['title'],
                        'requested_url': result['requested_url'],
                        'final_url': result['final_url'],
                        'http_status': result['http_status'],
                        'download_url': f"/history/{task.id}/download/",
                        'message': f"Successfully scraped webpage title."
                    })
                messages.success(request, f"Title scraped: {result['title']}")
                return redirect('task_details', task_id=task.id)
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                errors = "; ".join([f"{f}: {e[0]}" for f, e in form.errors.items()])
                return JsonResponse({'success': False, 'error': errors}, status=400)
    else:
        form = ScrapeTitleForm()

    return render(request, 'scrape_title.html', {'form': form})


# ==============================================================================
# 6. AUTOMATION HISTORY VIEW
# ==============================================================================

@login_required
def history_view(request):
    """
    Lists previously executed tasks with search, type filters, status filters,
    sorting, and pagination.
    """
    # Regular users see only their tasks; staff can view all if requested
    tasks_query = AutomationTask.objects.filter(user=request.user)

    # Search query
    q = request.GET.get('q', '').strip()
    if q:
        tasks_query = tasks_query.filter(task_name__icontains=q) | tasks_query.filter(input_summary__icontains=q)

    # Task type filter
    task_type = request.GET.get('task_type', '').strip()
    if task_type in ('MOVE_JPG', 'EXTRACT_EMAILS', 'SCRAPE_TITLE'):
        tasks_query = tasks_query.filter(task_type=task_type)

    # Status filter
    status = request.GET.get('status', '').strip()
    if status in ('SUCCESS', 'FAILED', 'RUNNING', 'PENDING'):
        tasks_query = tasks_query.filter(status=status)

    # Date sort order
    sort_order = request.GET.get('sort', 'desc').strip()
    if sort_order == 'asc':
        tasks_query = tasks_query.order_by('created_at')
    else:
        tasks_query = tasks_query.order_by('-created_at')

    # Pagination: 10 tasks per page
    paginator = Paginator(tasks_query, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'q': q,
        'task_type': task_type,
        'status': status,
        'sort_order': sort_order,
        'total_count': paginator.count,
    }
    return render(request, 'history.html', context)


# ==============================================================================
# 7. TASK DETAILS VIEW
# ==============================================================================

@login_required
def task_details_view(request, task_id):
    """
    Displays full execution details, timestamps, duration, outcomes, and errors.
    Enforces user authorization checks.
    """
    task = get_object_or_404(AutomationTask, id=task_id)

    # Security check: User must own the task or be administrative staff
    if task.user != request.user and not request.user.is_staff:
        return HttpResponseForbidden("Access Denied: You do not have permission to view this task.")

    activities = task.activities.all()

    context = {
        'task': task,
        'activities': activities,
    }
    return render(request, 'task_details.html', context)


# ==============================================================================
# 8. OUTPUT FILE DOWNLOAD VIEW
# ==============================================================================

@login_required
def download_output_view(request, task_id):
    """
    Safely serves the generated output file for a task to authorized users.
    """
    task = get_object_or_404(AutomationTask, id=task_id)

    # Security check: User must own the task or be administrative staff
    if task.user != request.user and not request.user.is_staff:
        return HttpResponseForbidden("Access Denied: You cannot download files from this task.")

    if not task.output_file:
        raise Http404("No output file was generated for this automation task.")

    file_path = Path(settings.MEDIA_ROOT) / task.output_file
    if not file_path.exists():
        raise Http404("The requested output file could not be found on the server.")

    # Audit download activity
    AutomationActivity.objects.create(
        user=request.user,
        automation_task=task,
        action='TASK_DOWNLOAD',
        details=f"User {request.user.username} downloaded output file '{task.output_filename}'."
    )

    response = FileResponse(open(file_path, 'rb'), as_attachment=True, filename=task.output_filename)
    return response


# ==============================================================================
# 9. ABOUT PROJECT VIEW
# ==============================================================================

def about_view(request):
    """
    Presents academic project documentation, architecture, security, and developer details.
    """
    return render(request, 'about.html')


# ==============================================================================
# 10. ADMIN DASHBOARD VIEW
# ==============================================================================

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def admin_dashboard_view(request):
    """
    Administrator dashboard providing system-wide analytics, configuration overview,
    failure monitoring, and audit log inspection.
    """
    total_users = User.objects.count()
    all_tasks = AutomationTask.objects.all()
    total_executions = all_tasks.count()
    total_success = all_tasks.filter(status='SUCCESS').count()
    total_failed = all_tasks.filter(status='FAILED').count()
    
    recent_all_tasks = all_tasks.select_related('user')[:10]
    recent_activities = AutomationActivity.objects.select_related('user', 'automation_task')[:15]
    configurations = AutomationConfiguration.objects.all()

    context = {
        'total_users': total_users,
        'total_executions': total_executions,
        'total_success': total_success,
        'total_failed': total_failed,
        'recent_all_tasks': recent_all_tasks,
        'recent_activities': recent_activities,
        'configurations': configurations,
    }
    return render(request, 'admin_dashboard.html', context)


# ==============================================================================
# 11. AUTHENTICATION: LOGIN, LOGOUT, REGISTER
# ==============================================================================

def login_view(request):
    """
    Handles user login authentication.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                AutomationActivity.objects.create(
                    user=user,
                    action='USER_LOGIN',
                    details=f"User {user.username} logged in successfully."
                )
                messages.success(request, f"Welcome back, {user.username}!")
                next_url = request.GET.get('next') or 'dashboard'
                return redirect(next_url)
            else:
                messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = UserLoginForm()

    return render(request, 'login.html', {'form': form})


def register_view(request):
    """
    Handles new user registration.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            AutomationActivity.objects.create(
                user=user,
                action='USER_REGISTER',
                details=f"New user {user.username} registered."
            )
            messages.success(request, "Account created successfully! You can now log in.")
            return redirect('login')
        else:
            messages.error(request, "Please correct the errors indicated below.")
    else:
        form = UserRegistrationForm()

    return render(request, 'register.html', {'form': form})


@login_required
def logout_view(request):
    """
    Handles user logout.
    """
    AutomationActivity.objects.create(
        user=request.user,
        action='USER_LOGOUT',
        details=f"User {request.user.username} logged out."
    )
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')
