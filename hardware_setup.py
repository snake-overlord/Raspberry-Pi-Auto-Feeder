import os

def create_servo():
    from gpiozero import Servo

    pin = int(os.getenv('FEEDER_SERVO_PIN', '18'))
    min_pw = float(os.getenv('FEEDER_SERVO_MIN_PW', '0.0005'))
    max_pw = float(os.getenv('FEEDER_SERVO_MAX_PW', '0.0025'))

    servo = Servo(pin, min_pulse_width=min_pw, max_pulse_width=max_pw)
    servo.value = 0
    return servo


def create_distance_sensor():
    import board
    import busio
    import adafruit_vl53l0x

    i2c = busio.I2C(board.SCL, board.SDA)
    return adafruit_vl53l0x.VL53L0X(i2c)


def create_weight_sensor():
    from JoyIT_hx711py import HX711

    dout = int(os.getenv('FEEDER_HX711_DOUT', '5'))
    sck = int(os.getenv('FEEDER_HX711_SCK', '6'))
    gain = int(os.getenv('FEEDER_HX711_GAIN', '128'))

    hx = HX711(dout, sck, gain=gain)

    offset = os.getenv('FEEDER_HX711_OFFSET')
    scale = os.getenv('FEEDER_HX711_SCALE')

    if offset not in (None, ''):
        hx.set_offset(float(offset))

    if scale not in (None, ''):
        hx.set_scale(float(scale))

    return hx
