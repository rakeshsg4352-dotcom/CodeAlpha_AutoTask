from django.contrib import admin
from .models import AutomationTask, AutomationConfiguration, AutomationActivity


@admin.register(AutomationTask)
class AutomationTaskAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'task_name',
        'task_type',
        'user',
        'status',
        'duration_display',
        'created_at'
    )
    list_filter = ('status', 'task_type', 'created_at')
    search_fields = ('task_name', 'input_summary', 'result_summary', 'user__username', 'error_message')
    readonly_fields = ('id', 'created_at', 'started_at', 'completed_at', 'duration_display')
    ordering = ('-created_at',)

    @admin.display(description='Duration (s)')
    def duration_display(self, obj):
        return f"{obj.duration_seconds}s" if obj.duration_seconds is not None else "-"


@admin.register(AutomationConfiguration)
class AutomationConfigurationAdmin(admin.ModelAdmin):
    list_display = ('configuration_name', 'approved_workspace', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active',)
    list_editable = ('is_active',)
    search_fields = ('configuration_name', 'approved_workspace')
    ordering = ('-created_at',)


@admin.register(AutomationActivity)
class AutomationActivityAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'automation_task', 'short_details')
    list_filter = ('action', 'timestamp')
    search_fields = ('user__username', 'action', 'details')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)

    @admin.display(description='Details')
    def short_details(self, obj):
        return (obj.details[:75] + '...') if len(obj.details) > 75 else obj.details
