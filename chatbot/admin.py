from django.contrib import admin
from .models import ChatMessage, ChatContext


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'module_id', 'message', 'timestamp')
    list_filter = ('module_id', 'user', 'timestamp')
    search_fields = ('message', 'response')
    date_hierarchy = 'timestamp'

@admin.register(ChatContext)
class ChatContextAdmin(admin.ModelAdmin):
    list_display = ('user', 'module_id', 'last_updated')
    list_filter = ('module_id', 'user')


