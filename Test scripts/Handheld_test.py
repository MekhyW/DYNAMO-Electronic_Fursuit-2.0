from datetime import datetime
import sys
from pynput import keyboard, mouse

def _ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

def _on_key_press(key):
    try:
        k = key.char
    except AttributeError:
        k = str(key)
    print(f"{_ts()} | KEY_PRESS | {k}")
    sys.stdout.flush()

def _on_key_release(key):
    try:
        k = key.char
    except AttributeError:
        k = str(key)
    print(f"{_ts()} | KEY_RELEASE | {k}")
    sys.stdout.flush()

def _on_mouse_move(x, y):
    print(f"{_ts()} | MOUSE_MOVE | {x},{y}")
    sys.stdout.flush()

def _on_mouse_click(x, y, button, pressed):
    state = "DOWN" if pressed else "UP"
    print(f"{_ts()} | MOUSE_CLICK_{state} | {button} @ {x},{y}")
    sys.stdout.flush()

def _on_mouse_scroll(x, y, dx, dy):
    print(f"{_ts()} | MOUSE_SCROLL | delta=({dx},{dy}) @ {x},{y}")
    sys.stdout.flush()

kl = keyboard.Listener(on_press=_on_key_press, on_release=_on_key_release)
ml = mouse.Listener(on_move=_on_mouse_move, on_click=_on_mouse_click, on_scroll=_on_mouse_scroll)
kl.start()
ml.start()
kl.join()
ml.join()