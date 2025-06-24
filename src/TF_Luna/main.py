from TfLunaI2C import TfLunaI2C
import time


if __name__ == '__main__':
    # Basic Usage:
    tf = TfLunaI2C()
    #print(tf)
    #while True :
    #    data = tf.read_data()
    #    tf.print_data()
    #    time.sleep(0.5)

    # change to metric
    tf.us = False
    print(tf)
    while True:
        data = tf.read_data()
        tf.print_data()
        time.sleep(0.5)
        
