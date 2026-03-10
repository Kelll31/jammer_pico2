"""
Генерация сигнала джаммера для MicroPython
Со всеми режимами работы: continuous, sweep, burst, noise
"""

import time
import math
import config
from machine import Pin, PWM

# ============================================================================
# ТИПЫ ДАННЫХ
# ============================================================================

class JammerMode:
    """Режимы работы джаммера"""
    CONTINUOUS = 0  # Непрерывное излучение
    SWEEP = 1       # Сканирование по частотам
    BURST = 2       # Импульсный режим
    NOISE = 3       # Широкополосный шум
    COUNT = 4       # Количество режимов

class JammerFreq:
    """Типы частот джаммера"""
    WIFI_24GHZ = 0
    WIFI_5GHZ = 1
    BLUETOOTH = 2
    CELLULAR = 3
    CUSTOM = 4      # Пользовательская частота
    COUNT = 5       # Количество режимов

class JammerState:
    """Состояния джаммера"""
    OFF = 0
    ON = 1
    STANDBY = 2
    ERROR = 3

class JammerError:
    """Ошибки джаммера"""
    NONE = 0
    INVALID_FREQ = 1
    INVALID_POWER = 2
    INVALID_MODE = 3
    HARDWARE = 4

# ============================================================================
# КЛАСС ДЖАММЕРА
# ============================================================================

class JammerSignal:
    """Класс для генерации сигнала джаммера"""
    
    def __init__(self, pin=config.JAMMER_SIGNAL_PIN):
        self.pin = pin
        self.enabled = False
        self.frequency_hz = 0
        self.power_level = config.JAMMER_DEFAULT_POWER_LEVEL
        self.mode = JammerMode.CONTINUOUS
        self.freq_mode = JammerFreq.WIFI_24GHZ
        self.state = JammerState.OFF
        self.last_error = JammerError.NONE
        self.custom_freq_hz = 0
        
        # Инициализация PWM
        self.pwm = PWM(Pin(pin))
        self.pwm.freq(1000)  # Начальная частота
        self.pwm.duty_u16(0)  # Выключено
        
        # Для режима sweep
        self.sweep_current_freq = 0
        self.sweep_min_freq = 0
        self.sweep_max_freq = 0
        self.sweep_direction = True  # true = вверх, false = вниз
        self.sweep_last_step = time.ticks_ms()
        
        # Для режима burst
        self.burst_last_toggle = time.ticks_ms()
        self.burst_state = True  # true = включён, false = выключен
        
        # Для режима noise
        self.noise_lfsr = config.JAMMER_NOISE_SEED
        self.noise_last_change = time.ticks_ms()
        
        # LED индикатор
        self.led = Pin(config.JAMMER_LED_PIN, Pin.OUT)
        self.led.value(0)
        
        # Установка частоты по умолчанию
        self.set_freq_mode(JammerFreq.WIFI_24GHZ)
    
    # ============================================================================
    # ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
    # ============================================================================
    
    def _set_error(self, error):
        """Установить ошибку"""
        self.last_error = error
        if error != JammerError.NONE:
            self.state = JammerState.ERROR
    
    def _clear_error(self):
        """Очистить ошибку"""
        self.last_error = JammerError.NONE
        if self.state == JammerState.ERROR:
            self.state = JammerState.OFF
    
    def _lfsr_next(self, lfsr):
        """LFSR для генерации псевдослучайных чисел (noise режим)"""
        bit = ((lfsr >> 0) ^ (lfsr >> 2) ^ (lfsr >> 3) ^ (lfsr >> 5)) & 1
        return (lfsr >> 1) | (bit << 30)
    
    def _apply_frequency(self):
        """Применить текущую частоту к PWM"""
        if self.frequency_hz == 0:
            return False
        
        try:
            # Ограничиваем частоту разумными пределами
            if self.frequency_hz < 100:
                freq = 100
            elif self.frequency_hz > 100_000_000:  # 100 MHz максимум для PWM
                freq = 100_000_000
            else:
                freq = self.frequency_hz
            
            self.pwm.freq(freq)
            return True
        except:
            self._set_error(JammerError.HARDWARE)
            return False
    
    def _apply_power_level(self):
        """Применить уровень мощности"""
        if not self.enabled:
            return
        
        # Преобразуем проценты в значение duty (0-65535)
        duty = int((self.power_level / 100.0) * 65535)
        self.pwm.duty_u16(duty)
    
    def _get_freq_range(self, freq_mode):
        """Получить диапазон частот для режима"""
        if freq_mode == JammerFreq.WIFI_24GHZ:
            return config.WIFI_24GHZ_MIN_FREQ, config.WIFI_24GHZ_MAX_FREQ
        elif freq_mode == JammerFreq.WIFI_5GHZ:
            return config.WIFI_5GHZ_MIN_FREQ, config.WIFI_5GHZ_MAX_FREQ
        elif freq_mode == JammerFreq.BLUETOOTH:
            return config.BLUETOOTH_MIN_FREQ, config.BLUETOOTH_MAX_FREQ
        elif freq_mode == JammerFreq.CELLULAR:
            return config.CELLULAR_MIN_FREQ, config.CELLULAR_MAX_FREQ
        elif freq_mode == JammerFreq.CUSTOM:
            return self.custom_freq_hz, self.custom_freq_hz
        else:
            return config.WIFI_24GHZ_MIN_FREQ, config.WIFI_24GHZ_MAX_FREQ
    
    # ============================================================================
    # ОСНОВНЫЕ ФУНКЦИИ
    # ============================================================================
    
    def enable(self, enable=True):
        """Включить/выключить генерацию сигнала"""
        if enable and self.state == JammerState.ERROR:
            return  # Не включаем при ошибке
        
        self.enabled = enable
        
        if enable:
            self.state = JammerState.ON
            self.led.value(1)
            
            # Сброс таймеров для режимов
            self.sweep_last_step = time.ticks_ms()
            self.burst_last_toggle = time.ticks_ms()
            self.noise_last_change = time.ticks_ms()
            self.burst_state = True
            
            # Включаем PWM
            self._apply_frequency()
            self._apply_power_level()
            self._clear_error()
        else:
            self.state = JammerState.OFF
            self.led.value(0)
            self.pwm.duty_u16(0)  # Выключаем PWM
    
    def disable(self):
        """Выключить генерацию сигнала"""
        self.enable(False)
    
    def set_frequency(self, frequency_hz):
        """Установить частоту джаммера"""
        if frequency_hz == 0:
            self._set_error(JammerError.INVALID_FREQ)
            return JammerError.INVALID_FREQ
        
        self.frequency_hz = frequency_hz
        self.freq_mode = JammerFreq.CUSTOM
        self.custom_freq_hz = frequency_hz
        
        if self.enabled:
            self._apply_frequency()
        
        self._clear_error()
        return JammerError.NONE
    
    def set_freq_mode(self, freq_mode):
        """Установить режим частоты (предопределённый)"""
        if freq_mode >= JammerFreq.COUNT:
            self._set_error(JammerError.INVALID_FREQ)
            return JammerError.INVALID_FREQ
        
        self.freq_mode = freq_mode
        
        # Вычисляем среднюю частоту для режима
        min_freq, max_freq = self._get_freq_range(freq_mode)
        self.frequency_hz = min_freq + (max_freq - min_freq) // 2
        
        # Для sweep режима сохраняем диапазон
        self.sweep_min_freq = min_freq
        self.sweep_max_freq = max_freq
        self.sweep_current_freq = min_freq
        
        if self.enabled:
            self._apply_frequency()
        
        self._clear_error()
        return JammerError.NONE
    
    def set_custom_frequency(self, frequency_hz):
        """Установить пользовательскую частоту"""
        if frequency_hz == 0:
            self._set_error(JammerError.INVALID_FREQ)
            return JammerError.INVALID_FREQ
        
        self.custom_freq_hz = frequency_hz
        self.freq_mode = JammerFreq.CUSTOM
        self.frequency_hz = frequency_hz
        
        if self.enabled:
            self._apply_frequency()
        
        self._clear_error()
        return JammerError.NONE
    
    def set_power_level(self, power_percent):
        """Установить уровень мощности (0-100%)"""
        if power_percent > config.JAMMER_MAX_POWER_LEVEL:
            self._set_error(JammerError.INVALID_POWER)
            return JammerError.INVALID_POWER
        
        if power_percent < config.JAMMER_MIN_POWER_LEVEL and power_percent != 0:
            power_percent = config.JAMMER_MIN_POWER_LEVEL
        
        self.power_level = power_percent
        
        if self.enabled:
            self._apply_power_level()
        
        self._clear_error()
        return JammerError.NONE
    
    def set_mode(self, mode):
        """Установить режим работы"""
        if mode >= JammerMode.COUNT:
            self._set_error(JammerError.INVALID_MODE)
            return JammerError.INVALID_MODE
        
        self.mode = mode
        
        # Инициализация параметров для режима
        if mode == JammerMode.SWEEP:
            min_freq, max_freq = self._get_freq_range(self.freq_mode)
            self.sweep_min_freq = min_freq
            self.sweep_max_freq = max_freq
            self.sweep_current_freq = min_freq
            self.sweep_direction = True
        elif mode == JammerMode.BURST:
            self.burst_state = True
        elif mode == JammerMode.NOISE:
            self.noise_lfsr = config.JAMMER_NOISE_SEED
        
        self._clear_error()
        return JammerError.NONE
    
    def process(self):
        """Обработка режимов (вызывать в цикле)"""
        if not self.enabled:
            return
        
        now = time.ticks_ms()
        
        if self.mode == JammerMode.SWEEP:
            # Проход по диапазону частот
            if time.ticks_diff(now, self.sweep_last_step) >= config.JAMMER_SWEEP_DELAY_MS:
                if self.sweep_direction:
                    self.sweep_current_freq += config.JAMMER_SWEEP_STEP_HZ
                    if self.sweep_current_freq >= self.sweep_max_freq:
                        self.sweep_current_freq = self.sweep_max_freq
                        self.sweep_direction = False
                else:
                    self.sweep_current_freq -= config.JAMMER_SWEEP_STEP_HZ
                    if self.sweep_current_freq <= self.sweep_min_freq:
                        self.sweep_current_freq = self.sweep_min_freq
                        self.sweep_direction = True
                
                self.frequency_hz = self.sweep_current_freq
                self._apply_frequency()
                self.sweep_last_step = now
        
        elif self.mode == JammerMode.BURST:
            # Импульсный режим
            delay_ms = config.JAMMER_BURST_ON_MS if self.burst_state else config.JAMMER_BURST_OFF_MS
            
            if time.ticks_diff(now, self.burst_last_toggle) >= delay_ms:
                self.burst_state = not self.burst_state
                
                if self.burst_state:
                    self._apply_power_level()  # Включаем
                else:
                    self.pwm.duty_u16(0)  # Выключаем
                
                self.burst_last_toggle = now
        
        elif self.mode == JammerMode.NOISE:
            # Псевдослучайная частота
            if time.ticks_diff(now, self.noise_last_change) >= 1:  # 1 мс
                self.noise_lfsr = self._lfsr_next(self.noise_lfsr)
                
                # Преобразуем LFSR в частоту в пределах диапазона
                min_freq, max_freq = self._get_freq_range(self.freq_mode)
                freq_range = max_freq - min_freq
                
                if freq_range > 0:
                    offset = (self.noise_lfsr % freq_range)
                    self.frequency_hz = min_freq + offset
                    
                    self._apply_frequency()
                    self.noise_last_change = now
    
    # ============================================================================
    # ГЕТТЕРЫ
    # ============================================================================
    
    def is_enabled(self):
        """Проверить, включён ли джаммер"""
        return self.enabled
    
    def get_frequency(self):
        """Получить текущую частоту"""
        return self.frequency_hz
    
    def get_power_level(self):
        """Получить текущий уровень мощности"""
        return self.power_level
    
    def get_mode(self):
        """Получить текущий режим работы"""
        return self.mode
    
    def get_freq_mode(self):
        """Получить текущий режим частоты"""
        return self.freq_mode
    
    def get_state(self):
        """Получить текущее состояние"""
        return self.state
    
    def get_last_error(self):
        """Получить последнюю ошибку"""
        return self.last_error
    
    # ============================================================================
    # СТРОКОВЫЕ ОПИСАНИЯ
    # ============================================================================
    
    @staticmethod
    def get_freq_name(freq_mode):
        """Получить строковое описание режима частоты"""
        names = [
            "WiFi 2.4GHz",
            "WiFi 5GHz",
            "Bluetooth",
            "Cellular",
            "Custom"
        ]
        
        if freq_mode >= JammerFreq.COUNT:
            return "Unknown"
        return names[freq_mode]
    
    @staticmethod
    def get_mode_name(mode):
        """Получить строковое описание режима работы"""
        names = [
            "Continuous",
            "Sweep",
            "Burst",
            "Noise"
        ]
        
        if mode >= JammerMode.COUNT:
            return "Unknown"
        return names[mode]
    
    @staticmethod
    def get_state_name(state):
        """Получить строковое описание состояния"""
        names = [
            "OFF",
            "ON",
            "STANDBY",
            "ERROR"
        ]
        
        if state >= JammerState.ERROR + 1:
            return "UNKNOWN"
        return names[state]
    
    @staticmethod
    def get_error_name(error):
        """Получить строковое описание ошибки"""
        names = [
            "None",
            "Invalid Frequency",
            "Invalid Power",
            "Invalid Mode",
            "Hardware Error"
        ]
        
        if error >= JammerError.HARDWARE + 1:
            return "Unknown"
        return names[error]
    
    def get_freq_range(self, freq_mode=None):
        """Получить диапазон частот для режима"""
        if freq_mode is None:
            freq_mode = self.freq_mode
        return self._get_freq_range(freq_mode)
    
    # ============================================================================
    # УПРАВЛЕНИЕ МОЩНОСТЬЮ
    # ============================================================================
    
    def increase_power(self, step=5):
        """Увеличить мощность на указанный шаг"""
        new_power = self.power_level + step
        if new_power > config.JAMMER_MAX_POWER_LEVEL:
            new_power = config.JAMMER_MAX_POWER_LEVEL
        return self.set_power_level(new_power)
    
    def decrease_power(self, step=5):
        """Уменьшить мощность на указанный шаг"""
        new_power = self.power_level - step
        if new_power < 0:
            new_power = 0
        return self.set_power_level(new_power)
    
    # ============================================================================
    # ЦИКЛИЧЕСКИЕ ОПЕРАЦИИ
    # ============================================================================
    
    def next_freq_mode(self):
        """Переключить на следующий режим частоты"""
        next_mode = (self.freq_mode + 1) % JammerFreq.COUNT
        return self.set_freq_mode(next_mode)
    
    def next_mode(self):
        """Переключить на следующий режим работы"""
        next_mode_val = (self.mode + 1) % JammerMode.COUNT
        return self.set_mode(next_mode_val)
    
    def toggle_enable(self):
        """Переключить состояние включения/выключения"""
        self.enable(not self.enabled)
        return self.enabled
