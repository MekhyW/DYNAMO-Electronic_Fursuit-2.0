import serial
import random

serial_port = 'COM3'
baud_rate = 9600
ser = None

def connect(port, baud):
    global ser
    ser = None
    try:
        ser = serial.Serial(port, baud, timeout=1)
        print(f"Connected to {port} at {baud} baud.")
    except serial.SerialException:
        print("Serial connection failed")
    return ser

def write_data(ser, value1, value2, value3, value4, value5, value6, value7, value8, value9, value10, value11):
    data_to_send = f"{value1},{value2},{value3},{value4},{value5},{value6},{value7},{value8},{value9},{value10},{value11}\n"
    if ser is not None:
        try:
            ser.write(data_to_send.encode())
        except serial.SerialException:
            connect(serial_port, baud_rate)
    return data_to_send

def read_data(ser):
    if ser is not None:
        try:
            data = ser.readline().decode().strip()
            while ser.in_waiting > 0:
                data = ser.readline().decode().strip()
        except UnicodeDecodeError:
            data = "Error"
        except serial.SerialException:
            connect(serial_port, baud_rate)
        return data
    else:
        return None

while True:
    if ser is None:
        connect(serial_port, baud_rate)
        continue
    value1 = random.randint(0, 100)
    value2 = random.randint(0, 100)
    value3 = random.randint(0, 100)
    value4 = random.randint(0, 100)
    value5 = random.randint(0, 100)
    value6 = random.randint(0, 100)
    value7 = random.randint(0, 100)
    value8 = random.randint(0, 100)
    value9 = random.randint(0, 100)
    value10 = random.randint(0, 100)
    value11 = random.randint(0, 100)
    sent_data = write_data(ser, value1, value2, value3, value4, value5, value6, value7, value8, value9, value10, value11)
    print(f"Sent to Arduino: {sent_data.strip()}")
    received_data = read_data(ser)
    print(f"Arduino says: {received_data}")