import Serial
import socket
import threading

host = "localhost"
port = 50000
client_socket = None
connected = False
socket_lock = threading.Lock()

screen_brightness = 100

def connect():
    global client_socket, connected
    try:
        if client_socket is not None:
            client_socket.close()
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        Serial.send_debug("Unity app connected!")
        connected = True
        return client_socket
    except ConnectionRefusedError:
        Serial.send_debug("Unity app connection refused. Is the app running?")
        connected = False
    except Exception as e:
        Serial.send_debug("Unexpected error on unity connection:", e)
        connected = False
    return None

def send(displacement_eye_x, displacement_eye_y, closeness_left, closeness_right, emotion_scores, manual_mode, manual_id, silly_mode):
    with socket_lock:
        displacement_eye_x = str(displacement_eye_x).replace(",", ".")
        displacement_eye_y = str(displacement_eye_y).replace(",", ".")
        closeness_left = str(closeness_left).replace(",", ".")
        closeness_right = str(closeness_right).replace(",", ".")
        emotion_scores = [str(0) if score < 0.01 else str(score).replace(",", ".") for score in emotion_scores]
        emotion_scores_string = " ".join(emotion_scores)
        message = f"{displacement_eye_x} {displacement_eye_y} {closeness_left} {closeness_right} {emotion_scores_string}"
        message += f" {manual_id}" if manual_mode and manual_id >= len(emotion_scores)-1 else " -1"
        message += " 1" if silly_mode else " 0"
        message += f" {screen_brightness}"
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

def send_eyes_video(url):
    with socket_lock:
        try:
            message = "VIDEO STOP" if url == "stop" else f"VIDEO PLAY {url}"
            client_socket.sendall(message.encode())
            response = client_socket.recv(1024).decode()
            return response
        except Exception as e:
            print(e)
            connect()
            return None
    
if __name__ == "__main__":
    connect()
    print(send(0, 0, 0, 0, [0, 0, 0, 0, 0, 0], False, 0, False))
    print(send_eyes_video("http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"))
    print(send_eyes_video("stop"))
