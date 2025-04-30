import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time
import json
import os
from screeninfo import get_monitors

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

# Get virtual desktop bounds (multi-monitor)
monitors = get_monitors()
screen_width = max(m.x + m.width for m in monitors) - min(m.x for m in monitors)
screen_height = max(m.y + m.height for m in monitors) - min(m.y for m in monitors)
screen_offset_x = min(m.x for m in monitors)
screen_offset_y = min(m.y for m in monitors)

# Disable PyAutoGUI fail-safe
pyautogui.FAILSAFE = False

# Initialize variables
smoothing_factor = 0.6
sensitivity_modes = {"High": 0.8, "Low": 0.4}
current_sensitivity = "Default"
prev_screen_x, prev_screen_y = pyautogui.position()
clicked = False
last_click_time = 0
click_cooldown = 0.5
prev_scroll_y = None
frame_roi_x_min, frame_roi_x_max = 64, 576
frame_roi_y_min, frame_roi_y_max = 48, 432
prev_time = time.time()
frame_count = 0
fps = 0
frame_skip = 2
frame_counter = 0
virtual_mouse_active = True
gesture_feedback = ""
feedback_timeout = 0
pinch_threshold = 0.03
fist_threshold = 0.05
is_dragging = False
drag_start_time = 0
drag_threshold = 0.3
calibration_mode = False

# Load settings
settings_file = "mouse_settings.json"
if os.path.exists(settings_file):
    try:
        with open(settings_file, "r") as f:
            settings = json.load(f)
            pinch_threshold = settings.get("pinch_threshold", 0.03)
            fist_threshold = settings.get("fist_threshold", 0.05)
            smoothing_factor = settings.get("smoothing_factor", 0.6)
            current_sensitivity = settings.get("current_sensitivity", "Default")
            frame_roi_x_min = settings.get("frame_roi_x_min", 64)
            frame_roi_x_max = settings.get("frame_roi_x_max", 576)
            frame_roi_y_min = settings.get("frame_roi_y_min", 48)
            frame_roi_y_max = settings.get("frame_roi_y_max", 432)
            print("Loaded settings from", settings_file)
    except Exception as e:
        print("Error loading settings:", e)

def save_settings():
    settings = {
        "pinch_threshold": pinch_threshold,
        "fist_threshold": fist_threshold,
        "smoothing_factor": smoothing_factor,
        "current_sensitivity": current_sensitivity,
        "frame_roi_x_min": frame_roi_x_min,
        "frame_roi_x_max": frame_roi_x_max,
        "frame_roi_y_min": frame_roi_y_min,
        "frame_roi_y_max": frame_roi_y_max
    }
    try:
        with open(settings_file, "w") as f:
            json.dump(settings, f)
        print("Saved settings to", settings_file)
    except Exception as e:
        print("Error saving settings:", e)

def is_pinch(hand_landmarks, threshold):
    thumb = hand_landmarks.landmark[4]
    index = hand_landmarks.landmark[8]
    distance = ((thumb.x - index.x)**2 + (thumb.y - index.y)**2)**0.5
    return distance < threshold

def is_fist(hand_landmarks, threshold):
    tips = [4, 8]
    bases = [2, 5]
    return all(
        abs(hand_landmarks.landmark[tips[i]].y - hand_landmarks.landmark[bases[i]].y) < threshold
        for i in range(2)
    )

def get_scroll_amount(hand_landmarks):
    index_y = hand_landmarks.landmark[8].y
    global prev_scroll_y
    if prev_scroll_y is None:
        prev_scroll_y = index_y
        return 0
    delta_y = index_y - prev_scroll_y
    prev_scroll_y = index_y
    return delta_y * 100

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to capture frame")
        break
    
    frame_counter += 1
    if frame_counter % frame_skip != 0:
        continue
    
    frame = cv2.flip(frame, 1)
    
    cv2.rectangle(frame, (frame_roi_x_min, frame_roi_y_min), (frame_roi_x_max, frame_roi_y_max), (255, 255, 0), 1)
    
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)
    
    if results.multi_hand_landmarks and virtual_mouse_active and not calibration_mode:
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
            
            screen_x = np.interp(index_x, [frame_roi_x_min, frame_roi_x_max], [0, screen_width])
            screen_y = np.interp(index_y, [frame_roi_y_min, frame_roi_y_max], [0, screen_height])
            
            screen_x = smoothing_factor * screen_x + (1 - smoothing_factor) * prev_screen_x
            screen_y = smoothing_factor * screen_y + (1 - smoothing_factor) * prev_screen_y
            prev_screen_x, prev_screen_y = screen_x, screen_y
            
            pyautogui.moveTo(screen_x + screen_offset_x, screen_y + screen_offset_y)
            
            current_time = time.time()
            pinch_detected = is_pinch(hand_landmarks, pinch_threshold)
            
            if pinch_detected and not is_dragging and not clicked and (current_time - last_click_time) > click_cooldown:
                if drag_start_time == 0:
                    drag_start_time = current_time
                elif current_time - drag_start_time > drag_threshold:
                    pyautogui.mouseDown()
                    is_dragging = True
                    gesture_feedback = "Dragging"
                    feedback_timeout = current_time + 1.0
                    print("Drag started")
            elif pinch_detected and is_dragging:
                gesture_feedback = "Dragging"
                feedback_timeout = current_time + 1.0
            elif not pinch_detected and is_dragging:
                pyautogui.mouseUp()
                is_dragging = False
                gesture_feedback = "Drag Ended"
                feedback_timeout = current_time + 1.0
                print("Drag ended")
            elif pinch_detected and not is_dragging and not clicked and (current_time - last_click_time) > click_cooldown:
                pyautogui.click()
                clicked = True
                last_click_time = current_time
                gesture_feedback = "Left Click Detected"
                feedback_timeout = current_time + 1.0
                print("Left click triggered")
            elif not pinch_detected:
                clicked = False
                drag_start_time = 0
            
            if is_fist(hand_landmarks, fist_threshold):
                pyautogui.rightClick()
                gesture_feedback = "Right Click Detected"
                feedback_timeout = current_time + 1.0
                print("Right click triggered")
            
            scroll_amount = get_scroll_amount(hand_landmarks)
            if abs(scroll_amount) > 5:
                pyautogui.scroll(int(scroll_amount))
                gesture_feedback = "Scrolling"
                feedback_timeout = current_time + 1.0
                print(f"Scroll: {scroll_amount:.1f}")
            
            print(f"Thumb tip: ({thumb_x}, {thumb_y})")
            print(f"Index fingertip: ({index_x}, {index_y})")
            print(f"Screen coordinates: ({screen_x:.1f}, {screen_y:.1f})")
    
    # Calculate FPS
    frame_count += 1
    current_time = time.time()
    if current_time - prev_time >= 1.0:
        fps = frame_count / (current_time - prev_time)
        frame_count = 0
        prev_time = current_time
    
    # Display UI elements
    cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    status_text = "Virtual Mouse: ON" if virtual_mouse_active else "Virtual Mouse: OFF"
    cv2.putText(frame, status_text, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    if gesture_feedback and current_time < feedback_timeout:
        cv2.putText(frame, gesture_feedback, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    cv2.putText(frame, f"Sensitivity: {current_sensitivity} ({smoothing_factor:.1f})", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, f"Pinch Thresh: {pinch_threshold:.3f}", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, f"Fist Thresh: {fist_threshold:.3f}", (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    calib_text = "Calibration: ON" if calibration_mode else "Calibration: OFF"
    cv2.putText(frame, calib_text, (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(frame, f"ROI: X({frame_roi_x_min},{frame_roi_x_max}) Y({frame_roi_y_min},{frame_roi_y_max})", (10, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    cv2.imshow("Virtual Mouse Feed", frame)
    
    # Handle key presses
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('t'):
        virtual_mouse_active = not virtual_mouse_active
        gesture_feedback = ""
        print(f"Virtual Mouse {'Enabled' if virtual_mouse_active else 'Disabled'}")
    elif key == ord('1'):
        smoothing_factor = sensitivity_modes["High"]
        current_sensitivity = "High"
        save_settings()
        print("Sensitivity set to High")
    elif key == ord('2'):
        smoothing_factor = sensitivity_modes["Low"]
        current_sensitivity = "Low"
        save_settings()
        print("Sensitivity set to Low")
    elif key == ord('p'):
        pinch_threshold = min(pinch_threshold + 0.005, 0.1)
        save_settings()
        print(f"Pinch threshold set to {pinch_threshold:.3f}")
    elif key == ord('P'):
        pinch_threshold = max(pinch_threshold - 0.005, 0.01)
        save_settings()
        print(f"Pinch threshold set to {pinch_threshold:.3f}")
    elif key == ord('f'):
        fist_threshold = min(fist_threshold + 0.005, 0.1)
        save_settings()
        print(f"Fist threshold set to {fist_threshold:.3f}")
    elif key == ord('F'):
        fist_threshold = max(fist_threshold - 0.005, 0.02)
        save_settings()
        print(f"Fist threshold set to {fist_threshold:.3f}")
    elif key == ord('c'):
        calibration_mode = not calibration_mode
        gesture_feedback = ""
        print(f"Calibration Mode {'Enabled' if calibration_mode else 'Disabled'}")
    elif calibration_mode:
        if key == ord('w'):
            frame_roi_y_min = max(frame_roi_y_min - 10, 0)
            frame_roi_y_max = max(frame_roi_y_max - 10, frame_roi_y_min + 50)
            save_settings()
            print(f"ROI Y adjusted: ({frame_roi_y_min}, {frame_roi_y_max})")
        elif key == ord('s'):
            frame_roi_y_max = min(frame_roi_y_max + 10, 480)
            frame_roi_y_min = min(frame_roi_y_min + 10, frame_roi_y_max - 50)
            save_settings()
            print(f"ROI Y adjusted: ({frame_roi_y_min}, {frame_roi_y_max})")
        elif key == ord('a'):
            frame_roi_x_min = max(frame_roi_x_min - 10, 0)
            frame_roi_x_max = max(frame_roi_x_max - 10, frame_roi_x_min + 50)
            save_settings()
            print(f"ROI X adjusted: ({frame_roi_x_min}, {frame_roi_x_max})")
        elif key == ord('d'):
            frame_roi_x_max = min(frame_roi_x_max + 10, 640)
            frame_roi_x_min = min(frame_roi_x_min + 10, frame_roi_x_max - 50)
            save_settings()
            print(f"ROI X adjusted: ({frame_roi_x_min}, {frame_roi_x_max})")

cap.release()
cv2.destroyAllWindows()
hands.close()