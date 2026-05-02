from time import sleep

from gpiozero import Servo
import board
import busio
import adafruit_vl53l0x

from hardware.hx711_driver import HX711Driver
from hardware.servo_driver import ServoDriver
from hardware.vl53_driver import DistanceSensor

from domain.bowl import Bowl
from domain.hopper import Hopper
from domain.dispenser import Dispenser

from fsm.feeder_fsm import FeederFSM

from JoyIT_hx711py import HX711

servo_hw = Servo(18)
servo = ServoDriver(servo_hw)

i2c = busio.I2C(board.SCL, board.SDA)
vl53 = adafruit_vl53l0x.VL53L0X(i2c)
distance = DistanceSensor(vl53)
distance.set_offset(70)


hx = HX711(5, 6)
scale_hw = hx 
scale = HX711Driver(scale_hw)

scale.set_scale(5.3)
scale.set_offset(8489863)


bowl = Bowl(scale)
hopper = Hopper(distance)

dispenser = Dispenser(servo, bowl)



fsm = FeederFSM(bowl, hopper, dispenser, telegram=None)

fsm.start()


while True:
    print("\nSTATUS")
    print("Weight:", bowl.total_weight())
    print("Food:", bowl.food_weight())
    print("Empty:", bowl.is_empty())
    print("Hopper low:", hopper.low_food())

    cmd = input("\n[f] feed, [q] quit: ")

    if cmd == "f":
        fsm.feed_request()

    elif cmd == "q":
        break

    sleep(1)