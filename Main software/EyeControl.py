import time
import random

EMOTION_LABELS = ['angry', 'disgusted', 'happy', 'neutral', 'sad', 'surprised']
EMOTION_LABELS_EXTRA = ['hypnotic', 'heart', 'rainbow', 'nightmare', 'gears', 'sans', 'mischievous']
EYELID_SETS = [(-0.2, -0.2), (-0.2, -0.2), (0.3, 0.3), (0.3, 0.3), (0.2, 0.6), (0.6, 0.2), (0, 0), (0, 0), (0, 0), (0, 0), (0, 0), (0, 0)]
emotion_scores = [0] * len(EMOTION_LABELS)
expression_manual_mode = False
expression_manual_id = 0
displacement_eye = (0,0)
left_eye_closeness = 0
right_eye_closeness = 0
eye_tracking_mode = True
crossed_eyes = False

TIMER_MOVE_RAND_MAX = 6
TIMER_EYELID_RAND_MAX = 12
timer_xmove = 0
timer_ymove = 0
timer_eyelidmove = 0
x_current = 0
y_current = 0

def random_gaussian(min_value=0.0, max_value=1.0):
    mean = (min_value + max_value) / 2.0
    sigma = (max_value - mean) / 3.0  # 99.7% of values within [min, max]
    value = random.gauss(mean, sigma)
    return max(min_value, min(max_value, value))  # clamp

def update_eye_movement():
    global timer_xmove, timer_ymove, timer_eyelidmove, x_current, y_current, displacement_eye, left_eye_closeness, right_eye_closeness
    if not eye_tracking_mode:
        displacement_eye = (0, 0)
        (left_eye_closeness, right_eye_closeness) = (0, 0)
        return
    now = time.time()
    if timer_xmove == 0 or now >= timer_xmove:
        timer_xmove = now + random_gaussian(0, TIMER_MOVE_RAND_MAX)
        x_current = random_gaussian(-1, 1)
    if timer_ymove == 0 or now >= timer_ymove:
        timer_ymove = now + random_gaussian(0, TIMER_MOVE_RAND_MAX)
        y_current = random_gaussian(-0.5, 0.5)
    if timer_eyelidmove == 0 or now >= timer_eyelidmove:
        timer_eyelidmove = now + random_gaussian(0, TIMER_EYELID_RAND_MAX)
        (left_eye_closeness, right_eye_closeness) = random.choice(EYELID_SETS)
    displacement_eye = (x_current, y_current)
