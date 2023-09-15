import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton
import traceback
import threading
import json

Token = json.load(open('credentials.json'))['fursuitbot_token']
ownerID = json.load(open('credentials.json'))['fursuitbot_ownerID']
fursuitbot = telepot.Bot(Token)

def DiscardPreviousUpdates():
    updates = fursuitbot.getUpdates()
    if updates:
        last_update_id = updates[-1]['update_id']
        fursuitbot.getUpdates(offset=last_update_id+1)

def thread_function(msg):
    pass

def thread_function_query(msg):
    pass

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