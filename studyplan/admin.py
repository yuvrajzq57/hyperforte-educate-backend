from django.contrib import admin
from django.utils.html import format_html
from .models import UserStudyPlan, StudyPlanDay


class StudyPlanDayInline(admin.TabularInline):
    model = StudyPlanDay
    extra = 0
    min_num = 1
    max_num = 7
    fields = ('day_of_week',)


@admin.register(UserStudyPlan)
class UserStudyPlanAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'enabled', 'preferred_time', 'reminder_email', 
                   'target_completion_date', 'study_days_list', 'created_at')
    list_filter = ('enabled', 'reminder_email', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at', 'study_days_list')
    inlines = [StudyPlanDayInline]
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'enabled')
        }),
        ('Study Preferences', {
            'fields': ('preferred_time', 'reminder_email', 'target_completion_date')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'study_days_list'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'
    
    def study_days_list(self, obj):
        days = obj.get_study_days_display()
        return ", ".join(days) if days else "None"
    study_days_list.short_description = 'Study Days'


@admin.register(StudyPlanDay)
class StudyPlanDayAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'day_of_week')
    list_filter = ('day_of_week',)
    search_fields = ('study_plan__user__email',)
    
    def user_email(self, obj):
        return obj.study_plan.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'study_plan__user__email'
