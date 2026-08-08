# Smart LMS with Face Recognition Attendance

A Django REST API for a Learning Management System with a face-recognition-based
attendance system designed around a real problem: unsupervised lab hours where
students could leave early and still get marked present.

## The core idea

Most face-recognition attendance projects apply biometric verification everywhere,
whether or not it's actually needed. This system uses two different verification
modes depending on the real risk in each situation:

- **Lecture sessions** — faculty is physically present, so attendance is marked
  manually. A human witness already solves the "who was here" problem.
- **Lab sessions** — faculty isn't consistently present for the full duration,
  which is where students could exploit the gap. Attendance here requires
  **three independent checks to pass**: the request must come from an approved
  lab computer's IP address, it must fall within the session's active time
  window, and the submitted photo must match the student's enrolled face
  encoding. All three must hold — a correct face from the wrong location, or
  the right location at the wrong time, is rejected.

## Features

- **Authentication**: JWT-based auth with three roles (admin, faculty, student),
  role-based permissions throughout
- **Attendance**: face enrollment, face-recognition lab attendance with
  IP + time-window verification, manual lecture attendance, role-scoped
  record viewing
- **LMS Core**: courses, enrollment, course materials, assignments,
  submissions with automatic late-detection, grading with mark validation,
  role-specific dashboards (student / faculty / admin)

## Tech stack

- Django 4.2 + Django REST Framework
- PostgreSQL
- JWT auth (djangorestframework-simplejwt)
- face_recognition (dlib-based) + OpenCV for face encoding and matching
- python-environ for environment-based configuration

## Setup

```bash
git clone https://github.com/PreethBalachandran/lms-face-recognition.git
cd lms-face-recognition
python -m venv venv
source venv/Scripts/activate   # venv\Scripts\activate on Windows cmd
pip install -r requirements.txt
cp .env.example .env           # then edit .env with your own values
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Project structure


## API overview

All endpoints are under `/api/`:
- `/api/auth/` — register, login, profile, admin user management
- `/api/attendance/` — face enrollment, session creation, marking, records
- `/api/lms/` — courses, materials, assignments, submissions, grading, dashboards

⚠️ Built as a learning project. Face encodings are stored as numerical
vectors, not raw images, for both performance and privacy reasons.