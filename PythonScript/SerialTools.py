import serial
import time
from typing import List

current_milli_time = lambda: int(round(time.time() * 1000))


class SerialTools:

    def __init__(self, port, baud, timeout=0):
        # Communication management
        self.has_token = True
        self.time_token_back = current_milli_time()

        # Buffers
        self.rcv_buffer: list = []
        self.send_buffer: list = []

        # Serial com
        self.com = serial.Serial()
        self.com.port = port
        self.com.baud = baud
        self.com.timeout = timeout
        self.com.setDTR(False)
        self.com.open()

    def give_token(self, token_duration=0):
        if token_duration > 0:
            self.has_token = False
            self.time_token_back = current_milli_time() + token_duration

    def check_token(self):
        if current_milli_time() > self.time_token_back:
            self.has_token = True
            print("OK")  # DEBUG

    def send(self, token_duration=0):
        self.check_token()
        if self.has_token:
            self.com.write(self.send_buffer)
            self.give_token(token_duration)
            print(f"Send : {self.send_buffer}")  # Debug
            self.send_buffer = []
            return True
        else:
            self.send_buffer = []
            return False

    def listen(self):
        self.check_token()
        while not self.has_token or self.com.in_waiting != 0:
            if self.com.in_waiting != 0:
                self.rcv_buffer += [self.com.read()]
            self.check_token()
        print(self.rcv_buffer)  # Debug

    def send_message(self, msg_id: int, message: List[int], token_duration=0):
        self.new_message(msg_id, message, token_duration)
        return self.send(token_duration)

    def new_message(self, msg_id: int, message: List[int], token_duration=0):
        msg_is_correct = True
        if 255 >= msg_id >= 0 and 65535 >= token_duration >= 0:
            for i in message:
                if 0 > i or i > 255:
                    msg_is_correct = False
                    break
            if msg_is_correct:
                if token_duration != 0:
                    self.fill_send_buffer(
                        [255, 255, 255] + [msg_id] + list(
                            int.to_bytes(token_duration, 2, byteorder='big')) + message + [254, 254,
                                                                                           254])
                else:
                    self.fill_send_buffer([255, 255, 255] + [msg_id] + message + [254, 254, 254])

    def fill_send_buffer(self, message: List[int]):
        self.send_buffer = message
