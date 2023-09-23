import threading
import time
import Waveform
import MachineVision
import Unity
import Assistant
import ControlBot

def machine_vision_thread():
    while True:
        try:
            MachineVision.main()
        except Exception as e:
            print(e)

def assistant_thread():
    Assistant.start()
    while True:
        try:
            Assistant.refresh()
            if Assistant.triggered:
                Assistant.triggered = False
                Waveform.play_audio("resources/assistant_listening.wav")
                time.sleep(0.5)
                Assistant.record_query()
                Waveform.play_audio("resources/assistant_ok.wav")
                transcript = Assistant.process_query()
                answer = Assistant.assistant_query(transcript)
                if len(answer):
                    print(answer)
                    Waveform.TTS(answer)
                else:
                    print("No answer")
                    Waveform.TTS("I don't have an answer to that")
                Assistant.start()
        except Exception as e:
            print(e)

def main():
    threading.Thread(target=machine_vision_thread).start()
    threading.Thread(target=assistant_thread).start()
    Unity.connect()
    ControlBot.StartBot()
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