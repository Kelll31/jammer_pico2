"""
Конфигурация оборудования для KELL31 Jammer на MicroPython
Аналогично C-версии, но адаптировано для MicroPython
"""

# ============================================================================
# КОНФИГУРАЦИЯ ОБОРУДОВАНИЯ (ILI9341 с тачскрином XPT2046)
# ============================================================================

# Дисплей ILI9341
DISPLAY_SPI_ID = 0
DISPLAY_DC_PIN = 20      # GP20 (Pin 26)
DISPLAY_RST_PIN = 21     # GP21 (Pin 27)
DISPLAY_CS_PIN = 17      # GP17 (Pin 22)
DISPLAY_BLK_PIN = 14     # GP14 (Pin 19)
DISPLAY_SCK_PIN = 18     # GP18 (Pin 24)
DISPLAY_MOSI_PIN = 19    # GP19 (Pin 25)
DISPLAY_MISO_PIN = 16    # GP16 (Pin 21)
DISPLAY_SPI_FREQ = 40_000_000  # 40 MHz

# Тачскрин XPT2046
TOUCH_CS_PIN = 22        # GP22 (Pin 29)
TOUCH_IRQ_PIN = 15       # GP15 (Pin 20)

# Джаммер
JAMMER_SIGNAL_PIN = 28   # GP28 (Pin 34)
JAMMER_LED_PIN = 25      # GP25 (LED на плате)

# Размеры дисплея
DISPLAY_WIDTH = 240
DISPLAY_HEIGHT = 320

# ============================================================================
# КОНФИГУРАЦИЯ ДЖАММЕРА
# ============================================================================

# Версия прошивки
FIRMWARE_VERSION_MAJOR = 1
FIRMWARE_VERSION_MINOR = 0
FIRMWARE_VERSION_PATCH = 0

# Параметры джаммера
JAMMER_MAX_POWER_LEVEL = 100
JAMMER_MIN_POWER_LEVEL = 1
JAMMER_DEFAULT_POWER_LEVEL = 50
JAMMER_SWEEP_STEP_HZ = 1_000_000      # 1 MHz шаг для sweep
JAMMER_SWEEP_DELAY_MS = 10            # Задержка между шагами sweep
JAMMER_BURST_ON_MS = 100              # Длительность импульса
JAMMER_BURST_OFF_MS = 50              # Пауза между импульсами
JAMMER_NOISE_SEED = 0x12345678        # Seed для генератора шума

# Определения частот для различных стандартов
WIFI_24GHZ_MIN_FREQ = 2_400_000_000  # 2.4 GHz
WIFI_24GHZ_MAX_FREQ = 2_483_500_000  # 2.4835 GHz
WIFI_5GHZ_MIN_FREQ = 5_150_000_000   # 5.15 GHz
WIFI_5GHZ_MAX_FREQ = 5_825_000_000   # 5.825 GHz
BLUETOOTH_MIN_FREQ = 2_402_000_000   # 2.402 GHz
BLUETOOTH_MAX_FREQ = 2_480_000_000   # 2.480 GHz
CELLULAR_700MHZ_FREQ = 700_000_000   # 700 MHz
CELLULAR_800MHZ_FREQ = 800_000_000   # 800 MHz
CELLULAR_900MHZ_FREQ = 900_000_000   # 900 MHz
CELLULAR_1800MHZ_FREQ = 1_800_000_000  # 1.8 GHz
CELLULAR_1900MHZ_FREQ = 1_900_000_000  # 1.9 GHz
CELLULAR_2100MHZ_FREQ = 2_100_000_000  # 2.1 GHz
CELLULAR_2600MHZ_FREQ = 2_600_000_000  # 2.6 GHz
CELLULAR_MIN_FREQ = CELLULAR_700MHZ_FREQ
CELLULAR_MAX_FREQ = CELLULAR_2600MHZ_FREQ

# ============================================================================
# КОНФИГУРАЦИЯ UI
# ============================================================================

UI_SCALE = 1               # Масштаб шрифта (1 или 2)
UI_FONT_COLOR = 0xFFFF     # Белый
UI_BG_COLOR = 0x0000       # Чёрный (Dark theme)
UI_HEADER_COLOR = 0x3186   # Тёмно-серый для большего контраста
UI_BUTTON_BG = 0x52AA      # Серый для кнопок (улучшенный контраст)
UI_BUTTON_ACTIVE_BG = 0x7BEF  # Светло-серый (для нажатого состояния)
UI_BUTTON_BORDER = 0xFFFF  # Белый

# Размеры кнопок
UI_BUTTON_HEIGHT = 40
UI_BUTTON_MIN_WIDTH = 70

# Отступы
UI_MARGIN = 5
UI_BUTTON_SPACING = 5

# Цвета (RGB565)
COLOR_BLACK = 0x0000
COLOR_WHITE = 0xFFFF
COLOR_RED = 0xF800
COLOR_GREEN = 0x07E0
COLOR_BLUE = 0x001F
COLOR_CYAN = 0x07FF
COLOR_MAGENTA = 0xF81F
COLOR_YELLOW = 0xFFE0
COLOR_ORANGE = 0xFC00
COLOR_PURPLE = 0x8010
COLOR_GRAY = 0x8410
COLOR_DARKGRAY = 0x4208
COLOR_LIGHTGRAY = 0xC618

# ============================================================================
# ПУТИ ФАЙЛОВ
# ============================================================================

SETTINGS_FILE = "settings.json"
FONT_FILE = "font.py"

# ============================================================================
# КАЛИБРОВКА ТАЧСКРИНА
# ============================================================================

# Значения по умолчанию (можно откалибровать)
TOUCH_CAL_MIN_X = 200
TOUCH_CAL_MIN_Y = 200
TOUCH_CAL_MAX_X = 3800
TOUCH_CAL_MAX_Y = 3800

# ============================================================================
# КНОПКИ (если используются аппаратные кнопки)
# ============================================================================

# Пины для аппаратных кнопок (опционально)
BUTTON_POWER_PIN = 2      # GP2 (Pin 4) - кнопка питания
BUTTON_MODE_PIN = 3       # GP3 (Pin 5) - кнопка режима
BUTTON_POWER_UP_PIN = 4   # GP4 (Pin 6) - кнопка увеличения мощности
BUTTON_POWER_DOWN_PIN = 5 # GP5 (Pin 7) - кнопка уменьшения мощности

# ============================================================================
# КОНФИГУРАЦИЯ SPI1 ДЛЯ RF-МОДУЛЕЙ (Core 1)
# ============================================================================

# SPI1 шина (выделена для Core 1)
SPI1_ID = 1
SPI1_SCK_PIN = 10         # GP10 (Pin 14)
SPI1_MOSI_PIN = 11        # GP11 (Pin 15)
SPI1_MISO_PIN = 12        # GP12 (Pin 16)
SPI1_FREQ = 8_000_000     # 8 MHz общая частота, переключается внутри менеджера

# CC1101 Sub-GHz Transceiver
CC1101_CS_PIN = 6         # GP6 (Pin 9)
CC1101_IRQ_PIN = 7        # GP7 (Pin 10) - опционально для прерываний

# NRF24L01 2.4GHz Transceiver
NRF24L01_CS_PIN = 8       # GP8 (Pin 11)
NRF24L01_CE_PIN = 9       # GP9 (Pin 12)
NRF24L01_IRQ_PIN = 13     # GP13 (Pin 17) - опционально

# SX1278 LoRa Transceiver
SX1278_CS_PIN = 26        # GP26 (Pin 31)
SX1278_RST_PIN = 27       # GP27 (Pin 32)
SX1278_DIO0_PIN = 0       # GP0 (Pin 1) - для прерываний

# I2C для Si4732 (используется Core 1)
I2C_ID = 0
I2C_SDA_PIN = 0           # GP0 (Pin 1) - если свободен, иначе выбери другой
I2C_SCL_PIN = 1           # GP1 (Pin 2)

# ============================================================================
# ПАРАМЕТРЫ RF-МОДУЛЕЙ
# ============================================================================

# CC1101 частоты (MHz)
CC1101_FREQ_315 = 315_000_000
CC1101_FREQ_433 = 433_920_000
CC1101_FREQ_868 = 868_350_000

# NRF24L01 каналы (2.4 GHz)
NRF24_CHANNEL_MIN = 0
NRF24_CHANNEL_MAX = 125
NRF24_DEFAULT_CHANNEL = 76  # 2.476 GHz

# SX1278 LoRa параметры
LORA_FREQ_MIN = 433_000_000
LORA_FREQ_MAX = 470_000_000
LORA_DEFAULT_FREQ = 434_000_000
LORA_SPREADING_FACTORS = [7, 8, 9, 10, 11, 12]
LORA_BANDWIDTHS = [125_000, 250_000, 500_000]

# Si4732 диапазоны
SI4732_FM_MIN = 87_500_000   # 87.5 MHz
SI4732_FM_MAX = 108_000_000  # 108 MHz
SI4732_AM_MIN = 520_000      # 520 kHz
SI4732_AM_MAX = 1710_000     # 1710 kHz

# ============================================================================
# IPC SHARED MEMORY КОНФИГУРАЦИЯ
# ============================================================================

# Размер буфера спектра (количество точек)
SPECTRUM_BUFFER_SIZE = 128

# Максимальное количество пакетов в буфере
MAX_PACKETS_BUFFER = 32
