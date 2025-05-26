from dotenv import load_dotenv
import os

try:
    load_dotenv('../.env')
    voicemod_key = os.getenv("voicemod_key")
    fursuitbot_token = os.getenv("fursuitbot_token")
    fursuitbot_ownerID = os.getenv("fursuitbot_ownerID")
    openai_key = os.getenv("openai_key")
    porcupine_key = os.getenv("porcupine_key")
except Exception as e:
    voicemod_key = None
    fursuitbot_token = None
    fursuitbot_ownerID = None
    openai_key = None
    porcupine_key = None
    print(f"Environment variable loading failed with error: {e}")