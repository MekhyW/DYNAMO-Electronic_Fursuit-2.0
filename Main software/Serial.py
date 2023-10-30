import serial
import time

port = 'COM4'
baud = 9600
ser = None

leds_brightness_default = 25
leds_color_options = ['White', 'Red', 'Purple', 'Yellow', 'Pink', 'Deep blue', 'Light blue', 'Orange', 'Green']
leds_effects_options = ['Solid Color', 'Fade', 'Wipe', 'Theater Chase', 'Rainbow', 'Strobe', 'Moving Substrips', 'None (Off)']

animatronics_on = 1
leds_on = 1
leds_brightness = leds_brightness_default
leds_color = 0
leds_effect = 0
leds_level = 0

def connect():
    global ser
    try:
        ser = serial.Serial(port, baud, timeout=1)
        print(f"Connected to {port} at {baud} baud.")
    except serial.SerialException:
        print("Serial connection failed. Retrying in 1 second...")
        time.sleep(1)
    return ser

def send(expression_scores_list):
    data_to_send = f"{animatronics_on},{leds_on},{leds_brightness},{leds_color},{leds_effect},{leds_level}"
    for score in expression_scores_list:
        data_to_send += f",{int(score*100)}"
    data_to_send += "\n"
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    ser.write(data_to_send.encode())
    return data_to_send