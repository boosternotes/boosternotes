from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'link', 'sent_at', 'created_at']
    list_filter = ['sent_at', 'created_at']
    search_fields = ['title', 'message']
    readonly_fields = ['sent_at', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'message', 'link')
        }),
        ('Metadata', {
            'fields': ('sent_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )




