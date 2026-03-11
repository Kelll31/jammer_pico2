"""
UI менеджер для KELL31 Jammer с Dark Cyber Theme
Multicore архитектура с Global Status Bar и 8 экранами
"""

import time
import config
from jammer_signal import JammerSignal, JammerMode, JammerFreq, JammerState

# Тип для callback функции (для совместимости с Pylance)
try:
    from typing import Callable, Optional, List, Dict, Any

    UIButtonCallback = Optional[Callable[[], None]]
except ImportError:
    UIButtonCallback = type(None)

# ============================================================================
# GLOBAL STATUS BAR (Верхние 20 пикселей)
# ============================================================================

class GlobalStatusBar:
    """Глобальная строка состояния поверх всех окон"""
    
    def __init__(self, ipc=None):
        self.ipc = ipc
        self.height = 20
        self.last_update = time.ticks_ms()
        self.battery_level = 100  # Процент заряда
        self.cpu_usage = 0  # Процент загрузки CPU
        self.active_icons = []  # Активные значки
        
    def update(self, ipc=None):
        """Обновить данные статус-бара"""
        if ipc:
            self.ipc = ipc
        
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_update) >= 1000:  # 1 Hz
            self.last_update = current_time
            
            # Обновляем активные значки на основе состояния IPC
            self.active_icons = []
            if self.ipc:
                if self.ipc.jammer_active:
                    self.active_icons.append("⚡")  # Джаммер активен
                if self.ipc.subghz_scanning:
                    self.active_icons.append("📡")  # Sub-GHz сканирование
                if self.ipc.nrf24_sniffing:
                    self.active_icons.append("📶")  # NRF24 сниффинг
                if self.ipc.lora_receiving:
                    self.active_icons.append("📡")  # LoRa приём
                if self.ipc.core1_status != "idle":
                    self.active_icons.append("🔄")  # Core 1 активен
            
            # Имитация изменения уровня заряда
            self.battery_level = max(0, self.battery_level - 0.1)
            if self.battery_level <= 0:
                self.battery_level = 100
    
    def draw(self, display, current_page_name=""):
        """Нарисовать статус-бар"""
        # Фон статус-бара (тёмно-серый с синим оттенком)
        display.fill_rect(0, 0, config.DISPLAY_WIDTH, self.height, 0x0861)
        
        # Батарея слева
        battery_width = 30
        battery_height = 12
        battery_x = 5
        battery_y = (self.height - battery_height) // 2
        
        # Контур батареи
        display.draw_rectangle(battery_x, battery_y, battery_width, battery_height, config.COLOR_CYAN)
        # Полоска батареи
        fill_width = int((battery_width - 2) * self.battery_level / 100)
        display.fill_rect(battery_x + 1, battery_y + 1, fill_width, battery_height - 2, config.COLOR_GREEN)
        
        # Процент заряда
        batt_text = f"{int(self.battery_level)}%"
        display.draw_text(battery_x + battery_width + 5, battery_y - 2, batt_text, config.COLOR_WHITE, 0x0861)
        
        # Текущая страница по центру
        page_text = current_page_name.upper()
        text_width = len(page_text) * 8
        text_x = (config.DISPLAY_WIDTH - text_width) // 2
        display.draw_text(text_x, 4, page_text, config.COLOR_YELLOW, 0x0861)
        
        # Активные значки справа
        icons_x = config.DISPLAY_WIDTH - 5
        for icon in reversed(self.active_icons):
            icons_x -= 16
            # Простые символьные иконки (используем текст)
            display.draw_text(icons_x, 4, icon, config.COLOR_CYAN, 0x0861)
        
        # Разделительная линия
        display.draw_line(0, self.height - 1, config.DISPLAY_WIDTH, self.height - 1, config.COLOR_DARKGRAY)

# ============================================================================
# БАЗОВЫЕ ВИДЖЕТЫ
# ============================================================================

class UIButton:
    """Класс кнопки UI"""
    
    def __init__(self, x, y, width, height, label,
                 color=config.UI_FONT_COLOR,
                 bg_color=config.UI_BUTTON_BG,
                 active_bg_color=config.UI_BUTTON_ACTIVE_BG,
                 border_color=config.UI_BUTTON_BORDER):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.label = label
        self.color = color
        self.bg_color = bg_color
        self.active_bg_color = active_bg_color
        self.border_color = border_color
        self.enabled = True
        self.visible = True
        self.pressed = False
        self.on_click: UIButtonCallback = None
    
    def contains(self, x, y):
        """Проверить, содержит ли кнопка точку"""
        if not self.enabled or not self.visible:
            return False
        return self.x <= x < self.x + self.width and self.y <= y < self.y + self.height
    
    def draw(self, display):
        """Нарисовать кнопку на дисплее"""
        if not self.visible:
            return
        
        bg_color = self.active_bg_color if self.pressed else self.bg_color
        
        # Фон кнопки
        display.fill_rect(self.x, self.y, self.width, self.height, bg_color)
        
        # Рамка
        display.draw_rectangle(self.x, self.y, self.width, self.height, self.border_color)
        
        # Текст
        text_x = self.x + (self.width - len(self.label) * 8) // 2
        text_y = self.y + (self.height - 12) // 2
        display.draw_text(text_x, text_y, self.label, self.color, bg_color)
    
    def click(self):
        """Выполнить действие кнопки"""
        if self.enabled and self.on_click:
            self.on_click()
            return True
        return False

class UIPage:
    """Базовый класс страницы UI"""
    
    def __init__(self, name):
        self.name = name
        self.buttons = []
        self.needs_redraw = True
    
    def add_button(self, button):
        """Добавить кнопку на страницу"""
        self.buttons.append(button)
        self.needs_redraw = True
    
    def remove_button(self, button):
        """Удалить кнопку со страницы"""
        if button in self.buttons:
            self.buttons.remove(button)
            self.needs_redraw = True
    
    def handle_touch(self, x, y):
        """Обработать касание"""
        touched = False
        for button in self.buttons:
            if button.contains(x, y):
                if not button.pressed:
                    button.pressed = True
                    self.needs_redraw = True
                    if button.click():
                        touched = True
            else:
                if button.pressed:
                    button.pressed = False
                    self.needs_redraw = True
        return touched
    
    def handle_touch_release(self):
        """Сбросить состояние кнопок при отпускании"""
        for button in self.buttons:
            if button.pressed:
                button.pressed = False
                self.needs_redraw = True
    
    def draw(self, display):
        """Нарисовать страницу (должен быть переопределён)"""
        pass
    
    def update(self, display):
        """Обновить отображение страницы и вернуть True если нужна перерисовка"""
        redraw_happened = False
        if self.needs_redraw:
            self.draw(display)
            # Рисуем все кнопки
            for button in self.buttons:
                button.draw(display)
            self.needs_redraw = False
            redraw_happened = True
        return redraw_happened

# ============================================================================
# 8 ЭКРАНОВ DARK CYBER THEME
# ============================================================================

class DashboardPage(UIPage):
    """Главное меню (Dashboard) - сетка 2x2 или список"""
    
    def __init__(self, ipc=None, ui_manager=None):
        super().__init__("dashboard")
        self.ipc = ipc
        self.ui_manager = ui_manager
        self._create_buttons()
    
    def _create_buttons(self):
        """Создать кнопки главного меню"""
        width = config.DISPLAY_WIDTH
        height = config.DISPLAY_HEIGHT - 20  # Учитываем статус-бар
        
        # Сетка 2x2
        btn_width = 100
        btn_height = 60
        margin_x = (width - btn_width * 2) // 3
        margin_y = 40
        
        # Строка 1
        y = 30
        self.btn_jammer = UIButton(margin_x, y, btn_width, btn_height, "JAMMER")
        self.btn_jammer.on_click = lambda: self._navigate_to("jammer")
        self.add_button(self.btn_jammer)
        
        self.btn_subghz = UIButton(margin_x * 2 + btn_width, y, btn_width, btn_height, "SUB-GHz")
        self.btn_subghz.on_click = lambda: self._navigate_to("subghz")
        self.add_button(self.btn_subghz)
        
        # Строка 2
        y += margin_y + btn_height
        self.btn_radio = UIButton(margin_x, y, btn_width, btn_height, "RADIO")
        self.btn_radio.on_click = lambda: self._navigate_to("radio")
        self.add_button(self.btn_radio)
        
        self.btn_spectrum = UIButton(margin_x * 2 + btn_width, y, btn_width, btn_height, "SPECTRUM")
        self.btn_spectrum.on_click = lambda: self._navigate_to("spectrum")
        self.add_button(self.btn_spectrum)
        
        # Строка 3 (дополнительные модули)
        y += margin_y + btn_height
        self.btn_nrf24 = UIButton(margin_x, y, btn_width, btn_height, "NRF24")
        self.btn_nrf24.on_click = lambda: self._navigate_to("nrf24")
        self.add_button(self.btn_nrf24)
        
        self.btn_lora = UIButton(margin_x * 2 + btn_width, y, btn_width, btn_height, "LoRa")
        self.btn_lora.on_click = lambda: self._navigate_to("lora")
        self.add_button(self.btn_lora)
        
        # Кнопка настроек внизу
        self.btn_settings = UIButton(width - 100, height - 40, 80, 30, "SETTINGS")
        self.btn_settings.on_click = lambda: self._navigate_to("settings")
        self.add_button(self.btn_settings)
    
    def _navigate_to(self, page_name):
        """Навигация на другую страницу"""
        if self.ui_manager:
            self.ui_manager.set_page(page_name)
            if self.ipc:
                self.ipc.set_ui_command("idle", page_name)
    
    def draw(self, display):
        """Нарисовать главное меню"""
        display.fill_screen(config.UI_BG_COLOR)
        
        # Заголовок
        display.draw_text(10, 5, "KELL31 MULTITOOL", config.COLOR_CYAN, config.UI_BG_COLOR)
        
        # Информация о состоянии
        if self.ipc:
            status_text = f"Core1: {self.ipc.core1_status}"
            display.draw_text(config.DISPLAY_WIDTH - 150, 5, status_text, config.COLOR_YELLOW, config.UI_BG_COLOR)
        
        self.needs_redraw = False

class JammerPage(UIPage):
    """Управление генератором помех"""
    
    def __init__(self, ipc=None, ui_manager=None):
        super().__init__("jammer")
        self.ipc = ipc
        self.ui_manager = ui_manager
        self._create_buttons()
    
    def _create_buttons(self):
        """Создать элементы управления джаммером"""
        width = config.DISPLAY_WIDTH
        
        # Кнопка START/STOP
        self.btn_start_stop = UIButton(20, 40, 200, 50, "START")
        self.btn_start_stop.on_click = self._toggle_jammer
        self.add_button(self.btn_start_stop)
        
        # Выбор режима
        y = 100
        self.btn_mode_cont = UIButton(20, y, 60, 30, "CONT")
        self.btn_mode_cont.on_click = lambda: self._set_mode(0)
        self.add_button(self.btn_mode_cont)
        
        self.btn_mode_sweep = UIButton(90, y, 60, 30, "SWEEP")
        self.btn_mode_sweep.on_click = lambda: self._set_mode(1)
        self.add_button(self.btn_mode_sweep)
        
        self.btn_mode_burst = UIButton(160, y, 60, 30, "BURST")
        self.btn_mode_burst.on_click = lambda: self._set_mode(2)
        self.add_button(self.btn_mode_burst)
        
        self.btn_mode_noise = UIButton(230, y, 60, 30, "NOISE")
        self.btn_mode_noise.on_click = lambda: self._set_mode(3)
        self.add_button(self.btn_mode_noise)
        
        # Управление частотой
        y = 150
        self.btn_freq_down = UIButton(20, y, 50, 30, "◀")
        self.btn_freq_down.on_click = self._decrease_freq
        self.add_button(self.btn_freq_down)
        
        self.btn_freq_up = UIButton(230, y, 50, 30, "▶")
        self.btn_freq_up.on_click = self._increase_freq
        self.add_button(self.btn_freq_up)
        
        # Управление мощностью
        y = 190
        self.btn_power_down = UIButton(20, y, 50, 30, "▼")
        self.btn_power_down.on_click = self._decrease_power
        self.add_button(self.btn_power_down)
        
        self.btn_power_up = UIButton(230, y, 50, 30, "▲")
        self.btn_power_up.on_click = self._increase_power
        self.add_button(self.btn_power_up)
        
        # Кнопка назад
        self.btn_back = UIButton(20, 250, 80, 30, "BACK")
        self.btn_back.on_click = lambda: self._navigate_to("dashboard")
        self.add_button(self.btn_back)
    
    def _toggle_jammer(self):
        """Включить/выключить джаммер"""
        if self.ipc:
            if self.ipc.jammer_active:
                self.ipc.set_ui_command("jammer_stop", "jammer")
                self.btn_start_stop.label = "START"
                self.btn_start_stop.bg_color = config.COLOR_GREEN
            else:
                self.ipc.set_ui_command("jammer_start", "jammer")
                self.btn_start_stop.label = "STOP"
                self.btn_start_stop.bg_color = config.COLOR_RED
            self.needs_redraw = True
    
    def _set_mode(self, mode):
        """Установить режим джаммера"""
        if self.ipc:
            self.ipc.jammer_mode = mode
            self.needs_redraw = True
    
    def _decrease_freq(self):
        """Уменьшить частоту"""
        if self.ipc:
            self.ipc.jammer_frequency = max(config.WIFI_24GHZ_MIN_FREQ, 
                                           self.ipc.jammer_frequency - 100_000_000)
            self.needs_redraw = True
    
    def _increase_freq(self):
        """Увеличить частоту"""
        if self.ipc:
            self.ipc.jammer_frequency = min(config.WIFI_5GHZ_MAX_FREQ,
                                           self.ipc.jammer_frequency + 100_000_000)
            self.needs_redraw = True
    
    def _decrease_power(self):
        """Уменьшить мощность"""
        if self.ipc:
            self.ipc.jammer_power = max(config.JAMMER_MIN_POWER_LEVEL,
                                       self.ipc.jammer_power - 10)
            self.needs_redraw = True
    
    def _increase_power(self):
        """Увеличить мощность"""
        if self.ipc:
            self.ipc.jammer_power = min(config.JAMMER_MAX_POWER_LEVEL,
                                       self.ipc.jammer_power + 10