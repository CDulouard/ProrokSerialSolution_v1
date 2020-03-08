from SerialTools import SerialTools
import serial
import time


def creat_serial_com(port, baud, timeout=0):
    com = serial.Serial()
    com.port = port
    com.baudrate = baud
    com.timeout = timeout
    com.setDTR(False)
    com.open()
    return com


if __name__ == "__main__":
    com = SerialTools("COM4", 115200)
    print(com.send_message(2, [], 500))
    com.com.close()
    # com.listen()

    # ser = creat_serial_com("COM4", 115200)
    # ser.write(com.send_buffer)
