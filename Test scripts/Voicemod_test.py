#https://control-api.voicemod.net/getting-started
import websockets
import asyncio
import json
import random
import string

with open("../Main software/credentials.json") as f:
    credentials = json.load(f)
voicemod_key = credentials["voicemod_key"]

async def send_message(websocket, message, only_once=False):
    response = None
    response_prev = None
    while True:
        try:
            await websocket.send(json.dumps(message))
            response = await asyncio.wait_for(websocket.recv(), timeout=1)
            response = json.loads(response)
            if response_prev == response or only_once:
                break
            response_prev = response
        except asyncio.TimeoutError:
            break
    return response

async def main():
    url = "ws://localhost:59129/v1"
    try:
        async with websockets.connect(url, ping_interval=10) as websocket_voicemod:
            register_message = {"action": "registerClient", "id": "ff7d7f15-0cbf-4c44-bc31-b56e0a6c9fa6",
                "payload": {"clientKey": voicemod_key}
            }
            register_response = await send_message(websocket_voicemod, register_message)
            print(register_response)
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
                                print(voice["friendlyName"], voice["id"])
                        else:
                            print("Error getting voices")
                    case "getMemes":
                        sounds = await send_message(websocket_voicemod, message)
                        if sounds is not None and 'actionObject' in sounds:
                            sounds = sounds["actionObject"]["listOfMemes"]
                            for sound in sounds:
                                print(sound["name"], sound["FileName"])
                        else:
                            print("Error getting sounds")
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
                        await send_message(websocket_voicemod, message, only_once=True)
                    case "loadVoice":
                        voice_id = input("Enter voice id: ")
                        message["payload"]["voiceId"] = voice_id
                        await send_message(websocket_voicemod, message, only_once=True)
                    case "playMeme":
                        meme_id = input("Enter sound id: ")
                        message["payload"]["FileName"] = meme_id
                        message["payload"]["IsKeyDown"] = True
                        await send_message(websocket_voicemod, message, only_once=True)
                    case "stopAllMemeSounds":
                        await send_message(websocket_voicemod, message)
                    case _:
                        print("Invalid command")
    except ConnectionRefusedError:
        print("Connection refused. Is Voicemod running?")

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())