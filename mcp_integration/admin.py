from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import MCPUserIntegration

@admin.register(MCPUserIntegration)
class MCPUserIntegrationAdmin(admin.ModelAdmin):
    """Admin interface for MCP User Integration."""
    list_display = (
        'user_email',
        'is_active',
        'last_synced',
        'created_at',
        'updated_at',
        'user_actions',
    )
    
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('created_at', 'updated_at', 'last_synced')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'is_active')
        }),
        ('Sync Information', {
            'fields': ('last_synced', 'created_at', 'updated_at')
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'
    
    def user_actions(self, obj):
        return format_html(
            '<a class="button" href="{}">View User</a>&nbsp;',
            reverse('admin:auth_user_change', args=[obj.user.id])
        )
    user_actions.short_description = 'Actions'
    user_actions.allow_tags = True
    
    def has_add_permission(self, request):
        return False
        
    def has_delete_permission(self, request, obj=None):
        return False
