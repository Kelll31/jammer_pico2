"""
Главный файл KELL31 Jammer на MicroPython
Аналог C-версии kelll31_jammer.cpp
"""

import time
import config
import _thread
from ili9341 import ILI9341
from xpt2046 import XPT2046
from jammer_signal import JammerSignal
from settings import Settings
from ui_manager import UIManager
from radio_cc1101 import Radio_CC1101
from radio_si4732 import Radio_Si4732
from radio_nrf24 import Radio_NRF24
from radio_sx1278 import Radio_SX1278
from spi_manager import init_managers, spi0_manager, spi1_manager, i2c_manager
from gui import GUI_Framework

# ============================================================================
# IPC SHARED MEMORY (Межъядерное взаимодействие)
# ============================================================================

class IPC_SharedMemory:
    """Разделяемая память между Core 0 и Core 1"""
    
    def __init__(self):
        # Блокировка для атомарного доступа
        self.lock = _thread.allocate_lock()
        
        # Команды от UI (Core 0 -> Core 1)
        self.ui_command = "idle"  # idle, jammer_start, jammer_stop, subghz_scan, nrf24_sniff, lora_rx, radio_tune
        self.active_app = "dashboard"  # dashboard, jammer, subghz, nrf24, lora, radio, spectrum, settings
        
        # Параметры джаммера
        self.jammer_active = False
        self.jammer_frequency = config.WIFI_24GHZ_MIN_FREQ
        self.jammer_mode = 0  # 0=continuous, 1=sweep, 2=burst, 3=noise
        self.jammer_power = config.JAMMER_DEFAULT_POWER_LEVEL
        
        # Параметры Sub-GHz (CC1101)
        self.subghz_frequency = config.CC1101_FREQ_433
        self.subghz_rssi = 0
        self.subghz_scanning = False
        
        # Параметры NRF24L01
        self.nrf24_channel = config.NRF24_DEFAULT_CHANNEL
        self.nrf24_sniffing = False
        self.nrf24_packets = []
        
        # Параметры LoRa (SX1278)
        self.lora_frequency = config.LORA_DEFAULT_FREQ
        self.lora_spreading_factor = 7
        self.lora_bandwidth = 125000
        self.lora_receiving = False
        self.lora_packets = []
        
        # Параметры Radio (Si4732)
        self.radio_frequency = 100_000_000  # 100 MHz FM
        self.radio_band = "FM"  # FM или AM
        self.radio_rssi = 0
        
        # Буфер спектра (заполняется Core 1)
        self.spectrum_data = [0] * config.SPECTRUM_BUFFER_SIZE
        
        # Статус Core 1
        self.core1_status = "idle"
        self.core1_last_update = time.ticks_ms()
        
        # Ошибки
        self.error_code = 0
        self.error_message = ""
    
    def set_ui_command(self, command, app=None):
        """Установить команду от UI (вызывается Core 0)"""
        with self.lock:
            self.ui_command = command
            if app:
                self.active_app = app
    
    def get_ui_command(self):
        """Получить текущую команду (вызывается Core 1)"""
        with self.lock:
            cmd = self.ui_command
            self.ui_command = "idle"  # Сброс после чтения
            return cmd
    
    def update_rssi(self, rssi, source="subghz"):
        """Обновить RSSI (вызывается Core 1)"""
        with self.lock:
            if source == "subghz":
                self.subghz_rssi = rssi
            elif source == "radio":
                self.radio_rssi = rssi
    
    def update_spectrum(self, data):
        """Обновить данные спектра (вызывается Core 1)"""
        with self.lock:
            if len(data) == len(self.spectrum_data):
                self.spectrum_data = data.copy()
    
    def add_packet(self, packet, source="nrf24"):
        """Добавить пакет в буфер (вызывается Core 1)"""
        with self.lock:
            if source == "nrf24":
                self.nrf24_packets.append(packet)
                if len(self.nrf24_packets) > config.MAX_PACKETS_BUFFER:
                    self.nrf24_packets.pop(0)
            elif source == "lora":
                self.lora_packets.append(packet)
                if len(self.lora_packets) > config.MAX_PACKETS_BUFFER:
                    self.lora_packets.pop(0)
    
    def clear_packets(self, source="nrf24"):
        """Очистить буфер пакетов (вызывается Core 0)"""
        with self.lock:
            if source == "nrf24":
                self.nrf24_packets = []
            elif source == "lora":
                self.lora_packets = []
    
    def set_error(self, code, message):
        """Установить ошибку (вызывается Core 1)"""
        with self.lock:
            self.error_code = code
            self.error_message = message
    
    def clear_error(self):
        """Очистить ошибку (вызывается Core 0)"""
        with self.lock:
            self.error_code = 0
            self.error_message = ""

# ============================================================================
# ОСНОВНОЙ КЛАСС ДЖАММЕРА
# ============================================================================

class KELL31Jammer:
    """Основной класс джаммера"""
    
    def __init__(self):
        self.display = None
        self.touch = None
        self.jammer = None
        self.settings = None
        self.ui = None
        
        # Менеджеры шин
        self.spi0_manager = None
        self.spi1_manager = None
        self.i2c_manager = None
        
        # RF модули
        self.radio_cc1101 = None
        self.radio_nrf24 = None
        self.radio_sx1278 = None
        self.radio_si4732 = None
        
        # GUI фреймворк
        self.gui_framework = None
        
        # Состояния
        self.running = False
        self.last_status_print = 0
        self.last_touch_check = 0
        self.last_settings_save = 0
        
        # IPC Shared Memory
        self.ipc = IPC_SharedMemory()
        
        # Состояния для отслеживания изменений
        self.last_freq_mode = None
        self.last_mode = None
        self.last_power = None
    
    def init_hardware(self):
        """Инициализация оборудования"""
        
        # Инициализация менеджеров шин
        self.spi0_manager, self.spi1_manager, self.i2c_manager = init_managers()
        
        # Инициализация дисплея (использует SPI0 через менеджер)
        self.display = ILI9341()
        
        # Инициализация тачскрина
        self.touch = XPT2046()
        
        # Инициализация джаммера
        self.jammer = JammerSignal()
        
        # Инициализация настроек
        self.settings = Settings()
        
        # Применяем настройки к джаммеру
        self.settings.apply_to_jammer(self.jammer)
        
        # Инициализация UI (будет обновлена в Шаге 3)
        self.ui = UIManager(self.display, self.jammer, self.settings)
        
        # Инициализация RF модулей (заглушки, будут реализованы в Шаге 2)
        try:
            # CC1101
            self.radio_cc1101 = Radio_CC1101(self.spi1_manager, config.CC1101_CS_PIN)
            # NRF24L01
            self.radio_nrf24 = Radio_NRF24(self.spi1_manager, config.NRF24L01_CS_PIN, config.NRF24L01_CE_PIN)
            # SX1278
            self.radio_sx1278 = Radio_SX1278(self.spi1_manager, config.SX1278_CS_PIN, config.SX1278_RST_PIN)
            # Si4732
            self.radio_si4732 = Radio_Si4732(self.i2c_manager)
        except Exception as e:
            print(f"Warning: RF modules initialization failed: {e}")
            # Продолжаем без RF модулей
        
        # GUI фреймворк (устаревший, будет заменён в Шаге 3)
        self.gui_framework = GUI_Framework(self.display, self.touch)
        self.gui_framework.render_main_menu()

        # Сохраняем начальные состояния
        self.last_freq_mode = self.jammer.get_freq_mode()
        self.last_mode = self.jammer.get_mode()
        self.last_power = self.jammer.get_power_level()
        
        # Синхронизация IPC с текущим состоянием джаммера
        self.ipc.jammer_active = self.jammer.is_enabled()
        self.ipc.jammer_frequency = self.jammer.get_frequency()
        self.ipc.jammer_mode = self.jammer.get_mode()
        self.ipc.jammer_power = self.jammer.get_power_level()
    
    def print_startup_info(self):
        """Вывести информацию при запуске (отключено)"""
        pass
    
    def process_touch(self):
        """Обработка касаний"""
        if not self.touch or not self.ui:
            return
            
        current_time = time.ticks_ms()
        
        # Проверяем касание каждые 10 мс
        if time.ticks_diff(current_time, self.last_touch_check) >= 10:
            self.last_touch_check = current_time
            
            if self.touch.is_touched():
                # Получаем координаты касания
                screen_x, screen_y, valid = self.touch.get_touch_coordinates()
                
                if valid:
                    # Обрабатываем касание в UI
                    self.ui.handle_touch(screen_x, screen_y)
                else:
                    # Сбрасываем состояния кнопок
                    self.ui.handle_touch_release()
            else:
                # Нет касания - сбрасываем состояния
                self.ui.handle_touch_release()
    
    def check_settings_changes(self):
        """Проверить изменения настроек для сохранения"""
        if not self.jammer or not self.settings:
            return
            
        current_time = time.ticks_ms()
        
        # Проверяем каждую секунду
        if time.ticks_diff(current_time, self.last_settings_save) >= 1000:
            self.last_settings_save = current_time
            
            current_freq = self.jammer.get_freq_mode()
            current_mode = self.jammer.get_mode()
            current_power = self.jammer.get_power_level()
            
            # Если настройки изменились, сохраняем
            if (current_freq != self.last_freq_mode or 
                current_mode != self.last_mode or 
                current_power != self.last_power):
                
                self.settings.save_from_jammer(self.jammer)
                
                self.last_freq_mode = current_freq
                self.last_mode = current_mode
                self.last_power = current_power
    
    def print_status(self):
        """Вывести статус в консоль (отключено)"""
        pass
    
    def rf_core_loop_state_machine(self):
        """
        State machine для Core 1 (Real-time RF задачи)
        Выполняется без блокирующих вызовов time.sleep()
        """
        last_update = time.ticks_ms()
        last_spectrum_update = time.ticks_ms()
        
        while self.running:
            current_time = time.ticks_ms()
            
            # Чтение команды от UI
            command = self.ipc.get_ui_command()
            
            # Обработка команд
            if command == "jammer_start":
                self.jammer.enable(True)
                self.ipc.jammer_active = True
                self.ipc.core1_status = "jammer_active"
            elif command == "jammer_stop":
                self.jammer.enable(False)
                self.ipc.jammer_active = False
                self.ipc.core1_status = "idle"
            elif command == "subghz_scan":
                self.ipc.subghz_scanning = True
                self.ipc.core1_status = "subghz_scanning"
            elif command == "nrf24_sniff":
                self.ipc.nrf24_sniffing = True
                self.ipc.core1_status = "nrf24_sniffing"
            elif command == "lora_rx":
                self.ipc.lora_receiving = True
                self.ipc.core1_status = "lora_receiving"
            elif command == "radio_tune":
                self.ipc.core1_status = "radio_tuning"
            
            # Обновление состояния джаммера (если активен)
            if self.ipc.jammer_active and self.jammer:
                self.jammer.process()
                # Синхронизация параметров из IPC
                self.jammer.set_frequency(self.ipc.jammer_frequency)
                self.jammer.set_mode(self.ipc.jammer_mode)
                self.jammer.set_power_level(self.ipc.jammer_power)
            
            # Обработка активного приложения
            if self.ipc.active_app == "subghz" and self.ipc.subghz_scanning:
                # Опрос CC1101
                if self.radio_cc1101 and time.ticks_diff(current_time, last_update) >= 50:  # 20 Hz
                    try:
                        with self.spi1_manager.acquire_cc1101():
                            rssi = self.radio_cc1101.read_rssi()
                            self.ipc.update_rssi(rssi, "subghz")
                    except Exception as e:
                        self.ipc.set_error(1, f"CC1101 error: {e}")
                    last_update = current_time
            
            elif self.ipc.active_app == "nrf24" and self.ipc.nrf24_sniffing:
                # Сниффинг NRF24
                if self.radio_nrf24 and time.ticks_diff(current_time, last_update) >= 100:  # 10 Hz
                    try:
                        with self.spi1_manager.acquire_nrf24():
                            packets = self.radio_nrf24.sniff_packets()
                            for pkt in packets:
                                self.ipc.add_packet(pkt, "nrf24")
                    except Exception as e:
                        self.ipc.set_error(2, f"NRF24 error: {e}")
                    last_update = current_time
            
            elif self.ipc.active_app == "lora" and self.ipc.lora_receiving:
                # Приём LoRa
                if self.radio_sx1278 and time.ticks_diff(current_time, last_update) >= 200:  # 5 Hz
                    try:
                        with self.spi1_manager.acquire_sx1278():
                            packets = self.radio_sx1278.receive_packets()
                            for pkt in packets:
                                self.ipc.add_packet(pkt, "lora")
                    except Exception as e:
                        self.ipc.set_error(3, f"SX1278 error: {e}")
                    last_update = current_time
            
            elif self.ipc.active_app == "radio":
                # Опрос Si4732
                if self.radio_si4732 and time.ticks_diff(current_time, last_update) >= 100:  # 10 Hz
                    try:
                        with self.i2c_manager.acquire():
                            rssi = self.radio_si4732.read_rssi()
                            self.ipc.update_rssi(rssi, "radio")
                    except Exception as e:
                        self.ipc.set_error(4, f"Si4732 error: {e}")
                    last_update = current_time
            
            # Обновление спектра (имитация)
            if time.ticks_diff(current_time, last_spectrum_update) >= 500:  # 2 Hz
                # Генерация тестовых данных спектра
                import random
                spectrum = [random.randint(0, 100) for _ in range(config.SPECTRUM_BUFFER_SIZE)]
                self.ipc.update_spectrum(spectrum)
                last_spectrum_update = current_time
            
            # Обновление времени последнего обновления Core 1
            self.ipc.core1_last_update = current_time
            
            # Неблокирующая задержка (используем time.ticks_diff для контроля частоты)
            # Цикл работает на частоте ~100 Hz (10 мс)
            elapsed = time.ticks_diff(time.ticks_ms(), current_time)
            if elapsed < 10:  # Минимальный интервал 10 мс
                # Используем time.sleep_us для микросекундной задержки
                time.sleep_us((10 - elapsed) * 1000)
    
    def rf_core_loop(self):
        """Real-time RF Tasks running on Core 1 (обёртка для совместимости)"""
        try:
            self.rf_core_loop_state_machine()
        except Exception as e:
            self.ipc.set_error(99, f"Core 1 crash: {e}")

    def run(self):
        """Основной цикл программы (Core 0: UI и файловая система)"""
        self.running = True
        
        # Start Core 1 thread for RF Tasks
        _thread.start_new_thread(self.rf_core_loop, ())

        try:
            # Инициализация Global Status Bar
            from ui_manager_new import GlobalStatusBar, DashboardPage, JammerPage, SubGhzPage
            status_bar = GlobalStatusBar(self.ipc)
            
            # Создание простого UI менеджера
            current_page = "dashboard"
            last_page_update = time.ticks_ms()
            
            while self.running:
                current_time = time.ticks_ms()
                
                # Обработка касаний (упрощённая)
                self.process_touch()
                
                # Обновление статус-бара
                status_bar.update(self.ipc)
                
                # Обновление UI каждые 50 мс (20 FPS)
                if time.ticks_diff(current_time, last_page_update) >= 50:
                    last_page_update = current_time
                    
                    # Очистка экрана (кроме статус-бара)
                    self.display.fill_rect(0, status_bar.height, config.DISPLAY_WIDTH, 
                                         config.DISPLAY_HEIGHT - status_bar.height, config.UI_BG_COLOR)
                    
                    # Отрисовка текущей страницы
                    if current_page == "dashboard":
                        self._draw_dashboard_page()
                    elif current_page == "jammer":
                        self._draw_jammer_page()
                    elif current_page == "subghz":
                        self._draw_subghz_page()
                    # TODO: добавить остальные страницы
                    
                    # Отрисовка статус-бара поверх всего
                    status_bar.draw(self.display, current_page)
                    
                    # Обмен буферов дисплея
                    self.display.swap_buffers()
                
                # Проверка изменений настроек
                self.check_settings_changes()
                
                # Небольшая задержка для снижения нагрузки на CPU
                time.sleep_ms(1)
                
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"UI Error: {e}")
        finally:
            self.cleanup()
    
    def _draw_dashboard_page(self):
        """Отрисовка главного меню"""
        display = self.display
        status_bar_height = 20
        
        # Заголовок
        display.draw_text(10, status_bar_height + 5, "KELL31 MULTITOOL", config.COLOR_CYAN, config.UI_BG_COLOR)
        
        # Информация о состоянии
        status_text = f"Core1: {self.ipc.core1_status}"
        display.draw_text(config.DISPLAY_WIDTH - 150, status_bar_height + 5, status_text, config.COLOR_YELLOW, config.UI_BG_COLOR)
        
        # Сетка кнопок (упрощённая)
        btn_width = 100
        btn_height = 60
        margin_x = (config.DISPLAY_WIDTH - btn_width * 2) // 3
        margin_y = 40
        
        y = status_bar_height + 30
        display.draw_rectangle(margin_x, y, btn_width, btn_height, config.COLOR_CYAN)
        display.draw_text(margin_x + 20, y + 20, "JAMMER", config.COLOR_CYAN, config.UI_BG_COLOR)
        
        display.draw_rectangle(margin_x * 2 + btn_width, y, btn_width, btn_height, config.COLOR_CYAN)
        display.draw_text(margin_x * 2 + btn_width + 10, y + 20, "SUB-GHz", config.COLOR_CYAN, config.UI_BG_COLOR)
        
        y += margin_y + btn_height
        display.draw_rectangle(margin_x, y, btn_width, btn_height, config.COLOR_CYAN)
        display.draw_text(margin_x + 20, y + 20, "RADIO", config.COLOR_CYAN, config.UI_BG_COLOR)
        
        display.draw_rectangle(margin_x * 2 + btn_width, y, btn_width, btn_height, config.COLOR_CYAN)
        display.draw_text(margin_x * 2 + btn_width + 10, y + 20, "SPECTRUM", config.COLOR_CYAN, config.UI_BG_COLOR)
    
    def _draw_jammer_page(self):
        """Отрисовка страницы джаммера"""
        display = self.display
        status_bar_height = 20
        
        # Заголовок
        display.draw_text(10, status_bar_height + 5, "JAMMER CONTROL", config.COLOR_RED, config.UI_BG_COLOR)
        
        # Статус
        status_text = "ACTIVE" if self.ipc.jammer_active else "IDLE"
        status_color = config.COLOR_RED if self.ipc.jammer_active else config.COLOR_GREEN
        display.draw_text(200, status_bar_height + 5, status_text, status_color, config.UI_BG_COLOR)
        
        # Параметры
        freq_mhz = self.ipc.jammer_frequency / 1e6
        freq_text = f"Freq: {freq_mhz:.1f} MHz"
        display.draw_text(20, status_bar_height + 40, freq_text, config.COLOR_CYAN, config.UI_BG_COLOR)
        
        power_text = f"Power: {self.ipc.jammer_power}%"
        display.draw_text(20, status_bar_height + 60, power_text, config.COLOR_YELLOW, config.UI_BG_COLOR)
        
        mode_names = ["CONT", "SWEEP", "BURST", "NOISE"]
        mode_text = f"Mode: {mode_names[self.ipc.jammer_mode]}"
        display.draw_text(20, status_bar_height + 80, mode_text, config.COLOR_PURPLE, config.UI_BG_COLOR)
    
    def _draw_subghz_page(self):
        """Отрисовка страницы Sub-GHz"""
        display = self.display
        status_bar_height = 20
        
        # Заголовок
        display.draw_text(10, status_bar_height + 5, "SUB-GHz SCANNER", config.COLOR_CYAN, config.UI_BG_COLOR)
        
        # Частота
        freq_mhz = self.ipc.subghz_frequency / 1e6
        freq_text = f"Frequency: {freq_mhz:.3f} MHz"
        display.draw_text(20, status_bar_height + 40, freq_text, config.COLOR_YELLOW, config.UI_BG_COLOR)
        
        # RSSI
        rssi_text = f"RSSI: {self.ipc.subghz_rssi} dBm"
        display.draw_text(20, status_bar_height + 60, rssi_text, config.COLOR_GREEN, config.UI_BG_COLOR)
        
        # Полоска RSSI
        bar_width = 200
        bar_height = 20
        bar_x = 40
        bar_y = status_bar_height + 90
        
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
        
        # Статус сканирования
        status_text = "SCANNING" if self.ipc.subghz_scanning else "IDLE"
        status_color = config.COLOR_RED if self.ipc.subghz_scanning else config.COLOR_GREEN
        display.draw_text(200, status_bar_height + 120, status_text, status_color, config.UI_BG_COLOR)
    
    def cleanup(self):
        """Очистка ресурсов при завершении"""
        if self.jammer:
            self.jammer.disable()
        
        if self.display:
            self.display.display_off()
        
        self.running = False
    
    def start(self):
        """Запуск джаммера"""
        try:
            self.print_startup_info()
            self.init_hardware()
            self.run()
        except Exception as e:
            self.cleanup()

def main():
    """Точка входа программы"""
    
    # Создаём и запускаем джаммер
    jammer = KELL31Jammer()
    jammer.start()

# Запуск программы
if __name__ == "__main__":
    main()