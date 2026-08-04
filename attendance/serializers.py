from rest_framework import serializers
from django.contrib.auth import get_user_model
import face_recognition
from .models import AttendanceSession
from .models import AttendanceRecord


User = get_user_model()


class FaceEnrollSerializer(serializers.Serializer):
    """
    Validates an uploaded photo and extracts a face encoding from it.
    Does NOT save anything itself — the view decides which student
    this encoding belongs to, based on who's making the request.
    """
    image = serializers.ImageField()
    student_id = serializers.IntegerField(required=False)

    def validate_image(self, image):
        # face_recognition needs a raw image array, not a Django file object directly
        loaded_image = face_recognition.load_image_file(image)
        face_locations = face_recognition.face_locations(loaded_image)

        if len(face_locations) == 0:
            raise serializers.ValidationError("No face detected in the photo. Try a clearer, front-facing image.")
        if len(face_locations) > 1:
            raise serializers.ValidationError("Multiple faces detected. Upload a photo with only one person.")

        encodings = face_recognition.face_encodings(loaded_image, known_face_locations=face_locations)
        # Stash the encoding on self so the view can grab it after validation —
        # avoids re-processing the image a second time.
        self.extracted_encoding = encodings[0]
        return image

class AttendanceSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceSession
        fields = [
            'id', 'course_name', 'session_type', 'session_date',
            'is_open', 'start_time', 'end_time', 'allowed_ip_addresses',
            'started_at',
        ]
        read_only_fields = ['id', 'session_date', 'started_at']

class MarkAttendanceSerializer(serializers.Serializer):
    """Validates the photo submitted to mark attendance for a LAB session."""
    session_id = serializers.IntegerField()
    image = serializers.ImageField()

    def validate_image(self, image):
        loaded_image = face_recognition.load_image_file(image)
        face_locations = face_recognition.face_locations(loaded_image)

        if len(face_locations) == 0:
            raise serializers.ValidationError("No face detected in the photo.")
        if len(face_locations) > 1:
            raise serializers.ValidationError("Multiple faces detected — only one person should be in frame.")

        encodings = face_recognition.face_encodings(loaded_image, known_face_locations=face_locations)
        self.extracted_encoding = encodings[0]
        return image

class ManualAttendanceSerializer(serializers.Serializer):
    """Faculty marks a single student present/absent directly — no face involved."""
    session_id = serializers.IntegerField()
    student_id = serializers.IntegerField()
    is_present = serializers.BooleanField(default=True)


class AttendanceRecordSerializer(serializers.ModelSerializer):
    """Used to display attendance records — read-only."""
    student_username = serializers.CharField(source='student.username', read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = [
            'id', 'student', 'student_username', 'is_present',
            'marked_via', 'marked_at', 'confidence_score', 'marked_from_ip',
        ]