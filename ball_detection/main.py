from flask import Flask, jsonify
import threading
import cv2 as cv
import numpy as np
import os
from time import time, sleep
from datetime import datetime, timezone
import requests
from flask import Flask, request


from dotenv import load_dotenv

load_dotenv()

"""connection"""
if os.getenv("CAMERA_CONNECT") == "True":
    CAMERA_CONNECT = True
else:
    CAMERA_CONNECT = False
if os.getenv("CAMERA_SERVO_CONNECT") == "True":
    CAMERA_SERVO_CONNECT = True
    INIT_START_TIME = None
else:
    CAMERA_SERVO_CONNECT = False
    INIT_START_TIME = 0
if os.getenv("COLOR_CONNECT") == "True":
    COLOR_CONNECT = True
else:
    COLOR_CONNECT = False

print(CAMERA_CONNECT, CAMERA_SERVO_CONNECT, COLOR_CONNECT)

shared_data = {
    "start_time": INIT_START_TIME,
    "data": None,
    "need_data": False,
    "condition": threading.Condition(),
}

"""function for getting ball information when detection"""


def get_distance(frame_width, radius):
    # distance = \frac{w_{real} * W_{frame}}{2 * w_{pixels} * tan(HFOV / 2)}
    w_real = float(os.getenv("BALL_DIAMETER"))
    HFOV = float(os.getenv("HFOV"))
    distance = (w_real * frame_width) / (
        2 * (2 * radius * 0.8) * np.tan(np.radians(HFOV) / 2)
    )
    return float(distance)


def get_angle(frame_width, x):
    # angle = \frac{\delta x}{W_{frame} * HFOV
    HFOV = float(os.getenv("HFOV"))
    angle = (x - frame_width / 2) / frame_width * HFOV
    return float(angle)


def get_cam_angle(start_time):
    # 90 ~ -90, -90 ~ 90 -- 20 ms/°, delay: 1s
    if not CAMERA_SERVO_CONNECT:
        return 0
    time_interval = 20
    angle = int((time() - start_time) * 1000 / time_interval) % (
        360 + 1000 / time_interval * 2 + 2
    )
    if angle <= 180:
        # -90 ~ 90
        angle -= 90
    elif angle <= 180 + 1000 / time_interval:
        # 1s
        angle = 90
    elif angle <= 180 + 1000 / time_interval + 181:
        # 90 ~ -90
        angle = 90 - (angle - 181 - 1000 / time_interval)
    else:
        # 1s
        angle = -90

    return int(angle)


def get_move_time(distance):
    # time = (distance - ACCE_DECE_DIST) / SPEED
    SPEED = float(os.getenv("SPEED"))
    ACCE_DECE_DIST = float(os.getenv("ACCE_DECE_DIST"))
    move_time = (distance - ACCE_DECE_DIST) / SPEED
    if move_time < 0:
        return -1
    return move_time


def get_car_move(distance, angle):
    y = distance
    x = float(y * np.tan(np.radians(angle)))
    move_time = [get_move_time(y), get_move_time(abs(x))]
    print(f"({x:.2f}, {y:.2f}); angle: {angle:.2f}")

    if x > 0:
        turn_direction = "right"
    else:
        turn_direction = "left"

    return move_time, turn_direction


"""color information"""
red_low_lower = np.array([0, 120, 120])
red_low_upper = np.array([10, 255, 255])
red_high_lower = np.array([170, 120, 120])
red_high_upper = np.array([180, 255, 255])
yellow_lower = np.array([20, 100, 150])
yellow_upper = np.array([30, 255, 255])
blue_lower = np.array([100, 150, 120])
blue_upper = np.array([140, 255, 255])

color_info = {
    "red": {
        "border_color": (26, 26, 154),
    },
    "yellow": {
        "border_color": (51, 153, 255),
    },
    "blue": {
        "border_color": (161, 28, 28),
    },
}


def opencv_thread(shared_data):
    WINDOW_NAME = "frame"

    detected_balls = []
    history_cam_angle = []
    turn_around = False

    if CAMERA_CONNECT:
        while shared_data["start_time"] is None:
            sleep(2)
    else:
        TEST_STREAM_URL = os.getenv("TEST_STREAM_URL")
        cap = cv.VideoCapture(TEST_STREAM_URL)

    while True:
        if CAMERA_CONNECT:
            frame = cv.imread("received_image.jpg")
            if frame is None:
                continue
        else:
            # frame = cv.imread("test_img/S__43565061_0.jpg")
            # frame = cv.resize(frame, dsize=None, fx=0.1, fy=0.1)
            ret, frame = cap.read()
            if not ret:
                raise ValueError("Can't receive frame.")

        # turn to hsv
        hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)

        # setup color mask
        color_info["red"]["mask"] = cv.inRange(hsv, red_low_lower, red_low_upper)
        red_high_mask = cv.inRange(hsv, red_high_lower, red_high_upper)
        cv.bitwise_or(
            color_info["red"]["mask"], red_high_mask, color_info["red"]["mask"]
        )
        color_info["yellow"]["mask"] = cv.inRange(hsv, yellow_lower, yellow_upper)
        color_info["blue"]["mask"] = cv.inRange(hsv, blue_lower, blue_upper)

        # find color in contours
        for color, info in color_info.items():
            # use erode + dilate to remove noises
            kernel = np.ones((5, 5), np.uint8)
            info["mask"] = cv.morphologyEx(info["mask"], cv.MORPH_CLOSE, kernel)

            # find contours
            contours, _ = cv.findContours(
                info["mask"], cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE
            )
            for contour in contours:
                ((x, y), radius) = cv.minEnclosingCircle(contour)
                cv.circle(
                    info["mask"], (int(x), int(y)), int(radius), info["border_color"], 2
                )

                # exclude too small case
                if cv.contourArea(contour) < 400 or radius <= 5:
                    continue

                # exclude not ball case
                circle_mask = np.zeros_like(info["mask"], dtype=np.uint8)
                cv.circle(circle_mask, (int(x), int(y)), int(radius), 255, -1)
                circle_area = cv.bitwise_and(
                    info["mask"], info["mask"], mask=circle_mask
                )
                if np.sum(circle_area > 0) / np.sum(circle_mask > 0) < 0.8:
                    continue

                cv.circle(frame, (int(x), int(y)), int(radius), info["border_color"], 2)
                distance = get_distance(frame.shape[1], radius)
                angle = get_angle(frame.shape[1], x)
                cam_angle = get_cam_angle(shared_data["start_time"])

                detected_balls.append(
                    {
                        "color": ["red", "yellow", "blue"].index(color),
                        "radius": radius,
                        "distance": distance,
                        "angle": float(angle),
                        "cam_angle": cam_angle,
                    }
                )

        # return the nearest ball
        with shared_data["condition"]:
            if shared_data["need_data"] is True:
                current_cam_angle = get_cam_angle(shared_data["start_time"])
                if CAMERA_CONNECT and CAMERA_SERVO_CONNECT:
                    if (
                        len(history_cam_angle) > 0
                        and current_cam_angle == history_cam_angle[-1]
                    ):
                        # time is not enough for 1 degree
                        pass
                    elif len(history_cam_angle) < 2:
                        # in middle of a one-way
                        history_cam_angle.append(current_cam_angle)
                    elif (current_cam_angle - history_cam_angle[1]) * (
                        history_cam_angle[1] - history_cam_angle[0]
                    ) > 0:
                        # in middle of a one-way
                        history_cam_angle.append(current_cam_angle)
                        history_cam_angle.pop(0)
                    elif turn_around is False:
                        # start a complete one-way
                        print("start")
                        detected_balls = []
                        history_cam_angle = []
                        turn_around = True
                    else:
                        # finish a complete one-way
                        print("done")
                        if len(detected_balls) > 0:
                            # get nearest
                            detected_balls = sorted(
                                detected_balls, key=lambda x: x["distance"]
                            )
                            nearest_ball = detected_balls[0]
                            move_time, turn_direction = get_car_move(
                                nearest_ball["distance"],
                                nearest_ball["angle"] + nearest_ball["cam_angle"],
                            )
                            nearest_ball["move_time1"] = move_time[0]
                            nearest_ball["move_time2"] = move_time[1]
                            nearest_ball["turn_direction"] = turn_direction[0]
                            shared_data["data"] = nearest_ball
                        else:
                            shared_data["data"] = ""

                        shared_data["condition"].notify_all()
                        detected_balls = []
                        history_cam_angle = []
                        turn_around = False
                else:
                    # finish a complete one-way
                    print("done")
                    if len(detected_balls) > 0:
                        # get nearest
                        detected_balls = sorted(
                            detected_balls, key=lambda x: x["distance"]
                        )
                        nearest_ball = detected_balls[0]
                        move_time, turn_direction = get_car_move(
                            nearest_ball["distance"],
                            nearest_ball["angle"] + nearest_ball["cam_angle"],
                        )
                        nearest_ball["move_time1"] = move_time[0]
                        nearest_ball["move_time2"] = move_time[1]
                        nearest_ball["turn_direction"] = turn_direction
                        shared_data["data"] = nearest_ball
                    else:
                        shared_data["data"] = ""

                    shared_data["condition"].notify_all()
                    detected_balls = []
                    history_cam_angle = []
                    turn_around = False

        # show frame
        cv.imshow(WINDOW_NAME, frame)
        # for color, info in color_info.items():
        #     cv.imshow(color, info["mask"])

        # check exit
        if cv.waitKey(1) == 27:
            print("Press esc to exit")
            break

        if cv.getWindowProperty(WINDOW_NAME, cv.WND_PROP_VISIBLE) < 1:
            print("Click 'x' to exit")
            break

    # cap.release()
    cv.destroyAllWindows()


"""for connection with car"""
app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    return "Hello"


@app.route("/start", methods=["POST"])
def get_start_time():
    try:
        # get camera boot time
        # if shared_data["start_time"] is None:
        time_full_str = request.get_data(as_text=True)
        print(time_full_str)
        datetime_str = time_full_str[: time_full_str.index(" + ")]
        ms_str = time_full_str[time_full_str.index(" + ") + 3 : -1]

        format_str = "%Y-%m-%d %H:%M:%S"
        dt = datetime.strptime(datetime_str, format_str).replace(tzinfo=timezone.utc)
        camera_boot_time = int(dt.timestamp()) + int(ms_str) / 1000
        shared_data["start_time"] = camera_boot_time
        print(f"Start time: {time_full_str}")
        return "Start time received successfully", 200
    except Exception as e:
        return f"Error: {str(e)}", 500


@app.route("/data", methods=["GET"])
def get_ball_data():
    with shared_data["condition"]:
        # ask to get nearest ball data
        shared_data["need_data"] = True
        shared_data["condition"].notify_all()
        shared_data["condition"].wait_for(lambda: shared_data["data"] is not None)
        result = shared_data["data"]

        # rotate gate
        if COLOR_CONNECT:
            color_url = os.getenv("COLOR_URL")
            if result != "":
                if result["color"] == 0:
                    color_url += "r"
                elif result["color"] == 1:
                    color_url += "y"
                else:
                    color_url += "b"

        try:
            response = requests.get(color_url)
            print(response)
        except Exception as e:
            print("fail to connect to color URL")

        shared_data["data"] = None
        shared_data["need_data"] = False

    print(f"\n{datetime.now()}\nSend {result}")
    return jsonify(result)


@app.route("/upload", methods=["POST"])
def get_pic():
    # get image from camera
    try:
        image_data = request.data
        with open("received_image.jpg", "wb") as f:
            f.write(image_data)
        return "Image received successfully", 200
    except Exception as e:
        return f"Error: {str(e)}", 500


if __name__ == "__main__":
    # opencv
    threading.Thread(target=opencv_thread, args=(shared_data,), daemon=True).start()

    # server
    app.run(host="0.0.0.0", port=5000)
