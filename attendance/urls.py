from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('enroll-face/', views.FaceEnrollView.as_view(), name='enroll-face'),
    path('sessions/create/', views.AttendanceSessionCreateView.as_view(), name='session-create'),
    path('sessions/', views.AttendanceSessionListView.as_view(), name='session-list'),
    path('mark-face/', views.MarkAttendanceFaceView.as_view(), name='mark-face'),
]