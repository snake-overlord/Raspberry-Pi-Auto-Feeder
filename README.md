# Raspberry Pi Pet Feeder

Автокормушка на Raspberry Pi с:
- FSM на `transitions`
- расписанием кормления
- Telegram-командами и уведомлениями
- логированием
- HX711 для веса миски
- VL53L0X для контроля корма в бункере
- сервоприводом для выдачи корма

## Что умеет
- выдавать обычную порцию по расписанию
- выдавать корм до нужного веса через Telegram (`/feed 40`)
- проверять, есть ли миска на месте
- проверять уровень корма в бункере
- делать повторную попытку при неудачной выдаче
- логировать работу и ошибки

## Команды Telegram
- `/feed` — выдать обычную порцию
- `/feed 40` — выдать корм до 40 г
- `/status` — показать текущее состояние
- `/reset` — сбросить ошибку
- `/calibrate` — откалибровать пустую миску
- `/daily` — показать статистику за день
- `/help` — список команд

## Установка
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Настройка
1. Скопируй `.env.example` в `.env`
2. Заполни токен бота и `chat_id`
3. Для HX711 через `JoyIT_hx711py` заполни в `.env`:
   - `FEEDER_HX711_DOUT`
   - `FEEDER_HX711_SCK`
   - `FEEDER_HX711_GAIN`
   - `FEEDER_HX711_OFFSET`
   - `FEEDER_HX711_SCALE`

## Калибровка HX711
В проект уже встроена библиотека `JoyIT_hx711py`. Запуск калибровки:

```bash
python3 calibrate_hx711.py
```


## Запуск
```bash
python3 main.py
```

## Тесты
```bash
python3 -m pytest -q tests
```
