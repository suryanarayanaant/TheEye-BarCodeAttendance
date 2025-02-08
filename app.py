import cv2
import numpy as np
from pyzbar.pyzbar import decode
import bcrypt
import csv
import base64
import re
import sqlite3
from bcrypt import hashpw, gensalt, checkpw
import pytesseract
import os
from flask import Flask, request, jsonify, render_template, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'participant_images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load Haar Cascade for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Database setup
def init_db():
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roll_number TEXT UNIQUE NOT NULL,
        name TEXT,
        image_path TEXT
    )
    ''')
    cursor.execute("PRAGMA table_info(attendance)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'name' not in columns:
        cursor.execute("ALTER TABLE attendance ADD COLUMN name TEXT")
    if 'image_path' not in columns:
        cursor.execute("ALTER TABLE attendance ADD COLUMN image_path TEXT")
    conn.commit()
    conn.close()


def authenticate_user(email, password):
    try:
        # Open the users.csv file
        with open('users.csv', 'r') as file:
            reader = csv.DictReader(file)
            # Iterate through users to find a match
            for row in reader:
                if row['email'] == email and bcrypt.checkpw(password.encode('utf-8'), row['password'].encode('utf-8')):
                    return True
        return False
    except FileNotFoundError:
        print("Error: 'users.csv' file not found.")
        return False

# Validate roll number format
def validate_roll_number(roll_number):
    pattern = r'^\d{2}[a-zA-Z]\d{3}$'
    return bool(re.match(pattern, roll_number))

# Store participant in the database
def store_participant(roll_number, name, image_path):
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT INTO attendance (roll_number, name, image_path) VALUES (?, ?, ?)',
            (roll_number, name, image_path)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"Roll number {roll_number} already exists in the database.")
    conn.close()

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('scan'))
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    if authenticate_user(email, password):
        session['user'] = email
        return redirect(url_for('scan'))
    else:
        return render_template('index.html', error="Invalid credentials")

@app.route('/scan')
def scan():
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template('scan.html')


@app.route('/capture', methods=['POST'])
def capture():
    try:
        data = request.json.get('frame', None)
        if not data:
            return jsonify({'status': 'failure', 'message': 'No frame data received'})

        # Decode the base64-encoded image
        img_data = base64.b64decode(data.split(',')[1])
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Perform face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))

        if len(faces) > 0:
            # Save the first detected face (assuming one participant per frame)
            x, y, w, h = faces[0]
            cropped_face = frame[y:y+h, x:x+w]
            image_name = f"participant_{len(os.listdir(UPLOAD_FOLDER)) + 1}.jpg"
            image_path = os.path.join(UPLOAD_FOLDER, image_name)
            cv2.imwrite(image_path, cropped_face)
        else:
            # Save the full frame if no face is detected
            image_name = f"participant_{len(os.listdir(UPLOAD_FOLDER)) + 1}_noface.jpg"
            image_path = os.path.join(UPLOAD_FOLDER, image_name)
            cv2.imwrite(image_path, frame)

        # Attempt to decode the QR code
        decoded_objects = decode(frame)
        for obj in decoded_objects:
            roll_number = obj.data.decode('utf-8')
            if validate_roll_number(roll_number):
                store_participant(roll_number, "Unknown", image_path)
                return jsonify({'status': 'success', 'qr_code': roll_number, 'name': "Unknown"})

        # If QR code fails, use OCR
        text = pytesseract.image_to_string(frame)
        roll_number_match = re.search(r'\d{2}[a-zA-Z]\d{3}', text)
        name_match = re.search(r'[A-Z][A-Za-z\s]+', text)

        if roll_number_match:
            roll_number = roll_number_match.group(0)
            name = name_match.group(0).strip() if name_match else "Unknown"
            store_participant(roll_number, name, image_path)
            return jsonify({'status': 'success', 'qr_code': roll_number, 'name': name})

        # If both QR and OCR fail
        return jsonify({'status': 'failure', 'message': 'Failed to extract QR code or text'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
