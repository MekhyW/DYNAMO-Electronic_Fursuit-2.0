import threading
import asyncio
import time
import Waveform
import MachineVision
import Unity
import Assistant
import Voicemod
import Serial
import ControlBot

def machine_vision_thread():
    MachineVision.open_camera(MachineVision.cap_id)
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

def voicemod_thread():
    while True:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(Voicemod.connect())

def main():
    threading.Thread(target=machine_vision_thread).start()
    threading.Thread(target=assistant_thread).start()
    threading.Thread(target=voicemod_thread).start()
    Unity.connect()
    Serial.connect()
    ControlBot.StartBot()
    while True:
        try:
            Unity.send(MachineVision.displacement_eye[0], MachineVision.displacement_eye[1], 
                       MachineVision.left_eye_closeness, MachineVision.right_eye_closeness, 
                       MachineVision.emotion_scores)
            Serial.send(MachineVision.emotion_scores)
            time.sleep(0.01)
        except Exception as e:
            print(e)

if __name__ == "__main__":
    main()