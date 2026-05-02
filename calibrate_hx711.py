import os

from JoyIT_hx711py import HX711


def load_env(path='.env'):
    if not os.path.exists(path):
        return

    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def env_int(name, default):
    value = os.getenv(name)
    if value is None or value == '':
        return int(default)
    return int(value)


def main():
    load_env()

    dout = env_int('FEEDER_HX711_DOUT', 5)
    sck = env_int('FEEDER_HX711_SCK', 6)
    gain = env_int('FEEDER_HX711_GAIN', 128)

    hx = HX711(dout, sck, gain=gain)

    print('Калибровка HX711 (JoyIT_hx711py)')
    input('Убери всё с весов и нажми Enter... ')
    offset = hx.read_average()
    hx.set_offset(offset)
    print(f'OFFSET = {offset}')

    input('Поставь известный груз и нажми Enter... ')
    measured = hx.read_average() - hx.get_offset()
    known_weight = float(input('Введите вес груза в граммах: ').replace(',', '.'))
    scale = measured / known_weight
    hx.set_scale(scale)

    print(f'SCALE = {scale}')
    print('\nДобавь в .env:')
    print(f'FEEDER_HX711_OFFSET={offset}')
    print(f'FEEDER_HX711_SCALE={scale}')

    print('\nПроверка. Ctrl+C для выхода.')
    while True:
        grams = hx.get_grams()
        print(f'{grams:.1f} g')
        hx.power_down()
        hx.power_up()


if __name__ == '__main__':
    main()
