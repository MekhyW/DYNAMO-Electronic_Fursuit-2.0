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
sfx_id = None
voice_id = None
voices = None

async def send_message(websocket, command, payload, only_once=False):
    response = None
    response_prev = None
    while True:
        try:
            message = {"action": command, "id": ''.join(random.choice(string.ascii_lowercase) for i in range(36)), "payload": payload}
            await websocket.send(json.dumps(message))
            response = await asyncio.wait_for(websocket.recv(), timeout=1)
            response = json.loads(response)
            if response_prev == response or only_once:
                break
            response_prev = response
        except asyncio.TimeoutError:
            print("Voicemod Timeout")
            break
    return response

async def getVoices():
    for attempt in range(3):
        voicesdicts = []
        voices = await send_message(voicemod_websocket, 'getVoices', {}, only_once=True)
        voices = voices['payload']
        if voices is not None and 'voices' in voices:
            voices = voices["voices"]
            for voice in voices:
                if voice["favorited"] == True:
                    voicesdicts.append({"name": voice["friendlyName"], "id": voice["id"]})
            return voicesdicts
    
#async def getAllSoundboard():
#    for attempt in range(3):
#        soundboardsdicts = []
#        soundboards = await send_message(voicemod_websocket, 'getAllSoundboard', {}, only_once=True)
#        if soundboards is not None and 'payload' in soundboards and 'soundboards' in soundboards['payload']:
#            for soundboard in soundboards['payload']['soundboards']:
#                soundboardsdicts.append({"name": soundboard["name"], "id": soundboard["id"], "sounds": soundboard["sounds"]})
#            return soundboardsdicts
    
async def toggleHearMyVoice():
    await send_message(voicemod_websocket, 'toggleHearMyVoice', {}, only_once=True)

async def toggleVoiceChanger():
    await send_message(voicemod_websocket, 'toggleVoiceChanger', {}, only_once=True)

async def toggleBackground():
    await send_message(voicemod_websocket, 'toggleBackground', {}, only_once=True)

async def setVoice(voice_id):
    await send_message(voicemod_websocket, 'loadVoice', {"voiceId": voice_id}, only_once=True)

async def playSFX(meme_id):
    await send_message(voicemod_websocket, 'playMeme', {"FileName": meme_id, "IsKeyDown": True}, only_once=True)

async def stopSFX():
    await send_message(voicemod_websocket, 'stopAllMemeSounds', {}, only_once=True)

async def connect():
    global voicemod_websocket, voices
    global toggle_hear_my_voice_flag, toggle_voice_changer_flag, toggle_background_flag, load_voice_flag
    global sfx_id, voice_id
    while True:
        try:
            async with websockets.connect(url, ping_interval=5) as websocket_voicemod:
                await send_message(websocket_voicemod, "registerClient", {"clientKey": voicemod_key})
                voicemod_websocket = websocket_voicemod
                print("Voicemod connected!")
                #soundboards = await getAllSoundboard()
                #print("Soundboards loaded")
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
                    #if play_sfx_flag:
                    #    await playSFX(sfx_id)
                    #    play_sfx_flag = False
                    #if stop_sfx_flag:
                    #    await stopSFX()
                    #    stop_sfx_flag = False
                    if load_voice_flag:
                        await setVoice(voice_id)
                        load_voice_flag = False
        except ConnectionRefusedError:
            print("Voicemod not running")
            time.sleep(1)
        except Exception as e:
            print(e)