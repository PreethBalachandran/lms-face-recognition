from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status

from .models import Course, Assignment, Submission

User = get_user_model()


class GradingValidationTests(TestCase):
    """Confirms grading enforces business rules: marks can't exceed
    max_marks, and only the owning faculty (or admin) can grade."""

    def setUp(self):
        self.client = APIClient()
        self.faculty = User.objects.create_user(username='owner_faculty', password='pass123', role='faculty')
        self.other_faculty = User.objects.create_user(username='other_faculty', password='pass123', role='faculty')
        self.student = User.objects.create_user(username='grading_student', password='pass123', role='student')

        self.course = Course.objects.create(
            faculty=self.faculty, name="Test Course", code="TC101"
        )
        self.assignment = Assignment.objects.create(
            course=self.course, title="Test Assignment", max_marks=50,
            due_date=timezone.now() + timedelta(days=7),
            created_by=self.faculty,
        )
        self.submission = Submission.objects.create(
            assignment=self.assignment, student=self.student,
            file="test.txt",
        )

    def test_marks_exceeding_max_marks_rejected(self):
        self.client.force_authenticate(user=self.faculty)
        response = self.client.post('/api/lms/submissions/grade/', {
            'submission_id': self.submission.id,
            'marks_obtained': 999,
            'feedback': 'test',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_owning_faculty_cannot_grade(self):
        """A faculty member who doesn't teach this course shouldn't be
        able to grade its submissions."""
        self.client.force_authenticate(user=self.other_faculty)
        response = self.client.post('/api/lms/submissions/grade/', {
            'submission_id': self.submission.id,
            'marks_obtained': 40,
            'feedback': 'test',
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owning_faculty_can_grade_successfully(self):
        self.client.force_authenticate(user=self.faculty)
        response = self.client.post('/api/lms/submissions/grade/', {
            'submission_id': self.submission.id,
            'marks_obtained': 45,
            'feedback': 'Great work',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.marks_obtained, 45)