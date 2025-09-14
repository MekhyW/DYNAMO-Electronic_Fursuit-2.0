import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
import subprocess

load_dotenv()
elevenlabs_client = ElevenLabs(api_key=os.getenv("eleven_api_key"))

def save_and_play_audio(text, filename):
    audio = elevenlabs_client.text_to_speech.convert(
        text=text, 
        voice_id="Rb9J9nOjoNgGbjJUN5wt", 
        voice_settings=VoiceSettings(stability=0.3, similarity_boost=1.0, style=0.0, speed=1.1, use_speaker_boost=True), 
        model_id="eleven_multilingual_v2", 
        output_format="mp3_44100_128"
    )
    with open(filename, "wb") as f:
        for chunk in audio:
            if chunk:
                f.write(chunk)
    subprocess.run(["start", filename], shell=True)

text = "My name is Yoshikage Kira. I'm 33 years old. My house is in the northeast section of Morioh, where all the villas are"
save_and_play_audio(text, "audio.mp3")
