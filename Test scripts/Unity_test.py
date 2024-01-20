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

def send_and_receive():
    global connected
    while True:
        displacement_eye_x = input("Enter eye x: ").replace(".", ",")
        displacement_eye_y = input("Enter eye y: ").replace(".", ",")
        left_eye_closeness = input("Enter left eye closeness: ").replace(".", ",")
        right_eye_closeness = input("Enter right eye closed: ").replace(".", ",")
        expression_scores = input("Enter the 6 expression scores (separated by spaces): ").replace(".", ",")
        manual_expression = input("Enter manual expression id: ").replace(".", ",")
        message = f"{displacement_eye_x} {displacement_eye_y} {left_eye_closeness} {right_eye_closeness} {expression_scores} {manual_expression}"
        try:
            client_socket.sendall(message.encode())
            response = client_socket.recv(1024).decode()
            print("Received response:", response)
        except Exception as e:
            print(e)
            connect()

if __name__ == "__main__":
    connect()
    send_and_receive()
