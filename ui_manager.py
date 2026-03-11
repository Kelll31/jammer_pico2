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


class UIScrollList:
    """Виджет списка с прокруткой"""

    def __init__(self, x, y, width, height, items, on_change=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.items = items
        self.selected_index = 0
        self.on_change = on_change
        self.visible = True
        self.item_height = 30

        # Кнопки прокрутки
        btn_width = 40
        self.btn_up = UIButton(x + width - btn_width, y, btn_width, height // 2 - 2, "^")
        self.btn_up.on_click = self._scroll_up
        self.btn_down = UIButton(
            x + width - btn_width, y + height // 2 + 2, btn_width, height // 2 - 2, "v"
        )
        self.btn_down.on_click = self._scroll_down

    def _scroll_up(self):
        if self.selected_index > 0:
            self.selected_index -= 1
            if self.on_change:
                self.on_change(self.selected_index)
            return True
        return False

    def _scroll_down(self):
        if self.selected_index < len(self.items) - 1:
            self.selected_index += 1
            if self.on_change:
                self.on_change(self.selected_index)
            return True
        return False

    def handle_touch(self, x, y):
        if not self.visible:
            return False

        if self.btn_up.contains(x, y):
            if not self.btn_up.pressed:
                self.btn_up.pressed = True
                self.btn_up.click()
            return True
        elif self.btn_down.contains(x, y):
            if not self.btn_down.pressed:
                self.btn_down.pressed = True
                self.btn_down.click()
            return True
        else:
            self.btn_up.pressed = False
            self.btn_down.pressed = False

        # Прямое нажатие на элементы списка
        list_width = self.width - 40
        if self.x <= x < self.x + list_width and self.y <= y < self.y + self.height:
            # Вычисляем индекс клика
            center_y = self.y + self.height // 2
            if y < center_y - self.item_height // 2:
                self._scroll_up()
            elif y > center_y + self.item_height // 2:
                self._scroll_down()
            return True

        return False

    def handle_touch_release(self):
        self.btn_up.pressed = False
        self.btn_down.pressed = False

    def draw(self, display):
        if not self.visible:
            return

        # Рамка списка
        display.draw_rectangle(self.x, self.y, self.width - 40, self.height, config.UI_BUTTON_BORDER)

        # Рисуем элементы (текущий, предыдущий, следующий)
        center_y = self.y + self.height // 2

        # Предыдущий
        if self.selected_index > 0:
            text = self.items[self.selected_index - 1]
            text_x = self.x + 10
            text_y = center_y - self.item_height
            display.draw_text(text_x, text_y, text, config.COLOR_GRAY, config.UI_BG_COLOR)

        # Текущий (выделенный)
        text = self.items[self.selected_index]
        text_x = self.x + 10
        text_y = center_y - 6
        # Выделяем фон
        display.fill_rect(self.x + 2, center_y - 12, self.width - 44, 24, config.UI_BUTTON_ACTIVE_BG)
        display.draw_text(text_x, text_y, text, config.COLOR_CYAN, config.UI_BUTTON_ACTIVE_BG)

        # Следующий
        if self.selected_index < len(self.items) - 1:
            text = self.items[self.selected_index + 1]
            text_x = self.x + 10
            text_y = center_y + self.item_height - 12
            display.draw_text(text_x, text_y, text, config.COLOR_GRAY, config.UI_BG_COLOR)

        # Кнопки
        self.btn_up.draw(display)
        self.btn_down.draw(display)


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

        # Если есть скролл лист, обрабатываем его
        if hasattr(self, 'scroll_list') and self.scroll_list.visible:
            if self.scroll_list.handle_touch(x, y):
                touched = True
                self.needs_redraw = True

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
        if hasattr(self, 'scroll_list'):
            self.scroll_list.handle_touch_release()
            self.needs_redraw = True

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


class MainPage(UIPage):
    """Главная страница джаммера"""

    def __init__(self, jammer, ui_manager=None):
        super().__init__("main")
        self.jammer = jammer
        self.ui_manager = ui_manager

        # Данные частот
        self.freq_names = [
            "WiFi 2.4GHz",
            "WiFi 5GHz",
            "Bluetooth",
            "Cellular",
            "Custom"
        ]

        # Создаём кнопки
        self._create_buttons()

    def _create_buttons(self):
        """Создать элементы главной страницы"""
        width = config.DISPLAY_WIDTH
        height = config.DISPLAY_HEIGHT

        # Скроллируемый список частот (заменяет старый текст частот)
        self.scroll_list = UIScrollList(
            10, 35, width - 20, 80, self.freq_names, self._on_freq_change
        )
        # Синхронизируем индекс с текущим режимом частоты
        self.scroll_list.selected_index = self.jammer.get_freq_mode()

        # Кнопки мощности (+ и -) перенесены выше
        btn_height = config.UI_BUTTON_HEIGHT
        btn_y = 130
        btn_width = 50

        self.btn_power_down = UIButton(20, btn_y, btn_width, btn_height, "-")
        self.btn_power_down.on_click = self._decrease_power
        self.add_button(self.btn_power_down)

        self.btn_power_up = UIButton(width - 70, btn_y, btn_width, btn_height, "+")
        self.btn_power_up.on_click = self._increase_power
        self.add_button(self.btn_power_up)

        # Кнопка START посередине
        start_width = 140
        start_height = 50
        start_x = (width - start_width) // 2
        start_y = 190

        self.btn_power = UIButton(start_x, start_y, start_width, start_height, "START")
        self.btn_power.on_click = self._toggle_power
        self.add_button(self.btn_power)

        # Кнопки MODE и SETUP снизу
        bottom_y = 260
        self.btn_mode = UIButton(20, bottom_y, 90, btn_height, "MODE")
        self.btn_mode.on_click = self._next_mode
        self.add_button(self.btn_mode)

        self.btn_settings = UIButton(width - 110, bottom_y, 90, btn_height, "SETUP")
        self.btn_settings.on_click = self._go_to_settings
        self.add_button(self.btn_settings)

    def _on_freq_change(self, index):
        """Callback при изменении частоты в скролл-листе"""
        self.jammer.set_freq_mode(index)
        self.needs_redraw = True

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

    def update(self, display):
        """Обновить отображение страницы и вернуть True если нужна перерисовка"""
        redraw_happened = super().update(display)

        # Обновляем скролл лист
        if self.needs_redraw and hasattr(self, 'scroll_list'):
            self.scroll_list.draw(display)
            redraw_happened = True

        return redraw_happened

    def draw(self, display):
        """Нарисовать главную страницу"""
        # Очищаем экран
        display.fill_screen(config.UI_BG_COLOR)

        # Заголовок
        self._draw_header(display, "KELLL31 JAMMER")

        # Рисуем скролл-лист частот
        self.scroll_list.draw(display)

        # Информация о режиме и мощности
        self._draw_info(display)

        # Обновляем кнопку питания
        self._update_power_button()

        # Рисуем статус-бар (снизу)
        self._draw_status_bar(display)

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

    def _draw_info(self, display):
        """Нарисовать информацию (Mode и Power)"""
        # Рисуем Power между кнопками - и +
        power_y = 140
        power = self.jammer.get_power_level()
        power_text = f"{power}%"

        text_width = len(power_text) * 8
        text_x = (config.DISPLAY_WIDTH - text_width) // 2
        display.draw_text(
            text_x, power_y, power_text, config.COLOR_YELLOW, config.UI_BG_COLOR
        )

        # Power label
        label_text = "POWER"
        label_width = len(label_text) * 8
        label_x = (config.DISPLAY_WIDTH - label_width) // 2
        display.draw_text(
            label_x, power_y - 12, label_text, config.UI_FONT_COLOR, config.UI_BG_COLOR
        )

        # Режим
        mode_y = 245
        mode = self.jammer.get_mode()
        mode_name = JammerSignal.get_mode_name(mode)
        mode_text = f"MODE: {mode_name}"

        text_width = len(mode_text) * 8
        text_x = (config.DISPLAY_WIDTH - text_width) // 2
        display.draw_text(
            text_x, mode_y, mode_text, config.COLOR_PURPLE, config.UI_BG_COLOR
        )

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
        width = config.DISPLAY_WIDTH

        y_offset = 40
        btn_height = config.UI_BUTTON_HEIGHT - 5

        # Кнопки яркости
        self.btn_bright_down = UIButton(120, y_offset, 40, btn_height, "-")
        self.btn_bright_down.on_click = self._decrease_brightness
        self.add_button(self.btn_bright_down)

        self.btn_bright_up = UIButton(180, y_offset, 40, btn_height, "+")
        self.btn_bright_up.on_click = self._increase_brightness
        self.add_button(self.btn_bright_up)

        y_offset += 45

        # Кнопка вращения экрана
        self.btn_rotate = UIButton(120, y_offset, 100, btn_height, "ROTATE")
        self.btn_rotate.on_click = self._rotate_screen
        self.add_button(self.btn_rotate)

        y_offset += 45

        # Dummy кнопка для Dark Theme ONLY
        self.btn_dark_theme = UIButton(120, y_offset, 100, btn_height, "DARK ONLY")
        self.btn_dark_theme.bg_color = config.COLOR_DARKGRAY
        self.btn_dark_theme.active_bg_color = config.COLOR_DARKGRAY
        # Нет on_click - кнопка "dummy" и ничего не делает
        self.add_button(self.btn_dark_theme)

        y_offset += 55

        # Кнопка RESET
        self.btn_reset = UIButton(60, y_offset, 120, btn_height, "RESET TO FACTORY")
        self.btn_reset.bg_color = config.COLOR_RED
        self.btn_reset.active_bg_color = config.COLOR_RED
        self.btn_reset.on_click = self._reset_settings
        self.add_button(self.btn_reset)

        y_offset += 55

        # Кнопка назад
        self.btn_back = UIButton(20, y_offset, 90, config.UI_BUTTON_HEIGHT, "BACK")
        self.btn_back.on_click = self._go_back
        self.add_button(self.btn_back)

        # Кнопка сохранения
        self.btn_save = UIButton(130, y_offset, 90, config.UI_BUTTON_HEIGHT, "SAVE")
        self.btn_save.on_click = self._save_settings
        self.add_button(self.btn_save)

    def _decrease_brightness(self):
        """Уменьшить яркость"""
        current = self.settings.get_brightness()
        self.settings.set_brightness(current - 10)
        self.needs_redraw = True

    def _increase_brightness(self):
        """Увеличить яркость"""
        current = self.settings.get_brightness()
        self.settings.set_brightness(current + 10)
        self.needs_redraw = True

    def _rotate_screen(self):
        """Повернуть экран"""
        current = self.settings.get_rotation()
        self.settings.set_rotation((current + 1) % 4)
        if hasattr(self.ui_manager, 'display') and self.ui_manager.display:
            self.ui_manager.display.set_rotation(self.settings.get_rotation())
        self.needs_redraw = True

    def _reset_settings(self):
        """Сбросить настройки к заводским"""
        self.settings.reset()
        self.settings.apply_to_jammer(self.jammer)
        self.needs_redraw = True

    def _go_back(self):
        """Вернуться на главную страницу"""
        if self.ui_manager:
            self.ui_manager.set_page("main")

    def _save_settings(self):
        """Сохранить настройки"""
        self.settings.save_from_jammer(self.jammer)
        self.needs_redraw = True

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
        y = 50

        # Яркость
        display.draw_text(10, y, "Bright:", config.UI_FONT_COLOR, config.UI_BG_COLOR)
        y += 45

        # Rotation
        display.draw_text(10, y, "Display:", config.UI_FONT_COLOR, config.UI_BG_COLOR)
        y += 45

        # Theme
        display.draw_text(10, y, "Theme:", config.UI_FONT_COLOR, config.UI_BG_COLOR)
        y += 45

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

    def handle_touch_release(self):
        """Обработать отпускание касания"""
        page = self.get_current_page()
        page.handle_touch_release()

    def update(self):
        """Обновить UI"""
        current_time = time.ticks_ms()

        # Обновляем каждые 20 мс для отзывчивости
        if time.ticks_diff(current_time, self.last_update) >= 20:
            self.last_update = current_time

            # Обновляем текущую страницу
            page = self.get_current_page()
            if page.update(self.display):
                # Обмениваем буферы только если была перерисовка
                self.display.swap_buffers()

    def process(self):
        """Обработать UI (вызывать в основном цикле)"""
        # Обновляем состояние джаммера
        self.jammer.process()

        # Обновляем UI
        self.update()
