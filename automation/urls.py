from django.urls import path
from . import views

urlpatterns = [
    # Core Dashboard & Catalog
    path('', views.dashboard_view, name='dashboard'),
    path('tasks/', views.tasks_view, name='tasks'),

    # Automation Tools
    path('tasks/move-jpg/', views.move_jpg_view, name='move_jpg'),
    path('tasks/extract-emails/', views.extract_emails_view, name='extract_emails'),
    path('tasks/scrape-title/', views.scrape_title_view, name='scrape_title'),

    # History & Details
    path('history/', views.history_view, name='history'),
    path('history/<int:task_id>/', views.task_details_view, name='task_details'),
    path('history/<int:task_id>/download/', views.download_output_view, name='download_output'),

    # Information & Administration
    path('about/', views.about_view, name='about'),
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),

    # Authentication
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
]
