from django.contrib import admin
from .models import ChatSession, ChatMessage, MediaAttachment, Diagnosis, Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'booking_reference',
        'customer_name',
        'customer_phone',
        'customer_email',
        'scheduled_date',
        'scheduled_time',
        'service_type',
        'status',
        'created_at'
    )
    list_filter = ('status', 'service_type', 'scheduled_date')
    search_fields = ('booking_reference', 'customer_name', 'customer_email', 'customer_phone', 'notes')
    readonly_fields = ('booking_reference', 'created_at')
    ordering = ('-created_at',)


@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'primary_issue',
        'severity',
        'estimated_cost_min',
        'estimated_cost_max',
        'diy_friendly',
        'ai_generated',
        'created_at'
    )
    list_filter = ('severity', 'ai_generated', 'diy_friendly')
    search_fields = ('primary_issue', 'summary_notes')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'car_year', 'car_make', 'car_model', 'stage', 'created_at', 'updated_at')
    list_filter = ('stage', 'car_make')
    search_fields = ('car_make', 'car_model')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'sender', 'short_content', 'ai_invoked', 'created_at')
    list_filter = ('sender', 'ai_invoked')
    search_fields = ('content',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    def short_content(self, obj):
        return (obj.content[:75] + '...') if len(obj.content) > 75 else obj.content
    short_content.short_description = 'Message Content'


@admin.register(MediaAttachment)
class MediaAttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'media_type', 'file_name', 'file_size', 'created_at')
    list_filter = ('media_type',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
