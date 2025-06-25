from TfLunaI2C import TfLunaI2C
import time


if __name__ == '__main__':
    # Basic Usage:
    tfluna = TfLunaI2C()
    tfluna.set_mode_continuous()
    tfluna.save()
    tfluna.reboot()
    #print(tf)
    #while True :
    #    data = tf.read_data()
    #    tf.print_data()
    #    time.sleep(0.5)

    # change to metric
    tfluna.us = False
    print(tfluna)
    while True:
        data = tfluna.read_data()
        tfluna.print_data()
        time.sleep(0.5)
        
