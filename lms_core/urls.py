from django.urls import path
from . import views

app_name = 'lms_core'

urlpatterns = [
    path('courses/create/', views.CourseCreateView.as_view(), name='course-create'),
    path('courses/', views.CourseListView.as_view(), name='course-list'),
    path('enroll/', views.EnrollView.as_view(), name='enroll'),
    path('my-enrollments/', views.MyEnrollmentsView.as_view(), name='my-enrollments'),
    path('materials/upload/', views.CourseMaterialUploadView.as_view(), name='material-upload'),
    path('materials/<int:course_id>/', views.CourseMaterialListView.as_view(), name='material-list'),
]