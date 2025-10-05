import websockets
import asyncio
import json
import random
import string
import time
from Environment import voicemod_key

voicemod_websocket = None
url = "ws://localhost:59129/v1"

toggle_hear_my_voice_flag = False
toggle_voice_changer_flag = False
toggle_background_flag = False
load_voice_flag = True
play_sound_flag = False
stop_sounds_flag = False
desired_status = True
voice_id = '2eeebd97-8de3-4d94-91ae-79e6588e7715'
sound_id = ''
voices = []
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
no_response_commands = ['playMeme', 'stopAllMemeSounds']

async def send_message(websocket, command, payload):
    message = {"action": command, "id": ''.join(random.choice(string.ascii_lowercase) for _ in range(36)), "payload": payload}
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
    global voices
    for _ in range(3):
        voices = []
        response = await send_message(voicemod_websocket, 'getVoices', {})
        if 'payload' not in response:
            continue
        response = response['payload']
        if response is not None and 'voices' in response:
            response = response["voices"]
            for voice in response:
                voices.append({"name": voice["friendlyName"], "id": voice["id"]})
            voices = sorted(voices, key=lambda k: k['name'])
            return

async def getSounds():
    global sounds
    for _ in range(3):
        sounds = []
        response = await send_message(voicemod_websocket, 'getMemes', {})
        if response is not None and 'actionObject' in response and 'listOfMemes' in response['actionObject']:
            for sound in response["actionObject"]["listOfMemes"]:
                if sound.get("Type") == "PlayStop" and sound.get('Name').islower():
                    sounds.append({"name": sound["Name"], "id": sound["FileName"]})
            sounds = sorted(sounds, key=lambda k: k['name'])
            return
        
async def getStatus(command):
    status = await send_message(voicemod_websocket, command, {})
    if not 'value' in status['actionObject']:
        return None
    return status['actionObject']['value']
    
async def toggleHearMyVoice(desired_status):
    status = await getStatus('getHearMyselfStatus')
    if status == desired_status:
        return
    return await send_message(voicemod_websocket, 'toggleHearMyVoice', {})

async def toggleVoiceChanger(desired_status):
    status = await getStatus('getVoiceChangerStatus')
    if status == desired_status:
        return
    return await send_message(voicemod_websocket, 'toggleVoiceChanger', {})

async def toggleBackground(desired_status):
    status = await getStatus('getBackgroundEffectStatus')
    if status == desired_status:
        return
    return await send_message(voicemod_websocket, 'toggleBackground', {})

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
                    await setVoice(voice_id)
                    time.sleep(5)
                    if not await getStatus('getHearMyselfStatus'):
                        await toggleHearMyVoice(True)
                    if not await getStatus('getVoiceChangerStatus'):
                        await toggleVoiceChanger(True)
                    if not await getStatus('getBackgroundEffectStatus'):
                        await toggleBackground(True)
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

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(connect())
    except Exception as e:
        print(e)