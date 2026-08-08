"""
Standalone test — proves face_recognition can detect a face and
extract a 128-number encoding from a real photo. No Django involved.
"""
import face_recognition

print("Loading image...")
image = face_recognition.load_image_file("test_images/test_face.jpg")

print("Detecting face locations...")
face_locations = face_recognition.face_locations(image)
print(f"Found {len(face_locations)} face(s)")

if len(face_locations) == 0:
    print("No face detected — try a clearer, more front-facing photo.")
elif len(face_locations) > 1:
    print("Multiple faces detected — for enrollment we need exactly one.")
else:
    print("Extracting face encoding...")
    encodings = face_recognition.face_encodings(image, known_face_locations=face_locations)
    encoding = encodings[0]
    print(f"Encoding shape: {encoding.shape}")
    print(f"First 5 values: {encoding[:5]}")
    print("SUCCESS — face_recognition is working correctly on your machine.")
    