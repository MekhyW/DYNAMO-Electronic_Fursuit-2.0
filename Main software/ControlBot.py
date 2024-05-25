import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton
import traceback
from contextlib import redirect_stdout
from io import StringIO
import subprocess, threading
import json, os, time
import Waveform
import MachineVision
import Windows
import Assistant
import Voicemod
import Serial

Token = json.load(open('credentials.json'))['fursuitbot_token']
ownerID = json.load(open('credentials.json'))['fursuitbot_ownerID']
fursuitbot = telepot.Bot(Token)

refsheetpath = 'https://i.postimg.cc/Y25LSW-z2/refsheet.png'
stickerpack = 'https://t.me/addstickers/MekhyW'
stickerexample = 'CAACAgEAAx0CcLzKZQACARtlFhtPqWsRwL8jMwTuhZELz6-jjAACxAMAAvBwgUWYjKWFS6B-MTAE'

main_menu_buttons = ['🎵 Media / Sound', '😁 Expression', '👀 Eye Tracking', '⚙️ Animatronic', '💡 LEDs', '🎙️ Voice', '🍪 Cookiebot (Assistant AI)', '🖼️ Refsheet / Sticker Pack', '🔒 Lock/Unlock Outsiders', '🔧 Debugging', '🛑 Shutdown']
main_menu_keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=button)] for button in main_menu_buttons], resize_keyboard=True)
inline_keyboard_mediasound = [[{'text': 'Play Music', 'callback_data': 'music'}, {'text': 'Play Sound Effect', 'callback_data': 'sfx'}], [{'text': '⏹️', 'callback_data': 'media stop'}, {'text': '⏸️', 'callback_data': 'media pause'}, {'text': '▶️', 'callback_data': 'media resume'}], [{'text': 'Volume', 'callback_data': 'volume'}], [{'text': 'Close Menu', 'callback_data': 'close'}]]
inline_keyboard_expression = [[{'text': 'Change Expression', 'callback_data': 'expression set'}], [{'text': 'Set to AUTOMATIC', 'callback_data': 'expression auto'}], [{'text': 'Silly Mode', 'callback_data': 'expression sillymode'}], [{'text': 'Close Menu', 'callback_data': 'close'}]]
inline_keyboard_eyetracking = [[{'text': 'ON', 'callback_data': 'eyetracking on'}, {'text': 'OFF', 'callback_data': 'eyetracking off'}], [{'text': 'Close Menu', 'callback_data': 'close'}]]
inline_keyboard_animatronic = [[{'text': 'ON', 'callback_data': 'animatronic on'}, {'text': 'OFF', 'callback_data': 'animatronic off'}], [{'text': 'Close Menu', 'callback_data': 'close'}]]
inline_keyboard_leds = [[{'text': 'ON', 'callback_data': 'leds on'}, {'text': 'OFF', 'callback_data': 'leds off'}], [{'text': 'Effect', 'callback_data': 'leds effect'}, {'text': 'Color', 'callback_data': 'leds color'}], [{'text': 'Brightness', 'callback_data': 'leds brightness'}], [{'text': 'Close Menu', 'callback_data': 'close'}]]
inline_keyboard_voice = [[{'text': 'Change Voice', 'callback_data': 'voice change'}], [{'text': 'Voice Changer ON', 'callback_data': 'voice changer on'}, {'text': 'Voice Changer OFF', 'callback_data': 'voice changer off'}], [{'text': '🔈', 'callback_data': 'voice hear on'}, {'text': '🔇', 'callback_data': 'voice hear off'}], [{'text': 'Background fx ON', 'callback_data': 'voice bg on'}, {'text': 'Background fx OFF', 'callback_data': 'voice bg off'}], [{'text': 'Close Menu', 'callback_data': 'close'}]]
inline_keyboard_cookiebot = [[{'text': 'Trigger Now', 'callback_data': 'assistant trigger'}], [{'text': 'Hotword Detection ON', 'callback_data': 'assistant hotword on'}, {'text': 'Hotword Detection OFF', 'callback_data': 'assistant hotword off'}], [{'text': 'Close Menu', 'callback_data': 'close'}]]
inline_keyboard_refsheet = [[{'text': 'Send Refsheet', 'callback_data': 'misc refsheet'}, {'text': 'Send Sticker Pack', 'callback_data': 'misc stickerpack'}], [{'text': 'Close Menu', 'callback_data': 'close'}]]
inline_keyboard_debugging = [[{'text': 'Resources', 'callback_data': 'debugging resources'}, {'text': 'Python Command', 'callback_data': 'debugging python'}, {'text': 'Shell Command', 'callback_data': 'debugging shell'}], [{'text': 'Close Menu', 'callback_data': 'close'}]]
inline_keyboard_shutdown = [[{'text': 'Shutdown', 'callback_data': 'shutdown turnoff'}, {'text': 'Reboot', 'callback_data': 'shutdown reboot'}, {'text': 'Kill Software', 'callback_data': 'shutdown kill'}], [{'text': 'Close Menu', 'callback_data': 'close'}]]

last_message_chat = {}
lock_outsider_commands = False

def PlayMusic(fursuitbot, chat_id, text):
    fursuitbot.sendMessage(chat_id, '>>>Downloading song with query "{}"...'.format(text))
    command = 'spotdl "{}" --format wav --preload --no-cache'.format(text)
    os.system(command)
    Waveform.stop_flag = True
    time.sleep(1)
    for file in os.listdir('.'):
        if file.endswith('.wav'):
            file_name = file
            break
    fursuitbot.sendMessage(chat_id, 'Done!\n>>>Playing now')
    Waveform.play_audio(file_name, delete=True)

def PlayAudioMessage(fursuitbot, chat_id, msg):
    fursuitbot.sendMessage(chat_id, '>>>Downloading sound...')
    file_name = '{}.ogg'.format(msg['message_id'])
    if 'voice' in msg:
        fursuitbot.download_file(msg['voice']['file_id'], file_name)
    elif 'audio' in msg:
        fursuitbot.download_file(msg['audio']['file_id'], file_name)
    fursuitbot.sendMessage(chat_id, 'Done!\n>>>Playing now')
    Waveform.play_audio(file_name, delete=True)

def ToggleOutsiderCommands(fursuitbot, chat_id):
    global lock_outsider_commands
    if int(chat_id) != int(ownerID):
        fursuitbot.sendMessage(chat_id, 'You are not the owner of this suit!')
        return
    lock_outsider_commands = not lock_outsider_commands
    if lock_outsider_commands:
        fursuitbot.sendMessage(chat_id, 'Outsider commands are now LOCKED')
    else:
        fursuitbot.sendMessage(chat_id, 'Outsider commands are now UNLOCKED')

def DiscardPreviousUpdates():
    updates = fursuitbot.getUpdates(timeout=-29)
    if updates:
        last_update_id = updates[-1]['update_id']
        fursuitbot.getUpdates(offset=last_update_id+1)

def ConfirmSuccess(from_id, msg, edit_text, query_id):
    fursuitbot.editMessageText((from_id, msg['message']['message_id']), edit_text)
    fursuitbot.answerCallbackQuery(query_id, text='Success!')
    if int(from_id) != int(ownerID):
        sender = fursuitbot.getChat(from_id)['first_name']
        fursuitbot.sendMessage(ownerID, f'{edit_text}\n(Command sent by {sender})')


def thread_function(msg):
    try:
        content_type, chat_type, chat_id = telepot.glance(msg)
        print(content_type, chat_type, chat_id, msg['message_id'])
        if lock_outsider_commands and int(chat_id) != int(ownerID):
            fursuitbot.sendMessage(chat_id, 'Outsider commands are currently LOCKED')
            return
        elif content_type == 'text':
            if chat_id in last_message_chat and 'data' in last_message_chat[chat_id] and last_message_chat[chat_id]['data'] in ['music', 'debugging python', 'debugging shell']:
                data = last_message_chat[chat_id]['data']
                last_message_chat[chat_id] = msg
                if msg['text'] == '/cancel':
                    fursuitbot.sendMessage(chat_id, 'Command was cancelled')
                elif data == 'music':
                    PlayMusic(fursuitbot, chat_id, msg['text'])
                elif data == 'debugging python':
                    output_buffer = StringIO()
                    with redirect_stdout(output_buffer):
                        try:
                            exec(msg['text'])
                            output = output_buffer.getvalue()
                            if output:
                                fursuitbot.sendMessage(chat_id, output)
                            else:
                                fursuitbot.sendMessage(chat_id, '(no output)')
                        except:
                            fursuitbot.sendMessage(chat_id, traceback.format_exc())
                elif data == 'debugging shell':
                    result = subprocess.run(msg['text'], shell=True, capture_output=True)
                    if result.stderr:
                        fursuitbot.sendMessage(chat_id, result.stderr.decode('utf-8', errors='ignore'))
                    elif result.stdout:
                        fursuitbot.sendMessage(chat_id, result.stdout.decode('utf-8', errors='ignore'))
                    else:
                        fursuitbot.sendMessage(chat_id, '(no output)')
            if msg['text'] not in main_menu_buttons:
                fursuitbot.sendMessage(chat_id, '>>>Awaiting -Command- or -Audio-', reply_markup=main_menu_keyboard)
            else:
                match msg['text']:
                    case '🎵 Media / Sound':
                        fursuitbot.sendMessage(chat_id, 'Media', reply_markup={'inline_keyboard': inline_keyboard_mediasound})
                    case '😁 Expression':
                        fursuitbot.sendMessage(chat_id, 'Expression', reply_markup={'inline_keyboard': inline_keyboard_expression})
                    case '👀 Eye Tracking':
                        fursuitbot.sendMessage(chat_id, 'Eye Tracking', reply_markup={'inline_keyboard': inline_keyboard_eyetracking})
                    case '⚙️ Animatronic':
                        fursuitbot.sendMessage(chat_id, 'Animatronic', reply_markup={'inline_keyboard': inline_keyboard_animatronic})
                    case '💡 LEDs':
                        fursuitbot.sendMessage(chat_id, 'LEDs', reply_markup={'inline_keyboard': inline_keyboard_leds})
                    case '🎙️ Voice':
                        fursuitbot.sendMessage(chat_id, 'Voice', reply_markup={'inline_keyboard': inline_keyboard_voice})
                    case '🍪 Cookiebot (Assistant AI)':
                        fursuitbot.sendMessage(chat_id, 'Cookiebot', reply_markup={'inline_keyboard': inline_keyboard_cookiebot})
                    case '🖼️ Refsheet / Sticker Pack':
                        fursuitbot.sendMessage(chat_id, 'Refsheet / Sticker Pack', reply_markup={'inline_keyboard': inline_keyboard_refsheet})
                    case '🔒 Lock/Unlock Outsiders':
                        ToggleOutsiderCommands(fursuitbot, chat_id)
                    case '🔧 Debugging':
                        fursuitbot.sendMessage(chat_id, 'Debugging', reply_markup={'inline_keyboard': inline_keyboard_debugging})
                    case '🛑 Shutdown':
                        fursuitbot.sendMessage(chat_id, 'Shutdown', reply_markup={'inline_keyboard': inline_keyboard_shutdown})
        elif content_type in ['voice', 'audio']:
            PlayAudioMessage(fursuitbot, chat_id, msg)
        else:
            fursuitbot.sendMessage(chat_id, 'I currently do not support this type of input  :(')
    except Exception as e:
        print(e)
        if 'ConnectionResetError' in traceback.format_exc():
            fursuitbot.sendMessage(chat_id, 'Connection Error, please try again')
        else:
            fursuitbot.sendMessage(ownerID, traceback.format_exc())
            fursuitbot.sendMessage(ownerID, str(msg))
            fursuitbot.sendMessage(chat_id, 'An error occurred, please try again')
    finally:
        last_message_chat[chat_id] = msg


def thread_function_query(msg):
    try:
        query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
        print('Callback Query:', query_id, from_id, query_data)
        if lock_outsider_commands and int(from_id) != int(ownerID):
            fursuitbot.answerCallbackQuery(query_id, text='Outsider commands are currently LOCKED')
            return
        match query_data.split()[0]:
            case 'close':
                fursuitbot.deleteMessage((from_id, msg['message']['message_id']))
            case 'music':
                fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Type the song name or YouTube link you want me to play!\nOr use /cancel to cancel the command.')
                fursuitbot.answerCallbackQuery(query_id, text='Enter name or link')
            case 'sfx':
                fursuitbot.deleteMessage((from_id, msg['message']['message_id']))
                with open('resources/soundtutorial.mp4', 'rb') as video:
                    fursuitbot.sendVideo(from_id, video, caption='You can forward me an audio or use an inline bot to search one!\n\nEXAMPLE:\n"@myinstantsbot {SOUND NAME}"')
                fursuitbot.answerCallbackQuery(query_id, text='Search SFX')
            case 'media':
                match ' '.join(query_data.split()[1:]):
                    case 'stop':
                        Waveform.stop_flag = True
                        ConfirmSuccess(from_id, msg, 'Media Stopped', query_id)
                    case 'pause':
                        Waveform.is_paused = True
                        ConfirmSuccess(from_id, msg, 'Media Paused', query_id)
                    case 'resume':
                        Waveform.is_paused = False
                        ConfirmSuccess(from_id, msg, 'Media Resumed', query_id)
            case 'volume':
                if len(query_data.split()) == 1:
                    fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Set Volume', reply_markup={'inline_keyboard': 
                        [[{'text': '⬅️ Go back', 'callback_data': 'volume goback'}], 
                            [{'text': '0%', 'callback_data': 'volume 0'}], 
                            [{'text': '25%', 'callback_data': 'volume 25'}], 
                            [{'text': '50%', 'callback_data': 'volume 50'}], 
                            [{'text': '75%', 'callback_data': 'volume 75'}], 
                            [{'text': '100%', 'callback_data': 'volume 100'}]]})
                elif query_data.split()[1] == 'goback':
                    fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Media', reply_markup={'inline_keyboard': inline_keyboard_mediasound})
                else:
                    Windows.set_system_volume(int(query_data.split()[1]) / 100)
                    ConfirmSuccess(from_id, msg, 'Volume set to {}%'.format(query_data.split()[1]), query_id)
            case 'expression':
                match query_data.split()[1]:
                    case 'set':
                        if len(query_data.split()) == 2:
                            fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Set Expression', reply_markup={'inline_keyboard': 
                                [[{'text': '⬅️ Go back', 'callback_data': 'expression set goback'}], 
                                 [{'text': '🙂  Neutral  🙂', 'callback_data': 'expression set 3'}], 
                                 [{'text': '🤩   Happy   🤩', 'callback_data': 'expression set 2'}], 
                                 [{'text': '😢    Sad    😢', 'callback_data': 'expression set 4'}], 
                                 [{'text': '😡   Angry   😡', 'callback_data': 'expression set 0'}], 
                                 [{'text': '😱 Surprised 😱', 'callback_data': 'expression set 5'}],
                                 [{'text': '😒 Disgusted 😒', 'callback_data': 'expression set 1'}],
                                 [{'text': '😏Mischievous😏', 'callback_data': 'expression set 12'}],
                                 [{'text': '😵‍💫  Hypnotic 😵‍💫', 'callback_data': 'expression set 6'}],
                                 [{'text': '❤️   Heart   ❤️', 'callback_data': 'expression set 7'}],
                                 [{'text': '🌈  Rainbow  🌈', 'callback_data': 'expression set 8'}],
                                 [{'text': '😈 Nightmare 😈', 'callback_data': 'expression set 9'}],
                                 [{'text': '⚙️ Gear eyes ⚙️', 'callback_data': 'expression set 10'}],
                                 [{'text': '💀   SANS    💀', 'callback_data': 'expression set 11'}]
                                ]})
                        elif query_data.split()[2] == 'goback':
                            fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Expression', reply_markup={'inline_keyboard': inline_keyboard_expression})
                        else:
                            MachineVision.expression_manual_mode = True
                            MachineVision.expression_manual_id = int(query_data.split()[2])
                            if MachineVision.expression_manual_id == 6:
                                Serial.leds_effect = next(i for i, effect in enumerate(Serial.leds_effects_options) if 'rainbow' in effect)
                            ConfirmSuccess(from_id, msg, 'Expression set to ID {}'.format(MachineVision.expression_manual_id), query_id)
                    case 'auto':
                        MachineVision.expression_manual_mode = False
                        ConfirmSuccess(from_id, msg, 'Expression set to AUTOMATIC', query_id)
                    case 'sillymode':
                        if len(query_data.split()) == 2:
                            fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Silly Mode', reply_markup={'inline_keyboard': 
                                [[{'text': '⬅️ Go back', 'callback_data': 'expression sillymode goback'}], 
                                 [{'text': 'ON', 'callback_data': 'expression sillymode on'}], 
                                 [{'text': 'OFF', 'callback_data': 'expression sillymode off'}]]})
                        elif query_data.split()[2] == 'goback':
                            fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Expression', reply_markup={'inline_keyboard': inline_keyboard_expression})
                        elif query_data.split()[2] == 'on':
                            MachineVision.eye_sily_mode = True
                            ConfirmSuccess(from_id, msg, 'Silly Mode set to ON', query_id)
                        elif query_data.split()[2] == 'off':
                            MachineVision.eye_sily_mode = False
                            ConfirmSuccess(from_id, msg, 'Silly Mode set to OFF', query_id)
            case 'eyetracking':
                match ' '.join(query_data.split()[1:]):
                    case 'on':
                        MachineVision.eye_tracking_mode = True
                        ConfirmSuccess(from_id, msg, 'Eye Tracking set to ON', query_id)
                    case 'off':
                        MachineVision.eye_tracking_mode = False
                        ConfirmSuccess(from_id, msg, 'Eye Tracking set to OFF', query_id)
            case 'animatronic':
                match ' '.join(query_data.split()[1:]):
                    case 'on':
                        Serial.animatronics_on = 1
                        ConfirmSuccess(from_id, msg, 'Animatronic set to ON', query_id)
                    case 'off':
                        Serial.animatronics_on = 0
                        ConfirmSuccess(from_id, msg, 'Animatronic set to OFF', query_id)
            case 'leds':
                match query_data.split()[1]:
                    case 'effect':
                        if len(query_data.split()) == 2:
                            options = []
                            for effect_id in range(len(Serial.leds_effects_options)):
                                options.append([{'text': Serial.leds_effects_options[effect_id].capitalize(), 'callback_data': 'leds effect {}'.format(effect_id)}])
                            fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Set Effect', reply_markup={'inline_keyboard':
                                [[{'text': '⬅️ Go back', 'callback_data': 'leds effect goback'}]] + options})
                        elif query_data.split()[2] == 'goback':
                            fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'LEDs', reply_markup={'inline_keyboard': inline_keyboard_leds})
                        else:
                            Serial.leds_on = 1
                            Serial.leds_effect = int(query_data.split()[2])
                            ConfirmSuccess(from_id, msg, 'LEDs Effect set to {}'.format(Serial.leds_effects_options[Serial.leds_effect].capitalize()), query_id)
                    case 'color':
                        if len(query_data.split()) == 2:
                            options = []
                            for color_id in range(len(Serial.leds_color_options)):
                                options.append([{'text': Serial.leds_color_options[color_id].capitalize(), 'callback_data': 'leds color {}'.format(color_id)}])
                            fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Set Color', reply_markup={'inline_keyboard':
                                [[{'text': '⬅️ Go back', 'callback_data': 'leds color goback'}]] + options})
                        elif query_data.split()[2] == 'goback':
                            fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'LEDs', reply_markup={'inline_keyboard': inline_keyboard_leds})
                        else:
                            Serial.leds_on = 1
                            Serial.leds_color = int(query_data.split()[2])
                            ConfirmSuccess(from_id, msg, 'LEDs Color set to {}'.format(Serial.leds_color_options[Serial.leds_color].capitalize()), query_id)
                    case 'brightness':
                        if len(query_data.split()) == 2:
                            fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Set Brightness', reply_markup={'inline_keyboard':
                                [[{'text': '⬅️ Go back', 'callback_data': 'leds brightness goback'}],
                                 [{'text': 'Weak', 'callback_data': f'leds brightness {int(Serial.leds_brightness_default/2)}'}],
                                 [{'text': 'Medium (default)', 'callback_data': f'leds brightness {int(Serial.leds_brightness_default)}'}],
                                 [{'text': 'Strong', 'callback_data': f'leds brightness {int(Serial.leds_brightness_default*2)}'}]]})
                        elif query_data.split()[2] == 'goback':
                            fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'LEDs', reply_markup={'inline_keyboard': inline_keyboard_leds})
                        else:
                            Serial.leds_on = 1
                            Serial.leds_brightness = int(query_data.split()[2])
                            ConfirmSuccess(from_id, msg, 'LEDs Brightness set to {}'.format(Serial.leds_brightness), query_id)
                    case 'on':
                        Serial.leds_on = 1
                        ConfirmSuccess(from_id, msg, 'LEDs set to ON', query_id)
                    case 'off':
                        Serial.leds_on = 0
                        ConfirmSuccess(from_id, msg, 'LEDs set to OFF', query_id)
            case 'voice':
                match query_data.split()[1]:
                    case 'change':
                        if len(query_data.split()) == 2:
                            voice_keyboard = [[{'text': '⬅️ Go back', 'callback_data': 'voice change goback'}], 
                                              [{'text': 'Gibberish Voices ➡️', 'callback_data': 'voice change gibberish'}]]
                            for voice in Voicemod.voices:
                                voice_keyboard.append([{'text': voice['name'], 'callback_data': 'voice change load {}'.format(voice['id'])}])
                            fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Voice Keyboard', reply_markup={'inline_keyboard': voice_keyboard})
                        elif query_data.split()[2] == 'load':
                            Waveform.stop_gibberish_flag = True
                            Voicemod.voice_id = query_data.split()[3]
                            Voicemod.load_voice_flag = True
                            ConfirmSuccess(from_id, msg, 'Voice loaded ID {}'.format(Voicemod.voice_id), query_id)
                        elif query_data.split()[2] == 'goback':
                            fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Voice', reply_markup={'inline_keyboard': inline_keyboard_voice})
                        elif query_data.split()[2] == 'gibberish':
                            voice_keyboard = [[{'text': '⬅️ Go back', 'callback_data': 'voice change'}]]
                            for voice in Voicemod.gibberish_voices:
                                voice_keyboard.append([{'text': voice['name'], 'callback_data': 'voice change load {}'.format(voice['id'])}])
                            fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Gibberish Voice Keyboard', reply_markup={'inline_keyboard': voice_keyboard})
                    case 'changer':
                        Waveform.stop_gibberish_flag = True
                        Voicemod.desired_status = query_data.split()[2] == 'on'
                        Voicemod.toggle_voice_changer_flag = True
                        ConfirmSuccess(from_id, msg, 'Voice Changer Toggled', query_id)
                    case 'hear':
                        Waveform.stop_gibberish_flag = True
                        Voicemod.desired_status = query_data.split()[2] == 'on'
                        Voicemod.toggle_hear_my_voice_flag = True
                        ConfirmSuccess(from_id, msg, 'Hear My Voice Toggled', query_id)
                    case 'bg':
                        Waveform.stop_gibberish_flag = True
                        Voicemod.desired_status = query_data.split()[2] == 'on'
                        Voicemod.toggle_background_flag = True
                        ConfirmSuccess(from_id, msg, 'Background FX Toggled', query_id)
            case 'assistant':
                match ' '.join(query_data.split()[1:]):
                    case 'trigger':
                        Assistant.trigger()
                        ConfirmSuccess(from_id, msg, 'Triggered!', query_id)
                    case 'hotword on':
                        Assistant.hotword_detection_enabled = True
                        ConfirmSuccess(from_id, msg, 'Hotword Detection set to ON\n\nNOTE: If the voice changer is ON, hotword detection may not work depending on the effect.', query_id)
                    case 'hotword off':
                        Assistant.hotword_detection_enabled = False
                        ConfirmSuccess(from_id, msg, 'Hotword Detection set to OFF', query_id)
            case 'misc':
                match ' '.join(query_data.split()[1:]):
                    case 'refsheet':
                        fursuitbot.deleteMessage((from_id, msg['message']['message_id']))
                        fursuitbot.sendChatAction(from_id, 'upload_photo')
                        while True:
                            try:
                                fursuitbot.sendPhoto(from_id, refsheetpath, caption='Here is my reference sheet!\n\nMekhy is a raccoon-wolf engineer who creates robots and performs experiments. He is very evil and unreliable/unpredictable (cartoon villain vibe *twirls mustache*), but despite this he manages to be very cute/charismatic and "soften" around friends and people he trusts! ;3')
                                break
                            except ConnectionResetError:
                                pass
                    case 'stickerpack':
                        fursuitbot.deleteMessage((from_id, msg['message']['message_id']))
                        fursuitbot.sendSticker(from_id, stickerexample)
                        fursuitbot.sendMessage(from_id, 'Add the sticker pack to your Telegram here: {}'.format(stickerpack))
            case 'debugging':
                if int(from_id) == int(ownerID):
                    match ' '.join(query_data.split()[1:]):
                        case 'resources':
                            cpu_info = Windows.get_cpu_info()
                            memory_info = Windows.get_memory_info()
                            disk_info = Windows.get_disk_info()
                            system_volume = Windows.get_system_volume()
                            fursuitbot.editMessageText((from_id, msg['message']['message_id']), 
                                f'CPU \n Physical cores: {cpu_info["physical_cores"]}\nTotal cores: {cpu_info["total_cores"]}\nMax frequency: {cpu_info["max_frequency"]}\nMin frequency: {cpu_info["min_frequency"]}\nCurrent frequency: {cpu_info["current_frequency"]}\nUsage: {cpu_info["usage"]}%\n\nRAM \n Total: {memory_info["total"]}\nAvailable: {memory_info["available"]}\nUsed: {memory_info["used"]}\nUsage: {memory_info["percent"]}%\n\nDisk \n Total: {disk_info["total"]}\nUsed: {disk_info["used"]}\nFree: {disk_info["free"]}\nUsage: {disk_info["percent"]}%\n\nVolume\nLevel: {100*system_volume}%')                  
                        case 'python':
                            fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Type the Python command you want me to execute\nOr use /cancel to cancel the command.')
                            fursuitbot.answerCallbackQuery(query_id, text='Enter Python command')
                        case 'shell':
                            fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Type the Shell command you want me to execute\nOr use /cancel to cancel the command.')
                            fursuitbot.answerCallbackQuery(query_id, text='Enter Shell command')
                else:
                    fursuitbot.answerCallbackQuery(query_id, text='FORBIDDEN')
            case 'shutdown':
                if int(from_id) == int(ownerID):
                    fursuitbot.deleteMessage((from_id, msg['message']['message_id']))
                    match ' '.join(query_data.split()[1:]):
                        case 'turnoff':
                            fursuitbot.sendMessage(from_id, 'Shutting down...')
                            Windows.shutdown()
                        case 'reboot':
                            fursuitbot.sendMessage(from_id, 'Rebooting...')
                            Windows.restart()
                        case 'kill':
                            fursuitbot.sendMessage(from_id, 'Killing software...')
                            Windows.kill_process('Unity.exe')
                            Windows.kill_process('VoicemodDesktop.exe') 
                            os._exit(0)
                else:
                    fursuitbot.answerCallbackQuery(query_id, text='FORBIDDEN')
    except Exception as e:
        print(e)
        if 'ConnectionResetError' in traceback.format_exc():
            fursuitbot.answerCallbackQuery(query_id, text='CONNECTION ERROR')
        else:
            fursuitbot.sendMessage(ownerID, traceback.format_exc())
            fursuitbot.sendMessage(ownerID, str(msg))
            fursuitbot.answerCallbackQuery(query_id, text='ERROR')
    finally:
        last_message_chat[from_id] = msg


def handle(msg):
    try:
        new_thread = threading.Thread(target=thread_function, args=(msg,))
        new_thread.start()
    except:
        fursuitbot.sendMessage(ownerID, traceback.format_exc())


def handle_query(msg):
    try:
        new_thread = threading.Thread(target=thread_function_query, args=(msg,))
        new_thread.start()
    except:
        fursuitbot.sendMessage(ownerID, traceback.format_exc())


def StartBot():
    global bot_online
    while True:
        try:
            DiscardPreviousUpdates()
            MessageLoop(fursuitbot, {'chat': handle, 'callback_query': handle_query}).run_as_thread()
            fursuitbot.sendMessage(ownerID, '>>> READY! <<<')
            print("Control bot online!")
            return True
        except Exception as e:
            print(e)
            print("Failed to start Control bot, retrying in 1 second...")
            time.sleep(1)
    

if __name__ == '__main__':
    StartBot()
    while True:
        pass