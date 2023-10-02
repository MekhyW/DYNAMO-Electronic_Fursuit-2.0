import socket

def send_and_receive():
    host = "localhost"
    port = 8765

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    
    while True:
        displacement_eye_x = input("Enter eye x: ").replace(".", ",")
        displacement_eye_y = input("Enter eye y: ").replace(".", ",")
        left_eye_closeness = input("Enter left eye closeness: ").replace(".", ",")
        right_eye_closeness = input("Enter right eye closed: ").replace(".", ",")
        expression_scores = input("Enter the 6 expression scores (separated by spaces): ").replace(".", ",")
        message = f"{displacement_eye_x} {displacement_eye_y} {left_eye_closeness} {right_eye_closeness} {expression_scores}"
        client_socket.sendall(message.encode())
        response = client_socket.recv(1024).decode()
        print("Received response:", response)

if __name__ == "__main__":
    send_and_receive()
