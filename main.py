"""
Главный файл KELL31 Jammer на MicroPython
Аналог C-версии kelll31_jammer.cpp
"""

import time
import config
from ili9341 import ILI9341
from xpt2046 import XPT2046
from jammer_signal import JammerSignal
from settings import Settings
from ui_manager import UIManager

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
        
        # Состояния для отслеживания изменений
        self.last_freq_mode = None
        self.last_mode = None
        self.last_power = None
    
    def init_hardware(self):
        """Инициализация оборудования"""
        print("Инициализация оборудования...")
        
        # Инициализация дисплея
        print("  Инициализация дисплея ILI9341...")
        self.display = ILI9341()
        print(f"    Дисплей инициализирован ({config.DISPLAY_WIDTH}x{config.DISPLAY_HEIGHT})")
        
        # Инициализация тачскрина
        print("  Инициализация тачскрина XPT2046...")
        self.touch = XPT2046()
        print("    Тачскрин инициализирован")
        
        # Инициализация джаммера
        print("  Инициализация джаммера...")
        self.jammer = JammerSignal()
        print("    Джаммер инициализирован")
        
        # Инициализация настроек
        print("  Инициализация настроек...")
        self.settings = Settings()
        print("    Настройки инициализированы")
        
        # Применяем настройки к джаммеру
        self.settings.apply_to_jammer(self.jammer)
        
        # Инициализация UI
        print("  Инициализация UI...")
        self.ui = UIManager(self.display, self.jammer, self.settings)
        print("    UI инициализирован")
        
        # Сохраняем начальные состояния
        self.last_freq_mode = self.jammer.get_freq_mode()
        self.last_mode = self.jammer.get_mode()
        self.last_power = self.jammer.get_power_level()
        
        print("Оборудование инициализировано успешно!")
    
    def print_startup_info(self):
        """Вывести информацию при запуске"""
        print("\n" + "="*50)
        print("KELL31 JAMMER v{}.{}.{}".format(
            config.FIRMWARE_VERSION_MAJOR,
            config.FIRMWARE_VERSION_MINOR,
            config.FIRMWARE_VERSION_PATCH
        ))
        print("="*50)
        print(f"Дисплей: {config.DISPLAY_WIDTH}x{config.DISPLAY_HEIGHT}")
        print(f"Частота SPI дисплея: {config.DISPLAY_SPI_FREQ} Гц")
        print(f"Пин джаммера: GP{config.JAMMER_SIGNAL_PIN}")
        print(f"Пин LED: GP{config.JAMMER_LED_PIN}")
        print("="*50 + "\n")
    
    def process_touch(self):
        """Обработка касаний"""
        if not self.touch or not self.ui:
            return
            
        current_time = time.ticks_ms()
        
        # Проверяем касание каждые 10 мс
        if time.ticks_diff(current_time, self.last_touch_check) >= 10:
            self.last_touch_check = current_time
            
            # Получаем координаты касания
            screen_x, screen_y, valid = self.touch.get_touch_coordinates()
            
            if valid:
                # Обрабатываем касание в UI
                self.ui.handle_touch(screen_x, screen_y)
                
                # Задержка для предотвращения множественных срабатываний
                time.sleep_ms(50)
    
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
        """Вывести статус в консоль"""
        if not self.jammer:
            return
            
        current_time = time.ticks_ms()
        
        # Выводим статус каждую секунду
        if time.ticks_diff(current_time, self.last_status_print) >= 1000:
            self.last_status_print = current_time
            
            state = self.jammer.get_state()
            freq_mode = self.jammer.get_freq_mode()
            mode = self.jammer.get_mode()
            power = self.jammer.get_power_level()
            
            state_name = JammerSignal.get_state_name(state)
            freq_name = JammerSignal.get_freq_name(freq_mode)
            mode_name = JammerSignal.get_mode_name(mode)
            
            print(f"State: {state_name} | Freq: {freq_name} | Mode: {mode_name} | Power: {power}%")
    
    def run(self):
        """Основной цикл программы"""
        print("Запуск основного цикла...")
        self.running = True
        
        try:
            while self.running:
                # Обработка касаний
                self.process_touch()
                
                # Обработка UI (включает обработку джаммера)
                if self.ui:
                    self.ui.process()
                
                # Проверка изменений настроек
                self.check_settings_changes()
                
                # Вывод статуса
                self.print_status()
                
                # Небольшая задержка для снижения нагрузки на CPU
                time.sleep_ms(1)
                
        except KeyboardInterrupt:
            print("\nОстановка по запросу пользователя...")
        except Exception as e:
            print(f"\nКритическая ошибка: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Очистка ресурсов при завершении"""
        print("Очистка ресурсов...")
        
        if self.jammer:
            self.jammer.disable()
            print("  Джаммер выключен")
        
        if self.display:
            self.display.display_off()
            print("  Дисплей выключен")
        
        self.running = False
        print("Ресурсы очищены")
    
    def start(self):
        """Запуск джаммера"""
        try:
            self.print_startup_info()
            self.init_hardware()
            self.run()
        except Exception as e:
            print(f"Ошибка при запуске: {e}")
            import traceback
            traceback.print_exc()
            self.cleanup()

def main():
    """Точка входа программы"""
    print("="*50)
    print("Запуск KELL31 Jammer на MicroPython")
    print("="*50)
    
    # Создаём и запускаем джаммер
    jammer = KELL31Jammer()
    jammer.start()
    
    print("\n" + "="*50)
    print("Программа завершена")
    print("="*50)

# Запуск программы
if __name__ == "__main__":
    main()