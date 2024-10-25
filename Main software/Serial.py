import serial

port = 'COM3'
baud = 9600
ser = None

leds_brightness_default = 25
leds_color_options = ['white', 'red', 'purple', 'yellow', 'pink', 'deep blue', 'light blue', 'orange', 'green']
leds_effects_options = ['solid color', 'fade', 'wipe', 'theater chase', 'rainbow', 'strobe', 'moving substrips', 'none (off)']

animatronics_on = 1
leds_on = 1
leds_brightness = leds_brightness_default
leds_color = 0
leds_effect = 0
leds_level = 0

def leds_level_from_int16(int16_value):
    global leds_effect, leds_level
    leds_effect = len(leds_effects_options)  # "Level" effect is last index + 1
    leds_level = int((int16_value / 32767) * 100) # Convert int16 to percentage int
    return leds_level

def connect():
    global ser
    ser = None
    try:
        ser = serial.Serial(port, baud, timeout=1)
        print(f"Connected to {port} at {baud} baud.")
    except serial.SerialException:
        print("Serial connection failed")
    except Exception as e:
        print("Unexpected error on serial connection:", e)
    return ser

def send(expression_scores_list):
    expression_scores_str = ",".join(map(lambda score: str(int(score * 100)), expression_scores_list))
    data_to_send = f"{animatronics_on},{leds_on},{leds_brightness},{leds_color},{leds_effect},{leds_level},{expression_scores_str}\n"
    response = None
    if ser is not None:
        try:
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            ser.write(data_to_send.encode())
            response = ser.readline().decode()
        except serial.SerialException:
            print("Serial connection failed")
            connect()
            return None
        finally:
            if response and "Invalid message format!" in response:
                raise Exception("AVR returned Invalid message format!")
            return response
    return None