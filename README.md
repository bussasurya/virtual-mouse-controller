# virtual-mouse-controlle

A Python-based project that uses OpenCV and MediaPipe for hand gesture recognition to control a virtual mouse and play the Chrome Dinosaur Game. The virtual mouse tracks thumb and index fingertips to move the cursor, click, drag, and scroll, while the Dino Game uses index finger movements to jump and duck.
Features

Virtual Mouse:

Tracks thumb (#4) and index (#8) fingertips via webcam.
Cursor movement: Index finger in ROI (x: 64–576, y: 48–432).
Gestures: Pinch (left click), fist (right click), scroll, drag.
Multi-monitor support, ROI calibration, settings persistence (mouse_settings.json).
UI feedback: FPS, gesture status, sensitivity controls.


Chrome Dinosaur Game Control:

Controls chrome://dino with hand gestures.
Jump: Move index finger upward (spacebar).
Duck: Drag index downward with middle/ring/pinky curled (down arrow).
Opens Chrome, focuses game window, and provides real-time UI feedback.



Requirements

Python 3.8+
Libraries:pip install opencv-python mediapipe numpy pyautogui


Webcam (640x480 recommended)
Google Chrome (for Dino Game)
Windows 10/11 (tested)

Installation

Clone the repository:
git clone https://github.com/bussasurya/virtual-mouse-controller.git
cd virtual-mouse-controller


Install dependencies:
pip install -r requirements.txt


Ensure Chrome is installed and set as default browser.


Usage
Virtual Mouse

Run the virtual mouse script:python mouse_multi.py


Controls:
Move index finger in ROI to control cursor.
Pinch (thumb-index) for left click.
Fist for right click.
Press t to toggle mouse, q to quit.
Adjust sensitivity: 1 (low), 2 (high); thresholds: p/P (pinch), f/F (fist).
Calibrate ROI: c, w/s/a/d.



Chrome Dinosaur Game

Run the gesture control script:python dino_gestures.py


Controls:
Flick index up to jump (starts game or jumps T-Rex).
Drag index down with middle/ring/pinky curled to duck.
Press q to quit.


Ensure Chrome window is focused (adjust pyautogui.click(x, y) if needed).

Project Structure

mouse_multi.py: Virtual mouse with multi-monitor support and calibration.
dino_gestures.py: Gesture control for Chrome Dinosaur Game.
hand_detection.py: Initial hand tracking prototype.
mouse_settings.json: Stores mouse sensitivity and ROI settings.
requirements.txt: Python dependencies.

Development

Status: Chrome Dino gesture control in progress (Step 3: Game Integration).
Next Steps: Optimize gestures, add toggle, refine UI.
Issues: If Microsoft Store opens instead of Chrome, set Chrome as default browser or update chrome_path in dino_gestures.py.

Contributing

Fork the repository.
Create a feature branch: git checkout -b feature-name.
Commit changes: git commit -m "Add feature".
Push to branch: git push origin feature-name.
Open a pull request.

License
MIT License. See LICENSE for details.
Acknowledgments

Built with OpenCV, MediaPipe, and PyAutoGUI.
Inspired by gesture-based UI experiments.
Developed by bussasurya.

