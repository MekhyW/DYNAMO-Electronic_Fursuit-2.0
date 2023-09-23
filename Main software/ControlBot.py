import Waveform
import Windows
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton
import traceback
import threading
import json
import os
import time

Token = json.load(open('credentials.json'))['fursuitbot_token']
ownerID = json.load(open('credentials.json'))['fursuitbot_ownerID']
fursuitbot = telepot.Bot(Token)

main_menu_buttons = ['🎵 Media / Sound', '😁 Expression', '👀 Eye Tracking', '⚙️ Animatronic', '💡 LEDs', '🎙️ Voice', '🍪 Cookiebot (Assistant AI)', '🖼️ Refsheet / Sticker Pack', '🔧 Debugging', '🛑 Shutdown']
main_menu_keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=button)] for button in main_menu_buttons], resize_keyboard=True)
inline_keyboard_mediasound = [[{'text': 'Play Music', 'callback_data': 'music'}, {'text': 'Play Sound Effect', 'callback_data': 'sfx'}], [{'text': 'Stop Media', 'callback_data': 'media stop'}, {'text': 'Pause Media', 'callback_data': 'media pause'}, {'text': 'Resume Media', 'callback_data': 'media resume'}], [{'text': 'Set Volume', 'callback_data': 'volume'}]]
inline_keyboard_expression = [[{'text': 'Change Expression', 'callback_data': 'expression set'}, {'text': 'Set to AUTOMATIC', 'callback_data': 'expression auto'}, {'text': 'Set to MANUAL', 'callback_data': 'expression manual'}]]
inline_keyboard_eyetracking = [[{'text': 'Set to ON', 'callback_data': 'eyetracking on'}, {'text': 'Set to OFF', 'callback_data': 'eyetracking off'}]]
inline_keyboard_animatronic = [[{'text': 'Set to ON', 'callback_data': 'animatronic on'}, {'text': 'Set to OFF', 'callback_data': 'animatronic off'}]]
inline_keyboard_leds = [[{'text': 'Set Effect', 'callback_data': 'leds effect'}, {'text': 'Set Brightness', 'callback_data': 'leds brightness'}], [{'text': 'Turn ON', 'callback_data': 'leds on'}, {'text': 'Turn OFF', 'callback_data': 'leds off'}]]
inline_keyboard_voice = [[{'text': 'Change Voice', 'callback_data': 'voice change'}, {'text': 'Voice Changer ON/OFF', 'callback_data': 'voice changer toggle'}], [{'text': 'Mute / Unmute', 'callback_data': 'voice hear toggle'}], [{'text': 'Background ON/OFF', 'callback_data': 'voice bg toggle'}]]
inline_keyboard_cookiebot = [[{'text': 'Trigger Now', 'callback_data': 'assistant trigger'}], [{'text': 'Hotword Detection ON', 'callback_data': 'assistant hotword on'}, {'text': 'Hotword Detection OFF', 'callback_data': 'assistant hotword off'}]]
inline_keyboard_refsheet = [[{'text': 'Send Refsheet', 'callback_data': 'misc refsheet'}, {'text': 'Send Sticker Pack', 'callback_data': 'misc stickerpack'}]]
inline_keyboard_debugging = [[{'text': 'Resources', 'callback_data': 'debugging resources'}, {'text': 'Python Command', 'callback_data': 'debugging python'}, {'text': 'Shell Command', 'callback_data': 'debugging shell'}]]
inline_keyboard_shutdown = [[{'text': 'Shutdown', 'callback_data': 'shutdown turnoff'}, {'text': 'Reboot', 'callback_data': 'shutdown reboot'}, {'text': 'Kill Software', 'callback_data': 'shutdown kill'}]]

last_message_chat = {}

def PlayMusic(fursuitbot, chat_id, text):
    Waveform.stop_flag = True
    time.sleep(1)
    for file in os.listdir('.'):
        if file.endswith('.wav'):
            os.remove(file)
    fursuitbot.sendMessage(chat_id, '>>>Downloading song with query "{}"...'.format(text))
    command = 'spotdl "{}" --format wav --preload --no-cache'.format(text)
    os.system(command)
    for file in os.listdir('.'):
        if file.endswith('.wav'):
            file_name = file
            break
    fursuitbot.sendMessage(chat_id, 'Done!\n>>>Playing now')
    Waveform.play_audio(file_name)
    os.remove(file_name)

def DiscardPreviousUpdates():
    updates = fursuitbot.getUpdates()
    if updates:
        last_update_id = updates[-1]['update_id']
        fursuitbot.getUpdates(offset=last_update_id+1)


def thread_function(msg):
    try:
        content_type, chat_type, chat_id = telepot.glance(msg)
        print(content_type, chat_type, chat_id, msg['message_id'])
        if chat_id in last_message_chat and 'data' in last_message_chat[chat_id] and last_message_chat[chat_id]['data'] == 'music':
            last_message_chat[chat_id] = msg
            if msg['text'] == '/cancel':
                fursuitbot.sendMessage(chat_id, 'Command was cancelled')
            else:
                PlayMusic(fursuitbot, chat_id, msg['text'])
        if msg['text'] not in main_menu_buttons:
            fursuitbot.sendChatAction(chat_id, 'typing')
            fursuitbot.sendMessage(chat_id, '>>>Awaiting -Command- or -Audio-', reply_markup=main_menu_keyboard)
        else:
            fursuitbot.sendChatAction(chat_id, 'typing')
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
                case '🔧 Debugging':
                    fursuitbot.sendMessage(chat_id, 'Debugging', reply_markup={'inline_keyboard': inline_keyboard_debugging})
                case '🛑 Shutdown':
                    fursuitbot.sendMessage(chat_id, 'Shutdown', reply_markup={'inline_keyboard': inline_keyboard_shutdown})
    except Exception as e:
        print(e)
        if 'ConnectionResetError' not in traceback.format_exc():
            fursuitbot.sendMessage(ownerID, traceback.format_exc())
            fursuitbot.sendMessage(ownerID, str(msg))
    finally:
        last_message_chat[chat_id] = msg


def thread_function_query(msg):
    try:
        query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
        print('Callback Query:', query_id, from_id, query_data)
        persist_msg = False
        match query_data.split()[0]:
            case 'music':
                fursuitbot.sendMessage(from_id, 'Type the song name or YouTube link you want me to play!\nOr use /cancel to cancel the command.')
                fursuitbot.answerCallbackQuery(query_id, text='Input name or link to song')
            case 'sfx':
                pass
            case 'media':
                match ' '.join(query_data.split()[1:]):
                    case 'stop':
                        Waveform.stop_flag = True
                    case 'pause':
                        Waveform.is_paused = True
                    case 'resume':
                        Waveform.is_paused = False
                fursuitbot.answerCallbackQuery(query_id, text='Done!')
            case 'volume':
                persist_msg = True
                if len(query_data.split()) == 1:
                    fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Set Volume', reply_markup={'inline_keyboard': [[{'text': '⬅️ Go back', 'callback_data': 'volume goback'}], [{'text': '0%', 'callback_data': 'volume 0'}], [{'text': '25%', 'callback_data': 'volume 25'}], [{'text': '50%', 'callback_data': 'volume 50'}], [{'text': '75%', 'callback_data': 'volume 75'}], [{'text': '100%', 'callback_data': 'volume 100'}]]})
                elif query_data.split()[1] == 'goback':
                    fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Media', reply_markup={'inline_keyboard': inline_keyboard_mediasound})
                else:
                    Windows.set_system_volume(int(query_data.split()[1]) / 100)
                    fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Volume set to {}%'.format(query_data.split()[1]))
                    fursuitbot.answerCallbackQuery(query_id, text='Done!')
            case 'expression':
                match ' '.join(query_data.split()[1:]):
                    case 'set':
                        pass
                    case 'auto':
                        pass
                    case 'manual':
                        pass
            case 'eyetracking':
                match ' '.join(query_data.split()[1:]):
                    case 'on':
                        pass
                    case 'off':
                        pass
            case 'animatronic':
                match ' '.join(query_data.split()[1:]):
                    case 'on':
                        pass
                    case 'off':
                        pass
            case 'leds':
                match ' '.join(query_data.split()[1:]):
                    case 'effect':
                        pass
                    case 'brightness':
                        pass
                    case 'on':
                        pass
                    case 'off':
                        pass
            case 'voice':
                match ' '.join(query_data.split()[1:]):
                    case 'change':
                        pass
                    case 'changer toggle':
                        pass
                    case 'hear toggle':
                        pass
                    case 'bg toggle':
                        pass
            case 'assistant':
                match ' '.join(query_data.split()[1:]):
                    case 'trigger':
                        pass
                    case 'hotword on':
                        pass
                    case 'hotword off':
                        pass
            case 'misc':
                match ' '.join(query_data.split()[1:]):
                    case 'refsheet':
                        pass
                    case 'stickerpack':
                        pass
            case 'debugging':
                if int(from_id) == int(ownerID):
                    match ' '.join(query_data.split()[1:]):
                        case 'resources':
                            pass
                        case 'python':
                            pass
                        case 'shell':
                            pass
                else:
                    fursuitbot.answerCallbackQuery(query_id, text='This is only available to the user of this fursuit!')
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
                    fursuitbot.answerCallbackQuery(query_id, text='This is only available to the user of this fursuit!')
        if not persist_msg:
            fursuitbot.deleteMessage((from_id, msg['message']['message_id']))
    except Exception as e:
        print(e)
        if 'ConnectionResetError' not in traceback.format_exc():
            fursuitbot.sendMessage(ownerID, traceback.format_exc())
            fursuitbot.sendMessage(ownerID, str(msg))
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
    try:
        DiscardPreviousUpdates()
        MessageLoop(fursuitbot, {'chat': handle, 'callback_query': handle_query}).run_as_thread()
        fursuitbot.sendMessage(ownerID, '>>> READY! <<<')
        print("Control bot online!")
        return True
    except Exception as e:
        print(e)
        return False
    

if __name__ == '__main__':
    StartBot()
    while True:
        pass