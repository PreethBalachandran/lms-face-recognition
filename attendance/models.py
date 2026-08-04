from django.db import models
from django.conf import settings
import json


class FaceEncoding(models.Model):
    """
    One row per student — their stored face 'fingerprint'.
    We store a 128-number array (as JSON text), NOT the raw photo.
    Only needed for students, since only lab sessions use face matching.
    """
    student = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='face_encoding',
        limit_choices_to={'role': 'student'},
    )
    encoding_data = models.TextField(
        help_text="128-number face encoding, stored as JSON text"
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_encoding(self, encoding_array):
        self.encoding_data = json.dumps(encoding_array.tolist())

    def get_encoding(self):
        return json.loads(self.encoding_data)

    def __str__(self):
        return f"Face encoding for {self.student.username}"


class AttendanceSession(models.Model):
    """
    One row per class period. Two modes:
    - LECTURE: faculty present, marks attendance manually
    - LAB: faculty not consistently present, face-lock required
      (student must be on an approved lab IP, during the time window,
      and pass a face match)
    """
    class SessionType(models.TextChoices):
        LECTURE = 'lecture', 'Lecture (Manual)'
        LAB = 'lab', 'Lab (Face-Locked)'

    faculty = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendance_sessions',
        limit_choices_to={'role': 'faculty'},
    )
    course_name = models.CharField(
        max_length=200,
        help_text="Temporary text field — will link to a real Course model in Phase 3"
    )
    session_type = models.CharField(max_length=10, choices=SessionType.choices, default=SessionType.LECTURE)

    session_date = models.DateField(auto_now_add=True)

    # Used by LECTURE sessions — faculty manually opens/closes the window
    is_open = models.BooleanField(default=True)

    # Used by LAB sessions — enforced time window, checked against real clock time
    start_time = models.TimeField(null=True, blank=True, help_text="Lab session start (LAB mode only)")
    end_time = models.TimeField(null=True, blank=True, help_text="Lab session end (LAB mode only)")

    # Used by LAB sessions — comma-separated list of allowed lab computer IPs
    # e.g. "192.168.1.10,192.168.1.11,192.168.1.12"
    # In production, these are the lab's static internal IPs.
    allowed_ip_addresses = models.TextField(
        blank=True,
        help_text="Comma-separated IPs allowed to mark attendance (LAB mode only)"
    )

    started_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-started_at']

    def get_allowed_ip_list(self):
        """Turn the comma-separated string into a clean Python list."""
        if not self.allowed_ip_addresses:
            return []
        return [ip.strip() for ip in self.allowed_ip_addresses.split(',') if ip.strip()]

    def __str__(self):
        return f"{self.course_name} — {self.session_date} ({self.get_session_type_display()})"


class AttendanceRecord(models.Model):
    """One row per student, per session — the actual attendance entry."""

    class MarkedVia(models.TextChoices):
        FACE_MATCH = 'face_match', 'Face Recognition (Lab)'
        MANUAL = 'manual', 'Manual (Faculty)'

    session = models.ForeignKey(
        AttendanceSession, on_delete=models.CASCADE, related_name='records'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendance_records',
        limit_choices_to={'role': 'student'},
    )
    is_present = models.BooleanField(default=True)
    marked_via = models.CharField(max_length=20, choices=MarkedVia.choices, default=MarkedVia.MANUAL)
    marked_at = models.DateTimeField(auto_now_add=True)

    # Only populated for face-matched records
    confidence_score = models.FloatField(
        null=True, blank=True,
        help_text="Face match distance score (lab sessions only, lower = better match)"
    )
    marked_from_ip = models.GenericIPAddressField(
        null=True, blank=True,
        help_text="IP address the request came from (lab sessions only)"
    )

    class Meta:
        unique_together = ['session', 'student']
        ordering = ['-marked_at']

    def __str__(self):
        status = "Present" if self.is_present else "Absent"
        return f"{self.student.username} — {status} ({self.session.course_name})"