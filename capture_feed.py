import cv2

# Initialize webcam
cap = cv2.VideoCapture(0)

# Check if webcam opened successfully
if not cap.isOpened():
    print("Error: Could not open webcam")
    exit()

# Set resolution to 640x480 for performance
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

while True:
    # Capture frame
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to capture frame")
        break
    
    # Flip frame horizontally for mirrored view
    frame = cv2.flip(frame, 1)
    
    # Resize frame to ensure consistent output (optional, since we set capture resolution)
    frame = cv2.resize(frame, (640, 480))
    
    # Display frame
    cv2.imshow("Virtual Mouse Feed", frame)
    
    # Exit on 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()