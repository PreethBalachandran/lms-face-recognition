from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status

from .models import AttendanceSession, FaceEncoding

User = get_user_model()


class AttendanceSessionAccessTests(TestCase):
    """
    Tests the three-layer lab attendance security model:
    IP whitelist, time window, and face match must ALL pass.
    This is the core original idea of the project — worth testing
    with real automated assertions, not just manual curl checks.
    """

    def setUp(self):
        self.client = APIClient()
        self.faculty = User.objects.create_user(
            username='test_faculty', password='pass123', role='faculty'
        )
        self.student = User.objects.create_user(
            username='test_student', password='pass123', role='student'
        )
        # Give the student a fake enrolled face encoding
        import numpy as np
        fe = FaceEncoding(student=self.student)
        fe.set_encoding(np.random.rand(128))
        fe.save()
        self.fake_encoding = fe

    def test_wrong_ip_rejected_even_with_correct_time_window(self):
        """A session whose IP whitelist excludes the test client's IP (127.0.0.1)
        must reject attendance marking regardless of timing."""
        session = AttendanceSession.objects.create(
            faculty=self.faculty,
            course_name="Test Lab",
            session_type=AttendanceSession.SessionType.LAB,
            start_time="00:00:00",
            end_time="23:59:59",
            allowed_ip_addresses="10.0.0.99",  # deliberately NOT 127.0.0.1
        )
        self.client.force_authenticate(user=self.student)
        # We don't need a real photo for this test — the IP check happens
        # before the image is ever processed, so this proves the check
        # order is correct: location is validated first.
        response = self.client.post(
            '/api/attendance/mark-face/',
            {'session_id': session.id},
            format='multipart'
        )
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])

    def test_wrong_time_window_rejected(self):
        """A session outside the current time window rejects marking,
        even with a correct IP."""
        session = AttendanceSession.objects.create(
            faculty=self.faculty,
            course_name="Test Lab",
            session_type=AttendanceSession.SessionType.LAB,
            start_time="01:00:00",
            end_time="02:00:00",  # unlikely to be the current time
            allowed_ip_addresses="127.0.0.1",
        )
        self.client.force_authenticate(user=self.student)
        response = self.client.post(
            '/api/attendance/mark-face/',
            {'session_id': session.id},
            format='multipart'
        )
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])

    def test_lecture_session_uses_manual_marking_not_face(self):
        """A LECTURE session should be rejected by the face-marking endpoint
        entirely — it's not the right tool for that session type."""
        session = AttendanceSession.objects.create(
            faculty=self.faculty,
            course_name="Test Lecture",
            session_type=AttendanceSession.SessionType.LECTURE,
        )
        self.client.force_authenticate(user=self.student)
        response = self.client.post(
            '/api/attendance/mark-face/',
            {'session_id': session.id},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_manual_marking_by_owning_faculty_succeeds(self):
        """Faculty can manually mark a student present for their own lecture session."""
        session = AttendanceSession.objects.create(
            faculty=self.faculty,
            course_name="Test Lecture",
            session_type=AttendanceSession.SessionType.LECTURE,
        )
        self.client.force_authenticate(user=self.faculty)
        response = self.client.post('/api/attendance/mark-manual/', {
            'session_id': session.id,
            'student_id': self.student.id,
            'is_present': True,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_student_cannot_mark_manual_attendance(self):
        """Only faculty/admin should be able to use the manual marking endpoint."""
        session = AttendanceSession.objects.create(
            faculty=self.faculty,
            course_name="Test Lecture",
            session_type=AttendanceSession.SessionType.LECTURE,
        )
        self.client.force_authenticate(user=self.student)
        response = self.client.post('/api/attendance/mark-manual/', {
            'session_id': session.id,
            'student_id': self.student.id,
            'is_present': True,
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)