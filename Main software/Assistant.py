from typing import AsyncIterable, Optional
from livekit import rtc
from livekit.agents import JobContext, JobProcess, WorkerOptions, cli, RoomInputOptions, RoomOutputOptions
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import elevenlabs, openai, silero, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from Environment import openai_key, livekit_url, livekit_api_key, livekit_api_secret, eleven_api_key, prompt_encryption_key
import os
os.environ["OPENAI_API_KEY"] = openai_key
os.environ["LIVEKIT_URL"] = livekit_url
os.environ["LIVEKIT_API_KEY"] = livekit_api_key
os.environ["LIVEKIT_API_SECRET"] = livekit_api_secret
os.environ["ELEVEN_API_KEY"] = eleven_api_key

KEYWORDS = ["cookiebot", "cookie bot", "cookie pot", "cookie bote"]
hotword_detection_enabled = True
keyword_detected = False

def decrypt_system_prompt(encryption_key):
    with open("models/system_prompt_encrypted.txt", "r", encoding='utf-8') as f:
        encrypted_data = f.read().strip()
        password = encryption_key.encode('utf-8')
        encrypted_bytes = base64.b64decode(encrypted_data)
        if encrypted_bytes.startswith(b"Salted__"):
            salt = encrypted_bytes[8:16]
            encrypted_content = encrypted_bytes[16:]
            import hashlib
            key_iv = hashlib.pbkdf2_hmac('sha256', password, salt, 10000, 48)  # 32 + 16
            key = key_iv[:32]
            iv = key_iv[32:48]
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted_padded = decryptor.update(encrypted_content) + decryptor.finalize()
            padding_length = decrypted_padded[-1]
            if padding_length <= 16:
                decrypted_text = decrypted_padded[:-padding_length].decode('utf-8')
                return decrypted_text

class Cookiebot(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=decrypt_system_prompt(prompt_encryption_key))

    async def stt_node(self, text: AsyncIterable[str], model_settings: Optional[dict] = None) -> Optional[AsyncIterable[rtc.AudioFrame]]:
        global keyword_detected
        parent_stream = super().stt_node(text, model_settings)
        if parent_stream is None:
            return None
        async def process_stream():
            async for event in parent_stream:
                if hasattr(event, 'type') and str(event.type) == "SpeechEventType.FINAL_TRANSCRIPT" and event.alternatives:
                    transcript = event.alternatives[0].text
                    print(f"Transcript: {transcript}")
                    if not keyword_detected:
                        for keyword in KEYWORDS:
                            if keyword.lower() in transcript.lower():
                                print(f"Activation keyword detected: '{keyword}'")
                                keyword_detected = True
                                await self.session.generate_reply(instructions="Keyword detected. How can I help you?")
                                break
                    elif keyword_detected and hotword_detection_enabled: # If keyword is already detected, process all messages
                        await self.session.generate_reply(instructions=transcript)
                yield event
        return process_stream()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    session = AgentSession(
        llm=openai.LLM(model="gpt-4o", temperature=0.9),
        stt=openai.STT(model="whisper-1", language="pt"),
        tts=elevenlabs.TTS(voice_id="cXQRjuAYvmCPhUeRKe7o", model="eleven_multilingual_v2"),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        allow_interruptions=True,
        preemptive_generation=False
    )
    await session.start(
        agent=Cookiebot(), 
        room=ctx.room,
        room_input_options=RoomInputOptions(noise_cancellation=noise_cancellation.BVC()),
        room_output_options=RoomOutputOptions(transcription_enabled=True),
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))