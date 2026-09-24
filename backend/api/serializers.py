import uuid
from rest_framework import serializers
from .models import ChatSession, ChatMessage, MediaAttachment, Diagnosis, Booking


class MediaAttachmentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = MediaAttachment
        fields = [
            'id', 'session', 'file', 'file_url', 'media_type',
            'file_name', 'file_size', 'analysis_summary', 'created_at'
        ]
        read_only_fields = ['id', 'file_url', 'created_at', 'analysis_summary']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and hasattr(obj.file, 'url'):
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'session', 'sender', 'content', 'ai_invoked', 'created_at']
        read_only_fields = ['id', 'created_at']


class DiagnosisSerializer(serializers.ModelSerializer):
    vehicle_summary = serializers.SerializerMethodField()

    class Meta:
        model = Diagnosis
        fields = [
            'id', 'session', 'primary_issue', 'severity', 'confidence_score',
            'symptoms', 'possible_causes', 'recommended_repairs',
            'estimated_cost_min', 'estimated_cost_max', 'diy_friendly',
            'summary_notes', 'ai_generated', 'vehicle_summary', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_vehicle_summary(self, obj):
        if obj.session:
            return f"{obj.session.car_year or ''} {obj.session.car_make} {obj.session.car_model}".strip() or "Unspecified Vehicle"
        return "Unknown Vehicle"


class BookingSerializer(serializers.ModelSerializer):
    diagnosis_details = DiagnosisSerializer(source='diagnosis', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'booking_reference', 'diagnosis', 'diagnosis_details',
            'customer_name', 'customer_email', 'customer_phone',
            'scheduled_date', 'scheduled_time', 'service_type',
            'mechanic_name', 'status', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'booking_reference', 'status', 'created_at']


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = serializers.SerializerMethodField()
    media_attachments = MediaAttachmentSerializer(many=True, read_only=True)
    diagnosis = DiagnosisSerializer(read_only=True)

    class Meta:
        model = ChatSession
        fields = [
            'id', 'client_id', 'car_make', 'car_model', 'car_year', 'mileage',
            'stage', 'created_at', 'updated_at', 'messages',
            'media_attachments', 'diagnosis'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_messages(self, obj):
        msgs = list(obj.messages.all().order_by('created_at'))
        has_welcome = any(m.sender == 'mechanic' and "Marcus Vance" in m.content for m in msgs)
        serialized = ChatMessageSerializer(msgs, many=True, context=self.context).data
        if not has_welcome:
            welcome_msg = {
                'id': f"welcome-{obj.id}",
                'session': str(obj.id),
                'sender': 'mechanic',
                'content': (
                    "Hey friend, I'm Marcus Vance, Senior Automotive Diagnostic Technician with 25+ years in the bay. "
                    "I'm here to help you troubleshoot strange noises, warning lights, fluid leaks, or starting issues. "
                    "What vehicle are you driving, and what's going on under the hood?"
                ),
                'ai_invoked': False,
                'created_at': obj.created_at.isoformat() if obj.created_at else None,
            }
            return [welcome_msg] + serialized
        return serialized


# Input serializers for clean validation and Swagger OpenAPI docs
class ChatRequestSerializer(serializers.Serializer):
    session_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    client_id = serializers.CharField(required=False, allow_blank=True, default='')
    message = serializers.CharField(required=True, allow_blank=False)
    media_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list
    )


class ChatResponseSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    reply = serializers.CharField()
    is_off_topic = serializers.BooleanField()
    intent_type = serializers.CharField()
    stage = serializers.CharField()
    diagnosis_ready = serializers.BooleanField()
    ai_invoked = serializers.BooleanField()
    quick_replies = serializers.ListField(child=serializers.CharField())
    diagnosis = DiagnosisSerializer(required=False, allow_null=True)


class MediaUploadSerializer(serializers.Serializer):
    session_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    file = serializers.FileField(required=True)


class BookingRequestSerializer(serializers.Serializer):
    diagnosis_id = serializers.IntegerField(required=True)
    customer_name = serializers.CharField(max_length=150, required=True)
    customer_email = serializers.EmailField(required=True)
    customer_phone = serializers.CharField(max_length=30, required=True)
    scheduled_date = serializers.DateField(required=True)
    scheduled_time = serializers.TimeField(required=True)
    service_type = serializers.CharField(max_length=100, default='Mobile Mechanic On-Site')
    notes = serializers.CharField(required=False, allow_blank=True, default='')
