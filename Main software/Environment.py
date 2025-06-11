from dotenv import load_dotenv
import os

try:
    load_dotenv('../.env')
    voicemod_key = os.getenv("voicemod_key")
    fursuitbot_token = os.getenv("fursuitbot_token")
    fursuitbot_ownerID = os.getenv("fursuitbot_ownerID")
    openai_key = os.getenv("openai_key")
    porcupine_key = os.getenv("porcupine_key")
    mqtt_host = os.getenv("mqtt_host")
    mqtt_port = int(os.getenv("mqtt_port"))
    mqtt_username = os.getenv("mqtt_username")
    mqtt_password = os.getenv("mqtt_password")
except Exception as e:
    voicemod_key = None
    fursuitbot_token = None
    fursuitbot_ownerID = None
    openai_key = None
    porcupine_key = None
    mqtt_host = None
    mqtt_port = None
    mqtt_username = None
    mqtt_password = None
    print(f"Environment variable loading failed with error: {e}")