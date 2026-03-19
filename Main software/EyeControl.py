import Serial
import Waveform
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
up_press_time = 0.0
down_press_time = 0.0
enter_press_time = 0.0
left_blink_until = 0.0
right_blink_until = 0.0
left_blink_prev = False
right_blink_prev = False

TIMER_MOVE_RAND_MAX = 6
TIMER_EYELID_RAND_MAX = 12
TIMER_MANUALTOAUTO_EXPR = 600
HOLD_THRESHOLD = 0.2
COMBO_WINDOW = 0.4
combo_buffer = []
pending_blink_timer = None
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
    left_holding  = left_held  and (now - left_press_time)  >= HOLD_THRESHOLD
    right_holding = right_held and (now - right_press_time) >= HOLD_THRESHOLD
    up_holding    = up_held    and (now - up_press_time)    >= HOLD_THRESHOLD
    down_holding  = down_held  and (now - down_press_time)  >= HOLD_THRESHOLD
    enter_holding = enter_held and (now - enter_press_time) >= HOLD_THRESHOLD
    crossed_eyes = True if enter_holding else False
    if (left_holding and not right_holding):
        x_current = 1
    elif (right_holding and not left_holding):
        x_current = -1
    elif timer_xmove == 0 or now >= timer_xmove:
        timer_xmove = now + random_gaussian(0, TIMER_MOVE_RAND_MAX)
        x_current = random_gaussian(-0.5, 0.5)
    if up_holding:
        y_current = 1
    elif timer_ymove == 0 or now >= timer_ymove:
        timer_ymove = now + random_gaussian(0, TIMER_MOVE_RAND_MAX)
        y_current = random_gaussian(-0.25, 0.25)
    if timer_eyelidmove == 0 or now >= timer_eyelidmove:
        timer_eyelidmove = now + random_gaussian(0, TIMER_EYELID_RAND_MAX)
        (left_eye_closeness, right_eye_closeness) = random.choice(EYELID_SETS)
    lb = now <= left_blink_until
    rb = now <= right_blink_until
    if down_holding:
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
    Serial.send_debug("Expression manual mode reset to auto")

EXPR_MAPPING = {
    (keyboard.Key.enter, keyboard.Key.enter): 'neutral',
    (keyboard.Key.enter, keyboard.Key.right): 'angry',
    (keyboard.Key.enter, keyboard.Key.left):  'disgusted',
    (keyboard.Key.enter, keyboard.Key.up):    'happy',
    (keyboard.Key.enter, keyboard.Key.down):  'sad',
    (keyboard.Key.up,    keyboard.Key.up):    'surprised',
    (keyboard.Key.left,  keyboard.Key.left):  'mischievous',
    (keyboard.Key.down,  keyboard.Key.down):  'nightmare',
    (keyboard.Key.right, keyboard.Key.right): 'heart',
    (keyboard.Key.up,    keyboard.Key.right): 'gears',
    (keyboard.Key.down,  keyboard.Key.right): 'sans',
    (keyboard.Key.up,    keyboard.Key.down):  'hypnotic',
    (keyboard.Key.down,  keyboard.Key.up):    'hypnotic',
    (keyboard.Key.left,  keyboard.Key.right): 'rainbow',
    (keyboard.Key.right, keyboard.Key.left):  'rainbow',
}

def _apply_expression(chosen):
    global expression_manual_mode, expression_manual_id, emotion_scores, manual_mode_timer
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
    Waveform.play_audio(f"sfx/expr_{chosen}.wav")

def _deferred_blink(key):
    global combo_buffer, left_blink_until, right_blink_until, pending_blink_timer
    pending_blink_timer = None
    if combo_buffer and combo_buffer[-1][0] == key: # Only blink if this key is still the last solo entry (no combo consumed it)
        now = time.time()
        combo_buffer = []
        if key == keyboard.Key.left:
            left_blink_until = now + 0.5
        elif key == keyboard.Key.right:
            right_blink_until = now + 0.5

def on_press(key):
    global left_held, right_held, up_held, down_held, enter_held
    global left_press_time, right_press_time, up_press_time, down_press_time, enter_press_time
    t = time.time()
    if key == keyboard.Key.left:
        if not left_held:
            left_press_time = t
        left_held = True
    elif key == keyboard.Key.right:
        if not right_held:
            right_press_time = t
        right_held = True
    elif key == keyboard.Key.up:
        if not up_held:
            up_press_time = t
        up_held = True
    elif key == keyboard.Key.down:
        if not down_held:
            down_press_time = t
        down_held = True
    elif key == keyboard.Key.enter:
        if not enter_held:
            enter_press_time = t
        enter_held = True

def on_release(key):
    global left_held, right_held, up_held, down_held, enter_held
    global left_press_time, right_press_time, up_press_time, down_press_time, enter_press_time
    global left_blink_until, right_blink_until
    global timer_xmove, timer_ymove, timer_eyelidmove
    global combo_buffer, pending_blink_timer
    t = time.time()
    press_times = {
        keyboard.Key.left:  left_press_time,
        keyboard.Key.right: right_press_time,
        keyboard.Key.up:    up_press_time,
        keyboard.Key.down:  down_press_time,
        keyboard.Key.enter: enter_press_time,
    }
    combo_keys = {keyboard.Key.left, keyboard.Key.right, keyboard.Key.up, keyboard.Key.down, keyboard.Key.enter}
    if key in combo_keys:
        held_duration = t - press_times.get(key, t)
        quick_tap = held_duration < HOLD_THRESHOLD
        if key == keyboard.Key.left:
            left_held = False
            timer_xmove = 0
        elif key == keyboard.Key.right:
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
        if quick_tap:
            combo_buffer = [(k, rt) for (k, rt) in combo_buffer if t - rt <= COMBO_WINDOW]
            combo_buffer.append((key, t))
            if len(combo_buffer) >= 2:
                k1, _ = combo_buffer[-2]
                k2, _ = combo_buffer[-1]
                chosen = EXPR_MAPPING.get((k1, k2))
                if chosen:
                    combo_buffer = []
                    if pending_blink_timer:
                        pending_blink_timer.cancel()
                    _apply_expression(chosen)
                    return
            if key in (keyboard.Key.left, keyboard.Key.right) and len(combo_buffer) == 1:
                if pending_blink_timer:
                    pending_blink_timer.cancel()
                pending_blink_timer = threading.Timer(COMBO_WINDOW, _deferred_blink, args=[key])
                pending_blink_timer.start()

keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
keyboard_listener.start()


if __name__ == "__main__":
    while True:
        update_eye_movement()
        time.sleep(0.01)