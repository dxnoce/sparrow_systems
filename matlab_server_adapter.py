import socket
import json
import struct
import cv2
from cache_manager import get_frame

HOST = "0.0.0.0"
PORT = 9999

MODE = "SERVE"

# ---------- SAFE SEND / RECEIVE ----------
def send_json(conn, obj):
    msg = json.dumps(obj).encode()
    conn.sendall(struct.pack(">I", len(msg)) + msg)

def recv_json(conn):
    raw_len = conn.recv(4)
    if not raw_len:
        return None

    msg_len = struct.unpack(">I", raw_len)[0]

    data = b''
    while len(data) < msg_len:
        packet = conn.recv(4096)
        if not packet:
            break
        data += packet

    return json.loads(data.decode())

# ---------- IMAGE ENCODING ----------
def encode_image(img):
    _, buffer = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    return buffer.tobytes().hex()

# ---------- COMMAND HANDLER ----------
def handle_command(cmd, conn):
    global MODE

    command = cmd[0]

    # MODE SWITCH
    if command == 98:
        MODE = "REPLAY"
        send_json(conn, {"status": "slaveModeReady"})
        return

    if command == 1:
        MODE = "SERVE"
        send_json(conn, {"status": "resetAck"})
        return

    # IMAGE REQUESTS
    if command in [10, 11, 15]:
        result = get_frame(cmd)

        if result is None:
            send_json(conn, {"error": "Invalid request"})
            return

        response = {
            "frame": result["frame"],
            "timestamp": result["timestamp"],
            "image": encode_image(result["image"])
        }

        send_json(conn, response)
        return

    send_json(conn, {"error": "Unknown command"})

# ---------- SERVER ----------
def start_server():
    global MODE

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()

        print(f"[INFO] Server running on {HOST}:{PORT}")

        while True:
            conn, addr = s.accept()
            print(f"[INFO] Connected: {addr}")

            with conn:
                try:
                    while True:
                        cmd = recv_json(conn)
                        if cmd is None:
                            break

                        print(f"[DEBUG] {cmd} | MODE={MODE}")
                        handle_command(cmd, conn)

                except Exception as e:
                    print("[ERROR]", e)

            print("[INFO] Connection closed")

if __name__ == "__main__":
    start_server()

