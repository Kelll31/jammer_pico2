"""
Обработка аппаратных кнопок для MicroPython
"""

import time
import config
from machine import Pin

# Флаг для определения среды выполнения
MICROPYTHON = True

class Button:
    """Класс для работы с аппаратной кнопкой"""
    
    def __init__(self, pin, pull_up=True, debounce_ms=50):
        self.pin = pin
        self.pull_up = pull_up
        
        # Инициализация пина
        if pull_up:
            self.io = Pin(pin, Pin.IN, Pin.PULL_UP)
        else:
            self.io = Pin(pin, Pin.IN)
        
        # Состояния
        self.last_state = self._read_raw()
        self.last_debounced_state = self.last_state
        self.last_change_time = time.ticks_ms()
        self.debounce_ms = debounce_ms
        
        # Callbacks
        self.on_press = None
        self.on_release = None
        self.on_click = None
        self.on_long_press = None
        
        # Для отслеживания длительного нажатия
        self.press_start_time = 0
        self.long_press_detected = False
        self.long_press_threshold = 1000  # 1 секунда
    
    def _read_raw(self):
        """Прочитать сырое состояние кнопки"""
        state = self.io.value()
        if self.pull_up:
            # При pull-up нажатие = 0, отпускание = 1
            return 0 if state == 0 else 1
        else:
            # При pull-down нажатие = 1, отпускание = 0
            return state
    
    def update(self):
        """Обновить состояние кнопки (вызывать в цикле)"""
        current_time = time.ticks_ms()
        raw_state = self._read_raw()
        
        # Дребезг
        if raw_state != self.last_state:
            self.last_state = raw_state
            self.last_change_time = current_time
        
        # Проверяем, прошло ли время дребезга
        if time.ticks_diff(current_time, self.last_change_time) >= self.debounce_ms:
            # Состояние изменилось
            if raw_state != self.last_debounced_state:
                self.last_debounced_state = raw_state
                
                # Нажатие (переход с 0 на 1)
                if raw_state == 1:
                    self.press_start_time = current_time
                    self.long_press_detected = False
                    
                    if self.on_press:
                        self.on_press()
                
                # Отпускание (переход с 1 на 0)
                else:
                    press_duration = time.ticks_diff(current_time, self.press_start_time)
                    
                    # Короткое нажатие (клик)
                    if not self.long_press_detected and self.on_click:
                        self.on_click()
                    
                    if self.on_release:
                        self.on_release()
        
        # Проверка длительного нажатия
        if (raw_state == 1 and  # Кнопка нажата
            not self.long_press_detected and  # Длинное нажатие ещё не обнаружено
            time.ticks_diff(current_time, self.press_start_time) >= self.long_press_threshold):
            
            self.long_press_detected = True
            
            if self.on_long_press:
                self.on_long_press()
    
    def is_pressed(self):
        """Проверить, нажата ли кнопка (с учётом дребезга)"""
        return self.last_debounced_state == 1
    
    def is_released(self):
        """Проверить, отпущена ли кнопка (с учётом дребезга)"""
        return self.last_debounced_state == 0
    
    def get_press_duration(self):
        """Получить длительность текущего нажатия (в мс)"""
        if self.is_pressed():
            return time.ticks_diff(time.ticks_ms(), self.press_start_time)
        return 0

class ButtonManager:
    """Менеджер для управления несколькими кнопками"""
    
    def __init__(self):
        self.buttons = {}
        self.last_update = time.ticks_ms()
    
    def add_button(self, name, pin, **kwargs):
        """Добавить кнопку"""
        button = Button(pin, **kwargs)
        self.buttons[name] = button
        return button
    
    def remove_button(self, name):
        """Удалить кнопку"""
        if name in self.buttons:
            del self.buttons[name]
    
    def get_button(self, name):
        """Получить кнопку по имени"""
        return self.buttons.get(name)
    
    def update(self):
        """Обновить все кнопки (вызывать в цикле)"""
        current_time = time.ticks_ms()
        
        # Обновляем каждые 10 мс
        if time.ticks_diff(current_time, self.last_update) >= 10:
            self.last_update = current_time
            
            for button in self.buttons.values():
                button.update()
    
    def process(self):
        """Обработать все кнопки (вызывать в основном цикле)"""
        self.update()

# Пример использования:
def create_default_button_manager():
    """Создать менеджер кнопок с настройками по умолчанию"""
    manager = ButtonManager()
    
    # Кнопка питания (если есть)
    if hasattr(config, 'BUTTON_POWER_PIN'):
        btn_power = manager.add_button('power', config.BUTTON_POWER_PIN)
        btn_power.long_press_threshold = 2000  # 2 секунды для длительного нажатия
    
    # Кнопка режима (если есть)
    if hasattr(config, 'BUTTON_MODE_PIN'):
        manager.add_button('mode', config.BUTTON_MODE_PIN)
    
    # Кнопка увеличения мощности (если есть)
    if hasattr(config, 'BUTTON_POWER_UP_PIN'):
        manager.add_button('power_up', config.BUTTON_POWER_UP_PIN)
    
    # Кнопка уменьшения мощности (если есть)
    if hasattr(config, 'BUTTON_POWER_DOWN_PIN'):
        manager.add_button('power_down', config.BUTTON_POWER_DOWN_PIN)
    
    return manager