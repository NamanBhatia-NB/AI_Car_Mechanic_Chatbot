from django.urls import path
from .views import (
    APIRootView, ChatView, MediaUploadView, DiagnosisView,
    BookingView, BookingDetailView, SessionHistoryView, ChatSessionsListView, HealthCheckView
)

urlpatterns = [
    path('', APIRootView.as_view(), name='api-root'),
    path('chat/', ChatView.as_view(), name='api-chat'),
    path('upload/', MediaUploadView.as_view(), name='api-upload'),
    path('diagnosis/', DiagnosisView.as_view(), name='api-diagnosis'),
    path('booking/', BookingView.as_view(), name='api-booking'),
    path('booking/<str:pk>/', BookingDetailView.as_view(), name='api-booking-detail'),
    path('chat/sessions/', ChatSessionsListView.as_view(), name='api-chat-sessions-list'),
    path('chat/history/<uuid:session_id>/', SessionHistoryView.as_view(), name='api-chat-history'),
    path('health/', HealthCheckView.as_view(), name='api-health'),
]

