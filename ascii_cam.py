import cv2
import numpy as np
import pyvirtualcam
import msvcrt
import threading
import time
from PIL import Image, ImageDraw, ImageFont

# --- Config ---
CAM_INDEX        = 0
ASPECT           = 400 / 720
ASCII_COLS       = 100
FONT_SIZE        = 16
FPS              = 30
FONT_PATH        = "C:/Windows/Fonts/cour.ttf"
COLOR_BOOST      = 2.0
BRIGHTNESS_BOOST = 1.5
ASCII_SCENE      = "Gárrulo"
GAMEPLAY_SCENE   = "Gameplay"
GAMEPLAY_CAM_GRP = "Webcam"   # group name in Gameplay scene containing the camera
OBS_HOST         = "localhost"
OBS_PORT         = 4455
OBS_PASSWORD     = ""

ASCII_CHARS = ' .\'`^",:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$'

current_scene = ""
scene_lock    = threading.Lock()
obs_cl        = None   # ReqClient, set by obs_listener

def pixel_to_ascii(gray_val):
    return ASCII_CHARS[int(gray_val / 255 * (len(ASCII_CHARS) - 1))]

def boost_saturation(frame_bgr, factor):
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * factor, 0, 255)
    hsv[:, :, 2] = np.clip(hsv[:, :, 2] * BRIGHTNESS_BOOST, 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

def frame_to_ascii_image(frame_bgr, cols, out_w, out_h, font, font_w, font_h):
    frame_bgr  = boost_saturation(frame_bgr, COLOR_BOOST)
    gray       = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    rgb        = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    rows       = int(cols * (out_h / out_w) * (font_w / font_h))
    small_gray = cv2.resize(gray, (cols, rows))
    small_rgb  = cv2.resize(rgb,  (cols, rows))
    img        = Image.new('RGB', (out_w, out_h), color=(0, 0, 0))
    draw       = ImageDraw.Draw(img)
    for i, (gray_row, color_row) in enumerate(zip(small_gray, small_rgb)):
        x = 0
        for gray_val, pixel_rgb in zip(gray_row, color_row):
            draw.text((x, i * font_h), pixel_to_ascii(gray_val),
                      font=font, fill=tuple(int(c) for c in pixel_rgb))
            x += font_w
    return np.array(img)

def _get_gameplay_cam_item_id():
    items = obs_cl.get_scene_item_list(GAMEPLAY_SCENE).scene_items
    item_id = next(
        (i['sceneItemId'] for i in items if i['sourceName'] == GAMEPLAY_CAM_GRP),
        None
    )
    if item_id is None:
        print(f"Could not find '{GAMEPLAY_CAM_GRP}' in '{GAMEPLAY_SCENE}'")
    return item_id

def release_gameplay_cam():
    """Disable the OBS webcam source so the physical camera is free for us to grab."""
    global obs_cl
    if obs_cl is None:
        return
    try:
        item_id = _get_gameplay_cam_item_id()
        if item_id is None:
            return
        obs_cl.set_scene_item_enabled(GAMEPLAY_SCENE, item_id, False)
        time.sleep(0.5)   # wait for OBS driver to release the device
        print("Gameplay cam released for ASCII capture.")
    except Exception as e:
        print(f"Release error: {e}")

def bounce_gameplay_cam():
    """Re-enable the OBS webcam source after we have released the physical camera."""
    global obs_cl
    if obs_cl is None:
        return
    try:
        time.sleep(0.4)   # give driver time to release
        item_id = _get_gameplay_cam_item_id()
        if item_id is None:
            return
        obs_cl.set_scene_item_enabled(GAMEPLAY_SCENE, item_id, False)
        time.sleep(0.3)
        obs_cl.set_scene_item_enabled(GAMEPLAY_SCENE, item_id, True)
        print("Gameplay cam bounced.")
    except Exception as e:
        print(f"Bounce error: {e}")

def obs_listener():
    global current_scene, obs_cl
    try:
        import obsws_python as obs
        obs_cl = obs.ReqClient(host=OBS_HOST, port=OBS_PORT, password=OBS_PASSWORD)
        with scene_lock:
            current_scene = obs_cl.get_current_program_scene().current_program_scene_name.lower()
        print(f"OBS connected. Current scene: {current_scene}")

        ev = obs.EventClient(host=OBS_HOST, port=OBS_PORT, password=OBS_PASSWORD)
        def on_current_program_scene_changed(data):
            global current_scene
            with scene_lock:
                current_scene = data.scene_name.lower()
            print(f"Scene: {current_scene}")
        ev.callback.register(on_current_program_scene_changed)
        threading.Event().wait()
    except ImportError:
        print("obsws-python not installed.")
        with scene_lock:
            current_scene = ASCII_SCENE.lower()
    except Exception as e:
        print(f"OBS WebSocket error: {e}")
        with scene_lock:
            current_scene = ASCII_SCENE.lower()

def main():
    global current_scene

    font     = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    test_img = Image.new('RGB', (200, 200))
    bbox     = ImageDraw.Draw(test_img).textbbox((0, 0), 'A', font=font)
    font_w   = bbox[2] - bbox[0]
    font_h   = bbox[3] - bbox[1]
    rows       = max(1, round(ASCII_COLS * ASPECT * (font_w / font_h)))
    OUT_WIDTH  = ASCII_COLS * font_w
    OUT_HEIGHT = rows * font_h
    print(f"Grid: {ASCII_COLS}×{rows} chars  |  Canvas: {OUT_WIDTH}×{OUT_HEIGHT}px")

    threading.Thread(target=obs_listener, daemon=True).start()

    blank = np.zeros((OUT_HEIGHT, OUT_WIDTH, 3), dtype=np.uint8)
    cap   = None

    with pyvirtualcam.Camera(width=OUT_WIDTH, height=OUT_HEIGHT, fps=FPS,
                              fmt=pyvirtualcam.PixelFormat.RGB) as cam:
        print(f"Virtual camera: {cam.device}")
        print("Press Q to quit.")

        while True:
            with scene_lock:
                in_ascii = current_scene == ASCII_SCENE.lower()

            if in_ascii:
                if cap is None:
                    release_gameplay_cam()
                    cap = cv2.VideoCapture(CAM_INDEX, cv2.CAP_DSHOW)
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  480)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 268)
                    print("Webcam opened.")
                ret, frame = cap.read()
                cam.send(frame_to_ascii_image(frame, ASCII_COLS, OUT_WIDTH, OUT_HEIGHT,
                                              font, font_w, font_h) if ret else blank)
            else:
                if cap is not None:
                    cap.release()
                    cap = None
                    print("Webcam released.")
                    threading.Thread(target=bounce_gameplay_cam, daemon=True).start()
                cam.send(blank)

            cam.sleep_until_next_frame()

            if msvcrt.kbhit() and msvcrt.getch() == b'q':
                break

    if cap is not None:
        cap.release()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
    input("Press Enter to exit...")