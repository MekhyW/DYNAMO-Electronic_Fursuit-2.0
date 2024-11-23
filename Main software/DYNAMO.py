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
import Environment

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
                Waveform.play_audio("sfx/assistant_listening.wav")
                time.sleep(0.5)
                Assistant.record_query()
                Waveform.play_audio("sfx/assistant_ok.wav")
                transcript = Assistant.process_query()
                answer = Assistant.assistant_query(transcript)
                Assistant.start()
                if len(answer):
                    Waveform.TTS_generate(answer)
                    Waveform.TTS_play()
                    ControlBot.fursuitbot.sendMessage(Environment.fursuitbot_ownerID, f'QUERY:\n{transcript}')
                    ControlBot.fursuitbot.sendMessage(Environment.fursuitbot_ownerID, f'RESPONSE:\n{answer}')
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

def serial_thread():
    while True:
        try:
            if Serial.ser is None:
                Serial.connect()
                time.sleep(1)
            else:
                Serial.send(MachineVision.emotion_scores)
        except Exception as e:
            print(f"Serial thread error: {e}")
        time.sleep(0.01)

def unity_thread():
    while True:
        try:
            if Unity.connected is False:
                Unity.connect()
                time.sleep(1)
            else:
                Unity.send(MachineVision.displacement_eye[0], MachineVision.displacement_eye[1], 
                        MachineVision.left_eye_closeness, MachineVision.right_eye_closeness, MachineVision.emotion_scores, 
                        MachineVision.expression_manual_mode, MachineVision.expression_manual_id, 
                        MachineVision.force_crossed_eye or MachineVision.cross_eyedness > MachineVision.cross_eyedness_threshold)
        except Exception as e:
            print(e)
        time.sleep(0.01)

def main():
    Waveform.play_audio("sfx/system_up.wav")
    threads = []
    threads.append(threading.Thread(target=machine_vision_thread))
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