import Voicemod
import EyeControl
import Unity
import Serial
import ControlBot
import threading
import asyncio
import time
import sys
import os

sys.stdin.close()
sys.stdin = open(os.devnull)

def eyecontrol_thread():
    while True:
        EyeControl.update_eye_movement()
        time.sleep(0.01)

def assistant_thread():
    os.system("python Assistant.py download-files")
    while True:
        os.system("python Assistant.py console")
        print("Assistant console process ended. Restarting...")

def voicemod_thread():
    while True:
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(Voicemod.connect())
        except Exception as e:
            print(e)
        finally:
            loop.close()
            time.sleep(1)

def controlbot_thread():
    ControlBot.StartBot()

def serial_thread():
    while True:
        try:
            if Serial.ser is None:
                Serial.connect()
                time.sleep(1)
            else:
                Serial.send(EyeControl.emotion_scores)
                if EyeControl.crossed_eyes:
                    Serial.send_debug(f"E,-1,-1,1,1,{EyeControl.left_eye_closeness},{EyeControl.right_eye_closeness},{EyeControl.expression_manual_id}")
                else:
                    Serial.send_debug(f"E,{EyeControl.displacement_eye[0]},{EyeControl.displacement_eye[1]},{EyeControl.displacement_eye[0]},{EyeControl.displacement_eye[1]},{EyeControl.left_eye_closeness},{EyeControl.right_eye_closeness},{EyeControl.expression_manual_id}")
        except Exception as e:
            print(f"Serial thread error: {e}")
        time.sleep(0.1)

def unity_thread():
    while True:
        try:
            if Unity.connected is False:
                Unity.connect()
                time.sleep(1)
            else:
                Unity.send(EyeControl.displacement_eye[0], EyeControl.displacement_eye[1], 
                        EyeControl.left_eye_closeness, EyeControl.right_eye_closeness, EyeControl.emotion_scores, 
                        EyeControl.expression_manual_mode, EyeControl.expression_manual_id, 
                        EyeControl.crossed_eyes)
        except Exception as e:
            print(e)
        time.sleep(0.01)

def main():
    threads = []
    threads.append(threading.Thread(target=eyecontrol_thread))
    threads.append(threading.Thread(target=assistant_thread))
    threads.append(threading.Thread(target=voicemod_thread))
    threads.append(threading.Thread(target=controlbot_thread))
    threads.append(threading.Thread(target=serial_thread))
    threads.append(threading.Thread(target=unity_thread))
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()