from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from django.contrib.auth import get_user_model
from django.http import JsonResponse

from .models import FaceEncoding
from .serializers import FaceEnrollSerializer

import face_recognition
import numpy as np
from datetime import datetime
from .models import FaceEncoding, AttendanceSession, AttendanceRecord
from .serializers import FaceEnrollSerializer, AttendanceSessionSerializer, MarkAttendanceSerializer
from rest_framework import generics
User = get_user_model()


def mark_attendance(request):
    # Old dummy view kept temporarily — will be replaced by the real
    # face-matching endpoint once enrollment is working.
    return JsonResponse({"status": "Attendance marked (dummy). Real logic coming soon!"})


class FaceEnrollView(APIView):
    """
    POST /api/attendance/enroll-face/
    - Students: enroll their own face (student_id ignored if sent)
    - Faculty/Admin: must provide student_id to enroll on that student's behalf
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser]  # needed to accept file uploads

    def post(self, request):
        serializer = FaceEnrollSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Decide WHO this encoding belongs to, based on the requester's role
        if request.user.is_student:
            target_student = request.user
        elif request.user.is_faculty or request.user.is_admin_role:
            student_id = request.data.get('student_id')
            if not student_id:
                return Response(
                    {"detail": "student_id is required when enrolling on behalf of a student."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            try:
                target_student = User.objects.get(id=student_id, role='student')
            except User.DoesNotExist:
                return Response(
                    {"detail": "No student found with that ID."},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            return Response({"detail": "Not permitted."}, status=status.HTTP_403_FORBIDDEN)

        # get_or_create: first enrollment creates the row, re-enrollment updates it
        face_encoding, created = FaceEncoding.objects.get_or_create(student=target_student)
        face_encoding.set_encoding(serializer.extracted_encoding)
        face_encoding.save()

        return Response({
            "detail": f"Face {'enrolled' if created else 're-enrolled'} successfully for {target_student.username}.",
            "student": target_student.username,
            "enrolled_at": face_encoding.enrolled_at,
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

class AttendanceSessionCreateView(generics.CreateAPIView):
    """
    POST /api/attendance/sessions/create/ — faculty/admin only.
    Faculty opens either a LECTURE session (manual marking) or
    a LAB session (face-lock, needs start_time/end_time/allowed_ip_addresses).
    """
    queryset = AttendanceSession.objects.all()
    serializer_class = AttendanceSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        if not (request.user.is_faculty or request.user.is_admin_role):
            return Response({"detail": "Only faculty or admin can create sessions."}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(faculty=self.request.user)


class AttendanceSessionListView(generics.ListAPIView):
    """GET /api/attendance/sessions/ — faculty sees their own sessions."""
    serializer_class = AttendanceSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_faculty:
            return AttendanceSession.objects.filter(faculty=self.request.user)
        elif self.request.user.is_admin_role:
            return AttendanceSession.objects.all()
        return AttendanceSession.objects.none()

class MarkAttendanceFaceView(APIView):
    """
    POST /api/attendance/mark-face/
    Student uploads a photo during a LAB session. Three checks, in order:
    1. Is the request coming from an allowed lab IP?
    2. Is it within the session's time window?
    3. Does the photo's face match the student's enrolled encoding?
    Only if all three pass does attendance get marked present.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser]

    # Lower = closer match. face_recognition's own docs suggest 0.6 as a
    # reasonable default threshold — stricter (lower) reduces false positives.
    MATCH_THRESHOLD = 0.6

    def post(self, request):
        if not request.user.is_student:
            return Response({"detail": "Only students can mark their own attendance."}, status=status.HTTP_403_FORBIDDEN)

        serializer = MarkAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            session = AttendanceSession.objects.get(id=serializer.validated_data['session_id'])
        except AttendanceSession.DoesNotExist:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

        if session.session_type != AttendanceSession.SessionType.LAB:
            return Response({"detail": "This session doesn't use face-lock marking."}, status=status.HTTP_400_BAD_REQUEST)

        # --- Check 1: IP address ---
        request_ip = request.META.get('REMOTE_ADDR')
        allowed_ips = session.get_allowed_ip_list()
        if allowed_ips and request_ip not in allowed_ips:
            return Response(
                {"detail": f"Attendance can only be marked from an approved lab computer. Your IP ({request_ip}) is not on the list."},
                status=status.HTTP_403_FORBIDDEN
            )

        # --- Check 2: Time window ---
        now_time = datetime.now().time()
        if session.start_time and session.end_time:
            if not (session.start_time <= now_time <= session.end_time):
                return Response(
                    {"detail": "Attendance can only be marked during the lab session's active time window."},
                    status=status.HTTP_403_FORBIDDEN
                )

        # --- Check 3: Face match ---
        try:
            stored_encoding_obj = FaceEncoding.objects.get(student=request.user)
        except FaceEncoding.DoesNotExist:
            return Response({"detail": "You haven't enrolled your face yet. Enroll first."}, status=status.HTTP_400_BAD_REQUEST)

        stored_encoding = np.array(stored_encoding_obj.get_encoding())
        new_encoding = serializer.extracted_encoding

        distance = face_recognition.face_distance([stored_encoding], new_encoding)[0]

        if distance > self.MATCH_THRESHOLD:
            return Response({
                "detail": "Face did not match enrolled record.",
                "confidence_score": float(distance),
            }, status=status.HTTP_401_UNAUTHORIZED)

        # All three checks passed — mark present (or update if already marked)
        record, created = AttendanceRecord.objects.update_or_create(
            session=session,
            student=request.user,
            defaults={
                'is_present': True,
                'marked_via': AttendanceRecord.MarkedVia.FACE_MATCH,
                'confidence_score': float(distance),
                'marked_from_ip': request_ip,
            }
        )

        return Response({
            "detail": "Attendance marked successfully.",
            "confidence_score": float(distance),
            "marked_at": record.marked_at,
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)