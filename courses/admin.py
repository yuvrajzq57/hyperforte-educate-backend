from django.contrib import admin
from .models import Course, Module, Section, Quiz, Question, QuestionOption

class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 1
    ordering = ['order_number']

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    ordering = ['order_number']
    show_change_link = True

class SectionInline(admin.TabularInline):
    model = Section
    extra = 1
    ordering = ['order_number']
    show_change_link = True

class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1
    ordering = ['order_number']
    show_change_link = True

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'level', 'estimated_duration', 'created_at')
    list_filter = ('level', 'created_at')
    search_fields = ('title', 'description')
    inlines = [ModuleInline]

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order_number')
    list_filter = ('course',)
    search_fields = ('title', 'description')
    inlines = [SectionInline]

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'content_type', 'order_number')
    list_filter = ('content_type', 'module__course')
    search_fields = ('title', 'content', 'summary')

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'passing_score')
    inlines = [QuestionInline]

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'quiz', 'order_number')
    list_filter = ('quiz',)
    inlines = [QuestionOptionInline]
    search_fields = ('question_text',)

@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = ('option_text', 'question', 'is_correct', 'order_number')
    list_filter = ('is_correct', 'question__quiz')
    search_fields = ('option_text',)
