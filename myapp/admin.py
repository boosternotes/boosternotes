from django.contrib import admin
from .models import *


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


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'amount', 'expiry_date', 'usage_limit', 'times_used', 'remaining_uses', 'is_active', 'created_at']
    list_filter = ['is_active', 'expiry_date', 'created_at']
    search_fields = ['code']
    readonly_fields = ['times_used', 'is_active', 'created_at']
    ordering = ['-created_at']

    def remaining_uses(self, obj):
        return obj.remaining_uses
    remaining_uses.short_description = "Remaining Uses"


admin.site.register(HardBook)
admin.site.register(HardBookImage)
admin.site.register(SiteSetting)
admin.site.register(NavbarSetting)
admin.site.register(BannerSetting)
admin.site.register(StatsSetting)
admin.site.register(AboutSetting)
admin.site.register(FooterSetting)
admin.site.register(Category)
admin.site.register(ELibraryModel)
admin.site.register(ELibraryPDF)