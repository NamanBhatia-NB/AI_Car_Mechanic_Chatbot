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


class ChatMessageInline(admin.StackedInline):
    model = ChatMessage
    extra = 0
    fields = ('sender', 'content', 'ai_invoked', 'created_at')
    readonly_fields = ('sender', 'content', 'ai_invoked', 'created_at')
    can_delete = False
    show_change_link = True


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = (
        'short_id',
        'client_tag',
        'vehicle_title',
        'stage',
        'message_count',
        'has_diagnosis',
        'created_at',
        'updated_at'
    )
    list_filter = ('stage', 'car_make', 'created_at')
    search_fields = ('id', 'client_id', 'car_make', 'car_model', 'car_year')
    readonly_fields = ('id', 'client_id', 'created_at', 'updated_at')
    inlines = [ChatMessageInline]
    ordering = ('-created_at',)

    def client_tag(self, obj):
        return (obj.client_id[:12] + '...') if len(obj.client_id) > 12 else (obj.client_id or 'Anonymous')
    client_tag.short_description = 'User / Client'

    def short_id(self, obj):
        return str(obj.id)[:8] + '...'
    short_id.short_description = 'Session ID'

    def vehicle_title(self, obj):
        return f"{obj.car_year or ''} {obj.car_make or 'Unspecified'} {obj.car_model or ''}".strip()
    vehicle_title.short_description = 'Vehicle'

    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'

    def has_diagnosis(self, obj):
        return hasattr(obj, 'diagnosis') and obj.diagnosis is not None
    has_diagnosis.boolean = True
    has_diagnosis.short_description = 'Diagnosed?'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'session_link', 'sender', 'short_content', 'ai_invoked', 'created_at')
    list_filter = ('sender', 'ai_invoked', 'created_at')
    search_fields = ('content', 'session__id', 'session__car_make', 'session__car_model')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    def session_link(self, obj):
        return f"{str(obj.session.id)[:8]} ({obj.session.car_make or 'Car'})"
    session_link.short_description = 'Chat Session'

    def short_content(self, obj):
        return (obj.content[:85] + '...') if len(obj.content) > 85 else obj.content
    short_content.short_description = 'Message Content'


@admin.register(MediaAttachment)
class MediaAttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'media_type', 'file_name', 'file_size', 'created_at')
    list_filter = ('media_type',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
