import openai
import pvporcupine
from pvrecorder import PvRecorder
import struct
import wave
import os
from Environment import openai_key, porcupine_key
import Serial

try:
    openai_client = openai.OpenAI(api_key=openai_key)
    porcupine = pvporcupine.create(access_key=porcupine_key, keyword_paths=["models/Cookie-Bot_en_windows_v3_0_0.ppn"])
    recorder = PvRecorder(device_index=-1, frame_length=porcupine.frame_length)
except Exception as e:
    openai_client = None
    porcupine = None
    recorder = None
    print(f"Assistant constructor failed with error: {e}")

previous_questions = ["who won the world series in 2020?", "você é fofo!"]
previous_answers = ["The Los Angeles Dodgers", "Não, você que é fofo! UwU"]
triggered = False
hotword_detection_enabled = True
current_pcm = None

def record_query(silence_window_s=2, silence_threshold_percent=50):
    print("Recording")
    wavfile = wave.open("sfx/query.wav", "wb")
    wavfile.setparams((1, 2, 16000, 512, "NONE", "NONE"))
    pcms = []
    remaining = int(16000 / 512 * silence_window_s)
    while remaining > 0:
        refresh()
        pcms.append(current_pcm)
        volume = Serial.leds_level_from_int16(max(current_pcm))
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
    try:
        with open("sfx/query.wav", "rb") as audio_file:
            transcript = openai_client.audio.transcriptions.create(model="whisper-1", file=audio_file)
        os.remove("sfx/query.wav")
        print(transcript.text)
        return transcript.text
    except Exception as e:
        print(f"Transcription failed with error: {e}")
        if os.path.exists("sfx/query.wav"):
            os.remove("sfx/query.wav")
        return ""

def assistant_query(query):
    global previous_question, previous_answer
    query = query.strip().lower()
    if not len(query):
        return ""
    prompt_beginning = "You are a helpful and silly assistant. Your name is Cookie Bot. Respond in the same language as the question, and try not to answer too long!"
    messages=[{"role": "system", "content": prompt_beginning}]
    for i in range(len(previous_questions)):
        messages.append({"role": "user", "content": previous_questions[i]})
        messages.append({"role": "assistant", "content": previous_answers[i], "name": "CookieBot"})
    messages.append({"role": "user", "content": query})
    try:
        completion = openai_client.chat.completions.create(model="gpt-4-turbo-preview", messages=messages, temperature=1)
    except Exception as e:
        print(e)
        return ""
    answer = completion.choices[0].message.content
    if len(answer):
        previous_questions.append(query)
        previous_answers.append(answer)
        while len(previous_questions) > 10:
            previous_questions.pop(0)
            previous_answers.pop(0)
    else:
        answer = "I don't have an answer to that"
    return answer

def trigger():
    global triggered
    triggered = True
    print("Assistant Triggered")

def start():
    if not recorder:
        return
    print("Assistant started!")
    recorder.start()

def refresh():
    global current_pcm
    if not recorder:
        return
    current_pcm = recorder.read()
    if triggered or not hotword_detection_enabled:
        return
    if porcupine.process(current_pcm) >= 0:
        trigger()

if __name__ == "__main__":
    start()
    while True:
        refresh()