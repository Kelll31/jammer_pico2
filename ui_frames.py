"""
Система событий и базовый Frame
Определение базовых структур: прямоугольники, типы событий, базовый класс 'Окно'.
"""

from micropython import const
import config

# Типы событий (порт frame_event.h)
EVENT_UNDEF = const(-1)
EVENT_PING = const(0)
EVENT_DRAW = const(1)
EVENT_CLICK_INSIDE = const(2)
EVENT_CLICK_OUTSIDE = const(3)
EVENT_TICK = const(4)
EVENT_CLOSE = const(5)
EVENT_TOUCH_DOWN = const(6)
EVENT_TOUCH_UP = const(7)
EVENT_TOUCH_MOVE = const(8)

# Типы фреймов (порт frame_type.h)
FRAME_ROOT = const(0)
FRAME_BBOX = const(1)

try:
    from typing import List, Any
except ImportError:
    pass

class Rect:
    """Прямоугольник (bounding box) - порт frame_rect.h"""
    def __init__(self, x: int = 0, y: int = 0, w: int = 0, h: int = 0) -> None:
        self.x: int = x
        self.y: int = y
        self.w: int = w
        self.h: int = h

    def contains(self, x: int, y: int) -> bool:
        return self.x <= x < self.x + self.w and self.y <= y < self.y + self.h

class BaseFrame:
    """Базовый класс 'Окно' (порт frame.h)"""
    def __init__(self, ui_manager: Any, title: str = "", x: int = 0, y: int = 0, width: int = config.DISPLAY_WIDTH, height: int = config.DISPLAY_HEIGHT) -> None:
        self.ui_manager: Any = ui_manager
        self.title: str = title
        self.rect: Rect = Rect(x, y, width, height)
        self.frame_type: int = FRAME_BBOX

        self.paper_color: int = config.UI_BG_COLOR
        self.ink_color: int = config.UI_FONT_COLOR

        self.widgets: List[Any] = []
        self.needs_redraw: bool = True

    def add_widget(self, widget: Any) -> None:
        self.widgets.append(widget)
        self.needs_redraw = True

    def on_enter(self) -> None:
        """Вызывается при открытии экрана."""
        self.needs_redraw = True

    def on_exit(self) -> None:
        """Очистка ресурсов."""
        pass

    def process_event(self, event: int, x: int, y: int) -> int:
        """Обработка событий."""
        if event == EVENT_TOUCH_DOWN:
            for widget in self.widgets:
                if widget.check_hit(x, y):
                    widget.process_event(EVENT_TOUCH_DOWN, x, y)
                    self.needs_redraw = True

        elif event == EVENT_TOUCH_UP:
            for widget in self.widgets:
                widget.process_event(EVENT_TOUCH_UP, x, y)
                self.needs_redraw = True

        elif event == EVENT_TICK:
            for widget in self.widgets:
                widget.process_event(EVENT_TICK, x, y)

        return 0

    def draw(self, display: Any) -> None:
        """Отрисовка в буфер дисплея."""
        if self.needs_redraw:
            display.fill_rect(self.rect.x, self.rect.y, self.rect.w, self.rect.h, self.paper_color)
            # Если фон перерисован, нужно заставить все виджеты перерисоваться
            for widget in self.widgets:
                widget.needs_redraw = True

        # Отрисовка виджетов
        for widget in self.widgets:
            if widget.needs_redraw:
                widget.draw(display)

        self.needs_redraw = False
