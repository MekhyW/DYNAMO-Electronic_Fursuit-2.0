from dotenv import load_dotenv
import os
load_dotenv('../.env')

voicemod_key = os.getenv("voicemod_key")
fursuitbot_token = os.getenv("fursuitbot_token")
fursuitbot_ownerID = os.getenv("fursuitbot_ownerID")
openai_key = os.getenv("openai_key")
porcupine_key = os.getenv("porcupine_key")