import socket
import time

host = "localhost"
port = 8765
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def connect():
    connected = False
    while not connected:
        try:
            client_socket.connect((host, port))
            print("Unity app connected!")
            connected = True
        except ConnectionRefusedError:
            print("Unity app connection refused. Retrying in 1 second...")
            time.sleep(1)
    return client_socket

def send(displacement_eye_x, displacement_eye_y, left_eye_closed, right_eye_closed, expression_scores_list):
    displacement_eye_x = str(displacement_eye_x).replace(".", ",")
    displacement_eye_y = str(displacement_eye_y).replace(".", ",")
    expression_scores_string = ""
    for score in expression_scores_list:
        if score < 0.01:
            score = 0
        expression_scores_string += str(score).replace(".", ",") + " "
    message = f"{displacement_eye_x} {displacement_eye_y} {left_eye_closed} {right_eye_closed} {expression_scores_string}"
    client_socket.sendall(message.encode())
    response = client_socket.recv(1024).decode()
    if "Invalid message format!" in response:
        raise Exception("Unity app returned Invalid message format!")
    return response