"""
Драйвер тачскрина XPT2046 для MicroPython
"""

import time
import config
from machine import Pin, SPI

# Каналы для измерения
XPT2046_CHANNEL_X = 0x5   # Канал X
XPT2046_CHANNEL_Y = 0x1   # Канал Y
XPT2046_CHANNEL_Z1 = 0x3  # Канал Z1 (для измерения давления)
XPT2046_CHANNEL_Z2 = 0x4  # Канал Z2 (для измерения давления)

class XPT2046:
    """Класс для работы с тачскрином XPT2046"""
    
    def __init__(self, spi_id=config.DISPLAY_SPI_ID,
                 cs_pin=config.TOUCH_CS_PIN,
                 irq_pin=config.TOUCH_IRQ_PIN,
                 sck_pin=config.DISPLAY_SCK_PIN,
                 mosi_pin=config.DISPLAY_MOSI_PIN,
                 miso_pin=config.DISPLAY_MISO_PIN,
                 spi_freq=2_500_000,  # 2.5 MHz для тачскрина
                 cal_min_x=config.TOUCH_CAL_MIN_X,
                 cal_min_y=config.TOUCH_CAL_MIN_Y,
                 cal_max_x=config.TOUCH_CAL_MAX_X,
                 cal_max_y=config.TOUCH_CAL_MAX_Y):
        
        # Сохранение калибровочных коэффициентов
        self.cal_min_x = cal_min_x
        self.cal_min_y = cal_min_y
        self.cal_max_x = cal_max_x
        self.cal_max_y = cal_max_y
        
        # Инициализация пинов
        self.cs = Pin(cs_pin, Pin.OUT, value=1)
        self.irq = Pin(irq_pin, Pin.IN, Pin.PULL_UP)
        
        # Инициализация SPI для тачскрина (более низкая частота)
        self.spi = SPI(spi_id, baudrate=spi_freq,
                      sck=Pin(sck_pin), mosi=Pin(mosi_pin), miso=Pin(miso_pin))
        
        # Переменные для фильтрации
        self.last_x = 0
        self.last_y = 0
        self.last_pressure = 0
        self.last_touch_time = 0
        
        # Флаг касания
        self.is_touching = False
        
        # Проверка доступности чипа
        if not self._check_presence():
            print("WARNING: Touch screen XPT2046 not detected!")
    
    def _check_presence(self):
        """Проверка наличия чипа XPT2046"""
        try:
            # Пробуем прочитать значение канала X
            value = self._read_channel(XPT2046_CHANNEL_X)
            return value != 0 and value != 0xFFF
        except:
            return False
    
    def _read_channel(self, channel):
        """Чтение значения с аналогового канала"""
        # Команда: старший бит = 1 (начало), следующие 3 бита = канал
        tx_data = bytearray([0x80 | (channel << 4), 0x00, 0x00])
        rx_data = bytearray(3)
        
        # Выбор чипа
        self.cs.value(0)
        
        # Отправка команды и чтение результата
        self.spi.write_readinto(tx_data, rx_data)
        
        # Снятие выбора чипа
        self.cs.value(1)
        
        # Объединение результатов (12 бит)
        result = ((rx_data[1] << 8) | rx_data[2]) >> 3
        return result
    
    def is_touched(self):
        """Проверка состояния прерывания (нажатия)"""
        # Пин IRQ уходит в 0 (LOW), когда происходит касание
        return self.irq.value() == 0
    
    def read_touch(self, num_samples=5):
        """Чтение координат касания с усреднением"""
        if not self.is_touched():
            return None, None, False
        
        sum_x = 0
        sum_y = 0
        valid_samples = 0
        
        for i in range(num_samples):
            raw_x = self._read_channel(XPT2046_CHANNEL_X)
            raw_y = self._read_channel(XPT2046_CHANNEL_Y)
            
            # Проверка достоверности значений
            if (raw_x != 0x000 and raw_x != 0xFFF and 
                raw_y != 0x000 and raw_y != 0xFFF):
                sum_x += raw_x
                sum_y += raw_y
                valid_samples += 1
            
            # Небольшая задержка между измерениями
            time.sleep_us(100)
        
        if valid_samples > 0:
            avg_x = sum_x // valid_samples
            avg_y = sum_y // valid_samples
            
            # Сохраняем последние значения
            self.last_x = avg_x
            self.last_y = avg_y
            self.last_touch_time = time.ticks_ms()
            self.is_touching = True
            
            return avg_x, avg_y, True
        
        return None, None, False
    
    def read_pressure(self):
        """Чтение давления (Z-ось)"""
        z1 = self._read_channel(XPT2046_CHANNEL_Z1)
        z2 = self._read_channel(XPT2046_CHANNEL_Z2)
        
        # Расчет давления по формуле Z = (z2 - z1) / z1
        if z1 != 0:
            pressure = (z2 - z1) * 0x1000 // z1
            self.last_pressure = pressure
            return pressure
        
        return 0
    
    def convert_to_screen(self, raw_x, raw_y, display_width=None, display_height=None):
        """Преобразование сырых значений в экранные координаты"""
        if display_width is None:
            display_width = config.DISPLAY_WIDTH
        if display_height is None:
            display_height = config.DISPLAY_HEIGHT
        
        # Применение калибровочных коэффициентов
        if (self.cal_max_x - self.cal_min_x) == 0 or (self.cal_max_y - self.cal_min_y) == 0:
            # Избегаем деления на ноль
            return 0, 0
        
        screen_x = ((raw_x - self.cal_min_x) * display_width) // (self.cal_max_x - self.cal_min_x)
        screen_y = ((raw_y - self.cal_min_y) * display_height) // (self.cal_max_y - self.cal_min_y)
        
        # Ограничение значений
        if screen_x < 0:
            screen_x = 0
        if screen_x >= display_width:
            screen_x = display_width - 1
        if screen_y < 0:
            screen_y = 0
        if screen_y >= display_height:
            screen_y = display_height - 1
        
        # Инверсия оси Y (если нужно)
        screen_y = display_height - screen_y - 1
        
        return screen_x, screen_y
    
    def get_touch_coordinates(self, display_width=None, display_height=None):
        """Получить координаты касания в экранных координатах"""
        raw_x, raw_y, valid = self.read_touch()
        
        if not valid:
            return None, None, False
        
        screen_x, screen_y = self.convert_to_screen(raw_x, raw_y, display_width, display_height)
        return screen_x, screen_y, True
    
    def calibrate(self, points=None):
        """
        Калибровка тачскрина
        
        points: список из 4 точек [(x1, y1), (x2, y2), (x3, y3), (x4, y4)]
                где x,y - экранные координаты для калибровки
        """
        if points is None:
            # Точки по умолчанию: углы экрана
            points = [
                (50, 50),                    # Левый верхний
                (config.DISPLAY_WIDTH - 50, 50),      # Правый верхний
                (config.DISPLAY_WIDTH - 50, config.DISPLAY_HEIGHT - 50),  # Правый нижний
                (50, config.DISPLAY_HEIGHT - 50)      # Левый нижний
            ]
        
        print("Калибровка тачскрина. Касайтесь указанных точек...")
        
        raw_points = []
        
        for i, (screen_x, screen_y) in enumerate(points):
            print(f"Точка {i+1}: коснитесь ({screen_x}, {screen_y})")
            
            # Ждём касания
            while not self.is_touched():
                time.sleep(0.01)
            
            # Читаем сырые координаты
            raw_x, raw_y, valid = self.read_touch(num_samples=10)
            
            if valid:
                raw_points.append((raw_x, raw_y))
                print(f"  Сырые значения: X={raw_x}, Y={raw_y}")
            
            # Ждём отпускания
            while self.is_touched():
                time.sleep(0.01)
            
            time.sleep(0.5)
        
        if len(raw_points) >= 2:
            # Простая калибровка: находим min/max
            raw_x_values = [p[0] for p in raw_points]
            raw_y_values = [p[1] for p in raw_points]
            
            self.cal_min_x = min(raw_x_values)
            self.cal_max_x = max(raw_x_values)
            self.cal_min_y = min(raw_y_values)
            self.cal_max_y = max(raw_y_values)
            
            print(f"Калибровка завершена:")
            print(f"  X: {self.cal_min_x} - {self.cal_max_x}")
            print(f"  Y: {self.cal_min_y} - {self.cal_max_y}")
            
            return True
        
        return False
    
    def get_calibration(self):
        """Получить текущие калибровочные коэффициенты"""
        return {
            'min_x': self.cal_min_x,
            'max_x': self.cal_max_x,
            'min_y': self.cal_min_y,
            'max_y': self.cal_max_y
        }
    
    def set_calibration(self, min_x, max_x, min_y, max_y):
        """Установить калибровочные коэффициенты"""
        self.cal_min_x = min_x
        self.cal_max_x = max_x
        self.cal_min_y = min_y
        self.cal_max_y = max_y
    
    def is_touch_held(self, threshold_ms=1000):
        """Проверка, удерживается ли касание"""
        if not self.is_touching:
            return False
        
        current_time = time.ticks_ms()
        return (current_time - self.last_touch_time) < threshold_ms
    
    def reset_touch_state(self):
        """Сбросить состояние касания"""
        self.is_touching = False
        self.last_touch_time = 0