import os
import random
import uuid
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import ChatSession, ChatMessage, MediaAttachment, Diagnosis, Booking
from .serializers import (
    ChatSessionSerializer, ChatMessageSerializer, MediaAttachmentSerializer,
    DiagnosisSerializer, BookingSerializer, ChatRequestSerializer,
    ChatResponseSerializer, MediaUploadSerializer, BookingRequestSerializer
)
from .services.guardrails import GuardrailService
from .services.state_machine import DiagnosticStateMachine
from .services.rule_diagnostics import RuleDiagnosisEngine
from .services.gemini_service import GeminiDiagnosticService


class ChatView(APIView):
    """
    POST /api/chat/
    Core conversational mechanic endpoint. Implements multi-tiered guardrails and state machine
    to ask diagnostic follow-ups and minimize Gemini API token usage.
    """
    parser_classes = [JSONParser]

    @extend_schema(
        request=ChatRequestSerializer,
        responses={200: ChatResponseSerializer},
        description="Interact with the senior mechanic agent. Supports text messages and uploaded media references."
    )
    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        session_id = serializer.validated_data.get('session_id')
        user_text = serializer.validated_data.get('message', '').strip()
        media_ids = serializer.validated_data.get('media_ids', [])

        # 1. Retrieve or create ChatSession
        if session_id:
            try:
                session = ChatSession.objects.get(id=session_id)
            except ChatSession.DoesNotExist:
                session = ChatSession.objects.create(id=session_id)
        else:
            session = ChatSession.objects.create()

        # Link media attachments to session if provided
        media_attachments = []
        if media_ids:
            media_attachments = list(MediaAttachment.objects.filter(id__in=media_ids))
            for media in media_attachments:
                if not media.session:
                    media.session = session
                    media.save()

        # Log User Message
        ChatMessage.objects.create(
            session=session,
            sender='user',
            content=user_text,
            ai_invoked=False
        )

        has_media = len(media_attachments) > 0
        is_active_session = bool(session.car_make or session.messages.filter(sender='user').count() > 1)

        # 2. Tier 0: Guardrail Evaluation (0 AI Cost)
        is_off_topic, canned_reply, quick_replies, intent_type = GuardrailService.check_query(
            user_text, has_media=has_media, is_active_session=is_active_session
        )

        if is_off_topic or canned_reply:
            ChatMessage.objects.create(
                session=session,
                sender='mechanic',
                content=canned_reply,
                ai_invoked=False
            )
            return Response({
                'session_id': session.id,
                'reply': canned_reply,
                'is_off_topic': is_off_topic,
                'intent_type': intent_type,
                'stage': session.stage,
                'diagnosis_ready': False,
                'ai_invoked': False,
                'quick_replies': quick_replies,
                'diagnosis': None
            })

        # 3. Tier 1: State Machine & Slot-Filling (0 AI Cost)
        message_history_count = session.messages.filter(sender='user').count()
        diagnosis_ready, follow_up, quick_replies = DiagnosticStateMachine.evaluate_flow(
            session=session,
            user_message=user_text,
            message_history_count=message_history_count,
            has_media=has_media
        )

        if not diagnosis_ready and follow_up:
            ChatMessage.objects.create(
                session=session,
                sender='mechanic',
                content=follow_up,
                ai_invoked=False
            )
            return Response({
                'session_id': session.id,
                'reply': follow_up,
                'is_off_topic': False,
                'intent_type': 'follow_up',
                'stage': session.stage,
                'diagnosis_ready': False,
                'ai_invoked': False,
                'quick_replies': quick_replies,
                'diagnosis': None
            })

        # 4. Formulate Diagnosis: Tier 2 (Rule Engine) OR Tier 3 (Gemini Multimodal)
        diagnosis_obj = getattr(session, 'diagnosis', None)
        ai_invoked = False

        if not diagnosis_obj:
            # Check conversation text + last user messages for rule match
            all_text = " ".join([m.content for m in session.messages.all()])
            matched_rule = RuleDiagnosisEngine.match_rule(all_text)

            if matched_rule and not has_media:
                # Tier 2: Zero-cost rule match
                diagnosis_obj = Diagnosis.objects.create(
                    session=session,
                    primary_issue=matched_rule['primary_issue'],
                    severity=matched_rule['severity'],
                    confidence_score=matched_rule['confidence_score'],
                    symptoms=matched_rule['symptoms'],
                    possible_causes=matched_rule['possible_causes'],
                    recommended_repairs=matched_rule['recommended_repairs'],
                    estimated_cost_min=matched_rule['cost_min'],
                    estimated_cost_max=matched_rule['cost_max'],
                    diy_friendly=matched_rule['diy_friendly'],
                    summary_notes=matched_rule['summary'],
                    ai_generated=False
                )
                ai_invoked = False
                mechanic_reply = (
                    f"Based on my garage inspection of the symptoms for your {session.car_year or ''} {session.car_make or 'vehicle'} "
                    f"{session.car_model or ''}, I have generated your diagnostic report: **{diagnosis_obj.primary_issue}**. "
                    f"Check out the diagnostic breakdown below. If you'd like to get this fixed, you can book one of our certified mechanics directly!"
                )
            else:
                # Tier 3: Multimodal or complex synthesis via Gemini Flash
                vehicle_str = f"{session.car_year or ''} {session.car_make} {session.car_model} (Mileage: {session.mileage or 'N/A'})".strip()
                conv_history = [{'sender': m.sender, 'text': m.content} for m in session.messages.all()]
                media_summaries = [m.analysis_summary for m in media_attachments if m.analysis_summary]

                ai_diag = GeminiDiagnosticService.generate_complex_diagnosis(
                    vehicle_info=vehicle_str,
                    conversation_history=conv_history,
                    media_summaries=media_summaries
                )

                diagnosis_obj = Diagnosis.objects.create(
                    session=session,
                    primary_issue=ai_diag['primary_issue'],
                    severity=ai_diag.get('severity', 'moderate'),
                    confidence_score=ai_diag.get('confidence_score', 0.85),
                    symptoms=ai_diag.get('symptoms', []),
                    possible_causes=ai_diag.get('possible_causes', []),
                    recommended_repairs=ai_diag.get('recommended_repairs', []),
                    estimated_cost_min=ai_diag.get('cost_min', 100),
                    estimated_cost_max=ai_diag.get('cost_max', 350),
                    diy_friendly=ai_diag.get('diy_friendly', False),
                    summary_notes=ai_diag.get('summary', ''),
                    ai_generated=ai_diag.get('ai_generated', True)
                )
                ai_invoked = ai_diag.get('ai_generated', False)
                mechanic_reply = (
                    f"I have finalized the comprehensive diagnostic inspection for your {vehicle_str or 'vehicle'}: "
                    f"**{diagnosis_obj.primary_issue}** (Urgency: {diagnosis_obj.get_severity_display()}). "
                    f"Review the full report card below and click 'Book Mechanic' to lock in an on-site service appointment."
                )

        else:
            mechanic_reply = (
                f"We previously diagnosed your vehicle with **{diagnosis_obj.primary_issue}**. "
                f"Would you like to proceed with booking a certified technician, or do you have further questions?"
            )

        ChatMessage.objects.create(
            session=session,
            sender='mechanic',
            content=mechanic_reply,
            ai_invoked=ai_invoked
        )

        return Response({
            'session_id': session.id,
            'reply': mechanic_reply,
            'is_off_topic': False,
            'intent_type': 'diagnosis',
            'stage': session.stage,
            'diagnosis_ready': True,
            'ai_invoked': ai_invoked,
            'quick_replies': ["Book Certified Mechanic", "What tools do I need?", "Can I drive it safely?"],
            'diagnosis': DiagnosisSerializer(diagnosis_obj, context={'request': request}).data
        })


class MediaUploadView(APIView):
    """
    POST /api/upload/
    Uploads automotive media (photo of warning light/engine bay, audio of engine rattle, video).
    Validates file formats and generates initial technical observation.
    """
    parser_classes = [MultiPartParser, FormParser]

    ALLOWED_EXTENSIONS = {
        'image': ['.jpg', '.jpeg', '.png', '.webp', '.bmp'],
        'audio': ['.mp3', '.wav', '.m4a', '.aac', '.ogg'],
        'video': ['.mp4', '.mov', '.webm', '.avi', '.mkv']
    }
    MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB

    @extend_schema(
        request=MediaUploadSerializer,
        responses={201: MediaAttachmentSerializer},
        description="Upload an image, audio clip, or video clip for mechanic analysis."
    )
    def post(self, request):
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response({'error': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate file size
        if uploaded_file.size > self.MAX_FILE_SIZE:
            return Response({'error': 'File exceeds maximum limit of 25MB.'}, status=status.HTTP_400_BAD_REQUEST)

        # Determine media type by extension
        _, ext = os.path.splitext(uploaded_file.name.lower())
        media_type = 'other'
        for m_type, extensions in self.ALLOWED_EXTENSIONS.items():
            if ext in extensions:
                media_type = m_type
                break

        if media_type == 'other':
            return Response({
                'error': f"Unsupported file format '{ext}'. Supported: JPG, PNG, MP3, WAV, M4A, MP4, MOV, WEBM."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Session linking (optional)
        session_id = request.data.get('session_id')
        session = None
        if session_id:
            try:
                session = ChatSession.objects.get(id=session_id)
            except ChatSession.DoesNotExist:
                session = ChatSession.objects.create(id=session_id)

        # Save record
        attachment = MediaAttachment.objects.create(
            session=session,
            file=uploaded_file,
            media_type=media_type,
            file_name=uploaded_file.name,
            file_size=uploaded_file.size
        )

        # Run AI media analysis
        try:
            analysis_summary = GeminiDiagnosticService.analyze_media(
                file_path=attachment.file.path,
                media_type=media_type,
                user_prompt=request.data.get('notes', '')
            )
            attachment.analysis_summary = analysis_summary
            attachment.save()
        except Exception as e:
            attachment.analysis_summary = f"[Analysis]: File uploaded successfully ({media_type})."
            attachment.save()

        return Response(
            MediaAttachmentSerializer(attachment, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )


class DiagnosisView(APIView):
    """
    POST /api/diagnosis/
    Retrieves or generates a formal diagnosis report for a session.
    """
    @extend_schema(
        request=ChatRequestSerializer,
        responses={200: DiagnosisSerializer},
        description="Fetch or trigger comprehensive diagnostic assessment for a session."
    )
    def post(self, request):
        session_id = request.data.get('session_id')
        if not session_id:
            return Response({'error': 'session_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        session = get_object_or_404(ChatSession, id=session_id)
        diagnosis = getattr(session, 'diagnosis', None)

        if not diagnosis:
            # Force generate diagnosis from existing messages
            all_text = " ".join([m.content for m in session.messages.all()])
            matched_rule = RuleDiagnosisEngine.match_rule(all_text)

            if matched_rule:
                diagnosis = Diagnosis.objects.create(
                    session=session,
                    primary_issue=matched_rule['primary_issue'],
                    severity=matched_rule['severity'],
                    confidence_score=matched_rule['confidence_score'],
                    symptoms=matched_rule['symptoms'],
                    possible_causes=matched_rule['possible_causes'],
                    recommended_repairs=matched_rule['recommended_repairs'],
                    estimated_cost_min=matched_rule['cost_min'],
                    estimated_cost_max=matched_rule['cost_max'],
                    diy_friendly=matched_rule['diy_friendly'],
                    summary_notes=matched_rule['summary'],
                    ai_generated=False
                )
            else:
                vehicle_str = f"{session.car_year or ''} {session.car_make} {session.car_model}".strip()
                conv_history = [{'sender': m.sender, 'text': m.content} for m in session.messages.all()]
                ai_diag = GeminiDiagnosticService.generate_complex_diagnosis(
                    vehicle_info=vehicle_str,
                    conversation_history=conv_history,
                    media_summaries=[]
                )
                diagnosis = Diagnosis.objects.create(
                    session=session,
                    primary_issue=ai_diag['primary_issue'],
                    severity=ai_diag.get('severity', 'moderate'),
                    confidence_score=ai_diag.get('confidence_score', 0.85),
                    symptoms=ai_diag.get('symptoms', []),
                    possible_causes=ai_diag.get('possible_causes', []),
                    recommended_repairs=ai_diag.get('recommended_repairs', []),
                    estimated_cost_min=ai_diag.get('cost_min', 100),
                    estimated_cost_max=ai_diag.get('cost_max', 350),
                    diy_friendly=ai_diag.get('diy_friendly', False),
                    summary_notes=ai_diag.get('summary', ''),
                    ai_generated=ai_diag.get('ai_generated', True)
                )

        return Response(DiagnosisSerializer(diagnosis, context={'request': request}).data)


class BookingView(APIView):
    """
    POST /api/booking/ - Create a certified mechanic appointment.
    GET /api/booking/{id}/ - Retrieve appointment status and assignment.
    """
    @extend_schema(
        request=BookingRequestSerializer,
        responses={201: BookingSerializer},
        description="Book a mechanic service appointment after receiving a diagnosis."
    )
    def post(self, request):
        serializer = BookingRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        diagnosis_id = serializer.validated_data['diagnosis_id']
        diagnosis = get_object_or_404(Diagnosis, id=diagnosis_id)

        # Generate unique human-readable booking reference
        ref_code = f"MECH-{random.randint(10000, 99999)}"
        while Booking.objects.filter(booking_reference=ref_code).exists():
            ref_code = f"MECH-{random.randint(10000, 99999)}"

        booking = Booking.objects.create(
            booking_reference=ref_code,
            diagnosis=diagnosis,
            customer_name=serializer.validated_data['customer_name'],
            customer_email=serializer.validated_data['customer_email'],
            customer_phone=serializer.validated_data['customer_phone'],
            scheduled_date=serializer.validated_data['scheduled_date'],
            scheduled_time=serializer.validated_data['scheduled_time'],
            service_type=serializer.validated_data.get('service_type', 'Mobile Mechanic On-Site'),
            notes=serializer.validated_data.get('notes', ''),
            status='confirmed'
        )

        # Update session stage
        if diagnosis.session:
            diagnosis.session.stage = 'booked'
            diagnosis.session.save()

        return Response(
            BookingSerializer(booking, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )


class BookingDetailView(APIView):
    """
    GET /api/booking/{id}/
    Accepts numeric primary key OR alphanumeric booking_reference (e.g. MECH-84920).
    """
    @extend_schema(
        responses={200: BookingSerializer},
        description="Retrieve booking details by integer ID or booking reference code."
    )
    def get(self, request, pk):
        if pk.isdigit():
            booking = get_object_or_404(Booking, id=int(pk))
        else:
            booking = get_object_or_404(Booking, booking_reference__iexact=pk)

        return Response(BookingSerializer(booking, context={'request': request}).data)


class SessionHistoryView(APIView):
    """
    GET /api/chat/history/{session_id}/
    Retrieves full transcript and state for a session.
    """
    def get(self, request, session_id):
        session = get_object_or_404(ChatSession, id=session_id)
        return Response(ChatSessionSerializer(session, context={'request': request}).data)


class HealthCheckView(APIView):
    """
    GET /api/health/
    System health status for hosting platforms (Render / Modal / Koyeb).
    """
    def get(self, request):
        return Response({
            'status': 'healthy',
            'service': 'Instant Mechanic Backend API',
            'version': '1.0.0',
            'gemini_configured': GeminiDiagnosticService.is_configured()
        })
