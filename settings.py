"""
Сохранение настроек джаммера в JSON файл
"""

import json
import os
import config
from jammer_signal import JammerMode, JammerFreq

class Settings:
    """Класс для работы с настройками джаммера"""
    
    def __init__(self, filename=config.SETTINGS_FILE):
        self.filename = filename
        self.data = self._get_default_settings()
        self.loaded = False
        
        # Загружаем настройки при инициализации
        self.load()
    
    def _get_default_settings(self):
        """Получить настройки по умолчанию"""
        return {
            'version': {
                'major': config.FIRMWARE_VERSION_MAJOR,
                'minor': config.FIRMWARE_VERSION_MINOR,
                'patch': config.FIRMWARE_VERSION_PATCH
            },
            'jammer': {
                'frequency_mode': JammerFreq.WIFI_24GHZ,
                'mode': JammerMode.CONTINUOUS,
                'power_level': config.JAMMER_DEFAULT_POWER_LEVEL,
                'custom_freq_hz': 0
            },
            'touch_calibration': {
                'kx1': 0.0,
                'kx2': 0.0,
                'kx3': 0.0,
                'ky1': 0.0,
                'ky2': 0.0,
                'ky3': 0.0
            },
            'display': {
                'brightness': 80,
                'rotation': 0
            }
        }
    
    def load(self):
        """Загрузить настройки из файла"""
        try:
            # В MicroPython используем try/except для проверки существования файла
            try:
                with open(self.filename, 'r') as f:
                    loaded_data = json.load(f)
                
                # Проверяем версию
                if 'version' in loaded_data:
                    # Можно добавить миграцию версий здесь
                    pass
                
                # Обновляем настройки
                self._merge_settings(loaded_data)
                self.loaded = True
                print(f"Настройки загружены из {self.filename}")
                return True
            except OSError:
                # Файл не существует
                print(f"Файл настроек {self.filename} не найден, используются настройки по умолчанию")
                return False
                
        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")
            return False
    
    def save(self):
        """Сохранить настройки в файл"""
        try:
            with open(self.filename, 'w') as f:
                # MicroPython json.dump не поддерживает indent, сохраняем без форматирования
                json.dump(self.data, f)
            print(f"Настройки сохранены в {self.filename}")
            return True
        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")
            return False
    
    def _merge_settings(self, new_data):
        """Объединить загруженные настройки с текущими"""
        def merge_dicts(base, new):
            for key, value in new.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    merge_dicts(base[key], value)
                else:
                    base[key] = value
        
        merge_dicts(self.data, new_data)
    
    def reset(self):
        """Сбросить настройки к значениям по умолчанию"""
        self.data = self._get_default_settings()
        self.save()
    
    # ============================================================================
    # ГЕТТЕРЫ ДЛЯ НАСТРОЕК ДЖАММЕРА
    # ============================================================================
    
    def get_jammer_settings(self):
        """Получить настройки джаммера"""
        return self.data.get('jammer', {})
    
    def get_frequency_mode(self):
        """Получить режим частоты"""
        return self.data['jammer'].get('frequency_mode', JammerFreq.WIFI_24GHZ)
    
    def get_mode(self):
        """Получить режим работы"""
        return self.data['jammer'].get('mode', JammerMode.CONTINUOUS)
    
    def get_power_level(self):
        """Получить уровень мощности"""
        return self.data['jammer'].get('power_level', config.JAMMER_DEFAULT_POWER_LEVEL)
    
    def get_custom_frequency(self):
        """Получить пользовательскую частоту"""
        return self.data['jammer'].get('custom_freq_hz', 0)
    
    # ============================================================================
    # СЕТТЕРЫ ДЛЯ НАСТРОЕК ДЖАММЕРА
    # ============================================================================
    
    def set_frequency_mode(self, freq_mode):
        """Установить режим частоты"""
        self.data['jammer']['frequency_mode'] = freq_mode
    
    def set_mode(self, mode):
        """Установить режим работы"""
        self.data['jammer']['mode'] = mode
    
    def set_power_level(self, power_level):
        """Установить уровень мощности"""
        self.data['jammer']['power_level'] = power_level
    
    def set_custom_frequency(self, freq_hz):
        """Установить пользовательскую частоту"""
        self.data['jammer']['custom_freq_hz'] = freq_hz
    
    # ============================================================================
    # НАСТРОЙКИ КАЛИБРОВКИ ТАЧСКРИНА
    # ============================================================================
    
    def get_touch_calibration(self):
        """Получить калибровку тачскрина (матрицу)"""
        return self.data.get('touch_calibration', {})
    
    def set_touch_calibration(self, cmat):
        """Установить калибровку тачскрина из объекта CalibrationMat"""
        if cmat is None:
            return
        self.data['touch_calibration'] = {
            'kx1': cmat.KX1,
            'kx2': cmat.KX2,
            'kx3': cmat.KX3,
            'ky1': cmat.KY1,
            'ky2': cmat.KY2,
            'ky3': cmat.KY3
        }
    
    # ============================================================================
    # НАСТРОЙКИ ДИСПЛЕЯ
    # ============================================================================
    
    def get_display_settings(self):
        """Получить настройки дисплея"""
        return self.data.get('display', {})
    
    def get_brightness(self):
        """Получить яркость подсветки"""
        return self.data['display'].get('brightness', 80)
    
    def get_rotation(self):
        """Получить ориентацию дисплея"""
        return self.data['display'].get('rotation', 0)
    
    def set_brightness(self, brightness):
        """Установить яркость подсветки"""
        if brightness < 0:
            brightness = 0
        if brightness > 100:
            brightness = 100
        self.data['display']['brightness'] = brightness
    
    def set_rotation(self, rotation):
        """Установить ориентацию дисплея"""
        self.data['display']['rotation'] = rotation % 4
    
    # ============================================================================
    # ПРИМЕНЕНИЕ НАСТРОЕК К ДЖАММЕРУ
    # ============================================================================
    
    def apply_to_jammer(self, jammer):
        """Применить настройки к объекту джаммера"""
        if not self.loaded:
            print("Настройки не загружены, применяются значения по умолчанию")
        
        # Применяем настройки джаммера
        jammer.set_freq_mode(self.get_frequency_mode())
        jammer.set_mode(self.get_mode())
        jammer.set_power_level(self.get_power_level())
        
        custom_freq = self.get_custom_frequency()
        if custom_freq > 0:
            jammer.set_custom_frequency(custom_freq)
        
        print("Настройки применены к джаммеру")
    
    def save_from_jammer(self, jammer):
        """Сохранить текущие настройки из объекта джаммера"""
        self.set_frequency_mode(jammer.get_freq_mode())
        self.set_mode(jammer.get_mode())
        self.set_power_level(jammer.get_power_level())
        
        if jammer.get_freq_mode() == JammerFreq.CUSTOM:
            self.set_custom_frequency(jammer.get_frequency())
        
        self.save()
    
    # ============================================================================
    # УТИЛИТЫ
    # ============================================================================
    
    def is_valid(self):
        """Проверить валидность настроек"""
        try:
            # Проверяем основные настройки
            jammer_settings = self.get_jammer_settings()
            if 'frequency_mode' not in jammer_settings:
                return False
            
            freq_mode = jammer_settings['frequency_mode']
            if not (0 <= freq_mode < JammerFreq.COUNT):
                return False
            
            mode = jammer_settings.get('mode', JammerMode.CONTINUOUS)
            if not (0 <= mode < JammerMode.COUNT):
                return False
            
            power = jammer_settings.get('power_level', 50)
            if not (0 <= power <= 100):
                return False
            
            return True
        except:
            return False
    
    def print_summary(self):
        """Вывести сводку настроек"""
        print("=== Сводка настроек ===")
        print(f"Версия: {self.data['version']['major']}.{self.data['version']['minor']}.{self.data['version']['patch']}")
        
        jammer = self.data['jammer']
        print(f"Режим частоты: {jammer['frequency_mode']}")
        print(f"Режим работы: {jammer['mode']}")
        print(f"Мощность: {jammer['power_level']}%")
        if jammer['custom_freq_hz'] > 0:
            print(f"Пользовательская частота: {jammer['custom_freq_hz']} Hz")
        
        touch = self.data['touch_calibration']
        print(f"Калибровка тачскрина: KX1={touch.get('kx1', 0):.4f}, KY1={touch.get('ky1', 0):.4f} ...")
        
        display = self.data['display']
        print(f"Дисплей: яркость {display['brightness']}%, поворот {display['rotation']}")
        print("=======================")