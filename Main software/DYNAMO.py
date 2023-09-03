import threading
import MachineVision

def machine_vision_thread():
    while True:
        try:
            MachineVision.main()
        except Exception as e:
            print(e)

def main():
    threading.Thread(target=machine_vision_thread).start()
    while True:
        pass

if __name__ == "__main__":
    main()