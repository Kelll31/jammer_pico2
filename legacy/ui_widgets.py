"""
Библиотека виджетов (порт widgets_utility.c)
Кнопки, текст, рамки.
"""

from micropython import const
import config
from ui_frames import Rect, EVENT_TOUCH_DOWN, EVENT_TOUCH_UP, EVENT_TICK, EVENT_CLICK_INSIDE

try:
    from typing import Callable, Optional, Any
except ImportError:
    pass

class Widget:
    """Базовый класс виджета"""
    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        self.rect: Rect = Rect(x, y, width, height)
        self.needs_redraw: bool = True

    def check_hit(self, x: int, y: int) -> bool:
        return self.rect.contains(x, y)

    def process_event(self, event: int, x: int, y: int) -> None:
        pass

    def draw(self, display: Any) -> None:
        pass

class Button(Widget):
    """Кнопка с состояниями Normal / Pressed"""
    def __init__(self, x: int, y: int, width: int, height: int, label: str,
                 color: int = config.UI_FONT_COLOR,
                 bg_color: int = config.UI_BUTTON_BG,
                 active_bg_color: int = config.UI_BUTTON_ACTIVE_BG,
                 border_color: int = config.UI_BUTTON_BORDER) -> None:
        super().__init__(x, y, width, height)
        self.label: str = label
        self.color: int = color
        self.bg_color: int = bg_color
        self.active_bg_color: int = active_bg_color
        self.border_color: int = border_color
        self.pressed: bool = False
        self.on_click: Optional[Callable[[], None]] = None

    def process_event(self, event: int, x: int, y: int) -> None:
        if event == EVENT_TOUCH_DOWN:
            if self.check_hit(x, y):
                if not self.pressed:
                    self.pressed = True
                    self.needs_redraw = True
        elif event == EVENT_TOUCH_UP:
            if self.pressed:
                self.pressed = False
                self.needs_redraw = True
                if self.check_hit(x, y) and self.on_click:
                    self.on_click()

    def draw(self, display: Any) -> None:
        if not self.needs_redraw:
            return

        bg_color = self.active_bg_color if self.pressed else self.bg_color

        display.fill_rect(self.rect.x, self.rect.y, self.rect.w, self.rect.h, bg_color)
        display.draw_rectangle(self.rect.x, self.rect.y, self.rect.w, self.rect.h, self.border_color)

        text_x = self.rect.x + (self.rect.w - len(self.label) * 8) // 2
        text_y = self.rect.y + (self.rect.h - 12) // 2

        display.draw_text(text_x, text_y, self.label, self.color, bg_color)
        self.needs_redraw = False

class Label(Widget):
    """Текстовая метка"""
    def __init__(self, x: int, y: int, text: str, color: int = config.UI_FONT_COLOR, bg_color: int = config.UI_BG_COLOR) -> None:
        # Оценка ширины текста (шрифт 8x12)
        width = len(text) * 8
        height = 12
        super().__init__(x, y, width, height)
        self.text: str = text
        self.color: int = color
        self.bg_color: int = bg_color

    def update_text(self, new_text: str) -> None:
        if self.text != new_text:
            self.text = new_text
            self.rect.w = len(new_text) * 8
            self.needs_redraw = True

    def draw(self, display: Any) -> None:
        if not self.needs_redraw:
            return
        display.draw_text(self.rect.x, self.rect.y, self.text, self.color, self.bg_color)
        self.needs_redraw = False

class Checkbox(Widget):
    """Чекбокс (Toggle)"""
    def __init__(self, x: int, y: int, width: int, height: int, label: str, checked: bool = False,
                 color: int = config.UI_FONT_COLOR,
                 bg_color: int = config.UI_BUTTON_BG,
                 active_bg_color: int = config.COLOR_GREEN) -> None:
        super().__init__(x, y, width, height)
        self.label: str = label
        self.checked: bool = checked
        self.color: int = color
        self.bg_color: int = bg_color
        self.active_bg_color: int = active_bg_color
        self.border_color: int = config.UI_BUTTON_BORDER
        self.on_change: Optional[Callable[[bool], None]] = None

    def process_event(self, event: int, x: int, y: int) -> None:
        if event == EVENT_TOUCH_DOWN:
            if self.check_hit(x, y):
                self.checked = not self.checked
                self.needs_redraw = True
                if self.on_change:
                    self.on_change(self.checked)

    def draw(self, display: Any) -> None:
        if not self.needs_redraw:
            return

        box_size = self.rect.h

        # Рисуем квадратик чекбокса
        box_bg = self.active_bg_color if self.checked else self.bg_color
        display.fill_rect(self.rect.x, self.rect.y, box_size, box_size, box_bg)
        display.draw_rectangle(self.rect.x, self.rect.y, box_size, box_size, self.border_color)

        # Галочка (если нужно)
        if self.checked:
            # Рисуем "X" или квадратик внутри
            display.fill_rect(self.rect.x + 4, self.rect.y + 4, box_size - 8, box_size - 8, config.COLOR_WHITE)

        # Текст
        text_x = self.rect.x + box_size + 8
        text_y = self.rect.y + (box_size - 12) // 2

        display.draw_text(text_x, text_y, self.label, self.color, config.UI_BG_COLOR)
        self.needs_redraw = False
