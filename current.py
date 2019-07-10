import numpy as np
import cv2
import time
import os
from _datetime import datetime
import datetime as dt

# String saved in log if no anomaly detected
status_good = "Good"
# String saved in log if bad or no welding detected
status_bad = "Bad"
# String saved in log if status can not be set
status_undef = "N/A"

# String saved in log as meaning of detected line
meaning_line = "Line (not welded)"
# String saved in log if no anomaly detected
meaning_clear = "-"
# String saved in log if camera can not be reached
meaning_undef = "Camera undefined"

# Local directory for log files
path_log = "log"
# Local directory to save images
path_temp = "temp"

# Strings saved in log as names of connected cameras
cam1_name = "Camera 1"
cam2_name = "Camera 2"

# Min percent of black to set as bad welded
detected_threshold_in_percent = 3
# Value of threshold to detect lines (not welded area)
# Depends from lighting; increase - bright, decrease - dark
detect_line_threshold = 60
# Value of threshold to detect holes (bad welded area)
# Depends from lighting; increase - dark, decrease - bright
detect_hole_threshold = 50

# Min length of line in pixels to be detected
min_line_length = 200
min_line_gap = 50

# Coordinates of detection area
x0 = 180
y0 = 180
x1 = 470
y1 = 280

# Flag of currently used camera
current_cam = 0
# Counter of current operation
counter = 0


# =========================================================

def create_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


# =========================================================

def create_timestamp():
    return dt.datetime.fromtimestamp(int(time.time()))


# =========================================================

def create_timestamp_millis():
    return int(round(time.time() * 1000))


# =========================================================

def current_cam_name():
    if current_cam == 0:
        return cam1_name
    else:
        return cam2_name


# =========================================================

def write_to_log(status, meaning):
    create_dir(path_log)

    # Create log file with name as current date
    td = dt.date.today()
    file_name = path_log + "/" + "log_{}.txt".format(td)

    # Create file if does not exist or append
    f = open(file_name, "a+")
    # Structure of string to write:
    # date-time, counter of actions, current camera, status of detection, meaning of detection
    f.write(str(create_timestamp()) + "\t" + str(counter) + "\t" + str(current_cam_name()) + "\t" + str(status) + "\t" +
            str(meaning) + "\n")
    f.close()


# =========================================================

def save_image(image):
    create_dir(path_temp)
    # Set file name as date-time stamp
    now = str(create_timestamp()).replace(":", "-").replace(" ", "_")
    img_name = "{}.jpg".format(now)

    # Draw black [(0,0,0)] rectangle [(x0, y0, x1, y1)] with line thickness 1 on image
    cv2.rectangle(image, (int(x0), int(y0)), (int(x1), int(y1)), (0, 0, 0), 1)
    # Save image in specified path
    cv2.imwrite(path_temp + "/" + img_name, image)


# =========================================================

def detect_line(origin):
    region = origin[int(y0):int(y1), int(x0):int(x1)]
    # Make origin image binary before detection;
    # 1 - inverse colors; background - black, anomaly - white
    rt, edges = cv2.threshold(region, detect_line_threshold, 255, 1)
    # Array of lines if any detected
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 200, minLineLength=min_line_length, maxLineGap=min_line_gap)

    # If found at least one line
    if hasattr(lines, 'any'):
        write_to_log(status_bad, meaning_line)
        return 1
    else:
        return 0


# =========================================================

def calc_percentage_of_black(t_image):
    roi = t_image[int(y0):int(y1), int(x0):int(x1)]

    # Total number of pixels in selected region
    total = roi.size
    # All not black pixels in region; black - (0,0,0)
    nz = cv2.countNonZero(roi)
    black = total - nz

    return black * 100 / total


# =========================================================

def detect_holes(origin):
    # Make origin image binary; background - white, anomaly - black
    rt, threshold_image = cv2.threshold(origin, detect_hole_threshold, 255, 0)
    black_pix = round(calc_percentage_of_black(threshold_image), 2)

    if black_pix >= detected_threshold_in_percent:
        write_to_log(status_bad, str(black_pix) + "%")
        return 1
    else:
        return 0


# =========================================================

def check_weld(original):
    if detect_holes(original) == 1 or detect_line(original) == 1:
        print("Bad")
    else:
        write_to_log(status_good, meaning_clear)
        print("Good")

    save_image(original)


# =========================================================

# Define connected cameras (if connected)
cam1 = cv2.VideoCapture(0)
cam2 = cv2.VideoCapture(1)

while True:
    # Check if camera 1 is ready
    if cam1.isOpened():
        # Read stream frame-by-frame
        ret1, frame1 = cam1.read()
        # Set frame gray before any manipulations with it
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        # Output modified stream frame-by-frame
        cv2.imshow('CAM 1', gray1)

    # Check if camera 2 is ready
    if cam2.isOpened():
        ret2, frame2 = cam2.read()
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        cv2.imshow('CAM 2', gray2)

    # Value of pressed button with delay 1
    k = cv2.waitKey(1)

    # Pressed "L" or "l"
    if k & 0xFF == 76 or k & 0xFF == 108:
        current_cam = 0
        try:
            gray1
        except NameError:
            print("Camera 1 is not ready")
            write_to_log(status_undef, meaning_undef)
        else:
            check_weld(gray1)
        counter += 1
    # Pressed "R" or "r"
    elif k & 0xFF == 82 or k & 0xFF == 114:
        current_cam = 1
        try:
            gray2
        except NameError:
            print("Camera 2 is not ready")
            write_to_log(status_undef, meaning_undef)
        else:
            check_weld(gray2)
        counter += 1
    # Exit from loop if "Esc" pressed
    elif k & 0xFF == 27:
        break

# Clear cache and close all windows created by process
cam1.release()
cam2.release()
cv2.destroyAllWindows()
