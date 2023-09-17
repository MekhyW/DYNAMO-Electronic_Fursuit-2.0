import pyaudio
import numpy as np
import matplotlib.pyplot as plt
import wave
from matplotlib.animation import ArtistAnimation
import keyboard
import time

p = pyaudio.PyAudio()
is_paused = False
chunk_size = 1024

def toggle_pause():
    global is_paused
    is_paused = not is_paused
    time.sleep(0.25)

def play_audio(filename):
    wf = wave.open(filename, 'rb')
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    print("Sample width:", wf.getsampwidth())
    print("Number of channels:", wf.getnchannels())
    print("Frame rate:", wf.getframerate())

    # Read first chunk of data
    data = wf.readframes(chunk_size)

    # Initialize the plot
    fig, ax = plt.subplots()
    frames = []

    while len(data) > 0:
        if keyboard.is_pressed('p'):
            print(f"Pause button: {not is_paused}")
            toggle_pause()

        if not is_paused:
            # Convert the binary data to numpy array
            audio_data = np.frombuffer(data, dtype=np.int16)

            print(f"Audio data (chunk of size {chunk_size}): {audio_data}")
            print(f"Max value in the chunk: {np.max(audio_data)}")

            # Play the audio by writing the audio data to the stream
            stream.write(data)

            # Plot the waveform
            line, = ax.plot(audio_data)
            frames.append([line])

            # Read the next chunk of data
            data = wf.readframes(chunk_size)

    ani = ArtistAnimation(fig, frames, interval=20, blit=True)
    plt.show()

    stream.stop_stream()
    stream.close()
    p.terminate()

if __name__ == "__main__":
    play_audio('Test scripts/query.wav')
