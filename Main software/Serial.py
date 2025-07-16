import serial

port = 'COM3'
baud = 9600
ser = None

leds_brightness_default = 50
leds_effects_options = ['solid_color', 'fade', 'wipe', 'theater_chase', 'rainbow', 'strobe', 'moving substrips', 'none (off)']

animatronics_on = 1
leds_on = 1
leds_brightness = leds_brightness_default
leds_color_r = 0
leds_color_g = 0
leds_color_b = 0
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

def send(expression_scores):
    expression_scores_str = ",".join(map(lambda score: str(int(score * 100)), expression_scores))
    data_to_send = f"{animatronics_on},{leds_on},{leds_brightness},{leds_color_r},{leds_color_g},{leds_color_b},{leds_effect},{leds_level},{expression_scores_str}\n"
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

if __name__ == "__main__":
    connect()
    send([animatronics_on, leds_on, leds_brightness, leds_color_r, leds_color_g, leds_color_b, leds_effect, leds_level, 0, 0, 0, 1, 0, 0])
