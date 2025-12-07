from django.contrib import admin
from django.utils.html import format_html
from .models import (
    StudentProfile, JobListing, JobMatchResult, JobSearchQuery, Skill
)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'training_track', 'skills_count', 'created_at')
    list_filter = ('training_track', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    
    def skills_count(self, obj):
        return len(obj.skills) if obj.skills else 0
    skills_count.short_description = 'Skills Count'


class JobMatchInline(admin.TabularInline):
    model = JobMatchResult
    extra = 0
    readonly_fields = ('match_score', 'readiness_days', 'created_at')
    can_delete = False
    show_change_link = True
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'job_type', 'location', 'posted_date', 'is_active')
    list_filter = ('job_type', 'is_active', 'source', 'posted_date')
    search_fields = ('title', 'company', 'description')
    readonly_fields = ('created_at', 'updated_at', 'external_id')
    inlines = [JobMatchInline]
    date_hierarchy = 'posted_date'
    list_per_page = 25


@admin.register(JobMatchResult)
class JobMatchResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'job_title', 'company', 'match_score', 'readiness_days', 'application_status', 'created_at')
    list_filter = ('application_status', 'match_score', 'created_at')
    search_fields = ('student__email', 'job__title', 'job__company')
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('student', 'job')
    
    def job_title(self, obj):
        return obj.job.title
    job_title.short_description = 'Job Title'
    job_title.admin_order_field = 'job__title'
    
    def company(self, obj):
        return obj.job.company
    company.short_description = 'Company'
    company.admin_order_field = 'job__company'


@admin.register(JobSearchQuery)
class JobSearchQueryAdmin(admin.ModelAdmin):
    list_display = ('student', 'search_summary', 'total_results', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('student__email', 'query_params')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    def search_summary(self, obj):
        params = obj.query_params
        return f"{params.get('search_terms', '')} in {params.get('location', '')}"
    search_summary.short_description = 'Search Query'


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'difficulty_level', 'average_learning_hours')
    list_filter = ('category', 'difficulty_level')
    search_fields = ('name', 'category')
    filter_horizontal = ('related_skills',)
    readonly_fields = ('created_at', 'updated_at')
