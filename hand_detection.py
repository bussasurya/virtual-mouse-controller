import cv2
import mediapipe as mp
import numpy as np
import pyautogui

# Initialize webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam")
    exit()

# Set resolution to 640x480 for performance
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

# Get screen resolution
screen_width, screen_height = pyautogui.size()

# Disable PyAutoGUI fail-safe (optional, use with caution)
pyautogui.FAILSAFE = False

while True:
    # Capture frame
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to capture frame")
        break
    
    # Flip frame horizontally for mirrored view
    frame = cv2.flip(frame, 1)
    
    # Resize frame to ensure consistent output
    frame = cv2.resize(frame, (640, 480))
    
    # Convert frame to RGB for MediaPipe
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Process frame for hand detection
    results = hands.process(frame_rgb)
    
    # Draw landmarks and move cursor if hands are detected
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Draw all landmarks and connections
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # Get thumb tip (landmark #4) coordinates
            thumb_tip = hand_landmarks.landmark[4]
            thumb_x = int(thumb_tip.x * frame.shape[1])
            thumb_y = int(thumb_tip.y * frame.shape[0])
            
            # Get index fingertip (landmark #8) coordinates
            index_tip = hand_landmarks.landmark[8]
            index_x = int(index_tip.x * frame.shape[1])
            index_y = int(index_tip.y * frame.shape[0])
            
            # Draw circles at thumb and index fingertips
            cv2.circle(frame, (thumb_x, thumb_y), 5, (0, 255, 0), -1)  # Green for thumb
            cv2.circle(frame, (index_x, index_y), 5, (0, 0, 255), -1)   # Red for index
            
            # Map index fingertip to screen coordinates
            screen_x = np.interp(index_x, [0, frame.shape[1]], [0, screen_width])
            screen_y = np.interp(index_y, [0, frame.shape[0]], [0, screen_height])
            
            # Move mouse cursor
            pyautogui.moveTo(screen_x, screen_y)
            
            # Print coordinates for debugging
            print(f"Thumb tip: ({thumb_x}, {thumb_y})")
            print(f"Index fingertip: ({index_x}, {index_y})")
            print(f"Screen coordinates: ({screen_x:.1f}, {screen_y:.1f})")
    
    # Display frame
    cv2.imshow("Virtual Mouse Feed", frame)
    
    # Exit on 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
hands.close()