"""
=================================== README ===================================
This script can be used to create a simple serial communication between an Arduino
and an other machine.
=============================================================
Just create a new SerialTools object and use the functions send_message,
listen_message and get_message, you DO NOT need to use others function excepted if you know
what you are doing.
=============================================================
Example :

from SerialTools import SerialTools

com = SerialTools("COM4", 115200)
print(com.send_message(2, [], 500))
com.listen_message()
print(com.get_message())
=============================================================
Please do not modify internal states of an instantiated class.
Do not use id 0, it is used to specified there is no message.
If you find a bug please contact us.
==============================================================================
"""

import serial
import time
from typing import List, Optional, Tuple

current_milli_time = lambda: int(round(time.time() * 1000))


def creat_serial_com(port: str, baud: int, timeout: Optional[int] = 0) -> serial.Serial:
    """
    Create a new serial object using given port and baud rate. This object will not reset the Arduino when it is
    opened.
    :param port:
    The port used for the serial communication
    :param baud:
    The baud rate used for the communication
    :param timeout:
    The timeout used for the read function (0 = non blocking)
    :return:
    A serial object that can be use for sending and receiving message
    """
    com = serial.Serial()
    com.port = port
    com.baudrate = baud
    com.timeout = timeout
    com.setDTR(False)
    com.open()
    return com


class SerialTools:

    def __init__(self, port: str, baud: int, timeout: Optional[int] = 0) -> None:
        """
        Create a new SerialTools object. It can be used to send and receive message from an Arduino if this Arduino
        use the program provided in the same project.
        :param port:
        The port used for the serial communication
        :param baud:
        The baud rate used for the communication
        :param timeout:
        The timeout used for the read function (0 = non blocking)
        """
        # Communication management
        self.has_token = True
        self.time_token_back = current_milli_time()

        # Buffers
        self.rcv_buffer: list = []
        self.send_buffer: list = []

        # Messages
        self.message: list = []
        self.message_id: int = 0

        # Serial com
        self.com = creat_serial_com(port, baud, timeout)

    def give_token(self, token_duration: Optional[int] = 0) -> None:
        """
        Use this function to tell the program it is not allowed to use the serial communication. When the token life
        duration is over the program will get the the token back to it and will be able to use the serial communication.
        :param token_duration:
        The time the program will wait until it can get the token back.
        """
        if token_duration > 0:
            self.has_token = False
            self.time_token_back = current_milli_time() + token_duration

    def check_token(self) -> None:
        """
        Check if the token duration is over. If it is self.has_token will be set to True.
        """
        if current_milli_time() > self.time_token_back:
            self.has_token = True

    def send(self, token_duration=0) -> bool:
        """
        If the program has the token, this method will send the content of self.send_buffer to the Arduino and return
        True. If the program do not have the token it will return false and not send the message to the Arduino.
        In both case the send_buffer is cleared after the execution of this method.
        :param token_duration:
        The optional duration the Arduino can send a reply after the reception of the message.
        :return:
        True if the program can send the message else False.
        """
        self.check_token()
        if self.has_token:
            self.com.write(self.send_buffer)
            self.give_token(token_duration)
            self.send_buffer = []
            return True
        else:
            self.send_buffer = []
            return False

    def listen(self) -> None:
        """
        This method will listen the Arduino while the program does not have the token or the buffer is not empty.
        If a message is received, it will be stored in the self.rcv_buffer attribute.
        WARNING : If the Arduino send a long message, this method can block the program for a long time.
        """
        self.check_token()
        while not self.has_token or self.com.in_waiting != 0:
            if self.com.in_waiting != 0:
                self.rcv_buffer += [int.from_bytes(self.com.read(), byteorder='big')]
            self.check_token()

    def listen_message(self) -> None:
        """
        This method use the method listen (see listen() for more details) the read self.rcv_buffer to detect if the
        received message has the correct format to be understood by the program.
        Ex : 255 255 255 id ... 254 254 254
        The id of the message is stored in sef.message_id and the content of the message is stored in self.message.
        """
        self.listen()
        if len(self.rcv_buffer) > 0:
            temp = []
            for c in self.rcv_buffer:
                temp += [c]
                if len(temp) == 3:
                    if temp[0] != 255 or temp[1] != 255 or temp[2] != 255:
                        temp = [temp[1], temp[2]]
                elif len(temp) >= 6:
                    if temp[-1] == 254 and temp[-2] == 254 and temp[-3] == 254:
                        self.message = temp[4:-3]
                        self.message_id = temp[3]
                        break
            self.rcv_buffer = []

    def send_message(self, msg_id: int, message: List[int], token_duration=0) -> bool:
        """
        Send a message to the Arduino with given parameter. See new_message() and send() for more information.
        :param msg_id:
        The id of the message, the Arduino will use this id to know what action it have to do.
        :param message:
        The content of the message.
        :param token_duration:
        The optional duration the Arduino can reply this message (Only use if the id of the message correspond to a
        request the Arduin
        True if the program can send the message else False.
        """
        self.new_message(msg_id, message, token_duration)
        return self.send(token_duration)

    def new_message(self, msg_id: int, message: List[int], token_duration=0) -> None:
        """
        The method create a new message that can be understood by the Arduino. The message will be stored in
        self.send_buffer.
        :param msg_id:
        The id of the message, the Arduino will use this id to know what action it have to do.
        :param message:
        The content of the message.
        :param token_duration:
        The optional duration the Arduino can reply this message (Only use if the id of the message correspond to a
        request the Arduino need to reply)
        """
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

    def fill_send_buffer(self, message: List[int]) -> None:
        """
        Fill self.send_buffer with the given list.
        :param message:
        The list to put in self.send_buffer.
        """
        self.send_buffer = message

    def get_message(self) -> Tuple[int, List[int]]:
        """
        This method returns message id and message content in a tuple the clear both attributes.
        :return:
        (0, []) if there is no message else (self.message_id, self.message)
        """
        if self.message_id == 0:
            return 0, []
        else:
            msg_id, msg = self.message_id, self.message
            self.message_id, self.message = 0, []
            return msg_id, msg
