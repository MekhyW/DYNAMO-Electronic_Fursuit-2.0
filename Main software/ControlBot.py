import Waveform
import MachineVision
import Windows
import Assistant
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton
import traceback
from contextlib import redirect_stdout
from io import StringIO
import subprocess
import threading
import json
import os
import time

Token = json.load(open('credentials.json'))['fursuitbot_token']
ownerID = json.load(open('credentials.json'))['fursuitbot_ownerID']
fursuitbot = telepot.Bot(Token)

refsheet = open('resources/refsheet.png', 'rb')
stickerpack = 'https://t.me/addstickers/MekhyW'
stickerexample = 'CAACAgEAAx0CcLzKZQACARtlFhtPqWsRwL8jMwTuhZELz6-jjAACxAMAAvBwgUWYjKWFS6B-MTAE'

main_menu_buttons = ['🎵 Media / Sound', '😁 Expression', '👀 Eye Tracking', '⚙️ Animatronic', '💡 LEDs', '🎙️ Voice', '🍪 Cookiebot (Assistant AI)', '🖼️ Refsheet / Sticker Pack', '🔒 Lock/Unlock Outsiders', '🔧 Debugging', '🛑 Shutdown']
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
lock_outsider_commands = False

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
    updates = fursuitbot.getUpdates()
    if updates:
        last_update_id = updates[-1]['update_id']
        fursuitbot.getUpdates(offset=last_update_id+1)


def thread_function(msg):
    try:
        content_type, chat_type, chat_id = telepot.glance(msg)
        print(content_type, chat_type, chat_id, msg['message_id'])
        if lock_outsider_commands and int(chat_id) != int(ownerID):
            fursuitbot.sendMessage(chat_id, 'Outsider commands are currently LOCKED')
            return
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
                case '🔒 Lock/Unlock Outsiders':
                    ToggleOutsiderCommands(fursuitbot, chat_id)
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
    global expression_manual_mode, expression_manual_id
    try:
        query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
        print('Callback Query:', query_id, from_id, query_data)
        if lock_outsider_commands and int(from_id) != int(ownerID):
            fursuitbot.answerCallbackQuery(query_id, text='Outsider commands are currently LOCKED')
            return
        match query_data.split()[0]:
            case 'music':
                fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Type the song name or YouTube link you want me to play!\nOr use /cancel to cancel the command.')
                fursuitbot.answerCallbackQuery(query_id, text='Enter name or link')
            case 'sfx':
                pass
            case 'media':
                match ' '.join(query_data.split()[1:]):
                    case 'stop':
                        Waveform.stop_flag = True
                        fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Media Stopped')
                    case 'pause':
                        Waveform.is_paused = True
                        fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Media Paused')
                    case 'resume':
                        Waveform.is_paused = False
                        fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Media Resumed')
                fursuitbot.answerCallbackQuery(query_id, text='Success!')
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
                    fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Volume set to {}%'.format(query_data.split()[1]))
                    fursuitbot.answerCallbackQuery(query_id, text='Success!')
            case 'expression':
                match query_data.split()[1]:
                    case 'set':
                        if len(query_data.split()) == 2:
                            fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Set Expression', reply_markup={'inline_keyboard': 
                                [[{'text': '⬅️ Go back', 'callback_data': 'expression set goback'}], 
                                 [{'text': 'Neutral', 'callback_data': 'expression set 3'}], 
                                 [{'text': 'Happy', 'callback_data': 'expression set 2'}], 
                                 [{'text': 'Sad', 'callback_data': 'expression set 4'}], 
                                 [{'text': 'Angry', 'callback_data': 'expression set 0'}], 
                                 [{'text': 'Surprised', 'callback_data': 'expression set 5'}],
                                 [{'text': 'Disgusted', 'callback_data': 'expression set 1'}],
                                 [{'text': 'Hypno', 'callback_data': 'expression set 6'}]]})
                        elif query_data.split()[2] == 'goback':
                            fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Expression', reply_markup={'inline_keyboard': inline_keyboard_expression})
                        else:
                            MachineVision.expression_manual_mode = True
                            MachineVision.expression_manual_id = int(query_data.split()[2])
                            fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Expression set to ID {}'.format(MachineVision.expression_manual_id))
                            fursuitbot.answerCallbackQuery(query_id, text='Success!')
                    case 'auto':
                        MachineVision.expression_manual_mode = False
                        fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Expression set to AUTOMATIC')
                        fursuitbot.answerCallbackQuery(query_id, text='Success!')
                    case 'manual':
                        MachineVision.expression_manual_mode = True
                        fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Expression set to MANUAL')
                        fursuitbot.answerCallbackQuery(query_id, text='Success!')
            case 'eyetracking':
                match ' '.join(query_data.split()[1:]):
                    case 'on':
                        MachineVision.eye_tracking_mode = True
                        fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Eye Tracking set to ON')
                        fursuitbot.answerCallbackQuery(query_id, text='Success!')
                    case 'off':
                        MachineVision.eye_tracking_mode = False
                        fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Eye Tracking set to OFF')
                        fursuitbot.answerCallbackQuery(query_id, text='Success!')
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
                        Assistant.trigger()
                        fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Triggered!')
                        fursuitbot.answerCallbackQuery(query_id, text='Success!')
                    case 'hotword on':
                        Assistant.hotword_detection_enabled = True
                        fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Hotword Detection set to ON\n\nNOTE: If the voice changer is ON, hotword detection may not work depending on the effect.')
                        fursuitbot.answerCallbackQuery(query_id, text='Success!')
                    case 'hotword off':
                        Assistant.hotword_detection_enabled = False
                        fursuitbot.editMessageText((from_id, msg['message']['message_id']), 'Hotword Detection set to OFF')
                        fursuitbot.answerCallbackQuery(query_id, text='Success!')
            case 'misc':
                match ' '.join(query_data.split()[1:]):
                    case 'refsheet':
                        while True:
                            try:
                                fursuitbot.sendPhoto(from_id, refsheet, caption='Refsheet')
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
        if 'ConnectionResetError' not in traceback.format_exc():
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
            time.sleep(1)
    

if __name__ == '__main__':
    StartBot()
    while True:
        pass