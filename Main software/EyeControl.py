import Serial
import threading
import time
import random
import json
from pynput import keyboard

EMOTION_LABELS = ['angry', 'disgusted', 'happy', 'neutral', 'sad', 'surprised', 'mischievous']
EMOTION_LABELS_EXTRA = ['hypnotic', 'heart', 'rainbow', 'nightmare', 'gears', 'sans']
EYELID_SETS = [(-0.2, -0.2), (-0.2, -0.2), (0.3, 0.3), (0.3, 0.3), (0.2, 0.6), (0.6, 0.2), (0, 0), (0, 0), (0, 0), (0, 0), (0, 0), (0, 0)]
emotion_scores = [0] * len(EMOTION_LABELS)
expression_manual_mode = False
manual_mode_timer = None
expression_manual_id = 0
displacement_eye = (0,0)
left_eye_closeness = 0
right_eye_closeness = 0
eye_tracking_mode = True
crossed_eyes = False

left_held = False
right_held = False
up_held = False
down_held = False
enter_held = False
left_press_time = 0.0
right_press_time = 0.0
left_blink_until = 0.0
right_blink_until = 0.0
left_blink_prev = False
right_blink_prev = False
expr_select_mode = False
expr_keys = []

TIMER_MOVE_RAND_MAX = 6
TIMER_EYELID_RAND_MAX = 12
TIMER_MANUALTOAUTO_EXPR = 600
timer_xmove = 0
timer_ymove = 0
timer_eyelidmove = 0
x_current = 0
y_current = 0

def call_controlbot_command(topic, payload):
    with open("controlbot_ipc.json", "w") as controlbot_ipc:
        json.dump({"topic": topic, "payload": payload, "user_info": {'id': 0, 'first_name': "Mekhy"}, "user_name": "Mekhy"}, controlbot_ipc)

def random_gaussian(min_value=0.0, max_value=1.0):
    mean = (min_value + max_value) / 2.0
    sigma = (max_value - mean) / 3.0  # 99.7% of values within [min, max]
    value = random.gauss(mean, sigma)
    return max(min_value, min(max_value, value))  # clamp

def update_eye_movement():
    global timer_xmove, timer_ymove, timer_eyelidmove, x_current, y_current, displacement_eye, left_eye_closeness, right_eye_closeness, crossed_eyes
    global left_held, right_held, up_held, down_held, left_blink_until, right_blink_until, left_blink_prev, right_blink_prev
    if not eye_tracking_mode:
        displacement_eye = (0, 0)
        (left_eye_closeness, right_eye_closeness) = (0, 0)
        return
    now = time.time()
    crossed_eyes = True if enter_held else False
    if (left_held and not right_held):
        x_current = 1
    elif (right_held and not left_held):
        x_current = -1
    elif timer_xmove == 0 or now >= timer_xmove:
        timer_xmove = now + random_gaussian(0, TIMER_MOVE_RAND_MAX)
        x_current = random_gaussian(-0.5, 0.5)
    if up_held:
        y_current = 1
    elif timer_ymove == 0 or now >= timer_ymove:
        timer_ymove = now + random_gaussian(0, TIMER_MOVE_RAND_MAX)
        y_current = random_gaussian(-0.25, 0.25)
    if timer_eyelidmove == 0 or now >= timer_eyelidmove:
        timer_eyelidmove = now + random_gaussian(0, TIMER_EYELID_RAND_MAX)
        (left_eye_closeness, right_eye_closeness) = random.choice(EYELID_SETS)
    lb = now <= left_blink_until
    rb = now <= right_blink_until
    if down_held:
        left_eye_closeness = 1.2
        right_eye_closeness = 1.2
    else:
        if lb:
            left_eye_closeness = 1.2
            right_eye_closeness = 0
        if rb:
            left_eye_closeness = 0
            right_eye_closeness = 1.2
        if (not lb and not rb) and (left_blink_prev or right_blink_prev):
            (left_eye_closeness, right_eye_closeness) = (0, 0)
            timer_eyelidmove = now + random_gaussian(0, TIMER_EYELID_RAND_MAX)
    left_blink_prev = lb
    right_blink_prev = rb
    displacement_eye = (x_current, y_current)

def reset_expression_manual_mode():
    global expression_manual_mode
    expression_manual_mode = False

def on_press(key):
    global left_held, right_held, up_held, down_held, enter_held, left_press_time, right_press_time, expression_manual_mode, expression_manual_id, emotion_scores, manual_mode_timer
    global expr_select_mode, expr_keys
    t = time.time()
    def is_cancel_key(k):
        if (hasattr(k, 'vk') and k.vk == 166) or (hasattr(k, 'value') and hasattr(k.value, 'vk') and k.value.vk == 166):
            Serial.send_debug("Cancel key pressed")
            return True
        return False
    if key == keyboard.Key.menu:
        expr_select_mode = True
        expr_keys = []
        Serial.send_debug("Expression select mode started")
        return
    if expr_select_mode:
        if is_cancel_key(key):
            expr_select_mode = False
            expr_keys = []
            return
        allowed = {keyboard.Key.enter, keyboard.Key.left, keyboard.Key.right, keyboard.Key.up, keyboard.Key.down}
        if key in allowed:
            expr_keys.append(key)
            if len(expr_keys) >= 2:
                mapping = {
                    (keyboard.Key.enter,keyboard.Key.enter): 'neutral',
                    (keyboard.Key.enter,keyboard.Key.right): 'angry',
                    (keyboard.Key.enter,keyboard.Key.left): 'disgusted',
                    (keyboard.Key.enter,keyboard.Key.up): 'happy',
                    (keyboard.Key.enter,keyboard.Key.down): 'sad',
                    (keyboard.Key.up,keyboard.Key.up): 'surprised',
                    (keyboard.Key.left,keyboard.Key.left): 'mischievous',
                    (keyboard.Key.down,keyboard.Key.down): 'nightmare',
                    (keyboard.Key.right,keyboard.Key.right): 'heart',
                    (keyboard.Key.up,keyboard.Key.right): 'gears',
                    (keyboard.Key.down,keyboard.Key.right): 'sans',
                    (keyboard.Key.up,keyboard.Key.down): 'hypnotic',
                    (keyboard.Key.down,keyboard.Key.up): 'hypnotic',
                    (keyboard.Key.left,keyboard.Key.right): 'rainbow',
                    (keyboard.Key.right,keyboard.Key.left): 'rainbow',
                }
                chosen = mapping.get((expr_keys[0], expr_keys[1]))
                if chosen:
                    if manual_mode_timer:
                        manual_mode_timer.cancel()
                    manual_mode_timer = threading.Timer(TIMER_MANUALTOAUTO_EXPR, reset_expression_manual_mode)
                    manual_mode_timer.start()
                    expression_manual_mode = True
                    if chosen in EMOTION_LABELS:
                        expression_manual_id = 0
                        for i in range(len(emotion_scores)):
                            emotion_scores[i] = 1 if EMOTION_LABELS[i] == chosen else 0
                    elif chosen in EMOTION_LABELS_EXTRA:
                        expression_manual_id = EMOTION_LABELS_EXTRA.index(chosen) + 6
                    Serial.send_debug(f"Emotion {chosen} selected")
                expr_select_mode = False
                expr_keys = []
        return
    if key == keyboard.Key.left:
        if not left_held:
            left_press_time = t
        left_held = True
    elif key == keyboard.Key.right:
        if not right_held:
            right_press_time = t
        right_held = True
    elif key == keyboard.Key.up:
        up_held = True
    elif key == keyboard.Key.down:
        down_held = True
    elif key == keyboard.Key.enter:
        enter_held = True

def on_release(key):
    global left_held, right_held, up_held, down_held, enter_held, left_press_time, right_press_time, left_blink_until, right_blink_until, timer_xmove, timer_ymove, timer_eyelidmove
    t = time.time()
    if key == keyboard.Key.left:
        if left_held and (t - left_press_time) < 0.3:
            left_blink_until = t + 0.5
        left_held = False
        timer_xmove = 0
    elif key == keyboard.Key.right:
        if right_held and (t - right_press_time) < 0.3:
            right_blink_until = t + 0.5
        right_held = False
        timer_xmove = 0
    elif key == keyboard.Key.up:
        up_held = False
        timer_ymove = 0
    elif key == keyboard.Key.down:
        down_held = False
        timer_eyelidmove = 0
    elif key == keyboard.Key.enter:
        enter_held = False

keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
keyboard_listener.start()


if __name__ == "__main__":
    while True:
        update_eye_movement()
        time.sleep(0.01)