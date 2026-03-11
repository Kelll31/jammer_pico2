"""
Драйвер тачскрина XPT2046 для MicroPython
"""

import time
import _thread
import config
from machine import Pin, SPI
from spi_manager import spi0_manager

# Каналы для измерения
XPT2046_CHANNEL_X = 0x5   # Канал X
XPT2046_CHANNEL_Y = 0x1   # Канал Y
XPT2046_CHANNEL_Z1 = 0x3  # Канал Z1 (для измерения давления)
XPT2046_CHANNEL_Z2 = 0x4  # Канал Z2 (для измерения давления)

class XPT2046:
    """Класс для работы с тачскрином XPT2046"""
    
    def __init__(self,
                 irq_pin=config.TOUCH_IRQ_PIN,
                 spi_freq=2_500_000,  # 2.5 MHz для тачскрина
                 cal_min_x=config.TOUCH_CAL_MIN_X,
                 cal_min_y=config.TOUCH_CAL_MIN_Y,
                 cal_max_x=config.TOUCH_CAL_MAX_X,
                 cal_max_y=config.TOUCH_CAL_MAX_Y,
                 min_flick_ms=10,
                 long_press_ms=500,
                 beta_shft=2):
        
        self.spi_freq = spi_freq

        # Сохранение калибровочной матрицы
        from touch_calibration import CalibrationMat
        self.cmat = CalibrationMat()
        
        # Инициализация пинов
        self.irq = Pin(irq_pin, Pin.IN, Pin.PULL_UP)
        
        # Переменные для фильтрации и IPC
        self.lock = _thread.allocate_lock()
        self.last_x = 0
        self.last_y = 0
        self.xf = 0
        self.yf = 0
        self.last_pressure = 0
        self.last_touch_time = 0
        
        # Параметры фильтра
        self.min_flick_ms = min_flick_ms
        self.long_press_ms = long_press_ms
        self.beta_shft = beta_shft

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
    
    def _read_channel(self, channel, spi):
        """Чтение значения с аналогового канала (внутри лок-контекста)"""
        tx_data = bytearray([0x80 | (channel << 4), 0x00, 0x00])
        rx_data = bytearray(3)
        spi.write_readinto(tx_data, rx_data)
        result = ((rx_data[1] << 8) | rx_data[2]) >> 3
        return result

    def _read_registers(self):
        """Чтение X и Y каналов одновременно в одном SPI локе"""
        with spi0_manager.acquire_touch(self.spi_freq) as spi:
            raw_x = self._read_channel(XPT2046_CHANNEL_X, spi)
            raw_y = self._read_channel(XPT2046_CHANNEL_Y, spi)
            return raw_x, raw_y
    
    def is_touched(self):
        """Проверка состояния прерывания (нажатия)"""
        return self.irq.value() == 0
    
    def get_raw_touch(self):
        """Опрос тачскрина с low-pass фильтрацией (из C кода) без блокирующих задержек"""
        if self.beta_shft > 0:
            if self.is_touched():
                now_ms = time.ticks_ms()

                # Если прошло много времени с последнего касания - сброс фильтра
                if time.ticks_diff(now_ms, self.last_touch_time) > self.long_press_ms:
                    raw_x, raw_y = self._read_registers()
                    self.last_touch_time = now_ms

                    with self.lock:
                        self.last_x = raw_x
                        self.last_y = raw_y
                        self.xf = raw_x << 14
                        self.yf = raw_y << 14
                        self.is_touching = True
                    return raw_x, raw_y, True

                # Иначе, если прошло достаточно времени для нового сэмпла, применяем фильтр
                if time.ticks_diff(now_ms, self.last_touch_time) > self.min_flick_ms:
                    raw_x, raw_y = self._read_registers()
                    self.last_touch_time = now_ms

                    with self.lock:
                        self.last_x = raw_x
                        self.last_y = raw_y

                        self.xf += ((raw_x << 14) - self.xf + (1 << (self.beta_shft - 1))) >> self.beta_shft
                        self.yf += ((raw_y << 14) - self.yf + (1 << (self.beta_shft - 1))) >> self.beta_shft

                        filtered_x = self.xf >> 14
                        filtered_y = self.yf >> 14
                        self.is_touching = True
                    return filtered_x, filtered_y, True

                # Слишком рано для нового сэмпла, возвращаем старое фильтрованное значение
                with self.lock:
                    return self.xf >> 14, self.yf >> 14, True
            else:
                with self.lock:
                    self.is_touching = False
                return None, None, False
        return None, None, False

    def read_touch(self):
        """Обёртка для совместимости с существующим кодом"""
        return self.get_raw_touch()
    
    def convert_to_screen(self, raw_x, raw_y, display_width=None, display_height=None):
        """Преобразование сырых значений в экранные координаты"""
        from touch_calibration import touch_transform_coords

        if display_width is None:
            display_width = config.DISPLAY_WIDTH
        if display_height is None:
            display_height = config.DISPLAY_HEIGHT

        screen_x, screen_y = touch_transform_coords(self.cmat, raw_x, raw_y)
        
        # Ограничение значений
        if screen_x < 0:
            screen_x = 0
        if screen_x >= display_width:
            screen_x = display_width - 1
        if screen_y < 0:
            screen_y = 0
        if screen_y >= display_height:
            screen_y = display_height - 1

        return screen_x, screen_y
    
    def get_touch_coordinates(self, display_width=None, display_height=None):
        """Получить координаты касания в экранных координатах"""
        raw_x, raw_y, valid = self.get_raw_touch()
        
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
            
            # Читаем сырые координаты.
            raw_x, raw_y, valid = self.get_raw_touch()
            # Подождём немного и перечитаем для фильтрации
            time.sleep_ms(100)
            raw_x, raw_y, valid = self.get_raw_touch()
            
            if valid:
                raw_points.append((raw_x, raw_y))
                print(f"  Сырые значения: X={raw_x}, Y={raw_y}")
            
            # Ждём отпускания
            while self.is_touched():
                time.sleep(0.01)
            
            time.sleep(0.5)
        
        from touch_calibration import calculate_calibration_mat
        cmat = calculate_calibration_mat(points, raw_points)
        if cmat is not None:
            self.cmat = cmat
            print(f"Калибровка завершена!")
            return True

        print("Ошибка калибровки.")
        return False
    
    def get_calibration(self):
        """Получить текущую калибровочную матрицу"""
        return self.cmat
    
    def set_calibration(self, cmat_dict):
        """Установить калибровочную матрицу из словаря"""
        if not cmat_dict:
            return

        self.cmat.KX1 = cmat_dict.get('kx1', 0.0)
        self.cmat.KX2 = cmat_dict.get('kx2', 0.0)
        self.cmat.KX3 = cmat_dict.get('kx3', 0.0)
        self.cmat.KY1 = cmat_dict.get('ky1', 0.0)
        self.cmat.KY2 = cmat_dict.get('ky2', 0.0)
        self.cmat.KY3 = cmat_dict.get('ky3', 0.0)
    
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