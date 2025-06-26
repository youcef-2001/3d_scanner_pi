from TfLunaI2C import TfLunaI2C


class TfLunaService:
    def __init__(self, i2c_bus=1, address=0x10):
        self.tf_luna = TfLunaI2C(i2c_bus, address)

    def get_distance(self):
        return self.tf_luna.get_distance()

    def get_temperature(self):
        return self.tf_luna.get_temperature()

    def get_signal_strength(self):
        return self.tf_luna.get_signal_strength()

    def get_version(self):
        return self.tf_luna.get_version()

        