import pyaudio
import numpy as np
import wave
import subprocess
import os
from gtts import gTTS
from googletrans import Translator
import Serial

translator = Translator()
p = pyaudio.PyAudio()
chunk_size = 4096

is_paused = False
stop_flag = False
audio_data = []
audio_data_max = 0

def play_audio(filename):
    global is_paused, stop_flag, audio_data, audio_data_max
    if filename[-4:] != ".wav":
        subprocess.call(["ffmpeg", "-i", filename, "-ar", "16000", filename[:-4] + ".wav", "-y"])
        filename = filename[:-4] + ".wav"
    wf = wave.open(filename, 'rb')
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)
    is_paused = False
    stop_flag = False
    data = wf.readframes(chunk_size)
    while len(data) > 0:
        if not is_paused:
            audio_data = np.frombuffer(data, dtype=np.int16)
            audio_data_max = np.max(audio_data)
            Serial.leds_effect = len(Serial.leds_effects_options) #"Level" effect is last index + 1
            Serial.leds_level = int((audio_data_max / 32767) * 100)
            stream.write(data)
            data = wf.readframes(chunk_size)
        if stop_flag:
            stop_flag = False
            break

def TTS(text):
    language = translator.detect(text).lang
    tts = gTTS(text=text, lang=language, slow=False)
    tts.save("resources/tts.mp3")
    subprocess.call(["ffmpeg", "-i", "resources/tts.mp3", "-filter:a", "atempo=1.5,aecho=0.8:0.9:20:0.6,asetrate=22050", "resources/tts_faster.mp3", "-y"])
    play_audio("resources/tts_faster.mp3")
    os.remove("resources/tts.mp3")
    os.remove("resources/tts_faster.mp3")
    os.remove("resources/tts_faster.wav")