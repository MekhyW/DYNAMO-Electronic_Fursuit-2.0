import asyncio
import aiohttp
import json
from typing import AsyncIterable, Optional
from livekit import rtc
from livekit.agents import JobContext, JobProcess, WorkerOptions, cli, RoomInputOptions, RoomOutputOptions
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import elevenlabs, openai, silero, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.agents.llm import function_tool
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from Environment import openai_key, livekit_url, livekit_api_key, livekit_api_secret, eleven_api_key, prompt_encryption_key, tavily_api_key
import os
os.environ["OPENAI_API_KEY"] = openai_key
os.environ["LIVEKIT_URL"] = livekit_url
os.environ["LIVEKIT_API_KEY"] = livekit_api_key
os.environ["LIVEKIT_API_SECRET"] = livekit_api_secret
os.environ["ELEVEN_API_KEY"] = eleven_api_key

KEYWORDS = ["cookiebot", "cookie bot", "cookie pot", "cookie bote"]
hotword_detection_enabled = True
manual_trigger = False

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
        parent_stream = super().stt_node(text, model_settings)
        if parent_stream is None:
            return None
        async def process_stream():
            global manual_trigger
            async for event in parent_stream:
                if hasattr(event, 'type') and str(event.type) == "SpeechEventType.FINAL_TRANSCRIPT" and event.alternatives:
                    transcript = event.alternatives[0].text
                    print(f"Transcript: {transcript}")
                    if manual_trigger or (hotword_detection_enabled and any(keyword.lower() in transcript.lower() for keyword in KEYWORDS)):
                        print(f"Activation keyword detected")
                        manual_trigger = False
                        yield event
        return process_stream()

    @function_tool()
    async def search_internet(self, query: str) -> str:
        """Search the internet for the given query and return the results."""
        try:
            if not query or not query.strip():
                return "Error: Search query cannot be empty."
            if not tavily_api_key:
                return "Error: Tavily API key not configured."
            url = "https://api.tavily.com/search"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {tavily_api_key}"
            }
            payload = {
                "query": query.strip(),
                "search_depth": "basic",
                "include_answer": True,
                "include_raw_content": False,
                "max_results": 5,
                "include_domains": [],
                "exclude_domains": []
            }
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._format_search_results(data, query)
                    elif response.status == 401:
                        return "Error: Invalid Tavily API key or authentication failed."
                    elif response.status == 429:
                        return "Error: Rate limit exceeded. Please try again later."
                    elif response.status == 400:
                        error_text = await response.text()
                        return f"Error: Invalid request format - {error_text}"
                    else:
                        return f"Error: API request failed with status {response.status}"
        except asyncio.TimeoutError:
            return "Error: Search request timed out. Please try again."
        except aiohttp.ClientError as e:
            return f"Error: Network connection failed - {str(e)}"
        except json.JSONDecodeError:
            return "Error: Invalid response format from search API."
        except Exception as e:
            return f"Error: Unexpected error during search - {str(e)}"
    
    def _format_search_results(self, data: dict, query: str) -> str:
        """Format the search results into a readable string."""
        try:
            results = []
            results.append(f"Search results for: {query}\n")
            if data.get("answer"):
                results.append(f"Quick Answer: {data['answer']}\n")
            if data.get("results"):
                results.append("Top Results:")
                for i, result in enumerate(data["results"][:5], 1):
                    title = result.get("title", "No title")
                    url = result.get("url", "")
                    content = result.get("content", "No description available")
                    if len(content) > 200:
                        content = content[:200] + "..."
                    results.append(f"\n{i}. {title}")
                    results.append(f"   {content}")
                    if url:
                        results.append(f"   Source: {url}")
            else:
                results.append("No search results found.")
            return "\n".join(results)
        except Exception as e:
            return f"Error formatting search results: {str(e)}"

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    session = AgentSession(
        llm=openai.LLM(model="gpt-4.1-nano", temperature=0.9),
        stt=openai.STT(model="whisper-1"),
        tts=elevenlabs.TTS(voice_id="Rb9J9nOjoNgGbjJUN5wt", model="eleven_multilingual_v2", voice_settings=elevenlabs.VoiceSettings(stability=0.3, similarity_boost=1.0, style=0.0, speed=1.05, use_speaker_boost=True)),
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