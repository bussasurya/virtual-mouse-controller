import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time
import webbrowser
import os
import subprocess

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
    min_tracking_confidence=0.4
)
mp_drawing = mp.solutions.drawing_utils

# Disable PyAutoGUI fail-safe
pyautogui.FAILSAFE = False

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
last_jump_time = 0
jump_cooldown = 0.3
is_ducking = False
prev_index_y = None
curl_threshold = 0.06
move_threshold = 0.1
game_started = False

def is_fingers_curled(hand_landmarks, threshold=0.06):
    tips = [12, 16, 20]  # Middle, ring, pinky
    bases = [9, 13, 17]
    distances = [
        abs(hand_landmarks.landmark[tips[i]].y - hand_landmarks.landmark[bases[i]].y)
        for i in range(3)
    ]
    print(f"Duck distances: Middle={distances[0]:.3f}, Ring={distances[1]:.3f}, Pinky={distances[2]:.3f}")
    return all(distance < threshold for distance in distances)

# Register Chrome explicitly
chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe"  # Adjust if Chrome is elsewhere
if os.path.exists(chrome_path):
    webbrowser.register("chrome", None, webbrowser.BackgroundBrowser(chrome_path))
else:
    print("Warning: Chrome executable not found at", chrome_path)

# Open Chrome Dino game
try:
    webbrowser.get("chrome").open("chrome://dino")
    print("Opened chrome://dino using webbrowser")
except webbrowser.Error:
    print("Failed to open with webbrowser, trying subprocess")
    try:
        subprocess.Popen([chrome_path, "chrome://dino"])
        print("Opened chrome://dino using subprocess")
    except FileNotFoundError:
        print("Error: Chrome not found. Please install Chrome or check path")

time.sleep(2)  # Wait for Chrome to open

# Focus Chrome window (adjust coordinates based on your screen)
# Find coordinates: python -c "import pyautogui; time.sleep(5); print(pyautogui.position())"
pyautogui.click(x=500, y=500)  # Click in Chrome window
print("Focused Chrome window")

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
            delta_y = 0
            if prev_index_y is not None:
                delta_y = index_tip.y - prev_index_y
                print(f"Index y-delta: {delta_y:.3f}")
            
            # Jump: Index moves up (y decreases)
            if delta_y < -move_threshold and (current_time - last_jump_time) > jump_cooldown:
                pyautogui.press("space")
                if not game_started:
                    gesture_feedback = "Game Started"
                    game_started = True
                    print("Game started")
                else:
                    gesture_feedback = "Jump Triggered"
                    print("Jump triggered")
                feedback_timeout = current_time + 1.0
                last_jump_time = current_time
            
            # Duck: Index moves down (y increases) with fingers curled
            fingers_curled = is_fingers_curled(hand_landmarks, curl_threshold)
            if delta_y > move_threshold and fingers_curled and not is_ducking:
                pyautogui.keyDown("down")
                is_ducking = True
                gesture_feedback = "Duck Triggered"
                feedback_timeout = current_time + 1.0
                print("Duck started")
            elif (delta_y <= move_threshold or not fingers_curled) and is_ducking:
                pyautogui.keyUp("down")
                is_ducking = False
                gesture_feedback = "Duck Ended"
                feedback_timeout = current_time + 1.0
                print("Duck ended")
            
            prev_index_y = index_tip.y
            print(f"Index move: {delta_y:.3f}, Fingers curled: {fingers_curled}")
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