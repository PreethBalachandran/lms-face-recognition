from django.shortcuts import render

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Course, Enrollment
from .serializers import CourseSerializer, EnrollmentSerializer


class CourseCreateView(generics.CreateAPIView):
    """POST /api/lms/courses/create/ — faculty/admin only."""
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        if not (request.user.is_faculty or request.user.is_admin_role):
            return Response({"detail": "Only faculty or admin can create courses."}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(faculty=self.request.user)


class CourseListView(generics.ListAPIView):
    """
    GET /api/lms/courses/
    - Students: see only courses they're actively enrolled in
    - Faculty: see only courses they teach
    - Admin: see all courses
    """
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_student:
            return Course.objects.filter(enrollments__student=user, enrollments__status='active')
        elif user.is_faculty:
            return Course.objects.filter(faculty=user)
        elif user.is_admin_role:
            return Course.objects.all()
        return Course.objects.none()


class EnrollView(APIView):
    """POST /api/lms/enroll/ — students enroll themselves in a course."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not request.user.is_student:
            return Response({"detail": "Only students can enroll in courses."}, status=status.HTTP_403_FORBIDDEN)

        course_id = request.data.get('course_id')
        if not course_id:
            return Response({"detail": "course_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            course = Course.objects.get(id=course_id, is_active=True)
        except Course.DoesNotExist:
            return Response({"detail": "Course not found or inactive."}, status=status.HTTP_404_NOT_FOUND)

        enrollment, created = Enrollment.objects.get_or_create(
            student=request.user, course=course,
            defaults={'status': Enrollment.Status.ACTIVE}
        )
        if not created:
            return Response({"detail": "Already enrolled in this course."}, status=status.HTTP_200_OK)

        serializer = EnrollmentSerializer(enrollment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MyEnrollmentsView(generics.ListAPIView):
    """GET /api/lms/my-enrollments/ — student sees their own enrollments."""
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Enrollment.objects.filter(student=self.request.user)# Create your views here.
