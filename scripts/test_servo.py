from gpiozero import Servo
from time import sleep

servo = Servo(18)

servo.value = 0.5
sleep(2)

servo.value = -0.5
sleep(2)

servo.value = 0