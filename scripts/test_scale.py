from JoyIT_hx711py import HX711
from time import sleep

hx = HX711(5, 6)
hx.set_offset(8489864)
while True:
    print(hx.get_grams())
    sleep(1)
