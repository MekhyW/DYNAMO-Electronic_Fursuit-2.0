import cv2
import pytesseract
import pyautogui
import os
import time

open_browser_button_text = "started"
login_button_text = "Google"
account_text = "Mekhy"

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def find_button_and_click(target_text):
    screenshot_path = 'screenshot.png'
    screenshot = pyautogui.screenshot()
    screenshot.save(screenshot_path)
    image = cv2.imread(screenshot_path)
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = pytesseract.image_to_data(rgb, output_type=pytesseract.Output.DICT)
    for i in range(0, len(results["text"])):
        text = results["text"][i].strip().lower()
        conf = int(results["conf"][i])
        if(len(text) == 0):
            continue
        print(f"Text: {text}, Confidence: {conf}")
        if target_text.lower() in text and conf > 50:
            center_x = results["left"][i] + results["width"][i] / 2
            center_y = results["top"][i] + results["height"][i] / 2
            pyautogui.click(center_x, center_y)
            print(f"Clicked the button with text: '{target_text}'")
    os.remove(screenshot_path)

time.sleep(20)
find_button_and_click(open_browser_button_text)
time.sleep(10)
find_button_and_click(login_button_text)
time.sleep(5)
find_button_and_click(account_text)