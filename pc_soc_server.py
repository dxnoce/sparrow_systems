#!/usr/bin/env python3

from numpysocket import NumpySocket
from soc_protocol import *
from cache_manager import get_frame
import numpy as np

IMAGE_SHAPE = (480, 640, 3)   # MUST match your cache_manager
PORT = 9999


class PCSoCServer:
    def __init__(self):
        self.sock = NumpySocket(image_shape=IMAGE_SHAPE)
        self.protocol = SoCProtocol(command_sender=self.send_command)

    # -------- SEND COMMAND TO MATLAB --------
    def send_command(self, cmd_array):
        cmd = cmd_array[0]

        self.sock.sendCmd(cmd)

        if cmd == CMD_LOG_DATA:
            self.sock.sendInt32(cmd_array[1])
            self.sock.sendFloat32(cmd_array[2])
            self.sock.sendFloat32(cmd_array[3])
            self.sock.sendFloat32(cmd_array[4])

        elif cmd == CMD_SEND_CALL:
            self.sock.sendUint8(cmd_array[1])

        elif cmd == CMD_SLAVE_MODE_READY:
            pass

    # -------- HANDLE MATLAB REQUEST --------
    def handle_matlab_request(self, cmd):
        if cmd == CMD_REQUEST_LATEST_IMAGE:
            frame_data = get_frame([10])

        elif cmd == CMD_REQUEST_NTH_PREVIOUS_IMAGE:
            offset = self.sock.receiveInt32()
            frame_data = get_frame([11, offset])

        elif cmd == CMD_REQUEST_IMAGE_AT_FRAME:
            frame_num = self.sock.receiveInt32()
            frame_data = get_frame([15, frame_num])

        else:
            print("Unknown request:", cmd)
            return

        frame_number = frame_data["frame"]
        image = frame_data["image"]

        # Send image back to MATLAB
        self.sock.sendCmd(CMD_PROCESS_IMAGE)
        self.sock.sendInt32(frame_number)
        self.sock.send(image)

    # -------- MAIN LOOP --------
    def run(self):
        print("[INFO] Waiting for MATLAB connection...")
        self.sock.startServer(PORT)

        print("[INFO] MATLAB connected")

        while True:
            try:
                cmd = self.sock.receiveCmd()
                if cmd is None:
                    break

                print("[DEBUG] Received CMD:", cmd)

                # MATLAB asking for image
                if cmd in [
                    CMD_REQUEST_LATEST_IMAGE,
                    CMD_REQUEST_NTH_PREVIOUS_IMAGE,
                    CMD_REQUEST_IMAGE_AT_FRAME
                ]:
                    self.handle_matlab_request(cmd)

                # MATLAB sending image (rare case)
                elif cmd == CMD_PROCESS_IMAGE:
                    frame_number = self.sock.receiveInt32()
                    image = self.sock.receive()

                    result = self.protocol.handle_incoming_command(
                        [CMD_PROCESS_IMAGE, frame_number, image]
                    )

                    print("[RESULT]", result)

                elif cmd == CMD_RESET:
                    self.protocol.handle_incoming_command([CMD_RESET])

                elif cmd == CMD_SLAVE_MODE:
                    self.protocol.handle_incoming_command([CMD_SLAVE_MODE])

                else:
                    print("[WARN] Unknown CMD:", cmd)

            except Exception as e:
                print("[ERROR]", e)
                break

        self.sock.close()


if __name__ == "__main__":
    server = PCSoCServer()
    server.run()

