/**
 * @file home_screen.c
 * @brief Главный экран с сеткой иконок в стиле Flipper Zero
 */

#include "config.h"
#include "screen_manager.h"
#include "module.h"
#include "screen_draw.h"
#include <stdio.h>
#include <string.h>
#include <ili9341.h>
#include <msp2807_touch.h>
#include <ui_context.h>
#include <ui_protos.h>
#include "GetUIContext.h"
#include "screen_touch_in_rect.h"

// ==========================================
// КОНФИГУРАЦИЯ HOME SCREEN
// ==========================================

#define HOME_SCREEN_WIDTH       240
#define HOME_SCREEN_HEIGHT      320
#define STATUS_BAR_HEIGHT       20
#define INFO_BAR_HEIGHT         16

// Параметры сетки
#define GRID_COLS               3
#define GRID_ROWS_VISIBLE       3
#define ICON_SIZE               56
#define ICON_SPACING            8
#define ICON_MARGIN_X           12
#define ICON_MARGIN_TOP         28

// Версия прошивки
#define FIRMWARE_VERSION        "1.0.0"

// ==========================================
// ДАННЫЕ ИКОНОК (BITMAP 1bpp примеры)
// ==========================================

// Простая иконка "молния" для джаммера (16x16)
static const uint8_t icon_jammer[] = {
    0x00, 0x18,
    0x00, 0x3C,
    0x00, 0x7E,
    0x00, 0x7E,
    0x00, 0x3C,
    0x00, 0x3C,
    0x00, 0x18,
    0x00, 0x18,
    0x00, 0x3C,
    0x00, 0x7E,
    0x00, 0xFF,
    0x00, 0xFF,
    0x00, 0x7E,
    0x00, 0x3C,
    0x00, 0x18,
    0x00, 0x00,
};

// Иконка "антенна" для Sub-GHz (16x16)
static const uint8_t icon_subghz[] = {
    0x00, 0x10,
    0x00, 0x38,
    0x00, 0x54,
    0x00, 0x54,
    0x00, 0x54,
    0x00, 0x54,
    0x00, 0x54,
    0x00, 0x54,
    0x00, 0x54,
    0x00, 0x54,
    0x00, 0x54,
    0x00, 0x54,
    0x00, 0x54,
    0x00, 0x54,
    0x00, 0x7C,
    0x00, 0x38,
};

// Иконка "радио" для Si4732 (16x16)
static const uint8_t icon_radio[] = {
    0x00, 0x00,
    0x00, 0x00,
    0x00, 0x00,
    0x3C, 0x3C,
    0x7E, 0x7E,
    0x7E, 0x7E,
    0x7E, 0x7E,
    0x7E, 0x7E,
    0x7E, 0x7E,
    0x7E, 0x7E,
    0x3C, 0x3C,
    0x18, 0x18,
    0x18, 0x18,
    0x3C, 0x3C,
    0x00, 0x00,
    0x00, 0x00,
};

// Иконка "график" для спектра (16x16)
static const uint8_t icon_spectrum[] = {
    0x00, 0x00,
    0x00, 0x00,
    0x00, 0x00,
    0x00, 0x00,
    0x01, 0x00,
    0x01, 0x04,
    0x01, 0x0C,
    0x05, 0x0C,
    0x05, 0x1C,
    0x0D, 0x1C,
    0x0D, 0x3C,
    0x1D, 0x3C,
    0x1D, 0x7C,
    0x3D, 0x7C,
    0x3D, 0xFC,
    0x7F, 0xFC,
};

// Иконка "шестерёнка" для настроек (16x16)
static const uint8_t icon_settings[] = {
    0x00, 0x00,
    0x00, 0x00,
    0x01, 0x80,
    0x03, 0xC0,
    0x06, 0x60,
    0x0C, 0x30,
    0x18, 0x18,
    0x18, 0x18,
    0x18, 0x18,
    0x18, 0x18,
    0x0C, 0x30,
    0x06, 0x60,
    0x03, 0xC0,
    0x01, 0x80,
    0x00, 0x00,
    0x00, 0x00,
};

// ==========================================
// КОНТЕКСТ HOME SCREEN
// ==========================================

typedef struct {
    uint32_t uptime_seconds;
    int scroll_offset;            // Смещение прокрутки
    int target_scroll_offset;     // Целевое смещение
    bool is_scrolling;            // Флаг прокрутки
    int scroll_velocity;          // Скорость прокрутки
    frame_rect icon_touch_rects[MODULE_COUNT]; // Тач-зоны иконок
} home_screen_ctx_t;

static home_screen_ctx_t s_home_ctx = {0};

// ==========================================
// МАССИВ МОДУЛЕЙ
// ==========================================

typedef struct {
    module_id_t id;
    const char *title;
    const uint8_t *icon_data;
    color_t color;
    screen_id_t target_screen;
} module_info_t;

static const module_info_t s_modules[] = {
    {MODULE_JAMMER,   "Jammer",   icon_jammer,   kRed,     SCREEN_JAMMER},
    {MODULE_SUBGHZ,   "Sub-GHz",  icon_subghz,   kOrange,  SCREEN_SUBGHZ},
    {MODULE_RADIO,    "Radio",    icon_radio,    kBlue,    SCREEN_RADIO},
    {MODULE_SPECTRUM, "Spectrum", icon_spectrum, kGreen,   SCREEN_SPECTRUM},
    {MODULE_SETTINGS, "Settings", icon_settings, kCyan,    SCREEN_SETTINGS},
};

#define MODULE_COUNT_ARR (sizeof(s_modules) / sizeof(s_modules[0]))

// ==========================================
// ЛОКАЛЬНЫЕ ФУНКЦИИ
// ==========================================

/// @brief Расчёт позиции иконки по индексу
static void get_icon_position(int index, int scroll_offset, int *out_x, int *out_y)
{
    int row = index / GRID_COLS;
    int col = index % GRID_COLS;
    
    int total_rows = (MODULE_COUNT_ARR + GRID_COLS - 1) / GRID_COLS;
    int grid_height = total_rows * (ICON_SIZE + ICON_SPACING) - ICON_SPACING;
    int start_y = ICON_MARGIN_TOP - scroll_offset;
    
    // Центрируем по вертикали если модулей мало
    if (grid_height < HOME_SCREEN_HEIGHT - STATUS_BAR_HEIGHT - INFO_BAR_HEIGHT - 40) {
        start_y = (HOME_SCREEN_HEIGHT - STATUS_BAR_HEIGHT - INFO_BAR_HEIGHT - grid_height) / 2;
    }
    
    *out_x = ICON_MARGIN_X + col * (ICON_SIZE + ICON_SPACING);
    *out_y = start_y + row * (ICON_SIZE + ICON_SPACING);
}

/// @brief Отрисовка главного экрана
static void home_screen_draw(void)
{
    screen_manager_ctx_t *mgr = screen_manager_get_ctx();
    if (mgr == NULL) return;
    
    ui_context *pUI = GetUIContext();
    if (pUI == NULL) return;
    
    screen_control_t *pScr = &pUI->mScreenCtl;
    
    // Очистка экрана
    TftFillRect(pScr, 0, 0, HOME_SCREEN_WIDTH, HOME_SCREEN_HEIGHT, kBlack);
    
    // Отрисовка статус-бара
    screen_draw_status_bar(pScr, mgr->battery_mv, mgr->core1_active, mgr->current_freq);
    
    // Отрисовка иконок с учётом прокрутки
    for (size_t i = 0; i < MODULE_COUNT_ARR; i++) {
        int icon_x, icon_y;
        get_icon_position(i, s_home_ctx.scroll_offset, &icon_x, &icon_y);
        
        // Пропускаем иконки вне экрана
        if (icon_y + ICON_SIZE < STATUS_BAR_HEIGHT || icon_y > HOME_SCREEN_HEIGHT - INFO_BAR_HEIGHT) {
            continue;
        }
        
        const module_info_t *mod = &s_modules[i];
        
        // Сохраняем тач-зону
        s_home_ctx.icon_touch_rects[mod->id].mTlx = icon_x;
        s_home_ctx.icon_touch_rects[mod->id].mTly = icon_y;
        s_home_ctx.icon_touch_rects[mod->id].mWidth = ICON_SIZE;
        s_home_ctx.icon_touch_rects[mod->id].mHeight = ICON_SIZE + 12; // + место для текста
        
        // Рисуем иконку
        screen_draw_flipper_icon(pScr, icon_x, icon_y, ICON_SIZE,
                                 mod->icon_data, 16, 16, mod->color, mod->title);
    }
    
    // Отрисовка инфо-панели
    screen_draw_info_bar(pScr, FIRMWARE_VERSION, s_home_ctx.uptime_seconds);
}

/// @brief Обработка тач-событий
static void home_screen_touch(int x, int y)
{
    screen_manager_ctx_t *mgr = screen_manager_get_ctx();
    
    // Проверка попадания в иконку
    for (size_t i = 0; i < MODULE_COUNT_ARR; i++) {
        const module_info_t *mod = &s_modules[i];
        frame_rect *rect = &s_home_ctx.icon_touch_rects[mod->id];
        
        if (screen_touch_in_rect(rect->mTlx, rect->mTly, rect->mWidth, rect->mHeight, x, y)) {
            // Переход к соответствующему экрану
            if (mod->target_screen != SCREEN_NONE) {
                screen_manager_navigate(mod->target_screen);
            }
            return;
        }
    }
    
    // Если тапнули вне иконок - можно реализовать жесты для прокрутки
    // Для простоты пока ничего не делаем
}

/// @brief Анимация прокрутки
static void home_screen_update_scroll(void)
{
    // Плавная прокрутка к целевой позиции
    if (s_home_ctx.scroll_offset != s_home_ctx.target_scroll_offset) {
        int diff = s_home_ctx.target_scroll_offset - s_home_ctx.scroll_offset;
        
        if (diff > 0) {
            s_home_ctx.scroll_offset += (diff + 3) / 4; // Плавное приближение
            if (s_home_ctx.scroll_offset > s_home_ctx.target_scroll_offset) {
                s_home_ctx.scroll_offset = s_home_ctx.target_scroll_offset;
            }
        } else {
            s_home_ctx.scroll_offset += (diff - 3) / 4;
            if (s_home_ctx.scroll_offset < s_home_ctx.target_scroll_offset) {
                s_home_ctx.scroll_offset = s_home_ctx.target_scroll_offset;
            }
        }
        
        // Перерисовка
        home_screen_draw();
    }
}

// ==========================================
// ОБРАБОТЧИК СОБЫТИЙ HOME SCREEN
// ==========================================

static int home_screen_event(screen_id_t id, screen_event_t evt, void *data, void *ctx)
{
    (void)id;
    (void)data;
    
    screen_manager_ctx_t *mgr = (screen_manager_ctx_t *)ctx;
    
    switch (evt) {
        case SCREEN_EVENT_INIT:
            s_home_ctx.scroll_offset = 0;
            s_home_ctx.target_scroll_offset = 0;
            s_home_ctx.uptime_seconds = 0;
            memset(s_home_ctx.icon_touch_rects, 0, sizeof(s_home_ctx.icon_touch_rects));
            break;
            
        case SCREEN_EVENT_SHOW:
            home_screen_draw();
            break;
            
        case SCREEN_EVENT_TICK:
            s_home_ctx.uptime_seconds = mgr->uptime_us / 1000000;
            home_screen_update_scroll();
            break;
            
        case SCREEN_EVENT_TOUCH: {
            screen_touch_data_t *touch = (screen_touch_data_t *)data;
            if (touch != NULL && touch->is_press) {
                home_screen_touch(touch->x, touch->y);
            }
            break;
        }
        
        case SCREEN_EVENT_HIDE:
        case SCREEN_EVENT_DEINIT:
            break;
            
        default:
            break;
    }
    
    return 0;
}

// ==========================================
// ДЕСКРИПТОР HOME SCREEN
// ==========================================

static screen_descriptor_t s_home_screen = {
    .id = SCREEN_HOME,
    .name = "home",
    .title = "Home",
    .icon_data = NULL,
    .icon_width = 0,
    .icon_height = 0,
    .color = kBlack,
    .ink = kWhite,
    .on_event = home_screen_event,
    .data = &s_home_ctx,
    .initialized = false,
    .visible = false,
    .has_status_bar = true,
    .has_info_bar = true,
};

// ==========================================
// ПУБЛИЧНЫЕ ФУНКЦИИ
// ==========================================

screen_descriptor_t* home_screen_get_descriptor(void)
{
    return &s_home_screen;
}

void home_screen_set_module_state(module_id_t id, module_state_t state)
{
    if (id < MODULE_COUNT) {
        // Можно добавить индикацию состояния
    }
}
