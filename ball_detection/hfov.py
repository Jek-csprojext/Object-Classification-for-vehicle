import cv2 as cv
import numpy as np
import os
from time import time
from dotenv import load_dotenv

load_dotenv()

# get distance
print(
    "Please place the target at a fixed position in front of the camera and measure the distance between the target and the camera\n"
)
distance = float(input("distance (cm): "))

# get correction points
correction_points = []


def add_correction_point(event, x, y, flags, param):
    global correction_points
    if event == cv.EVENT_LBUTTONDOWN:
        correction_points.append((x, y))


def empty_callback(event, x, y, flags, param):
    pass


WINDOW_NAME = "Correction"
cv.namedWindow(WINDOW_NAME)
cv.setWindowProperty(WINDOW_NAME, cv.WND_PROP_TOPMOST, 1)
cv.setMouseCallback(WINDOW_NAME, add_correction_point)


last_frame = None
correction_finish_time = None

# stream_url = os.getenv("TEST_STREAM_URL")
# cap = cv.VideoCapture(stream_url)
cap = cv.VideoCapture(0)


while True:
    ret, frame = cap.read()
    if not ret:
        raise ValueError("Can't receive frame.")
    frame = cv.imread("received_image.jpg")

    hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)

    for point in correction_points:
        cv.circle(frame, point, 5, (0, 0, 255), -1)
        cv.putText(
            frame,
            f"{point}",
            (point[0] - 5, point[1] - 10),
            cv.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 0),
            2,
        )

    cv.imshow(WINDOW_NAME, frame)

    if len(correction_points) == 2:
        if correction_finish_time is None:
            cv.setMouseCallback(WINDOW_NAME, empty_callback)
            correction_finish_time = time()
        elif time() - correction_finish_time > 1:
            last_frame = frame
            break

    if cv.waitKey(1) == 27:
        print("Press esc to exit")
        last_frame = frame
        break

    if cv.getWindowProperty(WINDOW_NAME, cv.WND_PROP_VISIBLE) < 1:
        print("Click 'x' to exit")
        last_frame = frame
        break

cap.release()
cv.destroyAllWindows()

# calculate HFOV
if len(correction_points) != 2:
    raise ValueError("Correction failed")

print()
w_pixels = np.linalg.norm(
    [np.array(correction_points[0]) - np.array(correction_points[1])]
)
print(f"target width (pixel): {w_pixels}")
w_real = float(input("target real width (cm): "))
frame_pixels = float(last_frame.shape[1])
print(f"frame width (pixel): {frame_pixels}")
w_frame = w_real / w_pixels * frame_pixels
print(f"frame real width (cm): {w_frame}")

hfov = np.degrees(2 * np.arctan(w_frame / (2 * distance)))
hfov = int(np.ceil(hfov / 5) * 5)
print(f"HFOV: {hfov}")

print("\nPlease copy the below sentence to .env file")
print(f"\nHFOV={hfov}\n")
