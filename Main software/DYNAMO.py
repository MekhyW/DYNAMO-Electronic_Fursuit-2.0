import threading
import time
import MachineVision
import Unity

def machine_vision_thread():
    while True:
        try:
            MachineVision.main()
        except Exception as e:
            print(e)

def main():
    threading.Thread(target=machine_vision_thread).start()
    Unity.connect()
    while True:
        try:
            Unity.send(MachineVision.displacement_eye[0], MachineVision.displacement_eye[1], 
                       MachineVision.left_eye_closed, MachineVision.right_eye_closed, 
                       MachineVision.emotion_scores)
            time.sleep(0.01)
        except Exception as e:
            print(e)

if __name__ == "__main__":
    main()