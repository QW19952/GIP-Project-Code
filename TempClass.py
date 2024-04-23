import board
import digitalio
import adafruit_max31856
import time
import numpy as np
import threading

#Cal Values
#1: -1.09
#2: -0.851
#3: -1.221
#4: -1.403

class ThermocoupleMeasurement:
    def __init__(self, pins=[board.D25, board.D24, board.D23, board.D18], cal_vals=[-1.090, -0.851, -1.221, -1.403]): 
        self.spi = board.SPI()
        self.cs_pins = [
            digitalio.DigitalInOut(pin)
            for pin in pins
        ]
        self.thermocouples = [
            adafruit_max31856.MAX31856(self.spi, cs_pin)
            for cs_pin in self.cs_pins
        ]
        self.data = [[] for _ in range(len(pins))]
        self.cal_vals = cal_vals

    def collect_data(self, num_sensors):
        if num_sensors < 1 or num_sensors > 4:
            raise ValueError("Number of sensors must be between 1 and 4")

        data = [None] * num_sensors
        threads = []

		# Define a function to read data from a thermocouple
        def read_data(i):
            thermocouple = self.thermocouples[i]
            thermocouple.initiate_one_shot_measurement()
            #while thermocouple.oneshot_pending:
                #continue
            temp = round(thermocouple.unpack_temperature() + self.cal_vals[i], 2)
            
            data[i] = temp

		# Create threads to read data from each thermocouple
        for i in range(num_sensors):
            thread = threading.Thread(target=read_data, args=(i,))
            threads.append(thread)
            thread.start()

		# Wait for all threads to finish
        for thread in threads:
            thread.join()

        return data
		


if __name__ == "__main__":
    collector = ThermocoupleMeasurement()
    num_sensors = 4   # For example, collect data from all four sensors
    while True:
		#
        start_time = time.time()

		# collect data
        collected_data = collector.collect_data(num_sensors)
        print("Collected data:", collected_data)

        end_time = time.time()
        execution_time = end_time - start_time
        print("Execution time:", execution_time, "seconds")

        time.sleep(1)

