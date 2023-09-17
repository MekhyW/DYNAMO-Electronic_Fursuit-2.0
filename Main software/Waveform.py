import pyaudio
import numpy as np
import wave

p = pyaudio.PyAudio()
chunk_size = 1024

is_paused = False
audio_data = []
audio_data_max = 0

def play_audio(filename):
    global is_paused, audio_data, audio_data_max
    wf = wave.open(filename, 'rb')
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)
    data = wf.readframes(chunk_size)
    while len(data) > 0:
        if not is_paused:
            audio_data = np.frombuffer(data, dtype=np.int16)
            audio_data_max = np.max(audio_data)
            stream.write(data)
            data = wf.readframes(chunk_size)