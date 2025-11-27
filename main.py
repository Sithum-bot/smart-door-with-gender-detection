import cv2
import time
import serial
import csv
from datetime import datetime

# Serial setup
try:
    ser = serial.Serial('COM4', 9600)
    time.sleep(2)
    print("Serial connected to ESP32.")
except Exception as e:
    print(f"Serial error: {e}")
    ser = None

# Gender model setup
MODEL = "models/deploy_gender.prototxt"
WEIGHTS = "models/gender_net.caffemodel"
gender_list = ['Male', 'Female']

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
net = cv2.dnn.readNetFromCaffe(MODEL, WEIGHTS)
cap = cv2.VideoCapture(0)

csv_file = "logs.csv"

confirmation_start_time = None
confirmed_gender = None
unlocked = False
cooldown_start = None
cooldown_duration = 5

while True:
    ret, frame = cap.read()
    if not ret:
        break

    now = time.time()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)

    if unlocked:
        # Show "unlocked" status for 5 seconds
        if now - cooldown_start >= cooldown_duration:
            unlocked = False
            confirmed_gender = None
        else:
            label = f"{confirmed_gender} - Unlocked"
            cv2.putText(frame, label, (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.imshow("Gender Detection", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            continue

    if len(faces) > 0:
        (x, y, w, h) = faces[0]
        face_img = frame[y:y+h, x:x+w].copy()
        blob = cv2.dnn.blobFromImage(face_img, 1, (227, 227), (104, 117, 123), swapRB=False)
        net.setInput(blob)
        preds = net.forward()
        gender = gender_list[preds[0].argmax()]

        # Confirmation logic
        if gender == confirmed_gender:
            if time.time() - confirmation_start_time >= 5:
                # Unlock
                if ser and ser.is_open:
                    try:
                        ser.write(f"{gender}\n".encode())
                        print(f"[SENT] {gender} sent to ESP32")
                    except Exception as e:
                        print(f"[ERROR] Serial write failed: {e}")

                # Log
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                try:
                    with open(csv_file, 'a', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow([timestamp, gender])
                        print(f"[LOGGED] {timestamp}, {gender}")
                except Exception as e:
                    print(f"[ERROR] Logging failed: {e}")

                unlocked = True
                cooldown_start = time.time()
            else:
                remaining = 5 - (time.time() - confirmation_start_time)
                label = f"{gender} - Confirming ({remaining:.1f}s)"
        else:
            confirmed_gender = gender
            confirmation_start_time = time.time()
            label = f"{gender} - Hold still 5s"

        # Draw box and label
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    else:
        confirmed_gender = None
        confirmation_start_time = None

    cv2.imshow("Gender Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
if ser and ser.is_open:
    ser.close()
print("[CLOSED] Program terminated.")
