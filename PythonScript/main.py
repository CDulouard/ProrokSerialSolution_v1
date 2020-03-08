from SerialTools import SerialTools
import serial
import time

if __name__ == "__main__":
    com = SerialTools("COM4", 115200)
    print(com.send_message(2, [], 500))
    com.listen()

    # ser = creat_serial_com("COM4", 115200)
    # ser.write(com.send_buffer)
