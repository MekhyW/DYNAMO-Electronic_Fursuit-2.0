import Windows
import telepot
from telepot.loop import MessageLoop
import paho.mqtt.client as mqtt
import ssl
import threading
import time
import uuid
from datetime import datetime, timezone
import traceback
import json
import os
from Environment import fursuitbot_token, fursuitbot_ownerID, mqtt_host, mqtt_port, mqtt_username, mqtt_password
import Waveform
import MachineVision
import Assistant
import Voicemod
import Unity
import Serial

refsheetpath = 'https://i.postimg.cc/Y25LSW-z2/refsheet.png'
stickerpack = 'https://t.me/addstickers/MekhyW'
mychatpath = 'https://t.me/MekhyW'
mqtt_client = None
last_mqtt_activity = 0
mqtt_health_check_interval = 60
mqtt_heartbeat_interval = 30
mqtt_keepalive_interval = 15

try:
    fursuitbot = telepot.Bot(fursuitbot_token)
except Exception as e:
    fursuitbot = None
    print(f"ControlBot constructor failed with error: {e}")

def on_mqtt_connect(client, userdata, flags, rc, properties=None):
    global last_mqtt_activity
    if rc != 0:
        print(f"MQTT connection failed with code {rc}")
        return
    print("Connected to MQTT broker")
    last_mqtt_activity = time.time()
    def setup_subscriptions():
        try:
            time.sleep(1)  # Brief delay to ensure connection is stable
            command_topics = [
                'dynamo/commands/play-sound-effect',
                'dynamo/commands/set-voice-effect',
                'dynamo/commands/set-output-volume',
                'dynamo/commands/microphone-toggle',
                'dynamo/commands/voice-changer-toggle',
                'dynamo/commands/background-sound-toggle',
                'dynamo/commands/leds-toggle',
                'dynamo/commands/leds-brightness',
                'dynamo/commands/eyes-brightness',
                'dynamo/commands/leds-color',
                'dynamo/commands/leds-effect',
                'dynamo/commands/hotword-detection-toggle',
                'dynamo/commands/hotword-trigger',
                'dynamo/commands/text-to-speech',
                'dynamo/commands/set-expression',
                'dynamo/commands/face-expression-tracking-toggle',
                'dynamo/commands/eye-tracking-toggle',
                'dynamo/commands/eyebrows-toggle',
                'dynamo/commands/shutdown',
                'dynamo/commands/reboot',
                'dynamo/commands/kill-software',
                'dynamo/commands/set-sound-device'
            ]
            for topic in command_topics:
                try:
                    result = client.subscribe(topic)
                    if result[0] == mqtt.MQTT_ERR_SUCCESS:
                        print(f"Subscribed to {topic}")
                    else:
                        print(f"Failed to subscribe to {topic}: {result}")
                    time.sleep(0.1)
                except Exception as e:
                    print(f"Error subscribing to {topic}: {e}")
            try:
                time.sleep(1.5)
                publish_device_data()
            except Exception as e:
                print(f"Error publishing device data: {e}")
            heartbeat_thread = threading.Thread(target=mqtt_heartbeat_worker, daemon=True)
            heartbeat_thread.start()
            Waveform.play_audio("sfx/bot_online.wav")
            print("MQTT Control bot online!")
            if fursuitbot:
                fursuitbot.sendMessage(fursuitbot_ownerID, '>>> CONTROL BOT READY! <<<')
        except Exception as e:
            print(f"Error in subscription setup: {e}")
        publish_voicemod_data() #Blocking loop waits for Voicemod data
    setup_thread = threading.Thread(target=setup_subscriptions, daemon=True)
    setup_thread.start()

def on_mqtt_disconnect(client, userdata, rc, properties=None):
    if rc == 0:
        print("MQTT: Disconnected cleanly")
        return
    print(f"MQTT: Unexpected disconnection (code: {rc})")
    if rc == 1:
        print("MQTT: Incorrect protocol version - check broker compatibility")
    elif rc == 2:
        print("MQTT: Invalid client identifier")
    elif rc == 3:
        print("MQTT: Server unavailable - broker may be down")
    elif rc == 4:
        print("MQTT: Check username and password")
    elif rc == 5:
        print("MQTT: Authorization failed")
    elif rc == 7:
        print("MQTT: Connection lost - network issue detected")
        print("MQTT: This usually indicates unstable network or broker overload")
    else:
        print(f"MQTT: Unknown disconnect reason: {rc}")

def send_telegram_log(command_description, user_info):
    """Send log message to both command issuer and owner via Telegram"""
    if not fursuitbot:
        return
    def telegram_worker():
        """Run telegram operations in separate thread to avoid blocking MQTT"""
        try:
            user_id = user_info.get('id')
            user_name = user_info.get('first_name', 'Unknown User')
            log_message = f">>> {command_description}"
            if user_id:
                try:
                    fursuitbot.sendMessage(user_id, log_message)
                except Exception as e:
                    print(f"Failed to send message to user {user_id}: {e}")
            if str(user_id) != str(fursuitbot_ownerID):
                try:
                    owner_message = f"🤖 MQTT Command Executed:\n{log_message}\n👤 Requested by: {user_name}"
                    fursuitbot.sendMessage(fursuitbot_ownerID, owner_message)
                except Exception as e:
                    print(f"Failed to send message to owner: {e}")
        except Exception as e:
            print(f"Error in telegram logging: {e}")
    telegram_thread = threading.Thread(target=telegram_worker, daemon=True)
    telegram_thread.start()

def on_mqtt_message(client, userdata, msg):
    """Handle incoming MQTT messages with improved error handling"""
    global last_mqtt_activity
    last_mqtt_activity = time.time()
    def process_message():
        """Process MQTT message in separate thread to prevent blocking"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            print(f"Received MQTT message on {topic}: {payload}")
            user_info = payload.get('user', {})
            user_name = user_info.get('first_name', 'Unknown')
            handle_mqtt_command(topic, payload, user_info, user_name)
        except json.JSONDecodeError as e:
            print(f"Error decoding MQTT message JSON: {e}")
        except Exception as e:
            print(f"Error processing MQTT message: {e}")
            traceback.print_exc()
    message_thread = threading.Thread(target=process_message, daemon=True)
    message_thread.start()

def handle_mqtt_command(topic, payload, user_info, user_name):
    """Handle specific MQTT commands"""
    try:
        if topic == 'dynamo/commands/play-sound-effect':
            effect_id = payload.get('effectId')
            if not effect_id:
                Voicemod.stop_sounds_flag = True
                Waveform.stop_flag = True
                return
            Voicemod.sound_id = str(effect_id)
            Voicemod.play_sound_flag = True
            print(f"Playing sound effect {effect_id} (requested by {user_name})")
            send_telegram_log(f"🔊 Playing sound effect #{effect_id}", user_info)
        elif topic == 'dynamo/commands/set-voice-effect':
            effect_id = payload.get('effectId')
            if effect_id is not None:
                Waveform.stop_gibberish_flag = True
                Voicemod.voice_id = str(effect_id)
                Voicemod.load_voice_flag = True
                print(f"Setting voice effect {effect_id} (requested by {user_name})")
                send_telegram_log(f"🎤 Voice effect changed to #{effect_id}", user_info)   
        elif topic == 'dynamo/commands/set-output-volume':
            volume = payload.get('volume')
            if volume is not None:
                Windows.set_system_volume(volume / 100.0)
                Waveform.play_audio("sfx/volume_set.wav")
                print(f"Setting output volume to {volume}% (requested by {user_name})")
                send_telegram_log(f"🔊 Output volume set to {volume}%", user_info)
        elif topic == 'dynamo/commands/microphone-toggle':
            enabled = payload.get('enabled')
            if enabled is not None:
                Voicemod.desired_status = enabled
                Voicemod.toggle_hear_my_voice_flag = True
                Waveform.play_audio("sfx/settings_toggle.wav")
                print(f"Microphone {'enabled' if enabled else 'disabled'} (requested by {user_name})")
                status = "enabled" if enabled else "disabled"
                send_telegram_log(f"🎙️ Microphone {status}", user_info)
        elif topic == 'dynamo/commands/voice-changer-toggle':
            enabled = payload.get('enabled')
            if enabled is not None:
                Waveform.stop_gibberish_flag = True
                Voicemod.desired_status = enabled
                Voicemod.toggle_voice_changer_flag = True
                Waveform.play_audio("sfx/settings_toggle.wav")
                print(f"Voice changer {'enabled' if enabled else 'disabled'} (requested by {user_name})")
                status = "enabled" if enabled else "disabled"
                send_telegram_log(f"🎤 Voice changer {status}", user_info)
        elif topic == 'dynamo/commands/background-sound-toggle':
            enabled = payload.get('enabled')
            if enabled is not None:
                Waveform.stop_gibberish_flag = True
                Voicemod.desired_status = enabled
                Voicemod.toggle_background_flag = True
                Waveform.play_audio("sfx/settings_toggle.wav")
                print(f"Background sound {'enabled' if enabled else 'disabled'} (requested by {user_name})")
                status = "enabled" if enabled else "disabled"
                send_telegram_log(f"🎵 Background sound {status}", user_info)
        elif topic == 'dynamo/commands/leds-toggle':
            enabled = payload.get('enabled')
            if enabled is not None:
                Serial.leds_on = 1 if enabled else 0
                MachineVision.eye_tracking_mode = False if enabled else True
                MachineVision.expression_manual_mode = True if enabled else False
                Waveform.play_audio("sfx/leds_state.wav")
                print(f"LEDs {'enabled' if enabled else 'disabled'} (requested by {user_name})")
                status = "enabled" if enabled else "disabled"
                send_telegram_log(f"💡 LEDs {status}", user_info)
        elif topic == 'dynamo/commands/leds-brightness':
            brightness = payload.get('brightness')
            if brightness is not None:
                Serial.leds_brightness = brightness
                MachineVision.eye_tracking_mode = False
                MachineVision.expression_manual_mode = True
                print(f"LEDs brightness set to {brightness}% (requested by {user_name})")
                send_telegram_log(f"💡 LEDs brightness set to {brightness}%", user_info)
        elif topic == 'dynamo/commands/eyes-brightness':
            brightness = payload.get('brightness')
            if brightness is not None:
                Unity.screen_brightness = brightness
                print(f"Eyes brightness set to {brightness}% (requested by {user_name})")
                send_telegram_log(f"👁️ Eyes brightness set to {brightness}%", user_info)
        elif topic == 'dynamo/commands/leds-color':
            color = payload.get('color')
            if color is not None:
                try:
                    Serial.leds_on = 1
                    color = color.lstrip('#')
                    Serial.leds_color_r = int(color[0:2], 16)
                    Serial.leds_color_g = int(color[2:4], 16)
                    Serial.leds_color_b = int(color[4:6], 16)
                    MachineVision.eye_tracking_mode = False
                    MachineVision.expression_manual_mode = True
                    Waveform.play_audio("sfx/leds_color.wav")
                    print(f"LEDs color set to {color} (requested by {user_name})")
                    send_telegram_log(f"🌈 LEDs color changed to ({Serial.leds_color_r}, {Serial.leds_color_g}, {Serial.leds_color_b})", user_info)
                except ValueError:
                    print(f"Unknown LED color: {color}")
                    send_telegram_log(f"❌ Unknown LED color: {color}", user_info)
        elif topic == 'dynamo/commands/leds-effect':
            effect = payload.get('effect')
            if effect is not None:
                try:
                    effect_index = Serial.leds_effects_options.index(effect.lower())
                    Serial.leds_on = 1
                    Serial.leds_effect = effect_index
                    MachineVision.eye_tracking_mode = False
                    MachineVision.expression_manual_mode = True
                    Waveform.play_audio("sfx/leds_effect.wav")
                    print(f"LEDs effect set to {effect} (requested by {user_name})")
                    send_telegram_log(f"✨ LEDs effect changed to {effect.title()}", user_info)
                except ValueError:
                    print(f"Unknown LED effect: {effect}")
                    send_telegram_log(f"❌ Unknown LED effect: {effect}", user_info)  
        elif topic == 'dynamo/commands/hotword-detection-toggle':
            enabled = payload.get('enabled')
            if enabled is not None:
                Assistant.hotword_detection_enabled = enabled
                Waveform.play_audio("sfx/settings_toggle.wav")
                print(f"Hotword detection {'enabled' if enabled else 'disabled'} (requested by {user_name})")
                status = "enabled" if enabled else "disabled"
                send_telegram_log(f"🗣️ Hotword detection {status}", user_info)
        elif topic == 'dynamo/commands/hotword-trigger':
            Assistant.manual_trigger = True
            print(f"Hotword triggered (requested by {user_name})")
            send_telegram_log(f"🗣️ Assistant hotword triggered", user_info)
        elif topic == 'dynamo/commands/text-to-speech':
            text = payload.get('text')
            if text:
                LogAIMessage(f"TTS message by {user_name}", text)
                TextToSpeech(text, user_name)
                send_telegram_log(f"🗣️ Text-to-speech: '{text[:1000]}{'...' if len(text) > 1000 else ''}'", user_info)
        elif topic == 'dynamo/commands/set-expression':
            expression = payload.get('expression')
            if expression is not None:
                if not expression.isdigit():
                    MachineVision.force_crossed_eye = True if expression == "SillyON" else False
                    return
                expr_id = int(expression)
                MachineVision.expression_manual_mode = True
                MachineVision.expression_manual_id = expr_id
                MachineVision.eye_tracking_mode = False
                if expr_id == 6:
                    Serial.leds_effect = next(i for i, effect in enumerate(Serial.leds_effects_options) if 'rainbow' in effect)
                sound_files = {
                    0: "sfx/expr_angry.wav", 1: "sfx/expr_disgusted.wav", 2: "sfx/expr_happy.wav",
                    3: None, 4: "sfx/expr_sad.wav", 5: "sfx/expr_surprised.wav",
                    6: "sfx/expr_hypnotic.wav", 7: "sfx/expr_heart.wav", 8: "sfx/expr_rainbow.wav",
                    9: "sfx/expr_nightmare.wav", 10: "sfx/expr_gear.wav", 11: "sfx/expr_sans.wav",
                    12: "sfx/expr_mischievous.wav"
                }
                led_col = {
                    0: (255, 0, 0), 1: (0, 255, 33), 2: (255, 255, 0), 3: (255, 255, 255),
                    4: (0, 0, 255), 5: (255, 128, 0), 6: (255, 255, 255), 7: (255, 0, 0),
                    8: (255, 255, 255), 9: (255, 0, 0), 10: (255, 255, 255), 11: (0, 0, 255),
                    12: (255, 0, 220)
                }
                led_eff = {
                    0: 3, 1: 2, 2: 1, 3: 0, 4: 1, 5: 5, 6: 4, 7: 2, 8: 4, 9: 5, 10: 0, 11: 0, 12: 3
                }
                if expr_id in sound_files and sound_files[expr_id]:
                    Waveform.play_audio(sound_files[expr_id])
                if expr_id in led_col:
                    Serial.leds_color_r, Serial.leds_color_g, Serial.leds_color_b = led_col[expr_id]
                    Serial.leds_effect = led_eff[expr_id]
                    Serial.leds_on = 1
                print(f"Expression set to {expression} (ID: {expr_id}) (requested by {user_name})")
                send_telegram_log(f"😊 Expression changed to {expression.title()}", user_info)
        elif topic == 'dynamo/commands/face-expression-tracking-toggle':
            enabled = payload.get('enabled')
            if enabled is not None:
                MachineVision.expression_manual_mode = not enabled
                if enabled:
                    MachineVision.force_crossed_eye = False
                    Serial.leds_on = 0
                    Waveform.play_audio("sfx/settings_toggle.wav")
                else:
                    Serial.leds_on = 1
                print(f"Face expression tracking {'enabled' if enabled else 'disabled'} (requested by {user_name})")
                status = "enabled" if enabled else "disabled"
                send_telegram_log(f"😊 Face expression tracking {status}", user_info)
        elif topic == 'dynamo/commands/eye-tracking-toggle':
            enabled = payload.get('enabled')
            if enabled is not None:
                MachineVision.eye_tracking_mode = enabled
                if enabled:
                    MachineVision.force_crossed_eye = False
                    Serial.leds_on = 0
                else:
                    Serial.leds_on = 1
                Waveform.play_audio("sfx/settings_toggle.wav")
                print(f"Eye tracking {'enabled' if enabled else 'disabled'} (requested by {user_name})")
                status = "enabled" if enabled else "disabled"
                send_telegram_log(f"👁️ Eye tracking {status}", user_info)
        elif topic == 'dynamo/commands/eyebrows-toggle':
            enabled = payload.get('enabled')
            if enabled is not None:
                Serial.animatronics_on = 1 if enabled else 0
                Waveform.play_audio("sfx/settings_toggle.wav")
                print(f"Eyebrows {'enabled' if enabled else 'disabled'} (requested by {user_name})")
                status = "enabled" if enabled else "disabled"
                send_telegram_log(f"🤨 Eyebrows {status}", user_info)
        elif topic == 'dynamo/commands/shutdown':
            print(f"Shutdown requested by {user_name}")
            send_telegram_log(f"⚠️ System shutdown initiated", user_info)
            Waveform.play_audio("sfx/system_down.wav")
            Windows.shutdown()
        elif topic == 'dynamo/commands/reboot':
            print(f"Reboot requested by {user_name}")
            send_telegram_log(f"🔄 System reboot initiated", user_info)
            Waveform.play_audio("sfx/system_down.wav")
            Windows.restart()
        elif topic == 'dynamo/commands/kill-software':
            print(f"Software kill requested by {user_name}")
            send_telegram_log(f"💀 Software termination initiated", user_info)
            Windows.kill_process('Eye-Graphics.exe')
            Windows.kill_process('VoicemodDesktop.exe')
            os._exit(0)
        elif topic == 'dynamo/commands/set-sound-device':
            device_type = payload.get('deviceType')
            device_name = payload.get('deviceName')
            if device_type and device_name:
                try:
                    Windows.set_default_sound_device(device_name, device_type)
                    Waveform.play_audio("sfx/sounddevice_set.wav")
                    print(f"Sound device set: {device_type} -> {device_name} (requested by {user_name})")
                    device_icon = "🎤" if device_type == "input" else "🔊"
                    send_telegram_log(f"{device_icon} {device_type.title()} device set to {device_name}", user_info)
                except Exception as e:
                    print(f"Error setting sound device: {e} (requested by {user_name})")
                    send_telegram_log(f"❌ Error setting sound device", user_info)
    except Exception as e:
        print(f"Error processing MQTT message: {e}")
        traceback.print_exc()

def publish_voicemod_data():
    """Publish Voicemod data to MQTT"""
    try:
        if not mqtt_client or not mqtt_client.is_connected():
            print("MQTT client not connected, skipping Voicemod data publish")
            return
        while not len(Voicemod.sounds) and not len(Voicemod.voices):
            time.sleep(1)
        sound_effects = []
        for sound in Voicemod.sounds:
            sound_effects.append({'id': sound['id'], 'name': sound['name']})
        mqtt_client.publish('dynamo/data/sound_effects', json.dumps(sound_effects), retain=True)
        voice_effects = []
        for voice in Voicemod.voices:
            voice_effects.append({'id': voice['id'], 'name': voice['name'], 'type': 'modulation'})
        for voice in Voicemod.gibberish_voices:
            voice_effects.append({'id': voice['id'], 'name': voice['name'], 'type': 'gibberish'})
        mqtt_client.publish('dynamo/data/voice_effects', json.dumps(voice_effects), retain=True)
    except Exception as e:
        print(f"Error publishing Voicemod data: {e}")

def publish_device_data():
    """Publish device information to MQTT data topics"""
    try:
        Windows.refresh_sound_devices()
        sound_devices = []
        for device in Windows.input_audio_devices:
            sound_devices.append(f"INPUT: {device['Name']}")
        for device in Windows.output_audio_devices:
            sound_devices.append(f"OUTPUT: {device['Name']}")
        mqtt_client.publish('dynamo/data/sound_devices', json.dumps(sound_devices), retain=True)
        try:
            anydesk_id = os.popen('for /f "tokens=*" %A in (\'"C:\Program Files (x86)\AnyDesk\AnyDesk.exe" --get-id\') do @echo %A').read().strip()
            mqtt_client.publish('dynamo/data/anydesk_id', json.dumps({'id': anydesk_id}), retain=True)
        except:
            print("AnyDesk not found")
        print("Published device data to MQTT")
    except Exception as e:
        print(f"Error publishing device data: {e}")

def mqtt_heartbeat_worker():
    """Send periodic heartbeat to maintain MQTT connection health"""
    global last_mqtt_activity, mqtt_heartbeat_interval
    while True:
        try:
            time.sleep(mqtt_heartbeat_interval)
            if mqtt_client and mqtt_client.is_connected():
                heartbeat_data = { 'timestamp': time.time() }
                mqtt_client.publish('dynamo/heartbeat', json.dumps(heartbeat_data), qos=0)
                last_mqtt_activity = time.time()
            else:
                break
        except Exception as e:
            print(f"Error in MQTT heartbeat: {e}")
            break

def setup_mqtt():
    """Setup MQTT client and connection"""
    global mqtt_client
    try:
        if mqtt_client:
            try:
                mqtt_client.loop_stop()
                mqtt_client.disconnect()
            except:
                print("Failed to disconnect existing MQTT client")
        mqtt_client = mqtt.Client(userdata=None, protocol=mqtt.MQTTv5)
        mqtt_client.tls_set(tls_version=ssl.PROTOCOL_TLS_CLIENT)
        mqtt_client.username_pw_set(mqtt_username, mqtt_password)
        mqtt_client.reconnect_delay_set(min_delay=1, max_delay=1)
        mqtt_client.on_connect = on_mqtt_connect
        mqtt_client.on_disconnect = on_mqtt_disconnect
        mqtt_client.on_message = on_mqtt_message
        print(f"Connecting to MQTT broker at {mqtt_host}:{mqtt_port}")
        result = mqtt_client.connect(mqtt_host, mqtt_port, keepalive=mqtt_keepalive_interval, clean_start=mqtt.MQTT_CLEAN_START_FIRST_ONLY)
        if result == 0:
            mqtt_client.loop_start()
            return True
        else:
            print(f"MQTT connection failed with result code: {result}")
            return False
    except Exception as e:
        print(f"Failed to setup MQTT: {e}")
        return False

def TextToSpeech(text, user_name="Unknown"):
    """Non-blocking text to speech function for MQTT commands"""
    def tts_worker():
        try:
            Waveform.play_audio("sfx/assistant_ok.wav")
            print(f"Generating TTS for: {text} (requested by {user_name})")
            Waveform.TTS_generate(text)
            Waveform.TTS_play_async()
        except Exception as e:
            print(f"Error in TTS: {e}")
    tts_thread = threading.Thread(target=tts_worker, daemon=True)
    tts_thread.start()

def PlayAudioMessage(fursuitbot, chat_id, msg):
    fursuitbot.sendMessage(chat_id, '<i>>>Downloading sound...</i>', parse_mode='HTML')
    file_name = '{}.ogg'.format(msg['message_id'])
    if 'voice' in msg:
        fursuitbot.download_file(msg['voice']['file_id'], file_name)
    elif 'audio' in msg:
        fursuitbot.download_file(msg['audio']['file_id'], file_name)
    fursuitbot.sendMessage(chat_id, '<b>Done!</b>\n<i>>>Playing now</i>', parse_mode='HTML')
    Waveform.play_audio(file_name, delete=True)

def LogAIMessage(query, answer):
    """Log AI conversation messages to MQTT chat_logs topic"""
    try:
        if not mqtt_client or not mqtt_client.is_connected():
            return
        timestamp = datetime.now(timezone.utc).isoformat()
        if query:
            prompt_message = {"id": str(uuid.uuid4()), "content": query, "type": "prompt", "timestamp": timestamp}
            mqtt_client.publish('dynamo/data/chat_logs', json.dumps(prompt_message, ensure_ascii=False), retain=False)
        if answer:
            response_message = {"id": str(uuid.uuid4()), "content": answer, "type": "response", "timestamp": timestamp}
            mqtt_client.publish('dynamo/data/chat_logs', json.dumps(response_message, ensure_ascii=False), retain=False)
    except Exception as e:
        print(f"Error logging AI message: {e}")

def DiscardPreviousUpdates():
    if fursuitbot:
        updates = fursuitbot.getUpdates(timeout=-29)
        if updates:
            last_update_id = updates[-1]['update_id']
            fursuitbot.getUpdates(offset=last_update_id+1)

def thread_function(msg):
    try:
        content_type, chat_type, chat_id = telepot.glance(msg)
        print(content_type, chat_type, chat_id, msg['message_id'])
        if content_type == 'text':
            if msg['text'].startswith('/privacy'):
                with open('privacy.html', 'r') as file:
                    privacy_text = file.read()
                fursuitbot.sendMessage(chat_id, privacy_text, parse_mode='HTML')
            else:
                fursuitbot.sendMessage(chat_id, "Open the App to control the fursuit by going to this bot's description and clicking 'Open App'\nDon't know how to use me? Click on 'Tutorial' on the bottom left corner", reply_markup={'inline_keyboard':[
                    [{'text': 'Check out my Refsheet!', 'url': refsheetpath}], 
                    [{'text': 'Check out my Stickers!', 'url': stickerpack}],
                    [{'text': 'Send me a private message', 'url': mychatpath}]
                ]})
        elif content_type in ['voice', 'audio']:
            PlayAudioMessage(fursuitbot, chat_id, msg)
        else:
            fursuitbot.sendMessage(chat_id, 'I currently do not support this type of input  :(')
    except Exception as e:
        print(e)
        if 'ConnectionResetError' in traceback.format_exc():
            fursuitbot.sendMessage(chat_id, 'Connection Error, please try again')
        else:
            if fursuitbot:
                fursuitbot.sendMessage(fursuitbot_ownerID, traceback.format_exc())
                fursuitbot.sendMessage(fursuitbot_ownerID, str(msg))
                fursuitbot.sendMessage(chat_id, 'An error occurred, please try again')

def handle(msg):
    try:
        new_thread = threading.Thread(target=thread_function, args=(msg,))
        new_thread.start()
    except:
        if fursuitbot:
            fursuitbot.sendMessage(fursuitbot_ownerID, traceback.format_exc())

def StartTelegramBot():
    if not fursuitbot:
        return False
    while True:
        try:
            DiscardPreviousUpdates()
            MessageLoop(fursuitbot, {'chat': handle}).run_as_thread()
            print("Telegram bot online!")
            return True
        except Exception as e:
            print(e)
            print("Failed to start Telegram bot, retrying in 1 second...")
            time.sleep(1)

def StartBot():
    """Start the control bot with MQTT and handle reconnections"""
    print("Starting DYNAMO Control Bot...")
    mqtt_success = setup_mqtt()
    print("MQTT setup successful" if mqtt_success else "MQTT setup failed")
    if mqtt_success:
        connection_timeout = 10
        start_time = time.time()
        while not mqtt_client.is_connected() and (time.time() - start_time) < connection_timeout:
            time.sleep(0.1)
        print("MQTT is ready!" if mqtt_client.is_connected() else "MQTT connection timeout, but will keep trying in background")
    if fursuitbot:
        telegram_thread = threading.Thread(target=StartTelegramBot, daemon=True)
        telegram_thread.start()
    last_reconnect_attempt = 0
    base_reconnect_interval = 2
    max_reconnect_interval = 30
    reconnect_attempts = 0
    connection_stable_time = 0
    while True:
        time.sleep(1)
        current_time = time.time()
        if mqtt_client and mqtt_client.is_connected():
            if last_mqtt_activity > 0 and (current_time - last_mqtt_activity) > mqtt_health_check_interval: # Check for stale connection (no activity for too long)
                print(f"MQTT connection appears stale (no activity for {current_time - last_mqtt_activity:.1f}s) - forcing reconnection")
                try:
                    mqtt_client.loop_stop()
                    mqtt_client.disconnect()
                except:
                    pass
                connection_stable_time = 0
                continue
            if connection_stable_time == 0:
                connection_stable_time = current_time
            elif current_time - connection_stable_time > 30:
                if reconnect_attempts > 0:
                    print("MQTT connection stable - resetting reconnection counter")
                    reconnect_attempts = 0
                    connection_stable_time = current_time
            continue
        connection_stable_time = 0
        current_interval = min(base_reconnect_interval + (reconnect_attempts * 2), max_reconnect_interval)
        if (current_time - last_reconnect_attempt) < current_interval:
            continue 
        try:
            print(f"Attempting to reconnect to MQTT... (attempt {reconnect_attempts + 1}, next attempt in {current_interval}s if this fails)")
            if setup_mqtt():
                print("MQTT reconnected successfully")
                reconnect_attempts = 0
                connection_stable_time = current_time
                time.sleep(2) # Wait a bit for connection to stabilize
            else:
                print(f"MQTT reconnection failed")
                reconnect_attempts += 1
        except Exception as e:
            print(f"MQTT reconnection failed: {e}")
            reconnect_attempts += 1
        finally:
            last_reconnect_attempt = current_time

if __name__ == '__main__':
    StartBot()