# IMPORTS
import utime as time
from machine import I2C, Pin, RTC
from ht16k33segment14 import HT16K33Segment14

# CONSTANTS
DELAY = 0.01
PAUSE = 3

i2c = I2C(0, scl=Pin(9), sda=Pin(8))    # Raspberry Pi Pico
#i2c = I2C(0, scl=Pin(5), sda=Pin(4))    # Adafruit Feather Huzzah ESP8256
#i2c = I2C(0, scl=Pin(17), sda=Pin(16))  # SparkFun ProMicro 2040
#i2c = I2C(1, scl=Pin(23), sda=Pin(22))  # Adafruit QTPy RP2040
    
display = HT16K33Segment14(i2c, is_ht16k33=True)
display.set_brightness(2)
display.clear()

point_state = True

display.set_character("B", 0, point_state)
display.set_character("U", 1, point_state)
display.set_character("G", 2, point_state)
display.set_character("S", 3, point_state)
display.draw()
time.sleep(3)
display.set_character("S", 0, point_state)
display.set_character("G", 1, point_state)
display.set_character("B", 2, point_state)
display.set_character("U", 3, point_state)
display.draw()

def show_string2(foo):
    print(f"HERE2: {foo}")
    foo = "FOFOFO"
    display.set_character(foo[0], 0, False)
    display.set_character("Z", 1, False)
    display.set_character("Z", 2, False)
    display.set_character("Z", 3, False)
    display.draw()

def show_string(foo):
    print(f"HERE: {foo}")
    display.set_character(foo[0], 0, False)
    display.set_character("R", 1, False)
    display.set_character("R", 2, False)
    display.set_character("R", 3, False)
    display.draw()
