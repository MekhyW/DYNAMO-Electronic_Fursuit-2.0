import ControlBot
import websockets
import asyncio
import json
import random
import string
import time
import os
from Environment import voicemod_key
import Waveform

voicemod_websocket = None
url = "ws://localhost:59129/v1"

toggle_hear_my_voice_flag = False
toggle_voice_changer_flag = False
toggle_background_flag = False
load_voice_flag = True
play_sound_flag = False
stop_sounds_flag = False
desired_status = True
voice_id = 'nofx'
sound_id = ''
voices = []
gibberish_voices = []
sounds = []

valid_response_actions = {
    'getHearMyselfStatus': ['getHearMyselfStatus'],
    'getVoiceChangerStatus': ['getVoiceChangerStatus'],
    'getBackgroundEffectStatus': ['getBackgroundEffectStatus'],
    'toggleHearMyVoice': ['hearMySelfEnabledEvent', 'hearMySelfDisabledEvent'],
    'toggleVoiceChanger': ['voiceChangerEnabledEvent', 'voiceChangerDisabledEvent'],
    'toggleBackground': ['backgroundEffectsEnabledEvent', 'backgroundEffectsDisabledEvent'],
    'getVoices': ['getVoices'],
    'loadVoice': ['loadVoice', 'voiceLoadedEvent'],
    'getMemes': ['getMemes'],
    'getBitmap': ['getBitmap']
}

async def send_message(websocket, command, payload):
    no_response_commands = ['playMeme', 'stopAllMemeSounds']
    message = {"action": command, "id": ''.join(random.choice(string.ascii_lowercase) for i in range(36)), "payload": payload}
    await websocket.send(json.dumps(message))
    if command in no_response_commands:
        return True
    while True:
        try:
            response = await websocket.recv()
            response = json.loads(response)
            if command in valid_response_actions and 'action' in response and response['action'] not in valid_response_actions[command]:
                continue
            return response
        except asyncio.TimeoutError:
            print("Voicemod Timeout")
            break
    return None

async def getVoices():
    global voices, gibberish_voices
    for _ in range(3):
        voices = []
        gibberish_voices = []
        response = await send_message(voicemod_websocket, 'getVoices', {})
        response = response['payload']
        if response is not None and 'voices' in response:
            response = response["voices"]
            for voice in response:
                if voice["favorited"]:
                    voices.append({"name": voice["friendlyName"], "id": voice["id"]})
            for gibberish_voice in os.listdir("sfx/gibberish_voices"):
                name = gibberish_voice.replace(".wav", "")
                gibberish_voices.append({"name": name, "id": f"gibberish-{name}"})
            voices = sorted(voices, key=lambda k: k['name'])
            gibberish_voices = sorted(gibberish_voices, key=lambda k: k['name'])
            return

async def getSounds():
    global sounds
    for _ in range(3):
        sounds = []
        response = await send_message(voicemod_websocket, 'getMemes', {})
        if response is not None and 'actionObject' in response and 'listOfMemes' in response['actionObject']:
            for sound in response["actionObject"]["listOfMemes"]:
                if sound.get("profile") == "Fursuit":
                    sounds.append({"name": sound["name"], "id": sound["FileName"]})
            sounds = sorted(sounds, key=lambda k: k['name'])
            return
        
async def getStatus(command):
    status = await send_message(voicemod_websocket, command, {})
    return status['actionObject']['value']
    
async def toggleHearMyVoice(desired_status):
    while True:
        response = await send_message(voicemod_websocket, 'toggleHearMyVoice', {})
        if (desired_status and 'action' in response and response['action'] == 'hearMySelfEnabledEvent') or ((not desired_status) and 'action' in response and response['action'] == 'hearMySelfDisabledEvent'):
            break

async def toggleVoiceChanger(desired_status):
    while True:
        response = await send_message(voicemod_websocket, 'toggleVoiceChanger', {})
        if (desired_status and 'action' in response and response['action'] == 'voiceChangerEnabledEvent') or ((not desired_status) and 'action' in response and response['action'] == 'voiceChangerDisabledEvent'):
            break

async def toggleBackground(desired_status):
    while True:
        response = await send_message(voicemod_websocket, 'toggleBackground', {})
        if (desired_status and 'action' in response and response['action'] == 'backgroundEffectsEnabledEvent') or ((not desired_status) and 'action' in response and response['action'] == 'backgroundEffectsDisabledEvent'):
            break

async def setVoice(voice_id):
    await send_message(voicemod_websocket, 'loadVoice', {"voiceId": voice_id})

async def playSound(meme_id):
    await send_message(voicemod_websocket, 'playMeme', {"FileName": meme_id, "IsKeyDown": True})

async def stopSounds():
    await send_message(voicemod_websocket, 'stopAllMemeSounds', {})

async def getBitmap(type, id):
    id_type = "voiceID" if type == "voice" else "memeId"
    for _ in range(3):
        response = await send_message(voicemod_websocket, 'getBitmap', {id_type: id})
        if response is not None and 'actionObject' in response and 'result' in response['actionObject']:
            return response['actionObject']['result']['default']

async def connect():
    global voicemod_websocket, toggle_hear_my_voice_flag, toggle_voice_changer_flag, toggle_background_flag, load_voice_flag, play_sound_flag, stop_sounds_flag, desired_status, voice_id, sound_id
    try:
        async with websockets.connect(url, ping_interval=5, max_size=2**30) as websocket_voicemod:
            await send_message(websocket_voicemod, "registerClient", {"clientKey": voicemod_key})
            voicemod_websocket = websocket_voicemod
            print("Voicemod connected!")
            await getVoices()
            print("Voices loaded")
            await getSounds()
            print("Soundboard loaded")
            ControlBot.publish_voicemod_data()
            while True:
                time.sleep(0.1)
                if toggle_hear_my_voice_flag:
                    await toggleHearMyVoice(desired_status)
                    toggle_hear_my_voice_flag = False
                if toggle_voice_changer_flag:
                    await toggleVoiceChanger(desired_status)
                    toggle_voice_changer_flag = False
                if toggle_background_flag:
                    await toggleBackground(desired_status)
                    toggle_background_flag = False
                if load_voice_flag:
                    load_voice_flag = False
                    if voice_id.startswith("gibberish-"):
                        if await getStatus('getHearMyselfStatus'):
                            await toggleHearMyVoice(False)
                        Waveform.gibberish(voice_id.replace("gibberish-", ""))
                    else:
                        await setVoice(voice_id)
                        time.sleep(5)
                        if not await getStatus('getHearMyselfStatus'):
                            await toggleHearMyVoice(True)
                        if not await getStatus('getVoiceChangerStatus'):
                            await toggleVoiceChanger(True)
                if play_sound_flag:
                    play_sound_flag = False
                    await playSound(sound_id)
                if stop_sounds_flag:
                    stop_sounds_flag = False
                    await stopSounds()
                try:
                    await asyncio.wait_for(websocket_voicemod.recv(), timeout=1)
                except asyncio.TimeoutError:
                    pass
    except ConnectionRefusedError:
        print("Voicemod not running")