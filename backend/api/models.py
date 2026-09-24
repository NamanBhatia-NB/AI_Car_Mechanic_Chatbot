import uuid
from django.db import models


class ChatSession(models.Model):
    STAGE_CHOICES = [
        ('initial', 'Initial Inquiry'),
        ('gathering_info', 'Gathering Vehicle Details'),
        ('diagnosed', 'Diagnosis Complete'),
        ('booking_pending', 'Booking in Progress'),
        ('booked', 'Appointment Booked'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    car_make = models.CharField(max_length=100, blank=True, default='')
    car_model = models.CharField(max_length=100, blank=True, default='')
    car_year = models.IntegerField(null=True, blank=True)
    mileage = models.IntegerField(null=True, blank=True)
    stage = models.CharField(max_length=50, choices=STAGE_CHOICES, default='initial')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        vehicle = f"{self.car_year or ''} {self.car_make} {self.car_model}".strip() or "Unknown Vehicle"
        return f"Session {str(self.id)[:8]} ({vehicle})"


class ChatMessage(models.Model):
    SENDER_CHOICES = [
        ('user', 'User'),
        ('mechanic', 'Senior Mechanic'),
        ('system', 'System'),
    ]

    session = models.ForeignKey(ChatSession, related_name='messages', on_delete=models.CASCADE)
    sender = models.CharField(max_length=20, choices=SENDER_CHOICES)
    content = models.TextField()
    ai_invoked = models.BooleanField(default=False, help_text="True if response consumed Gemini API tokens")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.sender}] {self.content[:40]}"


class MediaAttachment(models.Model):
    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('audio', 'Audio'),
        ('video', 'Video'),
        ('other', 'Other'),
    ]

    session = models.ForeignKey(ChatSession, null=True, blank=True, related_name='media_attachments', on_delete=models.SET_NULL)
    file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPE_CHOICES)
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.IntegerField(default=0)
    analysis_summary = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.media_type}: {self.file_name or self.file.name}"


class Diagnosis(models.Model):
    SEVERITY_CHOICES = [
        ('low', 'Low - Safe to drive temporarily'),
        ('moderate', 'Moderate - Schedule service soon'),
        ('critical', 'Critical - Do NOT drive, towing recommended'),
    ]

    session = models.OneToOneField(ChatSession, related_name='diagnosis', on_delete=models.CASCADE)
    primary_issue = models.CharField(max_length=255)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='moderate')
    confidence_score = models.FloatField(default=0.85)
    symptoms = models.JSONField(default=list, help_text="List of identified symptoms")
    possible_causes = models.JSONField(default=list, help_text="List of probable root causes")
    recommended_repairs = models.JSONField(default=list, help_text="List of actionable repairs or parts")
    estimated_cost_min = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    estimated_cost_max = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    diy_friendly = models.BooleanField(default=False)
    summary_notes = models.TextField(blank=True)
    ai_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Diagnosis ({self.severity}): {self.primary_issue}"


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Confirmation'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    booking_reference = models.CharField(max_length=32, unique=True)
    diagnosis = models.ForeignKey(Diagnosis, related_name='bookings', on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=150)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=30)
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    service_type = models.CharField(max_length=100, default='Mobile Mechanic On-Site')
    mechanic_name = models.CharField(max_length=100, default='Marcus Vance (Master Automotive Technician)')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='confirmed')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking {self.booking_reference} for {self.customer_name}"
