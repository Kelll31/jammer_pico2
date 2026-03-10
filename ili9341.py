"""
Драйвер дисплея ILI9341 для MicroPython
С поддержкой двойной буферизации
"""

import time
import framebuf
import config
from machine import Pin, SPI

# Регистры ILI9341
ILI9341_NOP = 0x00
ILI9341_SWRESET = 0x01
ILI9341_RDDID = 0x04
ILI9341_RDDST = 0x09
ILI9341_SLPIN = 0x10
ILI9341_SLPOUT = 0x11
ILI9341_PTLON = 0x12
ILI9341_NORON = 0x13
ILI9341_INVOFF = 0x20
ILI9341_INVON = 0x21
ILI9341_DISPOFF = 0x28
ILI9341_DISPON = 0x29
ILI9341_CASET = 0x2A
ILI9341_RASET = 0x2B
ILI9341_RAMWR = 0x2C
ILI9341_RAMRD = 0x2E
ILI9341_PTLAR = 0x30
ILI9341_COLMOD = 0x3A
ILI9341_MADCTL = 0x36
ILI9341_MADCTL_MY = 0x80
ILI9341_MADCTL_MX = 0x40
ILI9341_MADCTL_MV = 0x20
ILI9341_MADCTL_ML = 0x10
ILI9341_MADCTL_RGB = 0x00
ILI9341_MADCTL_BGR = 0x08
ILI9341_PIXFMT = 0x3A
ILI9341_FRMCTR1 = 0xB1
ILI9341_DFUNCTR = 0xB6
ILI9341_GAMMASET = 0xF2
ILI9341_GMCTRP1 = 0xE0
ILI9341_GMCTRN1 = 0xE1

class ILI9341:
    """Класс для работы с дисплеем ILI9341 с двойной буферизацией"""
    
    def __init__(self, spi_id=config.DISPLAY_SPI_ID, 
                 dc_pin=config.DISPLAY_DC_PIN,
                 rst_pin=config.DISPLAY_RST_PIN,
                 cs_pin=config.DISPLAY_CS_PIN,
                 blk_pin=config.DISPLAY_BLK_PIN,
                 sck_pin=config.DISPLAY_SCK_PIN,
                 mosi_pin=config.DISPLAY_MOSI_PIN,
                 width=config.DISPLAY_WIDTH,
                 height=config.DISPLAY_HEIGHT,
                 spi_freq=config.DISPLAY_SPI_FREQ):
        
        self.width = width
        self.height = height
        self.rotation = 0
        
        # Инициализация пинов
        self.dc = Pin(dc_pin, Pin.OUT, value=1)
        self.rst = Pin(rst_pin, Pin.OUT, value=1)
        self.cs = Pin(cs_pin, Pin.OUT, value=1)
        self.blk = Pin(blk_pin, Pin.OUT, value=0)
        
        # Инициализация SPI
        self.spi = SPI(spi_id, baudrate=spi_freq, 
                      sck=Pin(sck_pin), mosi=Pin(mosi_pin))
        
        # Двойная буферизация: создаем два буфера
        self.buffer_size = width * height * 2  # 2 байта на пиксель (RGB565)
        self.buffer1 = bytearray(self.buffer_size)
        self.buffer2 = bytearray(self.buffer_size)
        
        # Текущий активный буфер для рисования
        self.active_buffer = self.buffer1
        # Буфер для отображения
        self.display_buffer = self.buffer2
        
        # Framebuffer для работы с графикой
        self.fb = framebuf.FrameBuffer(self.active_buffer, width, height, framebuf.RGB565)
        
        # Кэширование последней позиции для оптимизации
        self.last_x = 0xFFFF
        self.last_y = 0xFFFF
        
        # Инициализация дисплея
        self._init_display()
        
        # Включение подсветки
        self.set_backlight(100)
        
        # Очистка экрана
        self.fill_screen(config.COLOR_BLACK)
        self.swap_buffers()
    
    def _write_command(self, cmd):
        """Запись команды в дисплей"""
        self.dc.value(0)
        self.cs.value(0)
        self.spi.write(bytearray([cmd]))
        self.cs.value(1)
    
    def _write_data(self, data):
        """Запись данных в дисплей"""
        self.dc.value(1)
        self.cs.value(0)
        if isinstance(data, int):
            self.spi.write(bytearray([data]))
        else:
            self.spi.write(data)
        self.cs.value(1)
    
    def _write_data_buffer(self, data):
        """Запись буфера данных"""
        self.dc.value(1)
        self.cs.value(0)
        self.spi.write(data)
        self.cs.value(1)
    
    def _init_display(self):
        """Инициализация дисплея ILI9341"""
        # Аппаратный сброс
        self.rst.value(0)
        time.sleep(0.1)
        self.rst.value(1)
        time.sleep(0.1)
        
        # Программный сброс
        self._write_command(ILI9341_SWRESET)
        time.sleep(0.15)
        
        # Выход из спящего режима
        self._write_command(ILI9341_SLPOUT)
        time.sleep(0.12)
        
        # Установка цветового режима: 16 бит (RGB565)
        self._write_command(ILI9341_PIXFMT)
        self._write_data(0x55)
        
        # Управление порядком данных памяти
        self._write_command(ILI9341_MADCTL)
        self._write_data(0x48)  # Порядок RGB, портретная ориентация
        
        # Установка частоты кадров
        self._write_command(ILI9341_FRMCTR1)
        self._write_data(0x00)
        self._write_data(0x1B)
        
        # Управление гамма-коррекцией
        self._write_command(ILI9341_GAMMASET)
        self._write_data(0x01)
        
        # Установка положительной гаммы
        self._write_command(ILI9341_GMCTRP1)
        gamma_pos = [
            0x0F, 0x2F, 0x2F, 0x0C, 0x0E, 0x08, 0x4E, 0xF1,
            0x37, 0x07, 0x10, 0x03, 0x0E, 0x09, 0x00
        ]
        self._write_data(bytearray(gamma_pos))
        
        # Установка отрицательной гаммы
        self._write_command(ILI9341_GMCTRN1)
        gamma_neg = [
            0x00, 0x10, 0x10, 0x02, 0x11, 0x06, 0x2B, 0x33,
            0x3F, 0x07, 0x04, 0x08, 0x03, 0x0E, 0x09
        ]
        self._write_data(bytearray(gamma_neg))
        
        # Включение инверсии
        self._write_command(ILI9341_INVON)
        
        # Нормальный режим отображения
        self._write_command(ILI9341_NORON)
        time.sleep(0.01)
        
        # Включение дисплея
        self._write_command(ILI9341_DISPON)
        time.sleep(0.1)
    
    def _set_address_window(self, x0, y0, x1, y1):
        """Установка области дисплея для записи"""
        # Проверяем, нужно ли обновлять окно
        if self.last_x == x0 and self.last_y == y0 and x0 == x1 and y0 == y1:
            return
        
        self.last_x = x0
        self.last_y = y0
        
        # Установка столбца
        self._write_command(ILI9341_CASET)
        data = bytearray([
            (x0 >> 8) & 0xFF, x0 & 0xFF,
            (x1 >> 8) & 0xFF, x1 & 0xFF
        ])
        self._write_data_buffer(data)
        
        # Установка строки
        self._write_command(ILI9341_RASET)
        data = bytearray([
            (y0 >> 8) & 0xFF, y0 & 0xFF,
            (y1 >> 8) & 0xFF, y1 & 0xFF
        ])
        self._write_data_buffer(data)
        
        # Команда записи в память
        self._write_command(ILI9341_RAMWR)
    
    def swap_buffers(self):
        """Обмен буферов: отображаем активный буфер"""
        # Копируем активный буфер в буфер отображения
        self.display_buffer[:] = self.active_buffer
        
        # Отправляем буфер отображения на дисплей
        self._set_address_window(0, 0, self.width - 1, self.height - 1)
        self._write_data_buffer(self.display_buffer)
    
    def get_framebuffer(self):
        """Получить текущий framebuffer для рисования"""
        return self.fb
    
    def fill_screen(self, color):
        """Заполнить весь экран цветом"""
        self.fb.fill(color)
    
    def fill_rect(self, x, y, w, h, color):
        """Заполнить прямоугольник цветом"""
        self.fb.fill_rect(x, y, w, h, color)
    
    def draw_pixel(self, x, y, color):
        """Нарисовать пиксель"""
        self.fb.pixel(x, y, color)
    
    def draw_line(self, x0, y0, x1, y1, color):
        """Нарисовать линию"""
        self.fb.line(x0, y0, x1, y1, color)
    
    def draw_rectangle(self, x, y, w, h, color):
        """Нарисовать прямоугольник (рамку)"""
        self.fb.rect(x, y, w, h, color)
    
    def draw_filled_rectangle(self, x, y, w, h, color):
        """Нарисовать заполненный прямоугольник"""
        self.fb.fill_rect(x, y, w, h, color)
    
    def draw_circle(self, x0, y0, r, color):
        """Нарисовать круг (алгоритм Брезенхема)"""
        x = r
        y = 0
        err = 0
        
        while x >= y:
            self.fb.pixel(x0 + x, y0 + y, color)
            self.fb.pixel(x0 + y, y0 + x, color)
            self.fb.pixel(x0 - y, y0 + x, color)
            self.fb.pixel(x0 - x, y0 + y, color)
            self.fb.pixel(x0 - x, y0 - y, color)
            self.fb.pixel(x0 - y, y0 - x, color)
            self.fb.pixel(x0 + y, y0 - x, color)
            self.fb.pixel(x0 + x, y0 - y, color)
            
            if err <= 0:
                y += 1
                err += 2 * y + 1
            if err > 0:
                x -= 1
                err -= 2 * x + 1
    
    def draw_filled_circle(self, x0, y0, r, color):
        """Нарисовать заполненный круг"""
        x = r
        y = 0
        err = 0
        
        while x >= y:
            # Горизонтальные линии для каждой пары y
            self.fb.hline(x0 - x, y0 + y, 2 * x, color)
            self.fb.hline(x0 - y, y0 + x, 2 * y, color)
            self.fb.hline(x0 - x, y0 - y, 2 * x, color)
            self.fb.hline(x0 - y, y0 - x, 2 * y, color)
            
            if err <= 0:
                y += 1
                err += 2 * y + 1
            if err > 0:
                x -= 1
                err -= 2 * x + 1
    
    def draw_triangle(self, x0, y0, x1, y1, x2, y2, color):
        """Нарисовать треугольник"""
        self.fb.line(x0, y0, x1, y1, color)
        self.fb.line(x1, y1, x2, y2, color)
        self.fb.line(x2, y2, x0, y0, color)

    def draw_text(self, x, y, text, color, bg_color=None, scale=1):
        """Нарисовать текст с использованием шрифта 8x12"""
        try:
            import font
        except ImportError:
            # Если шрифт недоступен, рисуем рамку
            if bg_color is not None:
                text_width = len(text) * 8 * scale
                text_height = 12 * scale
                self.fb.fill_rect(x, y, text_width, text_height, bg_color)
            self.fb.rect(x, y, len(text) * 8 * scale, 12 * scale, color)
            return

        font_width = font.FONT_WIDTH
        font_height = font.FONT_HEIGHT

        # Рисуем фон под текстом
        if bg_color is not None:
            text_bg_width = len(text) * font_width * scale
            text_bg_height = font_height * scale
            self.fb.fill_rect(x, y, text_bg_width, text_bg_height, bg_color)

        # Рисуем каждый символ
        for i, char in enumerate(text):
            char_code = ord(char)
            char_data = font.get_char_data(char_code)

            # Позиция символа
            char_x = x + i * font_width * scale

            # Рисуем пиксели символа
            for row in range(font_height):
                if row < len(char_data):
                    byte_val = char_data[row]
                else:
                    byte_val = 0

                for col in range(font_width):
                    # Проверяем бит
                    if byte_val & (0x80 >> col):
                        # Рисуем пиксель с учётом масштаба
                        pixel_x = char_x + col * scale
                        pixel_y = y + row * scale

                        if scale > 1:
                            # При масштабе > 1 рисуем квадрат
                            for sx in range(scale):
                                for sy in range(scale):
                                    self.fb.pixel(pixel_x + sx, pixel_y + sy, color)
                        else:
                            self.fb.pixel(pixel_x, pixel_y, color)

    def set_rotation(self, rotation):
        """Установить ориентацию дисплея"""
        self.rotation = rotation & 3
        madctl = ILI9341_MADCTL_RGB

        if self.rotation == 0:  # Портретная 0°
            madctl = ILI9341_MADCTL_MX | ILI9341_MADCTL_RGB
        elif self.rotation == 1:  # Ландшафтная 90°
            madctl = ILI9341_MADCTL_MV | ILI9341_MADCTL_MY | ILI9341_MADCTL_RGB
        elif self.rotation == 2:  # Портретная 180°
            madctl = ILI9341_MADCTL_MY | ILI9341_MADCTL_RGB
        elif self.rotation == 3:  # Ландшафтная 270°
            madctl = ILI9341_MADCTL_MX | ILI9341_MADCTL_MY | ILI9341_MADCTL_MV | ILI9341_MADCTL_RGB
        
        self._write_command(ILI9341_MADCTL)
        self._write_data(madctl)
    
    def set_backlight(self, brightness):
        """Установить яркость подсветки (0-100)"""
        if brightness > 100:
            brightness = 100
        # Простое включение/выключение (можно расширить до PWM)
        self.blk.value(1 if brightness > 0 else 0)
    
    def display_on(self):
        """Включить дисплей"""
        self._write_command(ILI9341_DISPON)
    
    def display_off(self):
        """Выключить дисплей"""
        self._write_command(ILI9341_DISPOFF)
    
    def sleep_in(self):
        """Перевести в спящий режим"""
        self._write_command(ILI9341_SLPIN)
    
    def sleep_out(self):
        """Вывести из спящего режима"""
        self._write_command(ILI9341_SLPOUT)
    
    def get_width(self):
        """Получить ширину дисплея с учётом ориентации"""
        if self.rotation == 1 or self.rotation == 3:
            return self.height
        return self.width
    
    def get_height(self):
        """Получить высоту дисплея с учётом ориентации"""
        if self.rotation == 1 or self.rotation == 3:
            return self.width
        return self.height