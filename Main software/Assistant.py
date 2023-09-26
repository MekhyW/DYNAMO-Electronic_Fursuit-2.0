import openai
import pvporcupine
from pvrecorder import PvRecorder
import struct
import wave
import json
import os

openai.api_key = json.load(open("credentials.json"))["openai_key"]
porcupine_access_key = json.load(open("credentials.json"))["porcupine_key"]
keyword_paths = ["resources/Cookie-Bot_en_windows_v2_1_0.ppn"]
porcupine = pvporcupine.create(access_key=porcupine_access_key, keyword_paths=keyword_paths)
recorder = PvRecorder(device_index=-1, frame_length=porcupine.frame_length)
previous_questions = ["Who won the world series in 2020?", "Você é fofo!"]
previous_answers = ["The Los Angeles Dodgers", "Não, você que é fofo! UwU"]

triggered = False
hotword_detection_enabled = True

def record_query():
    print("Recording")
    wavfile = wave.open("resources/query.wav", "wb")
    wavfile.setparams((1, 2, 16000, 512, "NONE", "NONE"))
    pcms = []
    for i in range(0, int(16000 / 512 * 5)):
        pcm = recorder.read()
        pcms.append(pcm)
    for pcm in pcms:
        wavfile.writeframes(struct.pack("h" * len(pcm), *pcm))
    wavfile.close()
    recorder.stop()

def process_query():
    with open("resources/query.wav", "rb") as query:
        print("Transcribing")
        transcript = openai.Audio.transcribe("whisper-1", query)['text']
    query.close()
    os.remove("resources/query.wav")
    print(transcript)
    return transcript

def assistant_query(query):
    global previous_question, previous_answer
    query = query.capitalize()
    prompt_beginning = "You are a helpful and silly assistant. Your name is Cookie Bot. Respond in the same language as the question"
    messages=[{"role": "system", "content": prompt_beginning}]
    for i in range(len(previous_questions)):
        messages.append({"role": "user", "content": previous_questions[i]})
        messages.append({"role": "assistant", "content": previous_answers[i]})
    messages.append({"role": "user", "content": query})
    completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
    answer = completion.choices[0].message.content
    if len(query) and len(answer):
        previous_questions.append(query)
        previous_answers.append(answer)
    return answer

def trigger():
    global triggered
    triggered = True
    print("Assistant Triggered")

def start():
    recorder.start()

def refresh():
    keyword_index = porcupine.process(recorder.read())
    if keyword_index >= 0 and hotword_detection_enabled:
        trigger()

if __name__ == "__main__":
    start()
    while True:
        refresh()