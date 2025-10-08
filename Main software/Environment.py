from dotenv import load_dotenv
import os

try:
    load_dotenv('../.env')
except Exception as e:
    print(f"Environment variable loading failed with error: {e}")

voicemod_key = os.getenv("voicemod_key")
fursuitbot_token = os.getenv("fursuitbot_token")
fursuitbot_ownerID = os.getenv("fursuitbot_ownerID")
livekit_url = os.getenv("livekit_url")
livekit_api_key = os.getenv("livekit_api_key")
livekit_api_secret = os.getenv("livekit_api_secret")
prompt_encryption_key = os.getenv("prompt_encryption_key")
deepgram_api_key = os.getenv("deepgram_api_key")
openai_key = os.getenv("openai_key")
tavily_api_key = os.getenv("tavily_api_key")
eleven_api_key = os.getenv("eleven_api_key")
mqtt_host = os.getenv("mqtt_host")
mqtt_port = int(os.getenv("mqtt_port"))
mqtt_username = os.getenv("mqtt_username")
mqtt_password = os.getenv("mqtt_password")