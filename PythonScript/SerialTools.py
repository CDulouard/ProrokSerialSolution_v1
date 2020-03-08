import serial
import time
from typing import List, Optional

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
        print(self.rcv_buffer)  # Debug

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
