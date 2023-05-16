"""
Author: Chris Knowles
Date: Apr 2020
Copyright: University of Sunderland, (c) 2020
File: bme680.py
Version: 1.0.0
Notes: BME680 module for all simulated ESP32 MicroPython application code used on the CET235 IoT module, ie.
       when NOT able to utilise the prototyping hardware rig
"""
import random

OS_2X = None
OS_4X = None
OS_8X = None
FILTER_SIZE_3 = None
ENABLE_GAS_MEAS = None

# To speed up change increase RANDOM_CHANGE_LIMIT towards 100 when it will change readings every time they are
# read, slow down change by decreasing RANDOM_CHANGE_LIMIT towards 0 when no change will occur
RANDOM_CHANGE_LIMIT = 67
RANDOM_SPIKE_LIMIT = 5

NORMAL_TEMPERATURE = 24.5
TEMPERATURE_INCREMENT = 0.1
TEMPERATURE_DECREMENT = -0.1

NORMAL_PRESSURE = 1010
PRESSURE_INCREMENT = 10
PRESSURE_DECREMENT = -10

NORMAL_HUMIDITY = 45.0
HUMIDITY_INCREMENT = 1
HUMIDITY_DECREMENT = -1

NORMAL_GAS_RESISTANCE = 5000
GAS_RESISTANCE_INCREMENT = 1000
GAS_RESISTANCE_DECREMENT = -1000

class Data:
    def __init__(self):
        self.temperature = NORMAL_TEMPERATURE  # In degrees Celsius
        self.pressure = NORMAL_PRESSURE        # In Hectopascals (1 hPa = 100 Pascals)
        self.humidity = NORMAL_HUMIDITY        # As a percentage (ie. relative humidity)
        self.gas_resistance = NORMAL_GAS_RESISTANCE
        self.heat_stable = True

class BME680:
    def __init__(self, i2c, i2c_addr):
        self.i2c = i2c
        self.i2c_addr = i2c_addr
        self.data = Data()
        self.temperature_target = NORMAL_TEMPERATURE
        self.pressure_target = NORMAL_PRESSURE
        self.humidity_target = NORMAL_HUMIDITY
        self.gas_resistance_target = NORMAL_GAS_RESISTANCE

    def set_humidity_oversample(self, value):
        pass

    def set_pressure_oversample(self, value):
        pass

    def set_temperature_oversample(self, value):
        pass

    def set_filter(self, value):
        pass

    def set_gas_status(self, value):
        pass

    def set_gas_heater_temperature(self, value):
        pass

    def set_gas_heater_duration(self, value):
        pass

    def select_gas_heater_profile(self, value):
        pass

    def get_sensor_data(self, temperature_target=None, pressure_target=None, humidity_target=None,
                        gas_resistance_target=None):
        """
        The sensor will always attempt to reach the provided ***_target value using the increment/decrement values
        for each environmental reading, note: passing None to a ***_target value will set that as the NORMAL_***
        pre-defined constant value for that reading type
        """
        if temperature_target is not None:
            self.temperature_target = temperature_target
        else:
            self.temperature_target = NORMAL_TEMPERATURE

        if pressure_target is not None:
            self.pressure_target = pressure_target
        else:
            self.pressure_target = NORMAL_PRESSURE

        if humidity_target is not None:
            self.humidity_target = humidity_target
        else:
            self.humidity_target = NORMAL_HUMIDITY

        if gas_resistance_target is not None:
            self.gas_resistance_target = gas_resistance_target
        else:
            self.gas_resistance_target = NORMAL_GAS_RESISTANCE

        rnd_temperature = random.randint(1, 100)
        rnd_pressure = random.randint(1, 100)
        rnd_humidity = random.randint(1, 100)
        rnd_gas_resistance = random.randint(1, 100)

        if rnd_temperature < RANDOM_CHANGE_LIMIT:
            rnd_spike = random.randint(1, 100)
            if rnd_spike < RANDOM_SPIKE_LIMIT:
                rnd_delta = random.randint(1, 100)
                if rnd_delta <= 50:
                    self.data.temperature += TEMPERATURE_DECREMENT
                else:
                    self.data.temperature += TEMPERATURE_INCREMENT
            else:
                if self.data.temperature > self.temperature_target:
                    self.data.temperature += TEMPERATURE_DECREMENT
                elif self.data.temperature < self.temperature_target:
                    self.data.temperature += TEMPERATURE_INCREMENT

        if rnd_pressure < RANDOM_CHANGE_LIMIT:
            rnd_spike = random.randint(1, 100)
            if rnd_spike < RANDOM_SPIKE_LIMIT:
                rnd_delta = random.randint(1, 100)
                if rnd_delta <= 50:
                    self.data.pressure += PRESSURE_DECREMENT
                else:
                    self.data.pressure += PRESSURE_INCREMENT
            else:
                if self.data.pressure > self.pressure_target:
                    self.data.pressure += PRESSURE_DECREMENT
                elif self.data.pressure < self.pressure_target:
                    self.data.pressure += PRESSURE_INCREMENT

        if rnd_humidity < RANDOM_CHANGE_LIMIT:
            rnd_spike = random.randint(1, 100)
            if rnd_spike < RANDOM_SPIKE_LIMIT:
                rnd_delta = random.randint(1, 100)
                if rnd_delta <= 50:
                    self.data.humidity += HUMIDITY_DECREMENT
                else:
                    self.data.humidity += HUMIDITY_INCREMENT
            else:
                if self.data.humidity > self.humidity_target:
                    self.data.humidity += HUMIDITY_DECREMENT
                elif self.data.humidity < self.humidity_target:
                    self.data.humidity += HUMIDITY_INCREMENT

        if rnd_gas_resistance < RANDOM_CHANGE_LIMIT:
            rnd_spike = random.randint(1, 100)
            if rnd_spike < RANDOM_SPIKE_LIMIT:
                rnd_delta = random.randint(1, 100)
                if rnd_delta <= 50:
                    self.data.gas_resistance += GAS_RESISTANCE_DECREMENT
                else:
                    self.data.gas_resistance += GAS_RESISTANCE_INCREMENT
            else:
                if self.data.gas_resistance > self.gas_resistance_target:
                    self.data.gas_resistance += GAS_RESISTANCE_DECREMENT
                elif self.data.gas_resistance < self.gas_resistance_target:
                    self.data.gas_resistance += GAS_RESISTANCE_INCREMENT

        return True
