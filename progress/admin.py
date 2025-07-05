from django.contrib import admin
from .models import UserModuleProgress, UserSectionProgress, UserQuizAttempt

@admin.register(UserModuleProgress)
class UserModuleProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'module', 'progress_percentage', 'is_completed', 'last_accessed')
    list_filter = ('is_completed', 'module__course')
    search_fields = ('user__email', 'module__title')
    readonly_fields = ('last_accessed', 'completed_at')
    list_select_related = ('user', 'module')

@admin.register(UserSectionProgress)
class UserSectionProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'section', 'is_completed', 'last_accessed')
    list_filter = ('is_completed', 'section__module__course')
    search_fields = ('user__email', 'section__title')
    readonly_fields = ('last_accessed', 'completed_at')
    list_select_related = ('user', 'section', 'section__module')

@admin.register(UserQuizAttempt)
class UserQuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'score', 'passed', 'completed_at')
    list_filter = ('passed', 'quiz__module__course')
    search_fields = ('user__email', 'quiz__title')
    readonly_fields = ('started_at', 'completed_at')
    list_select_related = ('user', 'quiz', 'quiz__module')
