from django.urls import path
from . import views

app_name = 'lms_core'

urlpatterns = [
    path('courses/create/', views.CourseCreateView.as_view(), name='course-create'),
    path('courses/', views.CourseListView.as_view(), name='course-list'),
    path('enroll/', views.EnrollView.as_view(), name='enroll'),
    path('my-enrollments/', views.MyEnrollmentsView.as_view(), name='my-enrollments'),
]