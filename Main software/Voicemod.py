import websockets
import asyncio
import json
import random
import string
import time

voicemod_key = json.load(open("credentials.json"))["voicemod_key"]
voicemod_websocket = None
url = "ws://localhost:59129/v1"

toggle_hear_my_voice_flag = False
toggle_voice_changer_flag = False
toggle_background_flag = False
load_voice_flag = False
voice_id = None
voices = None

async def send_message(websocket, command, payload):
    while True:
        try:
            message = {"action": command, "id": ''.join(random.choice(string.ascii_lowercase) for i in range(36)), "payload": payload}
            await websocket.send(json.dumps(message))
            response = await websocket.recv()
            response = json.loads(response)
            valid_response_actions = {
                'toggleHearMyVoice': ['hearMySelfEnabledEvent', 'hearMySelfDisabledEvent'],
                'toggleVoiceChanger': ['voiceChangerEnabledEvent', 'voiceChangerDisabledEvent'],
                'toggleBackground': ['backgroundEffectsEnabledEvent', 'backgroundEffectsDisabledEvent'],
                'getVoices': ['getVoices'],
                'loadVoice': ['loadVoice']
            }
            if command in valid_response_actions and 'action' in response and response['action'] not in valid_response_actions[command]:
                continue
            return response
        except asyncio.TimeoutError:
            print("Voicemod Timeout")
            break
    return None

async def getVoices():
    for attempt in range(3):
        voicesdicts = []
        voices = await send_message(voicemod_websocket, 'getVoices', {})
        voices = voices['payload']
        if voices is not None and 'voices' in voices:
            voices = voices["voices"]
            for voice in voices:
                if voice["favorited"]:
                    voicesdicts.append({"name": voice["friendlyName"], "id": voice["id"]})
            return voicesdicts
    
async def toggleHearMyVoice():
    await send_message(voicemod_websocket, 'toggleHearMyVoice', {})

async def toggleVoiceChanger():
    await send_message(voicemod_websocket, 'toggleVoiceChanger', {})

async def toggleBackground():
    await send_message(voicemod_websocket, 'toggleBackground', {})

async def setVoice(voice_id):
    await send_message(voicemod_websocket, 'loadVoice', {"voiceId": voice_id})

async def connect():
    global voicemod_websocket, voices, voice_id
    global toggle_hear_my_voice_flag, toggle_voice_changer_flag, toggle_background_flag, load_voice_flag
    try:
        async with websockets.connect(url, ping_interval=5, max_size=2**30) as websocket_voicemod:
            await send_message(websocket_voicemod, "registerClient", {"clientKey": voicemod_key})
            voicemod_websocket = websocket_voicemod
            print("Voicemod connected!")
            voices = await getVoices()
            print("Voices loaded")
            while True:
                time.sleep(0.1)
                if toggle_hear_my_voice_flag:
                    await toggleHearMyVoice()
                    toggle_hear_my_voice_flag = False
                if toggle_voice_changer_flag:
                    await toggleVoiceChanger()
                    toggle_voice_changer_flag = False
                if toggle_background_flag:
                    await toggleBackground()
                    toggle_background_flag = False
                if load_voice_flag:
                    await setVoice(voice_id)
                    load_voice_flag = False
    except ConnectionRefusedError:
        print("Voicemod not running")