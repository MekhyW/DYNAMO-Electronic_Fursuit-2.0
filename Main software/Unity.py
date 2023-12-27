import socket

host = "localhost"
port = 8765
client_socket = None
connected = False

def connect():
    global client_socket, connected
    try:
        if client_socket is not None:
            client_socket.close()
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        print("Unity app connected!")
        connected = True
        return client_socket
    except ConnectionRefusedError:
        print("Unity app connection refused. Is the app running?")
        connected = False

def send(displacement_eye_x, displacement_eye_y, left_eye_closeness, right_eye_closeness, expression_scores_list):
    displacement_eye_x = str(displacement_eye_x).replace(".", ",")
    displacement_eye_y = str(displacement_eye_y).replace(".", ",")
    left_eye_closeness = str(left_eye_closeness).replace(".", ",")
    right_eye_closeness = str(right_eye_closeness).replace(".", ",")
    expression_scores_list = [str(0) if score < 0.01 else str(score).replace(".", ",") for score in expression_scores_list]
    expression_scores_string = " ".join(expression_scores_list)
    message = f"{displacement_eye_x} {displacement_eye_y} {left_eye_closeness} {right_eye_closeness} {expression_scores_string}"
    response = None
    try:
        client_socket.sendall(message.encode())
        response = client_socket.recv(1024).decode()
    except Exception as e:
        print(e)
        connect()
        return None
    finally:
        if response and "Invalid message format!" in response:
            raise Exception("Unity app returned Invalid message format!")
        return response