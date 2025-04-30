import cv2

# Initialize webcam
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture video")
        break
    
    # Flip the frame horizontally to correct mirroring
    frame = cv2.flip(frame, 1)  # 1 = horizontal flip, 0 = vertical flip, -1 = both
    
    # Display the frame
    cv2.imshow("Webcam Test", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()