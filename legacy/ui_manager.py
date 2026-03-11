"""
UI менеджер для KELL31 Jammer с Dark Cyber Theme
Упрощённая версия с Global Status Bar и 8 экранами
"""

import time
import config

# ============================================================================
# GLOBAL STATUS BAR (Верхние 20 пикселей)
# ============================================================================

class GlobalStatusBar:
    """Глобальная строка состояния поверх всех окон"""
    
    def __init__(self, ipc=None):
        self.ipc = ipc
        self.height = 20
        self.last_update = time.ticks_ms()
        self.battery_level = 100
        
    def update(self, ipc=None):
        """Обновить данные статус-бара"""
        if ipc:
            self.ipc = ipc
        
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_update) >= 1000:
            self.last_update = current_time
            
            # Имитация разряда батареи
            self.battery_level = max(0, self.battery_level - 0.1)
            if self.battery_level <= 0:
                self.battery_level = 100
    
    def draw(self, display, current_page_name=""):
        """Нарисовать статус-бар"""
        # Фон статус-бара
        display.fill_rect(0, 0, config.DISPLAY_WIDTH, self.height, 0x0861)
        
        # Батарея слева
        battery_width = 30
        battery_height = 12
        battery_x = 5
        battery_y = (self.height - battery_height) // 2
        
        # Контур батареи
        display.draw_rectangle(battery_x, battery_y, battery_width, battery_height, config.COLOR_CYAN)
        # Заряд
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
        
        # Активные значки справа (если есть IPC)
        if self.ipc:
            icons_x = config.DISPLAY_WIDTH - 5
            if self.ipc.jammer_active:
                icons_x -= 16
                display.draw_text(icons_x, 4, "⚡", config.COLOR_CYAN, 0x0861)
            if self.ipc.subghz_scanning:
                icons_x -= 16
                display.draw_text(icons_x, 4, "📡", config.COLOR_CYAN, 0x0861)
        
        # Разделительная линия
        display.draw_line(0, self.height - 1, config.DISPLAY_WIDTH, self.height - 1, config.COLOR_DARKGRAY)

# ============================================================================
# БАЗОВЫЕ ВИДЖЕТЫ
# ============================================================================

class UIButton:
    """Простая кнопка UI"""

    def __init__(self, x, y, width, height, label,
                 color=config.UI_FONT_COLOR,
                 bg_color=config.UI_BUTTON_BG,
                 active_bg_color=config.UI_BUTTON_ACTIVE_BG):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.label = label
        self.color = color
        self.bg_color = bg_color
        self.active_bg_color = active_bg_color
        self.pressed = False
        self.on_click = None  # type: ignore
    
    def contains(self, x, y):
        """Проверить, содержит ли кнопка точку"""
        return self.x <= x < self.x + self.width and self.y <= y < self.y + self.height
    
    def draw(self, display):
        """Нарисовать кнопку"""
        bg_color = self.active_bg_color if self.pressed else self.bg_color
        
        # Фон кнопки
        display.fill_rect(self.x, self.y, self.width, self.height, bg_color)
        
        # Рамка
        display.draw_rectangle(self.x, self.y, self.width, self.height, config.UI_BUTTON_BORDER)
        
        # Текст
        text_x = self.x + (self.width - len(self.label) * 8) // 2
        text_y = self.y + (self.height - 12) // 2
        display.draw_text(text_x, text_y, self.label, self.color, bg_color)

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
    
    def handle_touch(self, x, y):
        """Обработать касание"""
        for button in self.buttons:
            if button.contains(x, y):
                if not button.pressed:
                    button.pressed = True
                    self.needs_redraw = True
                    if button.on_click:
                        button.on_click()
                return True
            elif button.pressed:
                button.pressed = False
                self.needs_redraw = True
        return False
    
    def handle_touch_release(self):
        """Сбросить состояние кнопок"""
        for button in self.buttons:
            if button.pressed:
                button.pressed = False
                self.needs_redraw = True
    
    def draw(self, display):
        """Нарисовать страницу (переопределить)"""
        pass
    
    def update(self, display):
        """Обновить отображение"""
        if self.needs_redraw:
            self.draw(display)
            for button in self.buttons:
                button.draw(display)
            self.needs_redraw = False
            return True
        return False

# ============================================================================
# 8 ЭКРАНОВ
# ============================================================================

class DashboardPage(UIPage):
    """Главное меню - сетка 2x2"""
    
    def __init__(self, ipc=None, ui_manager=None):
        super().__init__("dashboard")
        self.ipc = ipc
        self.ui_manager = ui_manager
        self._create_buttons()
    
    def _create_buttons(self):
        """Создать кнопки главного меню"""
        width = config.DISPLAY_WIDTH
        height = config.DISPLAY_HEIGHT - 20
        
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
        
        # Строка 3
        y += margin_y + btn_height
        self.btn_nrf24 = UIButton(margin_x, y, btn_width, btn_height, "NRF24")
        self.btn_nrf24.on_click = lambda: self._navigate_to("nrf24")
        self.add_button(self.btn_nrf24)
        
        self.btn_lora = UIButton(margin_x * 2 + btn_width, y, btn_width, btn_height, "LoRa")
        self.btn_lora.on_click = lambda: self._navigate_to("lora")
        self.add_button(self.btn_lora)
        
        # Кнопка настроек
        self.btn_settings = UIButton(width - 100, height - 40, 80, 30, "SETTINGS")
        self.btn_settings.on_click = lambda: self._navigate_to("settings")
        self.add_button(self.btn_settings)
    
    def _navigate_to(self, page_name):
        """Навигация на другую страницу"""
        if self.ui_manager:
            self.ui_manager.set_page(page_name)
    
    def draw(self, display):
        """Нарисовать главное меню"""
        display.fill_screen(config.UI_BG_COLOR)
        display.draw_text(10, 5, "KELL31 MULTITOOL", config.COLOR_CYAN, config.UI_BG_COLOR)
        
        if self.ipc:
            status_text = f"Core1: {self.ipc.core1_status}"
            display.draw_text(config.DISPLAY_WIDTH - 150, 5, status_text, config.COLOR_YELLOW, config.UI_BG_COLOR)

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
                                       self.ipc.jammer_power + 10)
            self.needs_redraw = True
    
    def _navigate_to(self, page_name):
        """Навигация на другую страницу"""
        if self.ui_manager:
            self.ui_manager.set_page(page_name)
    
    def draw(self, display):
        """Нарисовать страницу джаммера"""
        display.fill_screen(config.UI_BG_COLOR)
        display.draw_text(10, 5, "JAMMER CONTROL", config.COLOR_RED, config.UI_BG_COLOR)
        
        if self.ipc:
            # Частота
            freq_mhz = self.ipc.jammer_frequency / 1e6
            freq_text = f"Freq: {freq_mhz:.1f} MHz"
            display.draw_text(80, 155, freq_text, config.COLOR_CYAN, config.UI_BG_COLOR)
            
            # Мощность
            power_text = f"Power: {self.ipc.jammer_power}%"
            display.draw_text(80, 195, power_text, config.COLOR_YELLOW, config.UI_BG_COLOR)
            
            # Режим
            mode_names = ["CONT", "SWEEP", "BURST", "NOISE"]
            mode_text = f"Mode: {mode_names[self.ipc.jammer_mode]}"
            display.draw_text(10, 135, mode_text, config.COLOR_PURPLE, config.UI_BG_COLOR)
            
            # Статус
            status_text = "ACTIVE" if self.ipc.jammer_active else "IDLE"
            status_color = config.COLOR_RED if self.ipc.jammer_active else config.COLOR_GREEN
            display.draw_text(200, 55, status_text, status_color, config.UI_BG_COLOR)

class SubGhzPage(UIPage):
    """Интерфейс работы с CC1101 (Sub-GHz)"""
    
    def __init__(self, ipc=None, ui_manager=None):
        super().__init__("subghz")
        self.ipc = ipc
        self.ui_manager = ui_manager
        self._create_buttons()
    
    def _create_buttons(self):
        """Создать элементы управления Sub-GHz"""
        width = config.DISPLAY_WIDTH
        
        # Кнопки выбора частоты
        y = 40
        self.btn_freq_315 = UIButton(20, y, 80, 30, "315 MHz")
        self.btn_freq_315.on_click = lambda: self._set_frequency(config.CC1101_FREQ_315)
        self.add_button(self.btn_freq_315)
        
        self.btn_freq_433 = UIButton(110, y, 80, 30, "433 MHz")
        self.btn_freq_433.on_click = lambda: self._set_frequency(config.CC1101_FREQ_433)
        self.add_button(self.btn_freq_433)
        
        self.btn_freq_868 = UIButton(200, y, 80, 30, "868 MHz")
        self.btn_freq_868.on_click = lambda: self._set_frequency(config.CC1101_FREQ_868)
        self.add_button(self.btn_freq_868)
        
        # Кнопка сканирования
        y = 80
        self.btn_scan = UIButton(20, y, 260, 40, "SCAN")
        self.btn_scan.on_click = self._toggle_scan
        self.add_button(self.btn_scan)
        
        # Кнопка назад
        self.btn_back = UIButton(20, 250, 80, 30, "BACK")
        self.btn_back.on_click = lambda: self._navigate_to("dashboard")
        self.add_button(self.btn_back)
    
    def _set_frequency(self, freq):
        """Установить частоту Sub-GHz"""
        if self.ipc:
            self.ipc.subghz_frequency = freq
            self.needs_redraw = True
    
    def _toggle_scan(self):
        """Включить/выключить сканирование"""
        if self.ipc:
            if self.ipc.subghz_scanning:
                self.ipc.subghz_scanning = False
                self.btn_scan.label = "SCAN"
                self.btn_scan.bg_color = config.UI_BUTTON_BG
            else:
                self.ipc.set_ui_command("subghz_scan", "subghz")
                self.ipc.subghz_scanning = True
                self.btn_scan.label = "STOP"
                self.btn_scan.bg_color = config.COLOR_RED
            self.needs_redraw = True
    
    def _navigate_to(self, page_name):
        """Навигация на другую страницу"""
        if self.ui_manager:
            self.ui_manager.set_page(page_name)
    
    def draw(self, display):
        """Нарисовать страницу Sub-GHz"""
        display.fill_screen(config.UI_BG_COLOR)
        display.draw_text(10, 5, "SUB-GHz SCANNER", config.COLOR_CYAN, config.UI_BG_COLOR)
        
        if self.ipc:
            # Частота
            freq_mhz = self.ipc.subghz_frequency / 1e6
            freq_text = f"Frequency: {freq_mhz:.3f} MHz"
            display.draw_text(20, 130, freq_text, config.COLOR_YELLOW, config.UI_BG_COLOR)
            
            # RSSI
            rssi_text = f"RSSI: {self.ipc.subghz_rssi} dBm"
            display.draw_text(20, 150, rssi_text, config.COLOR_GREEN, config.UI_BG_COLOR)
            
            # Полоска RSSI
            bar_width = 200
            bar_height = 20
            bar_x = 40
            bar_y = 180
            
            # Фон полоски
            display.fill_rect(bar_x, bar_y, bar_width, bar_height, config.COLOR_DARKGRAY)
            
            # Заполнение (RSSI от -90 до -40 dBm)
            rssi_norm = max(0, min(100, int((self.ipc.subghz_rssi + 90) * 2)))
            fill_width = int(bar_width * rssi_norm / 100)
            
            # Цвет в зависимости от уровня сигнала
            if rssi_norm > 70:
                bar_color = config.COLOR_GREEN
            elif rssi_norm > 40:
                bar_color = config.COLOR_YELLOW
            else:
                bar_color = config.COLOR_RED
            
            display.fill_rect(bar_x, bar_y, fill_width, bar_height, bar_color)
            
            # Статус
            status_text = "SCANNING" if self.ipc.subghz_scanning else "IDLE"
            status_color = config.COLOR_RED if self.ipc.subghz_scanning else config.COLOR_GREEN
            display.draw_text(200, 85, status_text, status_color, config.UI_BG_COLOR)

# ============================================================================
# ОСТАЛЬНЫЕ СТРАНИЦЫ (упрощённые)
# ============================================================================

class RadioPage(UIPage):
    """Управление Si4732"""
    
    def __init__(self, ipc=None, ui_manager=None):
        super().__init__("radio")
        self.ipc = ipc
        self.ui_manager = ui_manager
        self._create_buttons()
    
    def _create_buttons(self):
        """Создать элементы управления радио"""
        width = config.DISPLAY_WIDTH
        
        # Кнопки диапазона
        y = 40
        self.btn_fm = UIButton(20, y, 80, 30, "FM")
        self.btn_fm.on_click = lambda: self._set_band("FM")
        self.add_button(self.btn_fm)
        
        self.btn_am = UIButton(110, y, 80, 30, "AM")
        self.btn_am.on_click = lambda: self._set_band("AM")
        self.add_button(self.btn_am)
        
        self.btn_sw = UIButton(200, y, 80, 30, "SW")
        self.btn_sw.on_click = lambda: self._set_band("SW")
        self.add_button(self.btn_sw)
        
        # Кнопки настройки
        y = 80
        self.btn_tune_down = UIButton(20, y, 50, 30, "◀")
        self.btn_tune_down.on_click = self._tune_down
        self.add_button(self.btn_tune_down)
        
        self.btn_tune_up = UIButton(230, y, 50, 30, "▶")
        self.btn_tune_up.on_click = self._tune_up
        self.add_button(self.btn_tune_up)
        
        # Кнопка назад
        self.btn_back = UIButton(20, 250, 80, 30, "BACK")
        self.btn_back.on_click = lambda: self._navigate_to("dashboard")
        self.add_button(self.btn_back)
    
    def _set_band(self, band):
        """Установить диапазон"""
        if self.ipc:
            self.ipc.radio_band = band
            self.needs_redraw = True
    
    def _tune_down(self):
        """Настроить вниз"""
        if self.ipc:
            self.ipc.radio_frequency -= 100_000  # 100 kHz
            self.needs_redraw = True
    
    def _tune_up(self):
        """Настроить вверх"""
        if self.ipc:
            self.ipc.radio_frequency += 100_000  # 100 kHz
            self.needs_redraw = True
    
    def _navigate_to(self, page_name):
        """Навигация на другую страницу"""
        if self.ui_manager:
            self.ui_manager.set_page(page_name)
    
    def draw(self, display):
        """Нарисовать страницу радио"""
        display.fill_screen(config.UI_BG_COLOR)
        display.draw_text(10, 5, "RADIO RECEIVER", config.COLOR_CYAN, config.UI_BG_COLOR)
        
        if self.ipc:
            # Частота
            freq_mhz = self.ipc.radio_frequency / 1e6
            freq_text = f"{freq_mhz:.3f} MHz"
            display.draw_text(100, 85, freq_text, config.COLOR_YELLOW, config.UI_BG_COLOR)
            
            # Диапазон
            band_text = f"Band: {self.ipc.radio_band}"
            display.draw_text(20, 130, band_text, config.COLOR_PURPLE, config.UI_BG_COLOR)
            
            # RSSI
            rssi_text = f"RSSI: {self.ipc.radio_rssi} dBµV"
            display.draw_text(20, 150, rssi_text, config.COLOR_GREEN, config.UI_BG_COLOR)

class SpectrumPage(UIPage):
    """Спектроанализатор"""
    
    def __init__(self, ipc=None, ui_manager=None):
        super().__init__("spectrum")
        self.ipc = ipc
        self.ui_manager = ui_manager
        self._create_buttons()
    
    def _create_buttons(self):
        """Создать элементы управления спектром"""
        # Кнопка назад
        self.btn_back = UIButton(20, 250, 80, 30, "BACK")
        self.btn_back.on_click = lambda: self._navigate_to("dashboard")
        self.add_button(self.btn_back)
    
    def _navigate_to(self, page_name):
        """Навигация на другую страницу"""
        if self.ui_manager:
            self.ui_manager.set_page(page_name)
    
    def draw(self, display):
        """Нарисовать спектр"""
        display.fill_screen(config.UI_BG_COLOR)
        display.draw_text(10, 5, "SPECTRUM ANALYZER", config.COLOR_CYAN, config.UI_BG_COLOR)
        
        if self.ipc:
            # Рисуем гистограмму спектра
            bar_width = 4
            bar_spacing = 1
            max_height = 150
            x = 20
            y_base = 200
            
            for i, value in enumerate(self.ipc.spectrum_data[:50]):  # Первые 50 точек
                bar_height = int(value * max_height / 100)
                display.fill_rect(x, y_base - bar_height, bar_width, bar_height, config.COLOR_CYAN)
                x += bar_width + bar_spacing

class NRF24Page(UIPage):
    """Сниффинг NRF24L01"""
    
    def __init__(self, ipc=None, ui_manager=None):
        super().__init__("nrf24")
        self.ipc = ipc
        self.ui_manager = ui_manager
        self._create_buttons()
    
    def _create_buttons(self):
        """Создать элементы управления NRF24"""
        width = config.DISPLAY_WIDTH
        
        # Кнопка сниффинга
        self.btn_sniff = UIButton(20, 40, 200, 50, "START SNIFF")
        self.btn_sniff.on_click = self._toggle_sniff
        self.add_button(self.btn_sniff)
        
        # Кнопка очистки
        self.btn_clear = UIButton(20, 100, 100, 30, "CLEAR")
        self.btn_clear.on_click = self._clear_packets
        self.add_button(self.btn_clear)
        
        # Кнопка назад
        self.btn_back = UIButton(20, 250, 80, 30, "BACK")
        self.btn_back.on_click = lambda: self._navigate_to("dashboard")
        self.add_button(self.btn_back)
    
    def _toggle_sniff(self):
        """Включить/выключить сниффинг"""
        if self.ipc:
            if self.ipc.nrf24_sniffing:
                self.ipc.nrf24_sniffing = False
                self.btn_sniff.label = "START SNIFF"
                self.btn_sniff.bg_color = config.UI_BUTTON_BG
            else:
                self.ipc.set_ui_command("nrf24_sniff", "nrf24")
                self.ipc.nrf24_sniffing = True
                self.btn_sniff.label = "STOP SNIFF"
                self.btn_sniff.bg_color = config.COLOR_RED
            self.needs_redraw = True
    
    def _clear_packets(self):
        """Очистить пакеты"""
        if self.ipc:
            self.ipc.clear_packets("nrf24")
            self.needs_redraw = True
    
    def _navigate_to(self, page_name):
        """Навигация на другую страницу"""
        if self.ui_manager:
            self.ui_manager.set_page(page_name)
    
    def draw(self, display):
        """Нарисовать страницу NRF24"""
        display.fill_screen(config.UI_BG_COLOR)
        display.draw_text(10, 5, "NRF24L01 SNIFFER", config.COLOR_CYAN, config.UI_BG_COLOR)
        
        if self.ipc:
            # Статус
            status_text = "SNIFFING" if self.ipc.nrf24_sniffing else "IDLE"
            status_color = config.COLOR_RED if self.ipc.nrf24_sniffing else config.COLOR_GREEN
            display.draw_text(200, 55, status_text, status_color, config.UI_BG_COLOR)
            
            # Количество пакетов
            count_text = f"Packets: {len(self.ipc.nrf24_packets)}"
            display.draw_text(20, 150, count_text, config.COLOR_YELLOW, config.UI_BG_COLOR)

class LoRaPage(UIPage):
    """Приём LoRa"""
    
    def __init__(self, ipc=None, ui_manager=None):
        super().__init__("lora")
        self.ipc = ipc
        self.ui_manager = ui_manager
        self._create_buttons()
    
    def _create_buttons(self):
        """Создать элементы управления LoRa"""
        width = config.DISPLAY_WIDTH
        
        # Кнопка приёма
        self.btn_receive = UIButton(20, 40, 200, 50, "START RX")
        self.btn_receive.on_click = self._toggle_receive
        self.add_button(self.btn_receive)
        
        # Кнопка очистки
        self.btn_clear = UIButton(20, 100, 100, 30, "CLEAR")
        self.btn_clear.on_click = self._clear_packets
        self.add_button(self.btn_clear)
        
        # Кнопка назад
        self.btn_back = UIButton(20, 250, 80, 30, "BACK")
        self.btn_back.on_click = lambda: self._navigate_to("dashboard")
        self.add_button(self.btn_back)
    
    def _toggle_receive(self):
        """Включить/выключить приём"""
        if self.ipc:
            if self.ipc.lora_receiving:
                self.ipc.lora_receiving = False
                self.btn_receive.label = "START RX"
                self.btn_receive.bg_color = config.UI_BUTTON_BG
            else:
                self.ipc.set_ui_command("lora_rx", "lora")
                self.ipc.lora_receiving = True
                self.btn_receive.label = "STOP RX"
                self.btn_receive.bg_color = config.COLOR_RED
            self.needs_redraw = True
    
    def _clear_packets(self):
        """Очистить пакеты"""
        if self.ipc:
            self.ipc.clear_packets("lora")
            self.needs_redraw = True
    
    def _navigate_to(self, page_name):
        """Навигация на другую страницу"""
        if self.ui_manager:
            self.ui_manager.set_page(page_name)
    
    def draw(self, display):
        """Нарисовать страницу LoRa"""
        display.fill_screen(config.UI_BG_COLOR)
        display.draw_text(10, 5, "LoRa RECEIVER", config.COLOR_CYAN, config.UI_BG_COLOR)
        
        if self.ipc:
            # Статус
            status_text = "RECEIVING" if self.ipc.lora_receiving else "IDLE"
            status_color = config.COLOR_RED if self.ipc.lora_receiving else config.COLOR_GREEN
            display.draw_text(200, 55, status_text, status_color, config.UI_BG_COLOR)
            
            # Количество пакетов
            count_text = f"Packets: {len(self.ipc.lora_packets)}"
            display.draw_text(20, 150, count_text, config.COLOR_YELLOW, config.UI_BG_COLOR)

class SettingsPage(UIPage):
    """Настройки системы"""
    
    def __init__(self, ipc=None, ui_manager=None):
        super().__init__("settings")
        self.ipc = ipc
        self.ui_manager = ui_manager
        self._create_buttons()
    
    def _create_buttons(self):
        """Создать элементы управления настройками"""
        width = config.DISPLAY_WIDTH
        
        # Кнопки яркости
        y = 40
        self.btn_bright_down = UIButton(120, y, 40, 30, "-")
        self.btn_bright_down.on_click = self._decrease_brightness
        self.add_button(self.btn_bright_down)
        
        self.btn_bright_up = UIButton(180, y, 40, 30, "+")
        self.btn_bright_up.on_click = self._increase_brightness
        self.add_button(self.btn_bright_up)
        
        # Кнопка вращения экрана
        y = 80
        self.btn_rotate = UIButton(120, y, 100, 30, "ROTATE")
        self.btn_rotate.on_click = self._rotate_screen
        self.add_button(self.btn_rotate)
        
        # Кнопка калибровки тачскрина
        y = 120
        self.btn_calibrate = UIButton(120, y, 100, 30, "CALIBRATE")
        self.btn_calibrate.on_click = self._calibrate_touch
        self.add_button(self.btn_calibrate)
        
        # Кнопка сброса
        y = 160
        self.btn_reset = UIButton(60, y, 120, 30, "RESET")
        self.btn_reset.bg_color = config.COLOR_RED
        self.btn_reset.on_click = self._reset_settings
        self.add_button(self.btn_reset)
        
        # Кнопка назад
        self.btn_back = UIButton(20, 250, 80, 30, "BACK")
        self.btn_back.on_click = lambda: self._navigate_to("dashboard")
        self.add_button(self.btn_back)
    
    def _decrease_brightness(self):
        """Уменьшить яркость"""
        # TODO: реализовать изменение яркости дисплея
        self.needs_redraw = True
    
    def _increase_brightness(self):
        """Увеличить яркость"""
        # TODO: реализовать изменение яркости дисплея
        self.needs_redraw = True
    
    def _rotate_screen(self):
        """Повернуть экран"""
        # TODO: реализовать вращение дисплея
        self.needs_redraw = True
    
    def _calibrate_touch(self):
        """Калибровать тачскрин"""
        # TODO: реализовать калибровку тачскрина
        self.needs_redraw = True
    
    def _reset_settings(self):
        """Сбросить настройки"""
        # TODO: реализовать сброс настроек
        self.needs_redraw = True
    
    def _navigate_to(self, page_name):
        """Навигация на другую страницу"""
        if self.ui_manager:
            self.ui_manager.set_page(page_name)
    
    def draw(self, display):
        """Нарисовать страницу настроек"""
        display.fill_screen(config.UI_BG_COLOR)
        display.draw_text(10, 5, "SETTINGS", config.COLOR_CYAN, config.UI_BG_COLOR)
        
        # Подписи
        display.draw_text(20, 45, "Brightness:", config.UI_FONT_COLOR, config.UI_BG_COLOR)
        display.draw_text(20, 85, "Rotation:", config.UI_FONT_COLOR, config.UI_BG_COLOR)
        display.draw_text(20, 125, "Touchscreen:", config.UI_FONT_COLOR, config.UI_BG_COLOR)
        display.draw_text(20, 165, "Factory reset:", config.UI_FONT_COLOR, config.UI_BG_COLOR)

# ============================================================================
# UI MANAGER
# ============================================================================

class UIManager:
    """Менеджер пользовательского интерфейса"""
    
    def __init__(self, display, ipc=None):
        self.display = display
        self.ipc = ipc
        self.status_bar = GlobalStatusBar(ipc)
        
        # Создаём страницы
        self.pages = {
            "dashboard": DashboardPage(ipc, self),
            "jammer": JammerPage(ipc, self),
            "subghz": SubGhzPage(ipc, self),
            "radio": RadioPage(ipc, self),
            "spectrum": SpectrumPage(ipc, self),
            "nrf24": NRF24Page(ipc, self),
            "lora": LoRaPage(ipc, self),
            "settings": SettingsPage(ipc, self),
        }
        
        self.current_page = "dashboard"
        self.last_update = time.ticks_ms()
    
    def set_page(self, page_name):
        """Установить текущую страницу"""
        if page_name in self.pages:
            self.current_page = page_name
            self.pages[page_name].needs_redraw = True
            return True
        return False
    
    def get_current_page(self):
        """Получить текущую страницу"""
        return self.pages[self.current_page]
    
    def handle_touch(self, x, y):
        """Обработать касание"""
        page = self.get_current_page()
        return page.handle_touch(x, y)
    
    def handle_touch_release(self):
        """Обработать отпускание касания"""
        page = self.get_current_page()
        page.handle_touch_release()
    
    def update(self):
        """Обновить UI"""
        current_time = time.ticks_ms()
        
        # Обновляем каждые 50 мс (20 FPS)
        if time.ticks_diff(current_time, self.last_update) >= 50:
            self.last_update = current_time
            
            # Обновляем статус-бар
            self.status_bar.update(self.ipc)
            
            # Обновляем текущую страницу
            page = self.get_current_page()
            if page.update(self.display):
                # Отрисовываем статус-бар поверх всего
                self.status_bar.draw(self.display, self.current_page)
                return True
        return False
    
    def process(self):
        """Обработать UI (вызывать в основном цикле)"""
        self.update()
