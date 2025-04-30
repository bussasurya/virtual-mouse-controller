import cv2
import mediapipe as mp
import numpy as np
import time

# Initialize webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam")
    exit()

# Set webcam resolution
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
mp_drawing = mp.solutions.drawing_utils

# ROI for gesture detection
frame_roi_x_min, frame_roi_x_max = 64, 576
frame_roi_y_min, frame_roi_y_max = 48, 432

# Performance variables
frame_skip = 2
frame_counter = 0
prev_time = time.time()
frame_count = 0
fps = 0

# Gesture variables
gesture_feedback = ""
feedback_timeout = 0
pinch_threshold = 0.03
fist_threshold = 0.05

def is_pinch(hand_landmarks, threshold=0.03):
    thumb = hand_landmarks.landmark[4]
    index = hand_landmarks.landmark[8]
    distance = ((thumb.x - index.x)**2 + (thumb.y - index.y)**2)**0.5
    return distance < threshold

def is_fist(hand_landmarks, threshold=0.05):
    tips = [4, 8]
    bases = [2, 5]
    return all(
        abs(hand_landmarks.landmark[tips[i]].y - hand_landmarks.landmark[bases[i]].y) < threshold
        for i in range(2)
    )

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to capture frame")
        break
    
    frame_counter += 1
    if frame_counter % frame_skip != 0:
        continue
    
    frame = cv2.flip(frame, 1)
    
    # Draw ROI
    cv2.rectangle(frame, (frame_roi_x_min, frame_roi_y_min), (frame_roi_x_max, frame_roi_y_max), (255, 255, 0), 1)
    
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)
    
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            thumb_tip = hand_landmarks.landmark[4]
            thumb_x = int(thumb_tip.x * 640)
            thumb_y = int(thumb_tip.y * 480)
            
            index_tip = hand_landmarks.landmark[8]
            index_x = int(index_tip.x * 640)
            index_y = int(index_tip.y * 480)
            
            cv2.circle(frame, (thumb_x, thumb_y), 5, (0, 255, 0), -1)
            cv2.circle(frame, (index_x, index_y), 5, (0, 0, 255), -1)
            
            current_time = time.time()
            if is_pinch(hand_landmarks, pinch_threshold):
                gesture_feedback = "Pinch Detected"
                feedback_timeout = current_time + 1.0
                print("Pinch: True")
            elif is_fist(hand_landmarks, fist_threshold):
                gesture_feedback = "Fist Detected"
                feedback_timeout = current_time + 1.0
                print("Fist: True")
            else:
                print("Pinch: False, Fist: False")
            
            print(f"Thumb tip: ({thumb_x}, {thumb_y})")
            print(f"Index fingertip: ({index_x}, {index_y})")
    
    # Calculate FPS
    frame_count += 1
    current_time = time.time()
    if current_time - prev_time >= 1.0:
        fps = frame_count / (current_time - prev_time)
        frame_count = 0
        prev_time = current_time
    
    # Display UI
    cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    if gesture_feedback and current_time < feedback_timeout:
        cv2.putText(frame, gesture_feedback, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    
    cv2.imshow("Dino Gesture Control", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
hands.close()