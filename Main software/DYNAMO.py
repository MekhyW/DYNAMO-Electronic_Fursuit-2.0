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
        time.sleep(0.01)

def assistant_thread():
    Assistant.start()
    while True:
        try:
            Assistant.refresh()
            if Assistant.triggered:
                Waveform.stop_flag = True
                Waveform.play_audio("resources/assistant_listening.wav")
                time.sleep(0.5)
                Assistant.record_query()
                Waveform.play_audio("resources/assistant_ok.wav")
                transcript = Assistant.process_query()
                answer = Assistant.assistant_query(transcript)
                Assistant.start()
                if len(answer):
                    Waveform.TTS(answer)
                    ControlBot.fursuitbot.sendMessage(ControlBot.ownerID, f'QUERY:\n{transcript}')
                    ControlBot.fursuitbot.sendMessage(ControlBot.ownerID, f'RESPONSE:\n{answer}')
                Assistant.triggered = False
        except Exception as e:
            print(e)
            Assistant.triggered = False
        time.sleep(0.01)

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

def main():
    threading.Thread(target=machine_vision_thread).start()
    threading.Thread(target=assistant_thread).start()
    threading.Thread(target=voicemod_thread).start()
    threading.Thread(target=controlbot_thread).start()
    while True:
        try:
            if Unity.connected is False:
                Unity.connect()
            else:
                Unity.send(MachineVision.displacement_eye[0], MachineVision.displacement_eye[1], 
                        MachineVision.left_eye_closeness, MachineVision.right_eye_closeness, 
                        MachineVision.emotion_scores, MachineVision.expression_manual_mode, MachineVision.expression_manual_id)
            if Serial.ser is None:
                Serial.connect()
            else:
                Serial.send(MachineVision.emotion_scores)
        except Exception as e:
            print(e)
        time.sleep(0.01)

if __name__ == "__main__":
    main()