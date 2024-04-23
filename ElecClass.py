from ADCDifferentialPi import ADCDifferentialPi
import threading
import time

class ElectricalMeasurement:
    def __init__(self, addresses=[0x68], reference_voltage=0.3707865169, bit_resolution=18):  #0x68, 0x6C, 0x6A, 0x6E #
        self.reference_voltage = reference_voltage
        self.adc_boards = [ADCDifferentialPi(addr, addr, bit_resolution) for addr in addresses]
        self.current_ref_values = [self.reference_voltage] * len(addresses) # All the same to start with 

    def read_voltage(self, adc_board, port, ref_volt):
        return self.adc_boards[adc_board].read_voltage(port) / ref_volt
        
            
    def calibrate_current(self, num_runs=10):
        # Calculate total over X number of run
        total = [0] * len(self.adc_boards)
        for _ in range(num_runs):
            recent = self.collect_current_data(len(self.adc_boards))
            recent = recent
            for i in range(len(self.adc_boards)):
                total[i] += (recent[i]/10) +2.5
        
        # Calculate mean values for each board
        mean = [x / num_runs for x in total]
        
        
        # Calculate new calibration values
        for i, y in enumerate(mean):
            error = y / 2.5
            new_ref = error * self.reference_voltage
            rounded_ref = round(new_ref, 9)
            self.current_ref_values[i] = rounded_ref
            
        return self.current_ref_values
        

    def collect_voltage_data(self, num_boards=1, port=2):
        if num_boards < 1 or num_boards > 4:
            raise ValueError("Number of ADC boards must be between 1 and 4")

        values = [0] * len(self.adc_boards)

        # Define a function to read voltage data from each ADC board
        def read_voltage_data(board_index, ref_volt):
            voltage = self.read_voltage(board_index, port, ref_volt)
            rounded_voltage = round(voltage, 4)
            values[board_index] = rounded_voltage

        # Create threads to read voltage data from each ADC board
        threads = []
        for i in range(num_boards):
            thread = threading.Thread(target=read_voltage_data, args=(i, self.reference_voltage))
            threads.append(thread)
            thread.start()

        # Wait for all threads to finish
        for thread in threads:
            thread.join()

        return values

    def collect_current_data(self, num_boards=1, port=1):
        if num_boards < 1 or num_boards > 4:
            raise ValueError("Number of ADC boards must be between 1 and 4")

        values = [0] * len(self.adc_boards)

        # Define a function to read current data from each ADC board
        def read_current_data(board_index, ref_volt):
            current = self.read_voltage(board_index, port, ref_volt)
            current = (current-2.5)*10
            # Round the current value to desired precision, for example, 2 decimal places
            rounded_current = round(current, 3)
            values[board_index] = rounded_current

        # Create threads to read current data from each ADC board
        threads = []
        for i in range(num_boards):
            thread = threading.Thread(target=read_current_data, args=(i,self.current_ref_values[i]))
            threads.append(thread)
            thread.start()

        # Wait for all threads to finish
        for thread in threads:
            thread.join()

        return values


if __name__ == "__main__":
    sensor = ElectricalMeasurement(bit_resolution=18)
    print(sensor.current_ref_values)
    sensor.calibrate_current()
    print(sensor.current_ref_values)
    
    num_boards =  1

    while True:
        start_time = time.time()

        # collect data
        collected_datac = sensor.collect_current_data(num_boards)
        collected_datav = sensor.collect_voltage_data(num_boards)
        
        

        end_time = time.time()
        execution_time = end_time - start_time
        print("Execution time:", execution_time, "seconds")
        print("Collected c data:", collected_datac)
        print("Collected v data:", collected_datav)
        time.sleep(1)

