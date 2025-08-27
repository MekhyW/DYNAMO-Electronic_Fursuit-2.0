import pyaudio
from pydub import AudioSegment
import numpy as np
import wave
import subprocess
import os
from gtts import gTTS
import langdetect
import Serial
import threading

p = pyaudio.PyAudio()
chunk_size = 4096

stop_flag = False

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
    global stop_flag
    stop_flag = False
    data = wf.readframes(chunk_size)
    while len(data) > 0:
        if stop_flag:
            stop_flag = False
            break
        audio_data = np.frombuffer(data, dtype=np.int16)
        audio_data_max = np.max(audio_data)
        Serial.leds_level_from_int16(audio_data_max)
        stream.write(data)
        data = wf.readframes(chunk_size)
    wf.close()

def close_audio_stream(stream):
    stream.stop_stream()
    stream.close()

def play_audio(filename, delete=False):
    if not os.path.isfile(filename):
        print(f"File {filename} does not exist")
        return
    filename = convert_to_wav(filename)
    if delete:
        normalize_audio(filename)
    wf = wave.open(filename, 'rb')
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()), channels=wf.getnchannels(), rate=wf.getframerate(), output=True)
    play_audio_stream(wf, stream)
    close_audio_stream(stream)
    if delete:
        os.remove(filename)

def play_audio_async(filename, delete=False):
    audio_thread = threading.Thread(target=play_audio, args=(filename, delete), daemon=True)
    audio_thread.start()
    return audio_thread

def TTS_generate(text):
    language = langdetect.detect(text)
    tts = gTTS(text=text, lang=language, slow=False)
    tts.save("sfx/tts.mp3")
    subprocess.call(["ffmpeg", "-i", "sfx/tts.mp3", "-filter:a", "atempo=1.5,aecho=0.8:0.9:20:0.6,asetrate=22050", "sfx/tts_faster.mp3", "-y"])
    os.remove("sfx/tts.mp3")

def TTS_play():
    play_audio("sfx/tts_faster.mp3", delete=True)

def TTS_play_async():
    def tts_worker():
        play_audio("sfx/tts_faster.mp3", delete=True)
    stop_flag = True
    tts_thread = threading.Thread(target=tts_worker, daemon=True)
    tts_thread.start()
    return tts_thread