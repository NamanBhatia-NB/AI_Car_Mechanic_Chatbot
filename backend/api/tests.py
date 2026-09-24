import io
from PIL import Image
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from .models import ChatSession, ChatMessage, Diagnosis, Booking, MediaAttachment


class InstantMechanicAPITests(APITestCase):

    def setUp(self):
        self.session = ChatSession.objects.create(
            car_make='Honda',
            car_model='Civic',
            car_year=2018
        )

    def test_health_check(self):
        """Test GET /api/health/ returns healthy status."""
        url = reverse('api-health')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'healthy')

    def test_guardrails_reject_off_topic(self):
        """Test Tier 0 Guardrail rejects non-automotive queries at zero AI cost."""
        url = reverse('api-chat')
        payload = {
            'session_id': str(self.session.id),
            'message': 'Write me an essay about the Roman Empire.'
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_off_topic'])
        self.assertFalse(response.data['ai_invoked'])
        self.assertIn("technician", response.data['reply'].lower())

    def test_greeting_immediate_canned_reply(self):
        """Test standard greetings are answered deterministically with 0 AI cost."""
        url = reverse('api-chat')
        payload = {
            'session_id': str(self.session.id),
            'message': 'Hello there!'
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_off_topic'])
        self.assertFalse(response.data['ai_invoked'])
        self.assertEqual(response.data['intent_type'], 'greeting')

    def test_state_machine_slot_filling(self):
        """Test Tier 1 prompts user for missing car make/model/year on first symptom."""
        new_session = ChatSession.objects.create()  # Empty vehicle info
        url = reverse('api-chat')
        payload = {
            'session_id': str(new_session.id),
            'message': 'My car has a strange vibration.'
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['ai_invoked'])
        self.assertFalse(response.data['diagnosis_ready'])
        self.assertIn("Year, Make, and Model", response.data['reply'])

    def test_rule_diagnosis_zero_cost(self):
        """Test Tier 2 rule engine matches classic battery dead / clicking sound deterministically."""
        url = reverse('api-chat')
        # Provide full context in message
        payload = {
            'session_id': str(self.session.id),
            'message': 'My 2018 Honda Civic makes a rapid clicking sound when turning key and won\'t turn over, dim lights.'
        }
        # First query triggers info gathering or diagnosis
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Request direct diagnosis
        payload_diag = {
            'session_id': str(self.session.id),
            'message': 'Give me diagnosis now please'
        }
        res_diag = self.client.post(url, payload_diag, format='json')
        self.assertEqual(res_diag.status_code, status.HTTP_200_OK)
        self.assertTrue(res_diag.data['diagnosis_ready'])
        self.assertIsNotNone(res_diag.data['diagnosis'])
        self.assertIn("Battery", res_diag.data['diagnosis']['primary_issue'])
        self.assertFalse(res_diag.data['ai_invoked'])  # 0 AI cost!

    def test_media_upload_and_validation(self):
        """Test POST /api/upload/ with valid image and invalid extension."""
        url = reverse('api-upload')

        # 1. Valid image upload
        image_io = io.BytesIO()
        image = Image.new('RGB', (100, 100), color='red')
        image.save(image_io, format='JPEG')
        image_file = SimpleUploadedFile("brake_pad.jpg", image_io.getvalue(), content_type="image/jpeg")

        response = self.client.post(url, {'file': image_file, 'session_id': str(self.session.id)}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['media_type'], 'image')
        self.assertIn('analysis_summary', response.data)

        # 2. Invalid extension upload (e.g. .exe)
        invalid_file = SimpleUploadedFile("script.exe", b"binarycontent", content_type="application/octet-stream")
        res_invalid = self.client.post(url, {'file': invalid_file}, format='multipart')
        self.assertEqual(res_invalid.status_code, status.HTTP_400_BAD_REQUEST)

    def test_booking_creation_and_retrieval(self):
        """Test POST /api/booking/ and GET /api/booking/{id}/."""
        # Create a diagnosis first
        diagnosis = Diagnosis.objects.create(
            session=self.session,
            primary_issue='Worn Brake Pads',
            severity='moderate',
            confidence_score=0.9,
            symptoms=['Squealing when braking'],
            possible_causes=['Brake pads at 2mm'],
            recommended_repairs=['Front brake pad replacement'],
            estimated_cost_min=180.00,
            estimated_cost_max=320.00,
            diy_friendly=False
        )

        booking_url = reverse('api-booking')
        payload = {
            'diagnosis_id': diagnosis.id,
            'customer_name': 'Alex Parker',
            'customer_email': 'alex@example.com',
            'customer_phone': '+1-555-019-2834',
            'scheduled_date': '2026-10-05',
            'scheduled_time': '10:00:00',
            'service_type': 'Mobile Mechanic On-Site',
            'notes': 'Car parked in driveway.'
        }
        res_book = self.client.post(booking_url, payload, format='json')
        self.assertEqual(res_book.status_code, status.HTTP_201_CREATED)
        self.assertIn('booking_reference', res_book.data)
        booking_ref = res_book.data['booking_reference']
        booking_id = res_book.data['id']

        # Retrieve by numeric ID
        detail_url_id = reverse('api-booking-detail', kwargs={'pk': str(booking_id)})
        res_get_id = self.client.get(detail_url_id)
        self.assertEqual(res_get_id.status_code, status.HTTP_200_OK)
        self.assertEqual(res_get_id.data['customer_name'], 'Alex Parker')

        # Retrieve by booking_reference code (e.g. MECH-12345)
        detail_url_ref = reverse('api-booking-detail', kwargs={'pk': booking_ref})
        res_get_ref = self.client.get(detail_url_ref)
        self.assertEqual(res_get_ref.status_code, status.HTTP_200_OK)
        self.assertEqual(res_get_ref.data['booking_reference'], booking_ref)
