import serial
import random

serial_port = 'COM10'
baud_rate = 9600

def connect(port, baud):
    try:
        ser = serial.Serial(port, baud, timeout=1)
        print(f"Connected to {port} at {baud} baud.")
    except serial.SerialException:
        print(f"Failed to connect to {port}. Please check the port and baud rate.")
        exit()
    return ser

def write_data(ser, value1, value2, value3, value4, value5, value6, value7, value8, value9, value10, value11):
    data_to_send = f"{value1},{value2},{value3},{value4},{value5},{value6},{value7},{value8},{value9},{value10},{value11}\n"
    ser.write(data_to_send.encode())
    return data_to_send

def read_data(ser):
    try:
        data = ser.readline().decode().strip()
        while ser.in_waiting > 0:
            data = ser.readline().decode().strip()
    except UnicodeDecodeError:
        data = "Error"
    return data

ser = connect(serial_port, baud_rate)
while True:
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