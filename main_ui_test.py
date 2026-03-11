"""
Тестовый скрипт для проверки интеграции SPI0 (ILI9341 + XPT2046)
на Core 0 с использованием Anti-Collision SPI-Manager.
"""

import time
import config
from spi_manager import init_managers, spi0_manager

# Сначала инициализируем менеджеры, потом импортируем драйверы
init_managers()

from ili9341 import ILI9341
from xpt2046 import XPT2046

def run_integration_test():
    print("Инициализация SPI менеджеров...")
    print("Инициализация ILI9341 дисплея...")
    display = ILI9341()

    print("Инициализация XPT2046 тачскрина...")
    touch = XPT2046()

    # Очистка дисплея
    print("Очистка экрана (заливка чёрным)...")
    display.fill_screen(config.COLOR_BLACK)
    display.draw_text(10, 10, "SPI ANTI-COLLISION TEST", config.COLOR_GREEN, config.COLOR_BLACK)
    display.draw_text(10, 30, "Touch the screen...", config.COLOR_WHITE, config.COLOR_BLACK)
    display.swap_buffers()

    print("Тест запущен. Нажмите Ctrl+C для выхода.")

    last_touch_check = time.ticks_ms()
    last_swap_time = time.ticks_ms()
    points_drawn = 0

    try:
        while True:
            current_time = time.ticks_ms()

            # Проверяем тачскрин не слишком часто, чтобы не блокировать всё
            if time.ticks_diff(current_time, last_touch_check) >= 10:
                last_touch_check = current_time

                # Используем get_touch_coordinates, который под капотом использует get_raw_touch с фильтрами
                screen_x, screen_y, valid = touch.get_touch_coordinates()

                if valid and screen_x is not None and screen_y is not None:
                    # Рисуем точку
                    display.draw_filled_circle(screen_x, screen_y, 2, config.COLOR_RED)
                    points_drawn += 1

            # Свапаем буфер не чаще ~30 раз в секунду (33ms)
            if time.ticks_diff(current_time, last_swap_time) >= 33:
                last_swap_time = current_time
                if points_drawn > 0:
                    display.swap_buffers()
                    points_drawn = 0

            # Используем sleep_us для небольшой передышки CPU, но не блокируемся надолго
            time.sleep_us(1000)

    except KeyboardInterrupt:
        print("Тест завершён пользователем.")

if __name__ == "__main__":
    run_integration_test()
