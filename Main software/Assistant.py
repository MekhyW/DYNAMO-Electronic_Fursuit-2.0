import asyncio
import aiohttp
import json
from typing import AsyncIterable, Optional
from livekit import rtc
from livekit.agents import JobContext, JobProcess, WorkerOptions, cli, RoomInputOptions, RoomOutputOptions, llm, FunctionTool, ModelSettings
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import elevenlabs, openai, silero, noise_cancellation, deepgram
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.agents.llm import function_tool
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from Environment import livekit_url, livekit_api_key, livekit_api_secret, prompt_encryption_key, deepgram_api_key, openai_key, tavily_api_key, eleven_api_key
import Waveform
import time
import threading
import os
os.environ["LIVEKIT_URL"] = livekit_url
os.environ["LIVEKIT_API_KEY"] = livekit_api_key
os.environ["LIVEKIT_API_SECRET"] = livekit_api_secret
os.environ["DEEPGRAM_API_KEY"] = deepgram_api_key
os.environ["OPENAI_API_KEY"] = openai_key
os.environ["ELEVEN_API_KEY"] = eleven_api_key

KEYWORDS = ["cookiebot", "cookie bot", "cookie pot", "cookie bote", "cookie butter", "cookieball", "cookie ball", "que bot", "cookiebar", "cookie bar", "kukibot"]
hotword_detection_enabled = True
manual_trigger = False
sounds = []
voices = []

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

def call_controlbot_command(topic, payload):
    with open("controlbot_ipc.json", "w") as controlbot_ipc:
        json.dump({"topic": topic, "payload": payload, "user_info": {'id': 0, 'first_name': "Cookiebot"}, "user_name": "Cookiebot"}, controlbot_ipc)

def text_to_speech(text):
    from elevenlabs.client import ElevenLabs
    from elevenlabs import VoiceSettings
    elevenlabs_client = ElevenLabs(api_key=eleven_api_key)
    audio = elevenlabs_client.text_to_speech.convert(text=text, voice_id="Rb9J9nOjoNgGbjJUN5wt", voice_settings=VoiceSettings(stability=0.3, similarity_boost=1.0, style=0.0, speed=1.1, use_speaker_boost=True), model_id="eleven_multilingual_v2", output_format="mp3_44100_128")
    with open("tts.mp3", "wb") as f:
        for chunk in audio:
            if chunk:
                f.write(chunk)
    Waveform.play_audio_async("tts.mp3", delete=True)

class Cookiebot(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=decrypt_system_prompt(prompt_encryption_key))
        self.transcript_buffer = []
        self.buffer_max_size = 3
        self.context_window_seconds = 15
        self.manual_listening_active = False
        self.manual_session_buffer = []
        self.thinking_audio_thread = None

    async def llm_node(self, chat_ctx: llm.ChatContext, tools: list[FunctionTool], model_settings: ModelSettings) -> AsyncIterable[llm.ChatChunk]:
        thinking_sound_started = False
        answer = ''
        async for chunk in Agent.default.llm_node(self, chat_ctx, tools, model_settings):
            if not thinking_sound_started:
                self.thinking_audio_thread = Waveform.play_audio_async("sfx/assistant_thinking.wav")
                thinking_sound_started = True
            chunktext = getattr(chunk.delta, 'content', '') if hasattr(chunk, 'delta') else str(chunk)
            if chunktext:
                answer += chunktext
            yield chunk
        if thinking_sound_started:
            Waveform.stop_flag = True
        call_controlbot_command("dynamo/chat_logs", {'answer': answer})

    async def stt_node(self, text: AsyncIterable[str], model_settings: Optional[dict] = None) -> Optional[AsyncIterable[rtc.AudioFrame]]:
        parent_stream = super().stt_node(text, model_settings)
        if parent_stream is None:
            return None
        async def process_stream():
            global manual_trigger
            async for event in parent_stream:
                if hasattr(event, 'type') and str(event.type) == "SpeechEventType.FINAL_TRANSCRIPT" and event.alternatives:
                    transcript = event.alternatives[0].text
                    current_time = time.time()
                    self.transcript_buffer.append({'text': transcript, 'timestamp': current_time, 'event': event})
                    self.transcript_buffer = [item for item in self.transcript_buffer if current_time - item['timestamp'] <= self.context_window_seconds]
                    self.transcript_buffer = self.transcript_buffer[-self.buffer_max_size:]
                    print(f"Transcript: {transcript}")
                    if manual_trigger:
                        print("Assistant manual trigger activated - starting listening session")
                        Waveform.play_audio_async("sfx/assistant_listening.wav")
                        manual_trigger = False
                        self.manual_listening_active = True
                        self.manual_session_buffer = []  # Clear previous manual session
                    if self.manual_listening_active:
                        self.manual_session_buffer.append(transcript)
                        print(f"Manual session collecting: {transcript}")
                        if len(self.manual_session_buffer) >= 1:  # Process after first complete sentence
                            print("Processing manual session input")
                            self.manual_listening_active = False
                            context_text = " ".join([item['text'] for item in self.transcript_buffer[-2:]])  # Last 2 context items
                            manual_text = " ".join(self.manual_session_buffer)
                            combined_text = f"{context_text} {manual_text}".strip()
                            modified_event = event
                            if hasattr(event, 'alternatives') and event.alternatives:
                                event.alternatives[0].text = combined_text
                            call_controlbot_command("dynamo/chat_logs", {'query': combined_text})
                            yield modified_event
                            self.manual_session_buffer = []
                        continue
                    elif hotword_detection_enabled and any(keyword.lower() in transcript.lower() for keyword in KEYWORDS):
                        print(f"Assistant activation keyword detected")
                        Waveform.play_audio("sfx/assistant_listening.wav")
                        combined_text = " ".join([item['text'] for item in self.transcript_buffer]).lower()
                        for keyword in KEYWORDS:
                            combined_text = combined_text.replace(keyword, "cookiebot")
                        modified_event = event
                        if hasattr(event, 'alternatives') and event.alternatives:
                            event.alternatives[0].text = combined_text
                        call_controlbot_command("dynamo/chat_logs", {'query': combined_text})
                        yield modified_event
                        self.transcript_buffer = []
                elif hasattr(event, 'type') and str(event.type) == "SpeechEventType.INTERIM_TRANSCRIPT":
                    print(f"Interim Transcript: {event.alternatives[0].text}")
        return process_stream()

    @function_tool()
    async def play_music(self, query: str) -> str:
        """Play music on the fursuit's audio system.
        
        Parameters:
        - query: The name of the song, artist, or genre to play
        
        Use this when user requests music playback, wants to listen to specific tracks, or mentions music preferences.
        Search for songs using song name, artist name, or genre, and begins to play the first result found."""
        call_controlbot_command('dynamo/spotify', {"action": "search_and_play", "query": query})
        return f"Searching and playing '{query}'"

    @function_tool()
    async def stop_music(self) -> str:
        """Stop the currently playing music on the fursuit's audio system.
        
        Use this when user requests to stop or pause music playback, wants to end listening to music, or mentions music control.
        Stops/pauses the music if it is currently playing, otherwise does nothing."""
        call_controlbot_command('dynamo/spotify', {"action": "pause"})
        return "Music stopped"

    @function_tool()
    async def set_output_volume(self, volume: int) -> str:
        """Control the system's master output volume level.
        
        Parameters:
        - volume: Volume level from 0 (mute) to 100 (maximum). Must be an integer.
        
        Use this when user wants to adjust how loud everything sounds, make things quieter/louder,
        or mute the system. This affects all audio output from the computer."""
        if not 0 <= volume <= 100:
            return "Volume must be between 0 and 100"
        call_controlbot_command('dynamo/commands/set-output-volume', {'volume': volume})
        return f"Output volume set to {volume}%"

    @function_tool()
    async def get_sound_effects(self) -> str:
        """Retrieve the complete list of available Voicemod sound effects that can be played. 
        Use this when the user asks what sounds are available or wants to browse sound options.
        Returns a formatted list of sound effect IDs that can be used with play_sound_effect()."""
        return f"Available sound effects: {sounds}"

    @function_tool()
    async def play_sound_effect(self, effect_id: str = None) -> str:
        """Play a specific Voicemod sound effect or stop all currently playing sounds.
        
        Parameters:
        - effect_id: The sound effect ID to play (get list with get_sound_effects()). 
                    If None or empty, stops all currently playing sound effects.
        
        Use this when user wants to play a specific sound, make noise, or stop all sounds.
        Always call get_sound_effects() first if you need to suggest available sounds."""
        call_controlbot_command('dynamo/commands/play-sound-effect', {'effectId': effect_id} if effect_id else {})
        if effect_id:
            return f"Playing sound effect {effect_id}"
        else:
            return "Stopped all sound effects"

    @function_tool()
    async def get_voice_effects(self) -> str:
        """Retrieve the complete list of available Voicemod voice effects/filters that can be applied.
        Use this when the user asks about voice changing options or wants to see available voice filters.
        Returns a formatted list of voice effect IDs that can be used with set_voice_effect()."""
        return f"Available voice effects: {voices}"
    
    @function_tool()
    async def set_voice_effect(self, effect_id: str) -> str:
        """Change the active voice effect/filter in Voicemod to modify how the user's voice sounds.
        
        Parameters:
        - effect_id: The voice effect ID to activate (get list with get_voice_effects())
        
        Use this when user wants to change their voice, sound different, or apply voice filters.
        Call get_voice_effects() first if you need to suggest available voice options."""
        call_controlbot_command('dynamo/commands/set-voice-effect', {'effectId': effect_id})
        return f"Voice effect set to {effect_id}"

    @function_tool()
    async def set_expression(self, expression: str) -> str:
        """Change the facial expression displayed on the fursuit's eye screens.
        
        Parameters:
        - expression: Expression ID (0-12) or 'SillyON'/'SillyOFF' for crossed eyes
            0: Angry - for frustration, anger, annoyance
            1: Disgusted - for disgust, revulsion, distaste  
            2: Happy - for joy, happiness, excitement
            3: Neutral - for calm, default, normal state
            4: Sad - for sadness, disappointment, sorrow
            5: Surprised - for shock, amazement, surprise
            6: Hypnotic - for mesmerizing, trance-like state
            7: Heart eyes - for love, affection, adoration
            8: Rainbow eyes - for pride, celebration, colorful mood
            9: Nightmare/demon - for scary, evil, menacing look
            10: Gear eyes - for mechanical, robotic, technical mood
            11: Sans undertale - for specific character reference
            12: Mischievous - for playful, sneaky, troublemaking
            SillyON/SillyOFF: Toggle crossed eyes effect
        
        Use this to match the user's mood, emotional state, or when they request specific expressions.
        Choose expressions that fit the context of the conversation or user's feelings."""
        call_controlbot_command('dynamo/commands/set-expression', {'expression': expression})
        return f"Expression set to {expression}"

    @function_tool()
    async def toggle_leds(self, enabled: bool) -> str:
        """Control the LED lighting system on the electronic fursuit.
        
        Parameters:
        - enabled: True to turn LEDs on, False to turn them off
        
        Use this when user wants to control suit lighting, turn lights on/off, or mentions LEDs, lighting, or glowing."""
        call_controlbot_command('dynamo/commands/leds-toggle', {'enabled': enabled})
        status = "enabled" if enabled else "disabled"
        return f"LEDs {status}"

    @function_tool()
    async def set_leds_color(self, color: str) -> str:
        """Change the color of the fursuit's LED lighting system using hex color codes.
        
        Parameters:
        - color: Hex color code (e.g., '#FF0000' for red, '#00FF00' for green, '#0000FF' for blue)
        
        Use this when user mentions specific colors, wants to change LED color, or describes color preferences.
        Convert color names to hex codes (red=#FF0000, blue=#0000FF, green=#00FF00, etc.)."""
        call_controlbot_command('dynamo/commands/leds-color', {'color': color})
        return f"LED color set to {color}"

    @function_tool()
    async def set_leds_effect(self, effect: str) -> str:
        """Apply visual effects to the fursuit's LED lighting system.
        
        Parameters:
        - effect: Effect name
            'solid_color': Static color, 
            'fade': Fade between colors,
            'wipe': Wipe effect,
            'theater_chase': Theater chase effect,
            'rainbow': Color cycling,
            'strobe': Strobe effect,
            'moving substrips': Moving sub-LED strips effect,
            'none (off)': Turn off LED effects
        
        Use this when user wants dynamic lighting, animated effects, or mentions specific lighting patterns.
        'static' = solid color, 'pulse' = breathing effect, 'rainbow' = color cycling."""
        call_controlbot_command('dynamo/commands/leds-effect', {'effect': effect})
        return f"LED effect set to {effect}"

    @function_tool()
    async def search_internet(self, query: str) -> str:
        """Search the internet for current information, facts, news, or answers to questions.
        
        Parameters:
        - query: The search terms or question to look up online
        
        Use this when:
        - User asks about current events, news, or recent information
        - You need factual information you don't have in your training data
        - User requests web search or wants to look something up
        - Questions about real-time data (weather, stocks, etc.)
        - Verification of facts or getting updated information
        
        Returns formatted search results with quick answers and source links."""
        try:
            if not query or not query.strip():
                return "Error: Search query cannot be empty."
            if not tavily_api_key:
                return "Error: Tavily API key not configured."
            url = "https://api.tavily.com/search"
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {tavily_api_key}"}
            payload = {"query": query.strip(), "search_depth": "basic", "include_answer": True, "include_raw_content": False, "max_results": 5, "include_domains": [], "exclude_domains": []}
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

def monitor_assistant_ipc():
    """Monitor for IPC requests"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    async def process_ipc_requests():
        while True:
            try:
                if os.path.exists("assistant_ipc.json"):
                    with open("assistant_ipc.json", "r") as assistant_ipc:
                        request = json.load(assistant_ipc)
                        print(request)
                    os.remove("assistant_ipc.json")
                    if request.get("command") == "tts":
                        text_to_speech(request["text"])
                    elif request.get("command") == "hotword_detection":
                        global hotword_detection_enabled
                        hotword_detection_enabled = request["enabled"]
                    elif request.get("command") == "hotword_trigger":
                        global manual_trigger
                        manual_trigger = True
                    elif request.get("command") == "update_sounds":
                        global sounds
                        sounds = request["sounds"]
                    elif request.get("command") == "update_voices":
                        global voices
                        voices = request["voices"]
            except Exception as e:
                print(f"IPC monitor error: {e}")
            await asyncio.sleep(0.1)
    try:
        loop.run_until_complete(process_ipc_requests())
    except Exception as e:
        print(f"IPC monitor thread error: {e}")
    finally:
        loop.close()

async def entrypoint(ctx: JobContext):
    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi", interim_results=True, no_delay=True, punctuate=True, filler_words=True),
        llm=openai.LLM(model="gpt-4.1-mini", temperature=0.9),
        tts=elevenlabs.TTS(voice_id="Rb9J9nOjoNgGbjJUN5wt", model="eleven_multilingual_v2", voice_settings=elevenlabs.VoiceSettings(stability=0.3, similarity_boost=1.0, style=0.0, speed=1.05, use_speaker_boost=True)),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        allow_interruptions=True,
        preemptive_generation=False
    )
    ipc_monitor_thread = threading.Thread(target=monitor_assistant_ipc, daemon=True)
    ipc_monitor_thread.start()
    await session.start(
        agent=Cookiebot(), 
        room=ctx.room,
        room_input_options=RoomInputOptions(noise_cancellation=noise_cancellation.BVC()),
        room_output_options=RoomOutputOptions(transcription_enabled=True),
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm, max_retry=float('inf')))