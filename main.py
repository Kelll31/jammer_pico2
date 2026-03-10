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
from gui import GUI_Framework

class KELL31Jammer:
    """Основной класс джаммера"""
    
    def __init__(self):
        self.display = None
        self.touch = None
        self.jammer = None
        self.settings = None
        self.ui = None
        
        self.running = False
        self.last_status_print = 0
        self.last_touch_check = 0
        self.last_settings_save = 0
        
        # Multicore IPC
        self.rf_task_lock = _thread.allocate_lock()

        # Placeholder hardware integration variables
        self.radio_cc1101 = None
        self.radio_si4732 = None
        self.gui_framework = None

        # Состояния для отслеживания изменений
        self.last_freq_mode = None
        self.last_mode = None
        self.last_power = None
    
    def init_hardware(self):
        """Инициализация оборудования"""
        
        # Инициализация дисплея
        self.display = ILI9341()
        
        # Инициализация тачскрина
        self.touch = XPT2046()
        
        # Инициализация джаммера
        self.jammer = JammerSignal()
        
        # Инициализация настроек
        self.settings = Settings()
        
        # Применяем настройки к джаммеру
        self.settings.apply_to_jammer(self.jammer)
        
        # Инициализация UI
        self.ui = UIManager(self.display, self.jammer, self.settings)
        
        # Initializing the App-Based Touch GUI and external modules
        self.gui_framework = GUI_Framework(self.display, self.touch)

        # Загружаем главное меню LVGL
        self.gui_framework.render_main_menu()

        # Note: Proper bus initialization with CS handling should be done before.
        # This is basic initialization just for architecture setup.
        # self.radio_cc1101 = Radio_CC1101(spi_bus, config.CC1101_CS_PIN)
        # self.radio_si4732 = Radio_Si4732(i2c_bus)

        # Сохраняем начальные состояния
        self.last_freq_mode = self.jammer.get_freq_mode()
        self.last_mode = self.jammer.get_mode()
        self.last_power = self.jammer.get_power_level()
    
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
    
    def rf_core_loop(self):
        """Real-time RF Tasks running on Core 1"""
        while self.running:
            # Safely query / execute RF logic using thread lock
            self.rf_task_lock.acquire()
            try:
                # Polling CC1101, processing RX interrupts, handling buffers
                # Handling SI4732 without causing UI freezes
                pass
            finally:
                self.rf_task_lock.release()

            time.sleep_ms(1)

    def run(self):
        """Основной цикл программы (Core 0: UI и файловая система)"""
        self.running = True
        
        # Start Core 1 thread for RF Tasks
        _thread.start_new_thread(self.rf_core_loop, ())

        try:
            while self.running:
                # Обработка касаний и GUI (исключительно на Core 0)
                self.process_touch()
                
                # Обработка UI
                if self.ui:
                    self.ui.process()

                # Обработка событий и отрисовка LVGL (на Core 0)
                if self.gui_framework:
                    self.gui_framework.update()
                
                # Проверка изменений настроек
                self.check_settings_changes()
                
                # Вывод статуса (отключено)
                # self.print_status()
                
                # Небольшая задержка для снижения нагрузки на CPU
                time.sleep_ms(1)
                
        except KeyboardInterrupt:
            pass
        except Exception as e:
            pass
        finally:
            self.cleanup()
    
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