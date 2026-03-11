"""
Верхняя панель (как в TopBarEventProc.c), которая всегда рисуется поверх остальных окон.
"""

import time
import config
from ui_frames import BaseFrame, Rect, EVENT_TICK
from ui_widgets import Label

try:
    from typing import Any, Optional
except ImportError:
    pass

class TopBar(BaseFrame):
    def __init__(self, ui_manager: Any, ipc: Optional[Any] = None) -> None:
        super().__init__(ui_manager, title="TopBar", x=0, y=0, width=config.DISPLAY_WIDTH, height=20)
        self.ipc: Optional[Any] = ipc
        self.paper_color: int = 0x0861  # Тёмно-серый с синим оттенком

        # Виджеты внутри топбара
        self.lbl_battery: Label = Label(5, 4, "100%", color=config.COLOR_WHITE, bg_color=self.paper_color)
        self.lbl_page: Label = Label((config.DISPLAY_WIDTH - 80) // 2, 4, "DASHBOARD", color=config.COLOR_YELLOW, bg_color=self.paper_color)
        self.lbl_icons: Label = Label(config.DISPLAY_WIDTH - 40, 4, "  ", color=config.COLOR_CYAN, bg_color=self.paper_color)

        self.add_widget(self.lbl_battery)
        self.add_widget(self.lbl_page)
        self.add_widget(self.lbl_icons)

        self.battery_level: float = 100.0
        self.last_update: int = time.ticks_ms()

    def process_event(self, event: int, x: int, y: int) -> int:
        # TopBar может перехватывать клики, если нужно (как в C-версии)
        if event == EVENT_TICK:
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, self.last_update) >= 1000:
                self.last_update = current_time
                self._update_data()

        # Не блокируем события, передаем дальше (если нужно)
        return super().process_event(event, x, y)

    def _update_data(self) -> None:
        # Батарея
        self.battery_level = max(0, self.battery_level - 0.1)
        if self.battery_level <= 0:
            self.battery_level = 100
        self.lbl_battery.update_text(f"{int(self.battery_level)}%")

        # Текущая страница
        active_frame = self.ui_manager.get_active_frame()
        if active_frame:
            page_text = active_frame.title.upper()
            # Центрируем текст страницы
            text_x = (config.DISPLAY_WIDTH - len(page_text) * 8) // 2
            self.lbl_page.rect.x = text_x
            self.lbl_page.update_text(page_text)

        # Иконки
        icons = ""
        if self.ipc:
            if self.ipc.jammer_active:
                icons += "!" # "⚡"
            if self.ipc.subghz_scanning:
                icons += "@" # "📡"
            if self.ipc.nrf24_sniffing:
                icons += "#" # "📶"

        # Сдвигаем иконки влево в зависимости от длины
        icons_x = config.DISPLAY_WIDTH - len(icons) * 8 - 5
        self.lbl_icons.rect.x = icons_x
        self.lbl_icons.update_text(icons)

        self.needs_redraw = True

    def draw(self, display: Any) -> None:
        if self.needs_redraw:
            display.fill_rect(self.rect.x, self.rect.y, self.rect.w, self.rect.h, self.paper_color)

            # Рисуем батарейку
            battery_width = 30
            battery_height = 12
            battery_x = 5
            battery_y = (self.rect.h - battery_height) // 2

            # Смещаем текст батареи, чтобы не наезжал на иконку
            self.lbl_battery.rect.x = battery_x + battery_width + 5

            display.draw_rectangle(battery_x, battery_y, battery_width, battery_height, config.COLOR_CYAN)
            fill_width = int((battery_width - 2) * self.battery_level / 100)
            display.fill_rect(battery_x + 1, battery_y + 1, fill_width, battery_height - 2, config.COLOR_GREEN)

            # Разделительная линия
            display.draw_line(0, self.rect.h - 1, config.DISPLAY_WIDTH, self.rect.h - 1, config.COLOR_DARKGRAY)

            for widget in self.widgets:
                widget.needs_redraw = True

        # Отрисовка текста (Label)
        for widget in self.widgets:
            if widget.needs_redraw:
                widget.draw(display)

        self.needs_redraw = False
