from SerialTools import SerialTools

if __name__ == "__main__":
    com = SerialTools("COM4", 115200)
    print(com.send_message(2, [], 500))
    com.listen_message()
    print(com.get_message())
