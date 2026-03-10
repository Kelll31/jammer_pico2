"""
UI менеджер для джаммера на MicroPython
Управление через тачскрин с двойной буферизацией
"""

import time
import config
from jammer_signal import JammerSignal, JammerMode, JammerFreq, JammerState

# Тип для callback функции (для совместимости с Pylance)
try:
    from typing import Callable, Optional

    UIButtonCallback = Optional[Callable[[], None]]
except ImportError:
    UIButtonCallback = type(None)


class UIButton:
    """Класс кнопки UI"""

    def __init__(
        self,
        x,
        y,
        width,
        height,
        label,
        color=config.UI_FONT_COLOR,
        bg_color=config.UI_BUTTON_BG,
        active_bg_color=config.UI_BUTTON_ACTIVE_BG,
        border_color=config.UI_BUTTON_BORDER,
    ):

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
        self.on_click: UIButtonCallback = None  # Вызывается при нажатии

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
        display.draw_rectangle(
            self.x, self.y, self.width, self.height, self.border_color
        )

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
                button.pressed = True
                if button.click():
                    touched = True
            else:
                button.pressed = False
        return touched

    def draw(self, display):
        """Нарисовать страницу (должен быть переопределён)"""
        pass

    def update(self, display):
        """Обновить отображение страницы"""
        if self.needs_redraw:
            self.draw(display)
            self.needs_redraw = False

        # Рисуем все кнопки
        for button in self.buttons:
            button.draw(display)

        return self.needs_redraw


class MainPage(UIPage):
    """Главная страница джаммера"""

    def __init__(self, jammer, ui_manager=None):
        super().__init__("main")
        self.jammer = jammer
        self.ui_manager = ui_manager

        # Создаём кнопки
        self._create_buttons()

    def _create_buttons(self):
        """Создать кнопки главной страницы"""
        width = config.DISPLAY_WIDTH
        height = config.DISPLAY_HEIGHT

        # Кнопка ON/OFF
        btn_width = 100
        btn_height = config.UI_BUTTON_HEIGHT
        btn_x = 20
        btn_y = 190

        self.btn_power = UIButton(btn_x, btn_y, btn_width, btn_height, "START")
        self.btn_power.on_click = self._toggle_power
        self.add_button(self.btn_power)

        # Кнопка MODE
        btn_x = 130
        self.btn_mode = UIButton(btn_x, btn_y, 90, btn_height, "MODE")
        self.btn_mode.on_click = self._next_mode
        self.add_button(self.btn_mode)

        # Кнопки мощности
        btn_y = 240
        btn_width = 50

        self.btn_power_down = UIButton(20, btn_y, btn_width, btn_height, "-")
        self.btn_power_down.on_click = self._decrease_power
        self.add_button(self.btn_power_down)

        self.btn_power_up = UIButton(80, btn_y, btn_width, btn_height, "+")
        self.btn_power_up.on_click = self._increase_power
        self.add_button(self.btn_power_up)

        # Кнопка настроек
        self.btn_settings = UIButton(150, btn_y, 70, btn_height, "SETUP")
        self.btn_settings.on_click = self._go_to_settings
        self.add_button(self.btn_settings)

    def _toggle_power(self):
        """Переключить питание джаммера"""
        self.jammer.toggle_enable()
        self._update_power_button()

    def _next_mode(self):
        """Переключить на следующий режим"""
        self.jammer.next_mode()
        self.needs_redraw = True

    def _increase_power(self):
        """Увеличить мощность"""
        self.jammer.increase_power()
        self.needs_redraw = True

    def _decrease_power(self):
        """Уменьшить мощность"""
        self.jammer.decrease_power()
        self.needs_redraw = True

    def _go_to_settings(self):
        """Перейти к настройкам"""
        # Навигация через UIManager
        if hasattr(self, "ui_manager") and self.ui_manager:
            self.ui_manager.set_page("settings")

    def _update_power_button(self):
        """Обновить текст кнопки питания"""
        if self.jammer.is_enabled():
            self.btn_power.label = "STOP"
            self.btn_power.bg_color = config.COLOR_RED
            self.btn_power.active_bg_color = config.COLOR_RED
        else:
            self.btn_power.label = "START"
            self.btn_power.bg_color = config.COLOR_GREEN
            self.btn_power.active_bg_color = config.COLOR_GREEN

    def draw(self, display):
        """Нарисовать главную страницу"""
        # Очищаем экран
        display.fill_screen(config.UI_BG_COLOR)

        # Заголовок
        self._draw_header(display, "KELLL31 JAMMER")

        # Блок состояния
        self._draw_status_block(display)

        # Информация
        self._draw_info(display)

        # Обновляем кнопку питания
        self._update_power_button()

        self.needs_redraw = False

    def _draw_header(self, display, title):
        """Нарисовать заголовок"""
        display.fill_rect(0, 0, config.DISPLAY_WIDTH, 25, config.UI_HEADER_COLOR)

        # Центрируем текст
        text_width = len(title) * 8
        text_x = (config.DISPLAY_WIDTH - text_width) // 2
        display.draw_text(
            text_x, 7, title, config.UI_FONT_COLOR, config.UI_HEADER_COLOR
        )

    def _draw_status_block(self, display):
        """Нарисовать блок состояния"""
        center_y = 80

        # Рамка состояния
        display.draw_rectangle(10, center_y - 15, 220, 50, config.UI_BUTTON_BORDER)

        # Статус
        state = self.jammer.get_state()
        state_name = JammerSignal.get_state_name(state)

        if state == JammerState.ON:
            state_color = config.COLOR_GREEN
        elif state == JammerState.ERROR:
            state_color = config.COLOR_RED
        else:
            state_color = config.COLOR_GRAY

        text_width = len(state_name) * 8
        text_x = (config.DISPLAY_WIDTH - text_width) // 2
        display.draw_text(
            text_x, center_y - 5, state_name, state_color, config.UI_BG_COLOR
        )

    def _draw_info(self, display):
        """Нарисовать информацию"""
        center_y = 80

        # Частота
        freq_mode = self.jammer.get_freq_mode()
        freq_name = JammerSignal.get_freq_name(freq_mode)
        freq_text = f"FREQ: {freq_name}"

        text_width = len(freq_text) * 8
        text_x = (config.DISPLAY_WIDTH - text_width) // 2
        display.draw_text(
            text_x, center_y + 25, freq_text, config.COLOR_CYAN, config.UI_BG_COLOR
        )

        # Режим
        mode = self.jammer.get_mode()
        mode_name = JammerSignal.get_mode_name(mode)
        mode_text = f"MODE: {mode_name}"

        text_width = len(mode_text) * 8
        text_x = (config.DISPLAY_WIDTH - text_width) // 2
        display.draw_text(
            text_x, center_y + 40, mode_text, config.COLOR_PURPLE, config.UI_BG_COLOR
        )

        # Мощность
        power = self.jammer.get_power_level()
        power_text = f"POWER: {power}%"

        text_width = len(power_text) * 8
        text_x = (config.DISPLAY_WIDTH - text_width) // 2
        display.draw_text(
            text_x, center_y + 55, power_text, config.COLOR_YELLOW, config.UI_BG_COLOR
        )

        # Статус бар
        self._draw_status_bar(display)

        self.needs_redraw = False

    def _draw_status_bar(self, display):
        """Нарисовать статус бар"""
        bar_y = config.DISPLAY_HEIGHT - 20
        display.fill_rect(0, bar_y, config.DISPLAY_WIDTH, 20, config.UI_HEADER_COLOR)

        # Статус слева
        state = self.jammer.get_state()
        state_name = JammerSignal.get_state_name(state)
        state_color = (
            config.COLOR_GREEN if state == JammerState.ON else config.COLOR_RED
        )
        status_text = f"STATUS: {state_name}"
        display.draw_text(
            5, bar_y + 4, status_text, state_color, config.UI_HEADER_COLOR
        )

        # Частота справа
        freq_mode = self.jammer.get_freq_mode()
        freq_name = JammerSignal.get_freq_name(freq_mode)
        text_width = len(freq_name) * 8
        display.draw_text(
            config.DISPLAY_WIDTH - text_width - 5,
            bar_y + 4,
            freq_name,
            config.COLOR_CYAN,
            config.UI_HEADER_COLOR,
        )

        self.needs_redraw = False


class SettingsPage(UIPage):
    """Страница настроек"""

    def __init__(self, jammer, settings, ui_manager):
        super().__init__("settings")
        self.jammer = jammer
        self.settings = settings
        self.ui_manager = ui_manager

        # Создаём кнопки
        self._create_buttons()

    def _create_buttons(self):
        """Создать кнопки страницы настроек"""
        # Кнопка назад
        self.btn_back = UIButton(20, 180, 90, config.UI_BUTTON_HEIGHT, "BACK")
        self.btn_back.on_click = self._go_back
        self.add_button(self.btn_back)

        # Кнопка сохранения
        self.btn_save = UIButton(130, 180, 90, config.UI_BUTTON_HEIGHT, "SAVE")
        self.btn_save.on_click = self._save_settings
        self.add_button(self.btn_save)

    def _go_back(self):
        """Вернуться на главную страницу"""
        if self.ui_manager:
            self.ui_manager.set_page("main")

    def _save_settings(self):
        """Сохранить настройки"""
        self.settings.save_from_jammer(self.jammer)
        self.needs_redraw = False

    def draw(self, display):
        """Нарисовать страницу настроек"""
        display.fill_screen(config.UI_BG_COLOR)
        self._draw_header(display, "SETTINGS")
        self._draw_settings(display)
        self.needs_redraw = False

    def _draw_header(self, display, title):
        """Нарисовать заголовок"""
        display.fill_rect(0, 0, config.DISPLAY_WIDTH, 25, config.UI_HEADER_COLOR)

        text_width = len(title) * 8
        text_x = (config.DISPLAY_WIDTH - text_width) // 2
        display.draw_text(
            text_x, 7, title, config.UI_FONT_COLOR, config.UI_HEADER_COLOR
        )

    def _draw_settings(self, display):
        """Нарисовать настройки"""
        y = 40

        # Частота
        freq_mode = self.jammer.get_freq_mode()
        freq_name = JammerSignal.get_freq_name(freq_mode)
        display.draw_text(10, y, "Frequency:", config.UI_FONT_COLOR, config.UI_BG_COLOR)
        display.draw_text(115, y, freq_name, config.COLOR_CYAN, config.UI_BG_COLOR)
        y += 25

        # Режим
        mode = self.jammer.get_mode()
        mode_name = JammerSignal.get_mode_name(mode)
        display.draw_text(10, y, "Mode:", config.UI_FONT_COLOR, config.UI_BG_COLOR)
        display.draw_text(115, y, mode_name, config.COLOR_PURPLE, config.UI_BG_COLOR)
        y += 25

        # Мощность
        power = self.jammer.get_power_level()
        power_text = f"{power}%"
        display.draw_text(10, y, "Power:", config.UI_FONT_COLOR, config.UI_BG_COLOR)
        display.draw_text(115, y, power_text, config.COLOR_YELLOW, config.UI_BG_COLOR)
        y += 35

        # Статус бар
        self._draw_status_bar(display)

        self.needs_redraw = False

    def _draw_status_bar(self, display):
        """Нарисовать статус бар"""
        bar_y = config.DISPLAY_HEIGHT - 20
        display.fill_rect(0, bar_y, config.DISPLAY_WIDTH, 20, config.UI_HEADER_COLOR)
        self.needs_redraw = False


class UIManager:
    """Менеджер пользовательского интерфейса"""

    def __init__(self, display, jammer, settings):
        self.display = display
        self.jammer = jammer
        self.settings = settings

        # Создаём страницы
        self.pages = {
            "main": MainPage(jammer, self),
            "settings": SettingsPage(jammer, settings, self),
        }

        self.current_page = "main"
        self.last_update = time.ticks_ms()

        # Инициализация
        self._init_ui()

    def _init_ui(self):
        """Инициализировать UI"""
        # Рисуем начальную страницу
        self.get_current_page().needs_redraw = True
        self.update()

    def get_current_page(self):
        """Получить текущую страницу"""
        return self.pages[self.current_page]

    def set_page(self, page_name):
        """Установить текущую страницу"""
        if page_name in self.pages:
            self.current_page = page_name
            self.get_current_page().needs_redraw = True
            return True
        return False

    def handle_touch(self, x, y):
        """Обработать касание"""
        page = self.get_current_page()
        return page.handle_touch(x, y)

    def update(self):
        """Обновить UI"""
        current_time = time.ticks_ms()

        # Обновляем каждые 100 мс
        if time.ticks_diff(current_time, self.last_update) >= 100:
            self.last_update = current_time

            # Обновляем текущую страницу
            page = self.get_current_page()
            page.update(self.display)

            # Обмениваем буферы (двойная буферизация)
            self.display.swap_buffers()

    def process(self):
        """Обработать UI (вызывать в основном цикле)"""
        # Обновляем состояние джаммера
        self.jammer.process()

        # Обновляем UI
        self.update()
