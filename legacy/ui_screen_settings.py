"""
Базовое меню с кнопками (аналог SettingsEventProc.c), где пользователь может листать опции.
"""

import config
from ui_frames import BaseFrame, Rect
from ui_widgets import Button, Label

try:
    from typing import Any, Optional
except ImportError:
    pass

class SettingsScreen(BaseFrame):
    def __init__(self, ui_manager: Any, ipc: Optional[Any] = None) -> None:
        super().__init__(ui_manager, title="SETTINGS", x=0, y=20, width=config.DISPLAY_WIDTH, height=config.DISPLAY_HEIGHT - 20)
        self.ipc: Optional[Any] = ipc
        self.paper_color: int = config.UI_BG_COLOR

        # Кнопки
        y: int = 40
        self.btn_bright_down: Button = Button(120, y, 40, 30, "-")
        self.btn_bright_down.on_click = self._decrease_brightness
        self.add_widget(self.btn_bright_down)

        self.btn_bright_up: Button = Button(180, y, 40, 30, "+")
        self.btn_bright_up.on_click = self._increase_brightness
        self.add_widget(self.btn_bright_up)

        y = 80
        self.btn_rotate: Button = Button(120, y, 100, 30, "ROTATE")
        self.btn_rotate.on_click = self._rotate_screen
        self.add_widget(self.btn_rotate)

        y = 120
        self.btn_calibrate: Button = Button(120, y, 100, 30, "CALIBRATE")
        self.btn_calibrate.on_click = self._calibrate_touch
        self.add_widget(self.btn_calibrate)

        y = 160
        self.btn_reset: Button = Button(60, y, 120, 30, "RESET", bg_color=config.COLOR_RED)
        self.btn_reset.on_click = self._reset_settings
        self.add_widget(self.btn_reset)

        # Назад
        self.btn_back: Button = Button(20, self.rect.h - 50, 80, 30, "BACK")
        self.btn_back.on_click = self._navigate_back
        self.add_widget(self.btn_back)

    def _decrease_brightness(self) -> None:
        self.needs_redraw = True

    def _increase_brightness(self) -> None:
        self.needs_redraw = True

    def _rotate_screen(self) -> None:
        self.needs_redraw = True

    def _calibrate_touch(self) -> None:
        self.needs_redraw = True

    def _reset_settings(self) -> None:
        self.needs_redraw = True

    def _navigate_back(self) -> None:
        self.ui_manager.pop_frame()

    def draw(self, display: Any) -> None:
        if self.needs_redraw:
            display.fill_rect(self.rect.x, self.rect.y, self.rect.w, self.rect.h, self.paper_color)

            display.draw_text(10, self.rect.y + 5, "SETTINGS", config.COLOR_CYAN, config.UI_BG_COLOR)

            display.draw_text(20, self.rect.y + 45, "Brightness:", config.UI_FONT_COLOR, config.UI_BG_COLOR)
            display.draw_text(20, self.rect.y + 85, "Rotation:", config.UI_FONT_COLOR, config.UI_BG_COLOR)
            display.draw_text(20, self.rect.y + 125, "Touchscreen:", config.UI_FONT_COLOR, config.UI_BG_COLOR)
            display.draw_text(20, self.rect.y + 165, "Factory reset:", config.UI_FONT_COLOR, config.UI_BG_COLOR)

            for widget in self.widgets:
                widget.needs_redraw = True

        # Отрисовка кнопок
        for widget in self.widgets:
            if widget.needs_redraw:
                widget.draw(display)

        self.needs_redraw = False
