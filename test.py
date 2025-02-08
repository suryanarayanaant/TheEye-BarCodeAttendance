from pyzbar.pyzbar import decode
import cv2

def detect_and_decode_barcode(image):
    barcodes = decode(image)
    for barcode in barcodes:
        barcode_data = barcode.data.decode('utf-8')
        print(f"Detected Barcode: {barcode_data}")
        return barcode_data
    return None

import pytesseract

def extract_text(image):
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray)
    print(f"Extracted Text: {text}")
    return text
def detect_faces(image):
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
    for (x, y, w, h) in faces:
        face = image[y:y+h, x:x+w]
        return face
    return None

import cv2

def process_image(image_path):
    image = cv2.imread(image_path)

    # Step 1: Detect barcode
    barcode = detect_and_decode_barcode(image)

    # Step 2: Extract text for roll number and name
    text = extract_text(image)

    # Step 3: Detect and crop face
    face = detect_faces(image)
    if face is not None:
        face_path = "detected_face.jpg"
        cv2.imwrite(face_path, face)
        print(f"Face saved at {face_path}")

    return barcode, text, face




if __name__ == "__main__":
    # Path to your image
    image_path = "participant_images\participant_1.jpg"

    # Process the image
    barcode, text, face = process_image(image_path)

    # Display results
    print(f"Barcode: {barcode}")
    print(f"Extracted Text: {text}")
    if face is not None:
        print("Face detected and saved.")
    else:
        print("No face detected.")
