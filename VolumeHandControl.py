import cv2
import time
import numpy as np
import math
import pyautogui
import HandTrackingModule as htm
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# Setup kamera
wCam, hCam = 640, 480
cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)

# Setup waktu & status
pTime = 0
muted = False
lastGestureTime = 0

# Deteksi tangan
detector = htm.handDetector(detectionCon=0.7)

# Setup pycaw volume
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
minVol, maxVol = volume.GetVolumeRange()[:2]
vol, volBar, volPer = 0, 400, 0

while True:
    success, img = cap.read()
    img = detector.findHands(img)
    lmList = detector.findPosition(img, draw=False)

    if len(lmList) != 0:
        fingers = detector.fingersUp()
        currentTime = time.time()

        # === Play/Pause ===
        if fingers == [1, 1, 1, 1, 1] and (currentTime - lastGestureTime) > 1:
            pyautogui.press("space")
            print("⏯️ Play/Pause")
            lastGestureTime = currentTime

        # === Mute ===
        elif fingers == [1, 1, 1, 0, 0] and not muted and (currentTime - lastGestureTime) > 1:
            volume.SetMute(1, None)
            print("🔇 Mute")
            muted = True
            lastGestureTime = currentTime

        # === Unmute ===
        elif fingers == [0, 0, 0, 0, 0] and muted and (currentTime - lastGestureTime) > 1:
            volume.SetMute(0, None)
            print("🔊 Unmute")
            muted = False
            lastGestureTime = currentTime

        # === Volume Control: Hanya aktif jika jempol & telunjuk terbuka ===
        elif fingers[0] and fingers[1] and sum(fingers) == 2:
            x1, y1 = lmList[4][1], lmList[4][2]
            x2, y2 = lmList[8][1], lmList[8][2]
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 15, (255, 0, 255), cv2.FILLED)
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
            cv2.circle(img, (cx, cy), 15, (255, 0, 255), cv2.FILLED)

            length = math.hypot(x2 - x1, y2 - y1)
            vol = np.interp(length, [30, 200], [minVol, maxVol])
            volBar = np.interp(length, [30, 200], [400, 150])
            volPer = np.interp(length, [30, 200], [0, 100])

            volume.SetMasterVolumeLevel(vol, None)

            if length < 30:
                cv2.circle(img, (cx, cy), 15, (0, 255, 0), cv2.FILLED)

    # UI Volume Bar
    cv2.rectangle(img, (50, 150), (85, 400), (0, 255, 0), 3)
    cv2.rectangle(img, (50, int(volBar)), (85, 400), (0, 255, 0), cv2.FILLED)
    cv2.putText(img, f'{int(volPer)} %', (40, 450),
                cv2.FONT_HERSHEY_COMPLEX, 1, (0, 250, 0), 3)

    # FPS
    cTime = time.time()
    fps = 1 / (cTime - pTime + 1e-5)
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (20, 50),
                cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 3)

    # Show
    cv2.imshow("Img", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
