#https://control-api.voicemod.net/getting-started
import websockets
import asyncio
import json
import random
import string

voicemod_key = ''
url = "ws://localhost:59129/v1"

async def send_message(websocket, message):
    while True:
        try:
            await websocket.send(json.dumps(message))
            response = await websocket.recv()
            response = json.loads(response)
            print(response)
            valid_response_actions = {
                'getHearMyselfStatus': ['getHearMyselfStatus'],
                'getVoiceChangerStatus': ['getVoiceChangerStatus'],
                'getBackgroundEffectStatus': ['getBackgroundEffectStatus'],
                'toggleHearMyVoice': ['hearMySelfEnabledEvent', 'hearMySelfDisabledEvent'],
                'toggleVoiceChanger': ['voiceChangerEnabledEvent', 'voiceChangerDisabledEvent'],
                'toggleBackground': ['backgroundEffectsEnabledEvent', 'backgroundEffectsDisabledEvent'],
                'getVoices': ['getVoices'],
                'loadVoice': ['loadVoice']
            }
            if message['action'] in valid_response_actions and 'action' in response and response['action'] not in valid_response_actions[message['action']]:
                continue
            return response
        except asyncio.TimeoutError:
            print("Timeout")
            break
    return None

async def main():
    try:
        async with websockets.connect(url, ping_interval=5, max_size=2**30) as websocket_voicemod:
            register_message = {"action": "registerClient", "id": "ff7d7f15-0cbf-4c44-bc31-b56e0a6c9fa6",
                "payload": {"clientKey": voicemod_key}
            }
            await send_message(websocket_voicemod, register_message)
            while True:
                command = input("Enter command: ")
                message = {"action": command, "id": ''.join(random.choice(string.ascii_lowercase) for i in range(36)), "payload": {}}
                match command:
                    case "exit" | "quit":
                        break
                    case "getVoices":
                        voices = await send_message(websocket_voicemod, message)
                        voices = voices['payload']
                        if voices is not None and 'voices' in voices:
                            voices = voices["voices"]
                            for voice in voices:
                                if voice.get("favorited"):
                                    print(voice["friendlyName"], voice["id"])
                        else:
                            print("Error getting voices")
                    case "getMemes":
                        sounds = await send_message(websocket_voicemod, message)
                        if sounds is not None and 'actionObject' in sounds and 'listOfMemes' in sounds['actionObject']:
                            sounds = sounds["actionObject"]["listOfMemes"]
                            for sound in sounds:
                                if sound.get("profile") == "Fursuit":
                                    print(sound["name"], sound["FileName"])
                        else:
                            print("Error getting sounds")
                    case "getAllSoundboard":
                        soundboards = await send_message(websocket_voicemod, message)
                        if soundboards is not None and 'payload' in soundboards and 'soundboards' in soundboards['payload']:
                            soundboards = soundboards["payload"]["soundboards"]
                            for soundboard in soundboards:
                                print(soundboard["name"])
                    case "getHearMyselfStatus" | "getVoiceChangerStatus" | "getBackgroundEffectStatus":
                        status = await send_message(websocket_voicemod, message)
                        if status is not None and 'actionObject' in status:
                            status = status["actionObject"]
                            if status is not None:
                                status = status['value']
                                print(status) 
                        else:
                            print("Error getting status")
                    case "toggleHearMyVoice" | "toggleVoiceChanger" | "toggleBackground":
                        await send_message(websocket_voicemod, message)
                    case "loadVoice":
                        voice_id = input("Enter voice id: ")
                        message["payload"]["voiceId"] = voice_id
                        await send_message(websocket_voicemod, message)
                    case "playMeme":
                        meme_id = input("Enter sound id: ")
                        message["payload"]["FileName"] = meme_id
                        message["payload"]["IsKeyDown"] = True
                        await send_message(websocket_voicemod, message)
                    case "stopAllMemeSounds":
                        await send_message(websocket_voicemod, message)
                    case "getBitmapVoice" | "getBitmapMeme":
                        id_type = "voiceID" if command == "getBitmapVoice" else "memeId"
                        prompt = "Enter id of voice or sound: " if command == "getBitmapVoice" else "Enter id of meme: "
                        id_value = input(prompt)
                        message["payload"][id_type] = id_value
                        message["action"] = "getBitmap"
                        bitmap = await send_message(websocket_voicemod, message)
                        if bitmap is not None and 'actionObject' in bitmap and 'result' in bitmap['actionObject']:
                            bitmap = bitmap["actionObject"]["result"]["default"]
                            print(bitmap)
                        else:
                            print("Error getting bitmap")
                    case _:
                        print("Invalid command")
    except ConnectionRefusedError:
        print("Connection refused. Is Voicemod running?")
    except Exception as e:
        print(e)

if __name__ == "__main__":
    while True:
        asyncio.get_event_loop().run_until_complete(main())