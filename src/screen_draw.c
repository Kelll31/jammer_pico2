#include "screen_draw.h"
#include "config.h"
#include <stdio.h>
#include <string.h>

// Отрисовка иконки в стиле Flipper Zero
void screen_draw_flipper_icon(screen_control_t *pscr, int x, int y, int size,
                              const uint8_t *icon_data, int icon_width, int icon_height,
                              color_t color, const char *title)
{
    // Отрисовка рамки иконки
    TftPutLine(pscr, x, y, x + size - 1, y);
    TftPutLine(pscr, x + size - 1, y, x + size - 1, y + size - 1);
    TftPutLine(pscr, x + size - 1, y + size - 1, x, y + size - 1);
    TftPutLine(pscr, x, y + size - 1, x, y);

    // Отрисовка иконки
    if (icon_data != NULL) {
        int icon_x = x + (size - icon_width) / 2;
        int icon_y = y + (size - icon_height) / 2 - 4; // Смещение для текста

        for (int i = 0; i < icon_height; i++) {
            for (int j = 0; j < icon_width; j++) {
                uint8_t byte = icon_data[i * (icon_width / 8) + j / 8];
                uint8_t bit = (byte >> (7 - (j % 8))) & 1;
                if (bit) {
                    TftPutPixel(pscr, icon_x + j, icon_y + i, color, kBlack);
                }
            }
        }
    }

    // Отрисовка текста под иконкой
    if (title != NULL) {
        int text_y = y + size + 2;
        TftPutString(pscr, title, x + (size - strlen(title) * 8) / 2, text_y, color, kBlack);
    }
}

// Отрисовка статус-бара
void screen_draw_status_bar(screen_control_t *pscr, int battery_mv, bool core1_active, int current_freq)
{
    // Фон статус-бара
    for (int y = 0; y < 20; y++) {
        for (int x = 0; x < 240; x++) {
            TftPutPixel(pscr, x, y, kBlue, kBlack);
        }
    }

    // Иконка батареи
    TftPutLine(pscr, 5, 5, 15, 5);
    TftPutLine(pscr, 15, 5, 15, 15);
    TftPutLine(pscr, 15, 15, 5, 15);
    TftPutLine(pscr, 5, 15, 5, 5);
    TftPutLine(pscr, 16, 7, 16, 13);
    TftPutLine(pscr, 16, 7, 18, 7);
    TftPutLine(pscr, 16, 13, 18, 13);
    TftPutLine(pscr, 18, 7, 18, 13);

    // Заряд батареи
    int battery_level = (battery_mv - 3000) / 10; // Упрощенный расчет
    if (battery_level > 10) battery_level = 10;
    if (battery_level < 0) battery_level = 0;

    for (int i = 0; i < battery_level; i++) {
        for (int y = 7; y < 7 + 6; y++) {
            TftPutPixel(pscr, 7 + i * 1, y, kGreen, kBlack);
        }
    }

    // Иконка активности Core 1
    if (core1_active) {
        for (int y = 8; y < 8 + 4; y++) {
            for (int x = 30; x < 30 + 4; x++) {
                TftPutPixel(pscr, x, y, kRed, kBlack);
            }
        }
    }

    // Текущая частота
    char freq_str[16];
    if (current_freq > 0) {
        snprintf(freq_str, sizeof(freq_str), "%d MHz", current_freq / 1000000);
        TftPutString(pscr, freq_str, 40, 5, kWhite, kBlue);
    }
}

// Отрисовка инфо-панели
void screen_draw_info_bar(screen_control_t *pscr, const char *firmware_version, uint32_t uptime_seconds)
{
    // Фон инфо-панели
    for (int y = 304; y < 304 + 16; y++) {
        for (int x = 0; x < 240; x++) {
            TftPutPixel(pscr, x, y, kBlack, kBlack); // As kDarkGray isn't defined, fallback to kBlack
        }
    }

    // Версия прошивки
    char version_str[32];
    snprintf(version_str, sizeof(version_str), "v%s", firmware_version);
    TftPutString(pscr, version_str, 5, 308, kWhite, kBlack);

    // Аптайм
    uint32_t hours = uptime_seconds / 3600;
    uint32_t minutes = (uptime_seconds % 3600) / 60;
    uint32_t seconds = uptime_seconds % 60;

    char uptime_str[32];
    snprintf(uptime_str, sizeof(uptime_str), "%02d:%02d:%02d", hours, minutes, seconds);
    TftPutString(pscr, uptime_str, 180, 308, kWhite, kBlack);
}