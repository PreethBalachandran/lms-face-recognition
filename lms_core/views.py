from django.shortcuts import render

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Course, Enrollment, CourseMaterial, Assignment, Submission
from .serializers import (
    CourseSerializer, EnrollmentSerializer, CourseMaterialSerializer,
    AssignmentSerializer, SubmissionSerializer,
)
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
class CourseMaterialUploadView(generics.CreateAPIView):
    """
    POST /api/lms/materials/upload/ — faculty who owns the course, or admin.
    """
    queryset = CourseMaterial.objects.all()
    serializer_class = CourseMaterialSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # needed for file upload

    def create(self, request, *args, **kwargs):
        course_id = request.data.get('course')
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({"detail": "Course not found."}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        is_owning_faculty = user.is_faculty and course.faculty_id == user.id
        if not (is_owning_faculty or user.is_admin_role):
            return Response(
                {"detail": "Only the faculty who owns this course (or an admin) can upload materials."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class CourseMaterialListView(generics.ListAPIView):
    """
    GET /api/lms/materials/<course_id>/
    - Students: only if actively enrolled in that course
    - Faculty: only if they own that course
    - Admin: always
    """
    serializer_class = CourseMaterialSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        course_id = self.kwargs['course_id']
        user = self.request.user

        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return CourseMaterial.objects.none()

        if user.is_admin_role:
            return CourseMaterial.objects.filter(course=course)
        elif user.is_faculty and course.faculty_id == user.id:
            return CourseMaterial.objects.filter(course=course)
        elif user.is_student:
            is_enrolled = Enrollment.objects.filter(student=user, course=course, status='active').exists()
            if is_enrolled:
                return CourseMaterial.objects.filter(course=course)
        return CourseMaterial.objects.none()
class AssignmentCreateView(generics.CreateAPIView):
    """POST /api/lms/assignments/create/ — faculty who owns the course, or admin."""
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        course_id = request.data.get('course')
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({"detail": "Course not found."}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        is_owning_faculty = user.is_faculty and course.faculty_id == user.id
        if not (is_owning_faculty or user.is_admin_role):
            return Response(
                {"detail": "Only the faculty who owns this course (or an admin) can create assignments."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class AssignmentListView(generics.ListAPIView):
    """
    GET /api/lms/assignments/<course_id>/
    Same visibility rule as materials: enrolled students, owning faculty, or admin.
    """
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        course_id = self.kwargs['course_id']
        user = self.request.user

        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Assignment.objects.none()

        if user.is_admin_role:
            return Assignment.objects.filter(course=course)
        elif user.is_faculty and course.faculty_id == user.id:
            return Assignment.objects.filter(course=course)
        elif user.is_student:
            is_enrolled = Enrollment.objects.filter(student=user, course=course, status='active').exists()
            if is_enrolled:
                return Assignment.objects.filter(course=course)
        return Assignment.objects.none()





class SubmitAssignmentView(APIView):
    """
    POST /api/lms/submissions/submit/
    Student submits work for an assignment. Must be enrolled in the
    assignment's course. Resubmission overwrites the previous file.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        if not request.user.is_student:
            return Response({"detail": "Only students can submit assignments."}, status=status.HTTP_403_FORBIDDEN)

        assignment_id = request.data.get('assignment')
        file = request.data.get('file')

        if not assignment_id or not file:
            return Response({"detail": "assignment and file are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            assignment = Assignment.objects.get(id=assignment_id)
        except Assignment.DoesNotExist:
            return Response({"detail": "Assignment not found."}, status=status.HTTP_404_NOT_FOUND)

        is_enrolled = Enrollment.objects.filter(
            student=request.user, course=assignment.course, status='active'
        ).exists()
        if not is_enrolled:
            return Response(
                {"detail": "You must be enrolled in this course to submit."},
                status=status.HTTP_403_FORBIDDEN
            )

        from django.utils import timezone
        is_late = timezone.now() > assignment.due_date

        submission, created = Submission.objects.update_or_create(
            assignment=assignment,
            student=request.user,
            defaults={'file': file, 'is_late': is_late}
        )

        serializer = SubmissionSerializer(submission)
        return Response({
            **serializer.data,
            "detail": "Submitted successfully." if created else "Resubmitted successfully (previous file replaced).",
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class AssignmentSubmissionsListView(generics.ListAPIView):
    """
    GET /api/lms/submissions/<assignment_id>/
    - Faculty who owns the course: see ALL submissions for that assignment
    - Student: see only their own submission
    - Admin: see all
    """
    serializer_class = SubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        assignment_id = self.kwargs['assignment_id']
        user = self.request.user

        try:
            assignment = Assignment.objects.get(id=assignment_id)
        except Assignment.DoesNotExist:
            return Submission.objects.none()

        if user.is_admin_role:
            return Submission.objects.filter(assignment=assignment)
        elif user.is_faculty and assignment.course.faculty_id == user.id:
            return Submission.objects.filter(assignment=assignment)
        elif user.is_student:
            return Submission.objects.filter(assignment=assignment, student=user)
        return Submission.objects.none()