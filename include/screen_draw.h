#ifndef SCREEN_DRAW_H
#define SCREEN_DRAW_H

#include "ili9341.h"
#include "frame.h"

// Отрисовка иконки в стиле Flipper Zero
void screen_draw_flipper_icon(screen_control_t *pscr, int x, int y, int size,
                              const uint8_t *icon_data, int icon_width, int icon_height,
                              color_t color, const char *title);

// Отрисовка статус-бара
void screen_draw_status_bar(screen_control_t *pscr, int battery_mv, bool core1_active, int current_freq);

// Отрисовка инфо-панели
void screen_draw_info_bar(screen_control_t *pscr, const char *firmware_version, uint32_t uptime_seconds);

#endif // SCREEN_DRAW_H