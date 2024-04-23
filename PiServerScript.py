import socket 
import time
import json
import board
import subprocess
from ElecClass import ElectricalMeasurement
from TempClass import ThermocoupleMeasurement
from RelayClass import RelayController
from CSVClass import CSVWriter

# Safety Functions

def voltage_safety(data, threshold):
    safe = False
	# Loop through the specified range of indices to check saftey conditions 
    for index, v in enumerate(data):
        if index > threshold:
            if v == 0:
                safe = True
            elif v != 0:
                safe = False
        else:
            if v > 0.1: #---------------------------------------------------------------Slight Buffer
                safe = True
            elif v <= 0.1:
                safe = False
                    
        # Check if V_safe is False, if so, break out of the loop
        if not safe:
            break
                
    return safe  
    
    
def voltagediff_safety(data, threshold):
    safe = False
	# Initialize variables to track the maximum and minimum voltage within the range
    max_voltage = data[0]
    min_voltage = data[0]

    # Loop through the specified range of indices
    for index, v in enumerate(data):
        if index > threshold:
            break  # Break out of the loop if the index exceeds the threshold
        if v > max_voltage:
            max_voltage = v  # Update max_voltage if v is greater
        elif v < min_voltage:
            min_voltage = v  # Update min_voltage if v is smaller

	# Calculate the maximum voltage difference
    max_difference = max_voltage - min_voltage
    print(max_voltage)
    print(min_voltage)
        
    if max_difference <= 0.05: #--------------------------------------------------------<--update
        safe = True
    else:
        safe = False
        
    return safe
    

def temp_safety(data, threshold, limit):
    safe = False 
	# Loop through the specified range of indices to check saftey conditions 
    for index, t in enumerate(data):
        if index <= threshold:
            if t < limit:
                safe = True
            elif t >= limit:
                safe = False
        # Check if V_safe is False, if so, break out of the loop
        if not safe:
            break
     
    return safe   
    

def lid_safety():
    safe = False
    if relay.read_switch_state():
        safe = True
    else:
        safe = False 
        
    return safe 
    
    
def supply_safety():
    safe = False
    if relay.check_12v_status():
        safe = True
    else:
        safe = False  
    
    return safe 
               

def check_safety_status(V_safe, V_diff_safe, T_safe, L_safe, S_safe):
    unsafe_variables = []

    if not V_safe:
        unsafe_variables.append("Battery Connections")
    if not V_diff_safe:
        unsafe_variables.append("Voltage differences")
    if not T_safe:
        unsafe_variables.append("Battery Temperature")
    if not L_safe:
        unsafe_variables.append("Box Lid Open")
    if not S_safe:
        unsafe_variables.append("No 12V Supply")

    return unsafe_variables
    

def set_bit_rate(ts): #-------------------------------------------------------------------update bands after testing
    if ts < 0.055:
        ADC = ElectricalMeasurement(bit_resolution=12)
        print('12')
    
    elif ts < 0.155:
        ADC = ElectricalMeasurement(bit_resolution=14)
        print('14')
    elif ts < 0.655:
        ADC = ElectricalMeasurement(bit_resolution=16)
        print('16')
    else:
        ADC = ElectricalMeasurement(bit_resolution=18)
    
    return ADC
		
    
def operate_battery_relays(count): 
    if count == 1 :
        relay.operate_relays_on([21])
    elif count == 2 :
        relay.operate_relays_on([21,26])
    elif count == 3 :
        relay.operate_relays_on([21,26,19])
    else:
        relay.operate_relays_on([21,26,19,13])
        
    
# Obtain IP adress
def get_ip_address(interface='wlan0'):
	while True:
		try:
			output = subprocess.check_output(['ifconfig',interface]).decode('utf-8')	
			ip_line = [line for line in output.split('\n') if line][1]
			ip_address = ip_line.split()[1]
			break 
			
		except Exception as e:
			print("ERROR:",e)
			time.sleep(3)
	
	return ip_address	

# Instantiate Classes
#ADC = ElectricalMeasurement(bit_resolution=18)
ADA = ThermocoupleMeasurement(pins=[board.D25, board.D24, board.D23, board.D18], cal_vals=[-1.090, -0.851, -1.221, -1.403])
csv_writer = CSVWriter(folder_path="/home/gip-pi/Documents/TestData")
relay = RelayController([20,21,26,19,13], 22, 27)

bufferSize = 1048576
ServerIP = get_ip_address()
ServerPort = 2222
RPIServer = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
RPIServer.bind((ServerIP,ServerPort))

cmd = None
System_Safe = False
Started = False

print('Server Up and Listening...')

# Set a timeout of 0.001 seconds (10 milliseconds)
RPIServer.settimeout(0.01) #-----------------------------update

while True:
	# Check for new Command
    c_time = time.time()
    try:
        cmd, address = RPIServer.recvfrom(bufferSize)
        cmd = cmd.decode('utf-8')
        print('Client Command & Address:', cmd,  address[0])
        
    except socket.timeout:
        #print("Timeout occurred while receiving data. Retrying...", cmd)
        pass
        
    # Carry Out command
    if cmd == 'Start' and System_Safe:

        if not Started:
           
            threshold_index = num_boards -1   # Set to number of batteries
            temp_limit = safety_temp
            
            RPIServer.settimeout(10)
            while True:
                data = 'CSV'
                data = data.encode('utf-8')
                RPIServer.sendto(data, address)
                
                time.sleep(1)
                
                start_run_time = time.time()
                
                data = f'{start_run_time}'
                data = data.encode('utf-8')
                RPIServer.sendto(data, address)
                
				
                try:
					# Receive data from the server
                    csv_cmd, _ = RPIServer.recvfrom(bufferSize)
                    csv_cmd = csv_cmd.decode('utf-8')
					
                    if csv_cmd == 'Done':
                         break

                except Exception as e:
                    print("Unexpected error:", e)
				
            RPIServer.settimeout(0.01)
			
			# Set up CSV file 
            inputs = [num_boards,time_step,safety_temp,run_time,start_run_time]
            csv_header = csv_writer.generate_headers(inputs)
            csv_writer.write_data(csv_header)
            
            # Initialize a list to store the collected data
            accumulated_json_data = []
            accumulated_csv_data =[]
            
            # CLose Relays 
            operate_battery_relays(num_boards)
            time.sleep(5)
            relay.operate_relays_on([20]) 
            time.sleep(1)
            
            Started = True
            period_time = 3.3  # Activates temptreture readings on first loop round
        
        #---------------------------Main Loop---------------------------
        
        # Start Loop Time    
        start_time = time.time() 
        
        # Ensure the test only runs for a desired amount of time    
        end_run_time = time.time()    
        total_run_time = end_run_time - start_run_time     
        if run_time != -1:
            if total_run_time >= run_time:
                cmd = 'Stop' 
           
        if Started:
			
            s_time = time.time()
            collected_v_data = ADC.collect_voltage_data(4) # collect voltage data
            collected_c_data = ADC.collect_current_data(4) # collect current data
            e_time = time.time()
            exe_time = e_time - s_time
            print(exe_time)
            
            # Safety Checks - at least every time step/ 3 sec
            if (start_time - period_time) >= 3:
				
                period_time = time.time()
                collected_t_data = ADA.collect_data(num_boards) # collect tempreture data
                
				# Step 1: Check Voltage is not negative and/or 0
                V_safe = voltage_safety(collected_v_data, threshold_index)

                # Step 2: Check Voltage diffrence 
                V_diff_safe = voltagediff_safety(collected_v_data, threshold_index)        

                # Step 3: Check safe tempretures for battreies connected 
                T_safe = temp_safety(collected_t_data, threshold_index, temp_limit)
 
                # Step 4: Check if box lid is shut 
                L_safe = lid_safety()
        
		        # Step 5: Check there is a 12V supply  
                S_safe = supply_safety()
            
                # Step 6: Check if all systems are safe 
                unsafe_vars = check_safety_status(V_safe, V_diff_safe, T_safe, L_safe, S_safe)
                
                if unsafe_vars:
                    print("The following safety variables are not safe:", unsafe_vars)
                    System_Safe = False
                else:
                    print("System is safe")
                    System_Safe = True
                    
                 
                
            # Combine the collected data into rows of voltage, current, and temperature
            collected_data = collected_v_data[:num_boards] + collected_c_data[:num_boards] + collected_t_data + [total_run_time]
            
            accumulated_json_data.append(collected_data)
            accumulated_csv_data.append(collected_data)
			
            # Check the length of the accumulated csv data list
            if len(accumulated_csv_data) >= 10:
                print("csv")
                # Write accumulated data to CSV file
                try:
                    csv_writer.write_data(accumulated_csv_data[:10])  # Write first 100 rows
         
                    # Clear the first 100 rows from the accumulated data list
                    accumulated_csv_data = accumulated_csv_data[10:]
                    
                except Exception as e:
                    print("Error writing data to CSV file:", e)
                
                
			    # Check the length of the accumulated json data list
                if len(accumulated_json_data) >= 100:
 				    # Write accumulated data to JSON               
                    try:
                        Json_to_send = csv_writer.generate_json(num_boards,accumulated_json_data[:100]) 
                        data_to_send = Json_to_send.encode('utf-8')
                        RPIServer.sendto(data_to_send, address)
					
                        # Clear the first 100 rows from the accumulated data list
                        accumulated_json_data = accumulated_json_data[100:]
                    
                    except Exception as e:
                        print("Error sending data to server:", e)
		
		
		# Ensure consistent time stepping
        execution_time = time.time()  - start_time  # Execution time in nanaoseconds
		
        while execution_time < time_step: 
            execution_time = time.time()  - start_time  # Execution time in nanoseconds
         
          
    elif cmd == 'Start' and not System_Safe:
        data = "Unsafe"
        data = data.encode('utf-8')
        RPIServer.sendto(data, address)
        cmd = 'Stop'
        

    elif cmd == 'Stop':
		#Open Relays
        relay.operate_relays_off([20,21,26,19,13]) # make sure all relyas are open 

        Started = False
        System_Safe = False
        data = 'Stopped'
        data = data.encode('utf-8')
        RPIServer.sendto(data, address)
        
        # Save left over data 
        # Write accumulated data to CSV file if there is data
        if accumulated_csv_data:
            try:
                csv_writer.write_data(accumulated_csv_data)  
        
				# Clear the rows from the accumulated data list
                accumulated_csv_data = []
            except Exception as e:
                print("Error writing data to CSV file:", e)

           
        # Write accumulated data to JSON
        if accumulated_json_data:
            num_entries_to_send = min(100, len(accumulated_json_data))  # Determine how many entries to send
            Json_to_send = csv_writer.generate_json(num_boards, accumulated_json_data[:num_entries_to_send]) 
            try:
                data_to_send = Json_to_send.encode('utf-8')
                RPIServer.sendto(data_to_send, address)
        
                # Clear the sent entries from the accumulated data list
                accumulated_json_data = accumulated_json_data[num_entries_to_send:]
                
            except Exception as e:
               print("Error sending data to server:", e)

        
         
    elif cmd == 'Setup':
        # Wait for JSON array
        json_data_received = False
        RPIServer.settimeout(1)
        
        while not json_data_received:
            try:
                # Receive data from the socket
                received_data, address = RPIServer.recvfrom(bufferSize)
                json_data = received_data.decode('utf-8')
                setup_data = json.loads(json_data)
                print('Received JSON data:', setup_data)
                
                # Assign JSON data to variables
                if 'batteries' in setup_data:
                    num_boards = int(setup_data['batteries'])
                
                if 'runtime' in setup_data:
                    run_time = int(setup_data['runtime'])
                    
                if 'time_step' in setup_data:
                    time_step = float(setup_data['time_step']) 
                
                if 'safety_temp' in setup_data:
                    safety_temp = int(setup_data['safety_temp'])
                    
                # Set bit rate for measuring based on timestep 
                ADC = set_bit_rate(time_step) 
                
                # Callibrates the current during setup 
                ADC.calibrate_current()
                
                data = 'Ready'
                data = data.encode('utf-8')
                RPIServer.sendto(data, address)

                RPIServer.settimeout(0.01)
                cmd = None
                json_data_received = True
                
            except json.JSONDecodeError:
                data = 'Not Ready'
                data = data.encode('utf-8')
                RPIServer.sendto(data, address)
                print('Invalid JSON data received. Waiting for valid JSON array.')
 
                
    elif cmd == 'Safety':
		# Assume it is not safe at the start 
        V_safe = False 		        # Voltages are correct
        V_diff_safe = False  		# VOltage diff isnt to big
        T_safe = False 				# Tempretures are safe
        L_safe = False 				# Lid of the box is closed
        S_safe = False 				# 12v Supply is on 
        
        System_Safe = False 		# All Systems are safe 
        
        v_safety_data = ADC.collect_voltage_data(4)  # Read Voltage on all boards
        threshold_index = num_boards - 1   # Set to number of batteries
        
        t_safety_data = ADA.collect_data(num_boards)
        temp_limit = safety_temp
        
        # Step 1: Check Voltage is not negative and/or 0
        V_safe = voltage_safety(v_safety_data, threshold_index)

        # Step 2: Check Voltage diffrence 
        V_diff_safe = voltagediff_safety(v_safety_data, threshold_index)        
   
        # Step 3: Check safe tempretures for battreies connected 
        T_safe = temp_safety(t_safety_data, threshold_index, temp_limit)
 
        # Step 4: Check if box lid is shut 
        L_safe = lid_safety()
        
		
		# Step 5: Check there is a 12V supply  
        S_safe = supply_safety()
            
        # Step 6: Check if all systems are safe 
        unsafe_vars = check_safety_status(V_safe, V_diff_safe, T_safe, L_safe, S_safe)
        
        
        if unsafe_vars:
            print("The following safety variables are not safe:", unsafe_vars)
            System_Safe = False
        else:
            System_Safe = True
        
        # Convert boolean to string
        if System_Safe:
            data = "System Safe"
            data = data.encode('utf-8')
            RPIServer.sendto(data, address)
            #cmd = None
        else:
            data = unsafe_vars
            list_as_string = str(data)
            data = list_as_string.encode('utf-8')
            RPIServer.sendto(data, address)
        



				 
            
            
		















