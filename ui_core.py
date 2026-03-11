"""
Ядро UI фреймворка, порт логики из ui_manage.c
Диспетчер окон (Frames), управление стеком экранов.
"""

import time
from micropython import const
from ui_frames import EVENT_TOUCH_DOWN, EVENT_TOUCH_UP, EVENT_TICK, BaseFrame

try:
    from typing import List, Optional, Any
except ImportError:
    pass

MAX_UI_DEPTH = const(8)

class UIManager:
    """Менеджер окон для KELL31 Jammer."""

    def __init__(self, display: Any, touch: Any, spi0_manager: Any) -> None:
        self.display = display
        self.touch = touch
        self.spi0_manager = spi0_manager

        self.frame_stack: List[BaseFrame] = []

        self.last_x: int = -1
        self.last_y: int = -1
        self.last_touch_tm: int = 0
        self.is_touched: bool = False

        # Для отрисовки
        self.needs_redraw: bool = True

        # Глобальный статус бар (если есть)
        self.topbar: Optional[BaseFrame] = None

    def set_topbar(self, topbar: BaseFrame) -> None:
        """Устанавливает верхнюю панель, которая рисуется поверх всех окон"""
        self.topbar = topbar

    def push_frame(self, frame: BaseFrame) -> None:
        """Добавить окно в стек."""
        if len(self.frame_stack) < MAX_UI_DEPTH:
            self.frame_stack.append(frame)
            frame.on_enter()
            self.needs_redraw = True
        else:
            print("UI Error: Max frame depth reached")

    def pop_frame(self) -> None:
        """Удалить окно из стека (возврат назад)."""
        if len(self.frame_stack) > 1: # Оставляем хотя бы один экран (главный)
            frame = self.frame_stack.pop()
            frame.on_exit()

            # При возврате вызываем on_enter у предыдущего экрана для перерисовки
            active = self.get_active_frame()
            if active:
                active.on_enter()

            self.needs_redraw = True

    def get_active_frame(self) -> Optional[BaseFrame]:
        """Получить текущее активное окно."""
        if self.frame_stack:
            return self.frame_stack[-1]
        return None

    def task_handler(self) -> None:
        """Главный метод обработки UI: опрос тача и отрисовка."""

        # 1. Обработка тачскрина
        current_time = time.ticks_ms()

        # Опрашиваем тачскрин
        # Предполагаем, что touch.is_touched() и touch.get_touch_coordinates() уже безопасны
        # в плане SPI коллизий (или их нужно обернуть в spi0_manager.acquire_touch())

        touched = False
        valid = False
        screen_x = -1
        screen_y = -1

        if self.touch:
            with self.spi0_manager.acquire_touch():
                touched = self.touch.is_touched()
                if touched:
                    screen_x, screen_y, valid = self.touch.get_touch_coordinates()

        active_frame = self.get_active_frame()
        if not active_frame:
            return

        event_generated = False

        if valid and touched:
            if not self.is_touched:
                # TOUCH_DOWN
                active_frame.process_event(EVENT_TOUCH_DOWN, screen_x, screen_y)
                if self.topbar:
                    self.topbar.process_event(EVENT_TOUCH_DOWN, screen_x, screen_y)
                self.is_touched = True
                self.last_touch_tm = current_time
                event_generated = True
            else:
                # TOUCH_MOVE (или удержание)
                # Если координаты изменились значительно, можно генерировать TOUCH_MOVE
                # Для простоты: просто обновляем last_x/last_y
                pass

            self.last_x = screen_x
            self.last_y = screen_y
        else:
            if self.is_touched:
                # TOUCH_UP
                active_frame.process_event(EVENT_TOUCH_UP, self.last_x, self.last_y)
                if self.topbar:
                    self.topbar.process_event(EVENT_TOUCH_UP, self.last_x, self.last_y)
                self.is_touched = False
                event_generated = True

        # Генерируем TICK событие
        active_frame.process_event(EVENT_TICK, 0, 0)
        if self.topbar:
            self.topbar.process_event(EVENT_TICK, 0, 0)

        # Собираем флаги потребности в перерисовке (включая виджеты)
        frame_redraw = active_frame.needs_redraw
        for w in active_frame.widgets:
            if w.needs_redraw:
                frame_redraw = True
                break

        topbar_redraw = False
        if self.topbar:
            if self.topbar.needs_redraw:
                topbar_redraw = True
            else:
                for w in self.topbar.widgets:
                    if w.needs_redraw:
                        topbar_redraw = True
                        break

        # Проверяем, нужна ли перерисовка
        if frame_redraw or topbar_redraw or self.needs_redraw:
            # 2. Отрисовка в буфер (в RAM) - не блокируем SPI!
            if frame_redraw:
                active_frame.draw(self.display)

            # Рисуем топбар поверх в буфер (в RAM)
            if self.topbar and topbar_redraw:
                self.topbar.draw(self.display)

            self.needs_redraw = False

            # Обновляем дисплей (blit) - только когда была отрисовка!
            # SPI шина блокируется только на время отправки готового буфера
            with self.spi0_manager.acquire_display():
                self.display.swap_buffers()
