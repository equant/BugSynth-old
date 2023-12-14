import os
#import my14seg
import mytft

import utime as time
from machine import I2C, Pin, RTC
from ht16k33segment14 import HT16K33Segment14

i2c = I2C(0, scl=Pin(9), sda=Pin(8))    # Raspberry Pi Pico
display = HT16K33Segment14(i2c, is_ht16k33=True)
display.set_brightness(2)
display.clear()

display.set_character("B", 0, True)
display.set_character("U", 1, True)
display.set_character("G", 2, True)
display.set_character("S", 3, True)
display.draw()
time.sleep(2)

images = os.listdir("images")

for image in images:

    try:
        display.set_character("X", 0, True)
        display.set_character("O", 1, True)
        display.set_character("X", 2, True)
        display.set_character("O", 3, True)
        display.draw()
    except:
        print("Can't do 14 segment")
    time.sleep(1)

    try:
        mytft.display_bitmap("images/" + image)
    except Exception as e:
        print("Can't do ttl")
        print(e)
    time.sleep(1)

    try:
        display.set_character(image[0], 0, True)
        display.set_character(image[1], 1, True)
        display.set_character(image[2], 2, True)
        display.set_character(image[3], 3, True)
        display.draw()
    except:
        print("Cnad do too")
    time.sleep(1)
