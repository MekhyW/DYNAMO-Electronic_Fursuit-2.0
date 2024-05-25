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

def send(displacement_eye_x, displacement_eye_y, closeness_left, closeness_right, emotion_scores, manual_mode, manual_id, silly_mode):
    displacement_eye_x = str(displacement_eye_x).replace(".", ",")
    displacement_eye_y = str(displacement_eye_y).replace(".", ",")
    closeness_left = str(closeness_left).replace(".", ",")
    closeness_right = str(closeness_right).replace(".", ",")
    emotion_scores = [str(0) if score < 0.01 else str(score).replace(".", ",") for score in emotion_scores]
    emotion_scores_string = " ".join(emotion_scores)
    message = f"{displacement_eye_x} {displacement_eye_y} {closeness_left} {closeness_right} {emotion_scores_string}"
    message += f" {manual_id}" if manual_mode and manual_id >= len(emotion_scores) else " -1"
    message += " 1" if silly_mode else " 0"
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