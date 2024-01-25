import pyaudio
from pydub import AudioSegment
import numpy as np
import wave
import subprocess
import os
from gtts import gTTS
from googletrans import Translator
import Serial
import Assistant

translator = Translator()
p = pyaudio.PyAudio()
chunk_size = 4096

is_paused = False
stop_flag = False
stop_gibberish_flag = False

def convert_to_wav(input_filename):
    if input_filename[-4:] != ".wav":
        output_filename = input_filename[:-4] + ".wav"
        subprocess.call(["ffmpeg", "-i", input_filename, "-ar", "16000", output_filename, "-y"])
        os.remove(input_filename)
        return output_filename
    return input_filename

def normalize_audio(file_path, target_dBFS=-20.0):
    audio = AudioSegment.from_file(file_path)
    normalized_audio = audio.normalize()
    change_in_dBFS = target_dBFS - normalized_audio.dBFS
    normalized_audio = normalized_audio.apply_gain(change_in_dBFS)
    normalized_audio.export(file_path, format="wav")

def play_audio_stream(wf, stream):
    global is_paused, stop_flag
    is_paused = False
    stop_flag = False
    data = wf.readframes(chunk_size)
    while len(data) > 0:
        if not is_paused:
            audio_data = np.frombuffer(data, dtype=np.int16)
            audio_data_max = np.max(audio_data)
            Serial.leds_level_from_int16(audio_data_max)
            stream.write(data)
            data = wf.readframes(chunk_size)
        if stop_flag:
            stop_flag = False
            break
    wf.close()

def close_audio_stream(stream):
    stream.stop_stream()
    stream.close()

def gibberish(filename, silence_threshold_percent=50):
    global stop_gibberish_flag
    stop_gibberish_flag = False
    wf = wave.open(f"resources/gibberish_voices/{filename}.wav", 'rb')
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()), channels=wf.getnchannels(), rate=wf.getframerate(), output=True)
    while True:
        if stop_gibberish_flag:
            stop_gibberish_flag = False
            break
        if wf.tell() >= wf.getnframes() - chunk_size:
            wf.rewind()
        Assistant.refresh()
        volume = Serial.leds_level_from_int16(max(Assistant.current_pcm))
        if volume > silence_threshold_percent:
            data = wf.readframes(chunk_size*2)
            stream.write(data)
    wf.close()
    close_audio_stream(stream)

def play_audio(filename, delete=False):
    filename = convert_to_wav(filename)
    normalize_audio(filename)
    wf = wave.open(filename, 'rb')
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()), channels=wf.getnchannels(), rate=wf.getframerate(), output=True)
    play_audio_stream(wf, stream)
    close_audio_stream(stream)
    if delete:
        os.remove(filename)

def TTS(text):
    language = translator.detect(text).lang
    tts = gTTS(text=text, lang=language, slow=False)
    tts.save("resources/tts.mp3")
    subprocess.call(["ffmpeg", "-i", "resources/tts.mp3", "-filter:a", "atempo=1.5,aecho=0.8:0.9:20:0.6,asetrate=22050", "resources/tts_faster.mp3", "-y"])
    os.remove("resources/tts.mp3")
    play_audio("resources/tts_faster.mp3", delete=True)