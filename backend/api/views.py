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

    def get(self, request):
        return Response({
            'message': 'Instant Mechanic Chat Endpoint. Send a POST request with {"message": "symptom"} to interact with the mechanic.',
            'method': 'POST',
            'interactive_docs': request.build_absolute_uri('/api/docs/')
        })

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
                    estimated_cost_min=ai_diag.get('cost_min', Decimal('2499.00')),
                    estimated_cost_max=ai_diag.get('cost_max', Decimal('2499.00')),
                    diy_friendly=ai_diag.get('diy_friendly', False),
                    summary_notes=ai_diag.get('summary', ''),
                    ai_generated=ai_diag.get('ai_generated', True)
                )
                ai_invoked = ai_diag.get('ai_generated', False)
                mechanic_reply = (
                    f"I have finalized the comprehensive diagnostic inspection for your {vehicle_str or 'vehicle'}: "
                    f"**{diagnosis_obj.primary_issue}** (Urgency: {diagnosis_obj.get_severity_display()}). "
                    f"All standard on-site repair packages are covered under our flat rate of **₹2,499**. "
                    f"Review the full report card below and click 'Book Mechanic' to lock in an on-site service appointment."
                )

        else:
            clean_msg = user_text.lower()
            new_rule_match = RuleDiagnosisEngine.match_rule(user_text)

            # 1. User reports a new mechanical fault or asks about another component (e.g. carburetor, brakes)
            if new_rule_match and new_rule_match['primary_issue'] != diagnosis_obj.primary_issue:
                diagnosis_obj.primary_issue = new_rule_match['primary_issue']
                diagnosis_obj.severity = new_rule_match['severity']
                diagnosis_obj.confidence_score = new_rule_match['confidence_score']
                diagnosis_obj.symptoms = new_rule_match['symptoms']
                diagnosis_obj.possible_causes = new_rule_match['possible_causes']
                diagnosis_obj.recommended_repairs = new_rule_match['recommended_repairs']
                diagnosis_obj.estimated_cost_min = new_rule_match['cost_min']
                diagnosis_obj.estimated_cost_max = new_rule_match['cost_max']
                diagnosis_obj.diy_friendly = new_rule_match['diy_friendly']
                diagnosis_obj.summary_notes = new_rule_match['summary']
                diagnosis_obj.ai_generated = False
                diagnosis_obj.save()

                mechanic_reply = (
                    f"Understood! Shifting diagnostic focus to your **{diagnosis_obj.primary_issue}**:\n\n"
                    f"{new_rule_match['summary']}\n\n"
                    f"Our certified mobile mechanics handle this complete diagnostic and repair package for our standard flat rate of **₹2,499**. "
                    f"Review the updated diagnostic card below or book an on-site service appointment!"
                )
                ai_invoked = False
                quick_replies = ["Book Certified Mechanic", "What tools do I need?", "Can I drive it safely?"]

            # 2. Driving safety inquiry
            elif any(s in clean_msg for s in ['safe to drive', 'drive safely', 'can i drive', 'can it drive', 'safe to continue', 'dangerous']):
                if diagnosis_obj.severity == 'critical':
                    mechanic_reply = (
                        f"⚠️ **Critical Safety Warning**: No, it is **not safe to drive** with **{diagnosis_obj.primary_issue}**. "
                        f"Continuing to run the vehicle risks catastrophic engine damage or complete loss of braking/steering control. "
                        f"Pull over safely and book our mobile mechanic or have the vehicle towed to a garage."
                    )
                else:
                    mechanic_reply = (
                        f"**Driving Safety Assessment**: For **{diagnosis_obj.primary_issue}**, you may cautiously drive short distances "
                        f"(e.g., straight to a repair facility or home), but avoid highway speeds or heavy acceleration. "
                        f"If you notice warning lights flashing or sudden loss of response, pull over immediately. "
                        f"You can book our certified technician for our standard ₹2,499 flat package below."
                    )
                ai_invoked = False
                quick_replies = ["Book Certified Mechanic", "What tools do I need?", "Ask about another symptom"]

            # 3. Tools / Equipment inquiry
            elif any(t in clean_msg for t in ['what tools', 'tools do i need', 'tools required', 'which tools', 'equipment', 'what tools are needed']):
                issue_lower = diagnosis_obj.primary_issue.lower()
                if 'battery' in issue_lower:
                    mechanic_reply = (
                        "For inspecting and servicing the battery/starter connections on your vehicle, you will need:\n"
                        "1. **10mm and 8mm socket/box wrenches** (for terminal clamp bolts and battery hold-down)\n"
                        "2. **Wire terminal cleaner brush & baking soda water** (to dissolve acidic corrosion crust)\n"
                        "3. **Digital Multimeter** (DC 20V setting; fully charged resting battery should read ≥ 12.6V)\n"
                        "4. **Nitrile mechanic gloves & eye protection** (to safeguard against sulfuric acid)\n"
                        "5. **Heavy-duty booster cables or jump pack**\n\n"
                        "If you prefer an expert to handle it with full diagnostic instruments, our certified mobile technician arrives on-site for our flat ₹2,499 rate."
                    )
                elif 'carburetor' in issue_lower or 'carburetor' in clean_msg or 'carb' in clean_msg:
                    mechanic_reply = (
                        "For inspecting and servicing the carburetor, you will need:\n"
                        "1. **Flathead & Phillips screwdrivers** (for idle mixture, throttle stop screws, and bowl fasteners)\n"
                        "2. **Aerosol Carburetor & Choke Cleaner** (to dissolve fuel varnish and carbon deposits)\n"
                        "3. **Can of compressed air or fine jet cleaning wire (.015\")** (to clear clogged brass orifices)\n"
                        "4. **Replacement bowl gasket and float needle valve**\n"
                        "5. **Clean lint-free shop towels & fuel catch container**\n\n"
                        "Our mobile technicians can also perform a complete ultrasonic clean and tune for our standard ₹2,499 flat package."
                    )
                elif 'brake' in issue_lower:
                    mechanic_reply = (
                        "For servicing the brake pads and rotors, you will need:\n"
                        "1. **Hydraulic floor jack and two rated jack stands** (never work under a car supported solely by a jack)\n"
                        "2. **Lug wrench / breaker bar & socket** (19mm or 21mm for wheel lugs)\n"
                        "3. **14mm / 17mm combination wrenches or ratchet sockets** (for caliper slide pin bolts)\n"
                        "4. **C-clamp or disc brake piston compressor** (to retract caliper piston)\n"
                        "5. **Aerosol brake parts cleaner, wire brush, and synthetic brake grease**\n\n"
                        "Our mobile technicians arrive on-site with all professional brake tools for our flat ₹2,499 rate."
                    )
                else:
                    mechanic_reply = (
                        f"For addressing **{diagnosis_obj.primary_issue}**, standard garage tools required include:\n"
                        "1. **Complete metric socket set (8mm - 19mm) and ratchet extensions**\n"
                        "2. **OBD-II live data scanner** (to clear and verify trouble codes)\n"
                        "3. **Floor jack, jack stands, and wheel chocks**\n"
                        "4. **Protective safety glasses and mechanic gloves**\n\n"
                        "Our certified mobile mechanics bring all specialized diagnostic tools directly to your driveway for our standard ₹2,499 package."
                    )
                ai_invoked = False
                quick_replies = ["Book Certified Mechanic", "Can I drive it safely?", "Ask another question"]

            # 4. DIY / "How to fix" procedure
            elif any(h in clean_msg for h in ['how to fix', 'how do i fix', 'how to repair', 'diy steps', 'steps to fix', 'can i fix it']):
                issue_lower = diagnosis_obj.primary_issue.lower()
                if 'battery' in issue_lower:
                    mechanic_reply = (
                        "Here is the senior technician step-by-step procedure to fix battery/starter issues:\n"
                        "1. **Safety First**: Turn off ignition and remove keys. Put on safety glasses and gloves.\n"
                        "2. **Disconnect Terminals**: Loosen the negative (-) black cable first, then positive (+) red cable.\n"
                        "3. **Clean Corrosion**: Scrub posts and cable clamps with baking soda solution and a wire brush until bright metal is exposed.\n"
                        "4. **Check Voltage**: Measure with a multimeter. If below 12.2V, charge the battery or attempt a jump start.\n"
                        "5. **Reconnect & Tighten**: Connect positive (+) first, then negative (-). Coat with dielectric grease to prevent future corrosion.\n\n"
                        "Need a certified technician to test your charging system on-site? Book our flat ₹2,499 package below."
                    )
                elif 'carburetor' in issue_lower or 'carb' in clean_msg or 'carburetor' in clean_msg or 'carebeaurator' in clean_msg:
                    mechanic_reply = (
                        "Here is the senior technician step-by-step procedure to service and tune a carburetor:\n"
                        "1. **Inspect Fuel Delivery**: Remove the air filter assembly. Verify fuel is reaching the bowl and the choke plate moves freely.\n"
                        "2. **Clean Throat & Jets**: Spray carburetor cleaner into the throat while cranking, and clear the idle air bleed holes.\n"
                        "3. **Float & Needle**: If fuel overflows, the float needle is stuck. Drop the float bowl, clean the needle seat, and check float height.\n"
                        "4. **Tune Mixture Screws**: Gently seat the idle mixture screw, then back it out 1.5 to 2 full turns to factory baseline, fine-tuning for smoothest idle.\n\n"
                        "Our certified mechanics can also rebuild and tune it at your location for our standard flat ₹2,499 package."
                    )
                elif 'brake' in issue_lower:
                    mechanic_reply = (
                        "Here is the technician procedure for brake service:\n"
                        "1. **Lift & Secure**: Loosen lug nuts, jack up the vehicle, and rest securely on jack stands.\n"
                        "2. **Remove Caliper**: Unbolt caliper slide pins and suspend the caliper with a wire hook (never hang by rubber hose).\n"
                        "3. **Replace Pads**: Slide out old worn pads, lubricate slide pins with silicone brake grease, and compress caliper piston.\n"
                        "4. **Inspect Rotors**: Check rotor surface for deep scoring or grooves. Resurface or replace if below discard thickness.\n"
                        "5. **Pump Pedal**: Before driving, pump the brake pedal 4-5 times to reseat the pads against the rotor.\n\n"
                        "Our mobile mechanics can replace your brake pads at your doorstep for our flat ₹2,499 rate."
                    )
                else:
                    mechanic_reply = (
                        f"Here is the technician roadmap to address **{diagnosis_obj.primary_issue}**:\n"
                        f"1. **Inspection**: Perform diagnostic checks on {', '.join(diagnosis_obj.symptoms[:2]) if diagnosis_obj.symptoms else 'the reported symptoms'}.\n"
                        f"2. **Component Service**: Follow recommended repairs: {', '.join(diagnosis_obj.recommended_repairs[:2]) if diagnosis_obj.recommended_repairs else 'inspect primary components'}.\n"
                        f"3. **Verification**: Clear any fault codes and test drive to ensure normal operation.\n\n"
                        f"You can also book an on-site master mechanic for our standard ₹2,499 package."
                    )
                ai_invoked = False
                quick_replies = ["Book Certified Mechanic", "What tools do I need?", "Can I drive it safely?"]

            # 5. Pricing or booking question
            elif any(b in clean_msg for b in ['book', 'schedule', 'price', 'cost', 'rate', 'how much', 'appointment', 'fee']):
                mechanic_reply = (
                    f"All certified mobile mechanic services for **{diagnosis_obj.primary_issue}** are covered under our transparent "
                    f"flat rate of **₹2,499** (includes complete on-site inspection, diagnostics, and standard labor). "
                    f"Click **'Book Certified Mechanic'** below to choose your preferred date, time, and service location!"
                )
                ai_invoked = False
                quick_replies = ["Book Certified Mechanic", "What tools do I need?", "Can I drive it safely?"]

            # 6. Fallback general technician prompt
            else:
                mechanic_reply = (
                    f"Regarding your vehicle and the **{diagnosis_obj.primary_issue}** diagnosis: "
                    f"Would you like me to walk through the DIY repair steps, review the tools you'll need, "
                    f"check driving safety, or schedule a certified mobile mechanic for our flat ₹2,499 service?"
                )
                ai_invoked = False
                quick_replies = ["Book Certified Mechanic", "What tools do I need?", "Can I drive it safely?"]

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
                    estimated_cost_min=ai_diag.get('cost_min', Decimal('2499.00')),
                    estimated_cost_max=ai_diag.get('cost_max', Decimal('2499.00')),
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
    def get(self, request):
        return Response({
            'message': 'Instant Mechanic Booking Endpoint. Send a POST request to book a technician, or GET /api/booking/<id_or_ref>/ to track an existing booking.',
            'method': 'POST',
            'interactive_docs': request.build_absolute_uri('/api/docs/')
        })

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


class APIRootView(APIView):
    """
    GET /api/
    Interactive API root overview and sitemap.
    """
    def get(self, request):
        base_url = request.build_absolute_uri('/api/')
        return Response({
            'service': 'Instant Mechanic AI Diagnostic & Booking REST API',
            'version': '1.0.0',
            'status': 'online',
            'gemini_configured': GeminiDiagnosticService.is_configured(),
            'documentation_swagger': request.build_absolute_uri('/api/docs/'),
            'schema_openapi': request.build_absolute_uri('/api/schema/'),
            'endpoints': {
                'chat': f'{base_url}chat/',
                'upload': f'{base_url}upload/',
                'diagnosis': f'{base_url}diagnosis/',
                'booking': f'{base_url}booking/',
                'booking_detail': f'{base_url}booking/<id_or_reference>/',
                'chat_history': f'{base_url}chat/history/<session_id>/',
                'health': f'{base_url}health/'
            }
        })

