import os
import cv2
import numpy as np

CACHE_DIR = "./cache/serve_1"
TEST_MODE = True
FPS = 60

def build_index():
    if not os.path.exists(CACHE_DIR):
        return []
    return sorted([
        int(f.split('_')[1].split('.')[0])
        for f in os.listdir(CACHE_DIR)
        if f.endswith(".png")
    ])

FRAME_INDEX = build_index()

def get_dummy_image():
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(img, "DUMMY FRAME", (50, 240),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
    return img

def load_frame(frame_num):
    path = os.path.join(CACHE_DIR, f"frame_{frame_num:04d}.png")
    if os.path.exists(path):
        return cv2.imread(path)
    return None

def get_timestamp(frame_num):
    return frame_num / FPS

def resolve_frame(command):
    global FRAME_INDEX

    if not FRAME_INDEX:
        return 0

    latest = FRAME_INDEX[-1]

    if command[0] == 10:          # latest
        return latest

    elif command[0] == 11:        # previous
        return max(0, latest - command[1])

    elif command[0] == 15:        # specific
        return command[1]

    return None

def get_frame(command):
    frame_num = resolve_frame(command)

    if frame_num is None:
        return None

    if TEST_MODE:
        img = get_dummy_image()
    else:
        img = load_frame(frame_num)
        if img is None:
            img = get_dummy_image()

    return {
        "frame": frame_num,
        "timestamp": get_timestamp(frame_num),
        "image": img
    }

