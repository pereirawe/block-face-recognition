import cv2
import face_recognition
import time
from PIL import Image, ImageDraw, ImageFont
import os  # For locking the computer

# Name for the reference face
name_face = "<FACE NAME HERE>"

# Path to the reference face image
face_path = f"faces/face_{name_face}.jpg"

# Load the reference image (the known face)
known_image = face_recognition.load_image_file(face_path)
known_encoding = face_recognition.face_encodings(known_image)[0]

# Initialize the camera
camera = cv2.VideoCapture(0)
print("Camera is running. Detecting faces...")

# Variables for timing and state
last_detection_time = time.time()
face_missing_time = 0


def block_computer():
    """Locks the computer."""
    print("Locking the computer...")
    if os.name == "nt":  # Windows
        os.system("rundll32.exe user32.dll,LockWorkStation")
    # else:
    # os.system("gnome-screensaver-command -l")
    # exit()


def process_frame(frame, timestamp):
    """Process the frame to detect faces and save annotated images."""
    global last_detection_time, face_missing_time

    # Save the captured frame temporarily
    name = "Unknown"
    unknown_image_path = f"{timestamp}_camera_image.jpg"
    cv2.imwrite(unknown_image_path, frame)

    # Load the captured image for comparison
    unknown_image = face_recognition.load_image_file(unknown_image_path)

    # Find all face locations and encodings in the unknown image
    face_locations = face_recognition.face_locations(unknown_image)
    face_encodings = face_recognition.face_encodings(unknown_image, face_locations)

    # Convert the unknown image to a PIL image for drawing
    pil_image = Image.fromarray(unknown_image)
    draw = ImageDraw.Draw(pil_image)

    # Optional: Load a font (if available, replace "arial.ttf" with a valid font path)
    try:
        font = ImageFont.truetype("arial.ttf", 20)  # Adjust size as needed
    except IOError:
        font = ImageFont.load_default()  # Fallback to default font

    face_found = False

    # Loop through each face found in the unknown image
    for (top, right, bottom, left), face_encoding in zip(
        face_locations, face_encodings
    ):
        # Compare the face with the known face
        matches = face_recognition.compare_faces([known_encoding], face_encoding)

        if matches[0]:
            name = name_face
            face_found = True
            last_detection_time = time.time()  # Reset detection time
            face_missing_time = 0  # Reset the missing timer

            # time.sleep(10)

        # Draw a rectangle around the face
        draw.rectangle(((left, top), (right, bottom)), outline=(0, 255, 0), width=2)

        # Calculate text size using textbbox
        text_bbox = draw.textbbox((0, 0), name, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        # Draw a filled rectangle for the name background
        draw.rectangle(
            ((left, bottom - text_height - 10), (left + text_width + 12, bottom)),
            fill=(0, 255, 0),
            outline=(0, 255, 0),
        )

        # Draw the name text
        draw.text((left + 6, bottom - text_height - 5), name, fill=(0, 0, 0), font=font)

    # If no face matches, increment the missing timer
    if not face_found:

        # Save the annotated image
        annotated_image_path = f"register/{timestamp}_annotated_face_{name}.jpg"
        pil_image.save(annotated_image_path)
        print(f"Annotated image saved as {annotated_image_path}.")

        face_missing_time = time.time() - last_detection_time
        block_computer()


while True:
    ret, frame = camera.read()  # Capture frame-by-frame
    if not ret:
        print("Failed to capture image from the camera.")
        break

    # Display the camera feed
    cv2.imshow("Camera", frame)

    # Process the frame periodically
    current_time = time.time()
    if current_time - last_detection_time >= 1:  # Process every second
        timestamp = int(current_time)
        process_frame(frame, timestamp)

    # Check if "William" has been missing for 30 seconds
    if face_missing_time >= 30:
        block_computer()
        break

    # Exit if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()
