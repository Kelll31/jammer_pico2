"""
Менеджеры SPI шин для KELL31 Jammer (RP2350 RISC-V)

Разделение шин:
- SPI0 (ID=0): выделен для Core 0 (дисплей ILI9341 и тачскрин XPT2046)
- SPI1 (ID=1): выделен для Core 1 (RF-модули: CC1101, NRF24L01, SX1278)

Каждый менеджер обеспечивает безопасное переключение CS пинов и изменение baudrate.
"""

import time
import _thread
import config
from machine import Pin, SPI

# ============================================================================
# SPI0 МЕНЕДЖЕР (Core 0 - UI)
# ============================================================================

class SPI0_Manager:
    """Управление SPI0 шиной для дисплея и тачскрина (Core 0)"""

    def __init__(self):
        # Инициализация SPI0
        self.spi = SPI(config.DISPLAY_SPI_ID,
                      baudrate=config.DISPLAY_SPI_FREQ,
                      sck=Pin(config.DISPLAY_SCK_PIN),
                      mosi=Pin(config.DISPLAY_MOSI_PIN),
                      miso=Pin(config.DISPLAY_MISO_PIN))

        # CS пины для устройств на SPI0
        self.display_cs = Pin(config.DISPLAY_CS_PIN, Pin.OUT, value=1)
        self.touch_cs = Pin(config.TOUCH_CS_PIN, Pin.OUT, value=1)

        # Текущее активное устройство
        self.active_device = None
        self.current_baudrate = config.DISPLAY_SPI_FREQ

        # Мьютекс для безопасности (если внутри Core 0 будут потоки)
        self.lock = _thread.allocate_lock()

    def _set_cs_high_all(self):
        """Установить все CS в HIGH (неактивно)"""
        self.display_cs.value(1)
        self.touch_cs.value(1)

    def _configure_for_device(self, device, baudrate=None):
        """Настроить SPI для конкретного устройства"""
        if baudrate and baudrate != self.current_baudrate:
            self.spi.init(baudrate=baudrate,
                         sck=Pin(config.DISPLAY_SCK_PIN),
                         mosi=Pin(config.DISPLAY_MOSI_PIN),
                         miso=Pin(config.DISPLAY_MISO_PIN))
            self.current_baudrate = baudrate
    
    def acquire_display(self, baudrate=config.DISPLAY_SPI_FREQ):
        """Получить доступ к дисплею (контекстный менеджер)"""
        return self.SPIDeviceBlocker(self, "display", self.display_cs, baudrate)
    
    def acquire_touch(self, baudrate=2_500_000):
        """Получить доступ к тачскрину (контекстный менеджер)"""
        return self.SPIDeviceBlocker(self, "touch", self.touch_cs, baudrate)
    
    class SPIDeviceBlocker:
        """Контекстный менеджер для безопасного доступа к устройству на разделяемой SPI шине"""
        def __init__(self, manager, device_name, cs_pin, baudrate):
            self.manager = manager
            self.device_name = device_name
            self.cs_pin = cs_pin
            self.baudrate = baudrate
        
        def __enter__(self):
            self.manager.lock.acquire()
            # Деактивируем все CS (поднимаем в HIGH)
            self.manager._set_cs_high_all()
            # Настраиваем baudrate если нужно
            self.manager._configure_for_device(self.device_name, self.baudrate)
            # Активируем нужное устройство (опускаем нужный CS в LOW)
            self.cs_pin.value(0)
            self.manager.active_device = self.device_name
            return self.manager.spi
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            # Снова возвращаем CS в HIGH
            self.cs_pin.value(1)
            self.manager.active_device = None
            self.manager.lock.release()
    
    def get_spi(self):
        """Получить объект SPI (для прямого использования с контекстом)"""
        return self.spi

# ============================================================================
# SPI1 МЕНЕДЖЕР (Core 1 - RF)
# ============================================================================

class SPI1_Manager:
    """Управление SPI1 шиной для RF-модулей (Core 1)"""
    
    def __init__(self):
        # Инициализация SPI1
        self.spi = SPI(config.SPI1_ID,
                      baudrate=config.SPI1_FREQ,
                      sck=Pin(config.SPI1_SCK_PIN),
                      mosi=Pin(config.SPI1_MOSI_PIN),
                      miso=Pin(config.SPI1_MISO_PIN))

        # CS пины для RF-модулей
        self.cc1101_cs = Pin(config.CC1101_CS_PIN, Pin.OUT, value=1)
        self.nrf24_cs = Pin(config.NRF24L01_CS_PIN, Pin.OUT, value=1)
        self.sx1278_cs = Pin(config.SX1278_CS_PIN, Pin.OUT, value=1)

        # Дополнительные управляющие пины
        self.nrf24_ce = Pin(config.NRF24L01_CE_PIN, Pin.OUT, value=0)
        self.sx1278_rst = Pin(config.SX1278_RST_PIN, Pin.OUT, value=1)

        # Текущее активное устройство
        self.active_device = None
        self.current_baudrate = config.SPI1_FREQ

        # Мьютекс для безопасности внутри Core 1
        self.lock = _thread.allocate_lock()

        # Специфичные baudrate для каждого устройства
        self.device_baudrates = {
            "cc1101": 5_000_000,   # 5 MHz для CC1101
            "nrf24": 8_000_000,    # 8 MHz для NRF24L01
            "sx1278": 10_000_000,  # 10 MHz для SX1278
        }

    def _set_cs_high_all(self):
        """Установить все CS в HIGH (неактивно)"""
        self.cc1101_cs.value(1)
        self.nrf24_cs.value(1)
        self.sx1278_cs.value(1)

    def _configure_for_device(self, device_name):
        """Настроить SPI baudrate для конкретного устройства"""
        baudrate = self.device_baudrates.get(device_name, config.SPI1_FREQ)
        if baudrate != self.current_baudrate:
            self.spi.init(baudrate=baudrate,
                         sck=Pin(config.SPI1_SCK_PIN),
                         mosi=Pin(config.SPI1_MOSI_PIN),
                         miso=Pin(config.SPI1_MISO_PIN))
            self.current_baudrate = baudrate
    
    def acquire_cc1101(self):
        """Получить доступ к CC1101 (контекстный менеджер)"""
        return self.SPIDeviceBlocker(self, "cc1101", self.cc1101_cs)
    
    def acquire_nrf24(self):
        """Получить доступ к NRF24L01 (контекстный менеджер)"""
        return self.SPIDeviceBlocker(self, "nrf24", self.nrf24_cs)
    
    def acquire_sx1278(self):
        """Получить доступ к SX1278 (контекстный менеджер)"""
        return self.SPIDeviceBlocker(self, "sx1278", self.sx1278_cs)
    
    class SPIDeviceBlocker:
        """Контекстный менеджер для безопасного доступа к RF-модулю"""
        def __init__(self, manager, device_name, cs_pin):
            self.manager = manager
            self.device_name = device_name
            self.cs_pin = cs_pin
        
        def __enter__(self):
            self.manager.lock.acquire()
            # Деактивируем все CS
            self.manager._set_cs_high_all()
            # Настраиваем baudrate для устройства
            self.manager._configure_for_device(self.device_name)
            # Активируем нужное устройство
            self.cs_pin.value(0)
            self.manager.active_device = self.device_name
            return self.manager.spi
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            # Деактивируем устройство
            self.cs_pin.value(1)
            self.manager.active_device = None
            self.manager.lock.release()
    
    def set_nrf24_ce(self, state):
        """Управление пином CE NRF24L01 (1 - передача/приём, 0 - standby)"""
        self.nrf24_ce.value(1 if state else 0)
    
    def reset_sx1278(self):
        """Сброс SX1278 (активный низкий уровень)"""
        self.sx1278_rst.value(0)
        time.sleep_us(100)
        self.sx1278_rst.value(1)
        time.sleep_ms(10)
    
    def get_spi(self):
        """Получить объект SPI (для прямого использования с контекстом)"""
        return self.spi

# ============================================================================
# I2C МЕНЕДЖЕР (Core 1 - Si4732)
# ============================================================================

class I2C_Manager:
    """Управление I2C шиной для Si4732 (Core 1)"""
    
    def __init__(self):
        from machine import I2C
        self.i2c = I2C(config.I2C_ID,
                       scl=Pin(config.I2C_SCL_PIN),
                       sda=Pin(config.I2C_SDA_PIN),
                       freq=400_000)  # 400 kHz стандарт
        
        self.lock = _thread.allocate_lock()
    
    def acquire(self):
        """Получить доступ к I2C (контекстный менеджер)"""
        return self._I2CContext(self)
    
    class _I2CContext:
        def __init__(self, manager):
            self.manager = manager
        
        def __enter__(self):
            self.manager.lock.acquire()
            return self.manager.i2c
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.manager.lock.release()
    
    def get_i2c(self):
        """Получить объект I2C"""
        return self.i2c

# ============================================================================
# ГЛОБАЛЬНЫЕ ЭКЗЕМПЛЯРЫ (создаются в main.py)
# ============================================================================

# Эти переменные будут инициализированы в main.py
spi0_manager = None  # Для Core 0
spi1_manager = None  # Для Core 1
i2c_manager = None   # Для Core 1

def init_managers():
    """Инициализация менеджеров (вызывается в main.py)"""
    global spi0_manager, spi1_manager, i2c_manager
    spi0_manager = SPI0_Manager()
    spi1_manager = SPI1_Manager()
    i2c_manager = I2C_Manager()
    return spi0_manager, spi1_manager, i2c_manager