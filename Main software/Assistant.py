import openai
import whisper
import pvporcupine
from pvrecorder import PvRecorder
import struct
import wave
import json
import os
import MachineVision
import Serial
import Windows

openai.api_key = json.load(open("credentials.json"))["openai_key"]
porcupine_access_key = json.load(open("credentials.json"))["porcupine_key"]
keyword_paths = ["resources/Cookie-Bot_en_windows_v2_1_0.ppn"]
porcupine = pvporcupine.create(access_key=porcupine_access_key, keyword_paths=keyword_paths)
recorder = PvRecorder(device_index=-1, frame_length=porcupine.frame_length)
whisper_model = whisper.load_model("base")
previous_questions = ["who won the world series in 2020?", "você é fofo!"]
previous_answers = ["The Los Angeles Dodgers", "Não, você que é fofo! UwU"]

triggered = False
hotword_detection_enabled = True

def assistant_hard_commands(query):
    if all(term in query for term in ["expression", "automatic"]):
        MachineVision.expression_manual_mode = False
        return True
    elif all(term in query for term in ["expression", "manual"]):
        MachineVision.expression_manual_mode = True
        return True
    elif all(term in query for term in ["set", "expression"]) and any(emotion in query for emotion in MachineVision.emotion_labels + MachineVision.emotion_labels_extra):
        MachineVision.expression_manual_mode = True
        MachineVision.expression_manual_id = next((i for i, emotion in enumerate(MachineVision.emotion_labels + MachineVision.emotion_labels_extra) if emotion in query), None)
        if MachineVision.expression_manual_id == 6:
            Serial.leds_effect = next(i for i, effect in enumerate(Serial.leds_effects_options) if 'Rainbow' in effect)
        return True
    elif all(term in query for term in ["eye", "tracking", "on"]):
        MachineVision.eye_tracking_mode = True
        return True
    elif all(term in query for term in ["eye", "tracking", "off"]):
        MachineVision.eye_tracking_mode = False
        return True
    elif all(term in query for term in ["animatronic", "on"]):
        Serial.animatronics_on = 1
        return True
    elif all(term in query for term in ["animatronic", "off"]):
        Serial.animatronics_on = 0
        return True
    elif all(term in query for term in ["leds", "on"]):
        Serial.leds_on = 1
        return True
    elif all(term in query for term in ["leds", "off"]):
        Serial.leds_on = 0
        return True
    elif all(term in query for term in ["set", "leds", "effect"]) and any(effect in query for effect in Serial.leds_effects_options):
        Serial.leds_effect = next((i for i, effect in enumerate(Serial.leds_effects_options) if effect in query), None)
        return True
    elif all(term in query for term in ["set", "leds", "color"]) and any(color in query for color in Serial.leds_color_options):
        Serial.leds_color = next((i for i, color in enumerate(Serial.leds_color_options) if color in query), None)
        return True
    elif all(term in query for term in ["shutdown", "system"]) or all(term in query for term in ["shut", "down", "system"]):
        Windows.shutdown()
    elif all(term in query for term in ["restart", "system"]) or all(term in query for term in ["reboot", "system"]):
        Windows.restart()
    else:
        return False

def record_query(silence_window_s=2, silence_threshold_percent=50):
    print("Recording")
    wavfile = wave.open("resources/query.wav", "wb")
    wavfile.setparams((1, 2, 16000, 512, "NONE", "NONE"))
    pcms = []
    remaining = int(16000 / 512 * silence_window_s)
    while remaining > 0:
        pcm = recorder.read()
        pcms.append(pcm)
        volume = Serial.leds_level_from_int16(max(pcm))
        if volume > silence_threshold_percent:
            remaining = int(16000 / 512 * silence_window_s)
        else:
            remaining -= 1
    for pcm in pcms:
        wavfile.writeframes(struct.pack("h" * len(pcm), *pcm))
    wavfile.close()
    recorder.stop()

def process_query():
    print("Transcribing")
    transcript = whisper_model.transcribe("resources/query.wav")['text']
    os.remove("resources/query.wav")
    print(transcript)
    return transcript

def assistant_query(query):
    global previous_question, previous_answer
    query = query.strip().lower()
    if assistant_hard_commands(query):
        print("Assistant command executed")
        return ""
    prompt_beginning = "You are a helpful and silly assistant. Your name is Cookie Bot. Respond in the same language as the question"
    messages=[{"role": "system", "content": prompt_beginning}]
    for i in range(len(previous_questions)):
        messages.append({"role": "user", "content": previous_questions[i]})
        messages.append({"role": "assistant", "content": previous_answers[i]})
    messages.append({"role": "user", "content": query})
    try:
        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
    except Exception as e:
        print(e)
        return ""
    answer = completion.choices[0].message.content
    if len(query) and len(answer):
        previous_questions.append(query)
        previous_answers.append(answer)
    else:
        answer = "I don't have an answer to that"
    return answer

def trigger():
    global triggered
    triggered = True
    print("Assistant Triggered")

def start():
    print("Assistant started!")
    recorder.start()

def refresh():
    if not hotword_detection_enabled:
        return
    if porcupine.process(recorder.read()) >= 0:
        trigger()

if __name__ == "__main__":
    start()
    while True:
        refresh()