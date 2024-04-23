import RPi.GPIO as GPIO
import time

class RelayController:
    def __init__(self, all_relay_pins = [20,21,26,19,13], V_pin = 22, switch_pin = 27):
        GPIO.setmode(GPIO.BCM)
        self.all_relay_pins = all_relay_pins
        self.switch_pin = switch_pin
        self.V_pin = V_pin
        GPIO.setup(self.switch_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.V_pin, GPIO.IN)
        time.sleep(0.5)
        for pin in self.all_relay_pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.HIGH)
            time.sleep(0.5)


    def operate_relays_on(self, relay_pins):
        for pin in relay_pins:
            GPIO.output(pin, GPIO.LOW)
            print(f"Relay {pin} is On")

    def operate_relays_off(self, relay_pins):
        for pin in relay_pins:
            GPIO.output(pin, GPIO.HIGH)
            print(f"Relay {pin} is Off")     
            
    def get_pins_by_indices(self, indices):
        selected_pins = []
        for idx in range(indices[0], indices[1] + 1):
            selected_pins.append(self.all_relay_pins[idx])
        return selected_pins   
        
    def read_switch_state(self):
        switch_state = GPIO.input(self.switch_pin)
        if switch_state == GPIO.LOW:
            return True # Lid is closed
        else:
            return False # Lid is open
    
    def check_12v_status(self):
        if GPIO.input(self.V_pin) == True:
             return True  # 12V supply is on
        else:
             return False  # 12V supply is off
            
    def cleanup(self):
        GPIO.cleanup()
        print("Bye")

# Usage
if __name__ == "__main__":
   
    all_pins = [20,21,26,19,13]
    v_pin = 12
    switch_pin = 27
    relay_controller = RelayController(all_pins, v_pin, switch_pin)
    i = 0
    
    while i < 10:
        
     if relay_controller.check_12v_status():
          print('true')
     else:
          print('false')
     
     i += 1
        
        
         
        
    
    relay_controller.cleanup()



