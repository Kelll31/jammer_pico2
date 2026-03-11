/**
 * @file config.h
 * @brief Глобальные аппаратные настройки проекта KELL31 Jammer
 *
 * Содержит определения пинов, частот и общих параметров для
 * микроконтроллеров RP2040 / RP2350.
 */

#include <stdbool.h>

// ==========================================
// ТИПЫ ДАННЫХ ДЛЯ UI
// ==========================================

typedef enum {
    kBlack,
    kBlue,
    kRed,
    kMagenta,
    kGreen,
    kCyan,
    kYellow,
    kWhite
} color_t;

typedef enum {
    SCREEN_NONE = 0,
    SCREEN_HOME,
    SCREEN_JAMMER,
    SCREEN_SUBGHZ,
    SCREEN_RADIO,
    SCREEN_SPECTRUM,
    SCREEN_SETTINGS
} screen_id_t;

typedef enum {
    SCREEN_EVENT_INIT = 0,
    SCREEN_EVENT_SHOW,
    SCREEN_EVENT_HIDE,
    SCREEN_EVENT_TICK,
    SCREEN_EVENT_TOUCH,
    SCREEN_EVENT_DEINIT
} screen_event_t;

typedef struct {
    int mTlx;
    int mTly;
    int mWidth;
    int mHeight;
} frame_rect;

typedef struct {
    int x;
    int y;
    bool is_press;
} screen_touch_data_t;

// ==========================================
// НАСТРОЙКИ ОБЩЕЙ ШИНЫ SPI0
// ==========================================
#define SPI_PORT        spi0
#define PIN_SPI0_MISO   16  // RX
#define PIN_SPI0_CS_DUMMY 255 // Dummy CS для инициализации шины (реальное управление ручное)
#define PIN_SPI0_SCK    18  // SCK
#define PIN_SPI0_MOSI   19  // TX

// ==========================================
// ДИСПЛЕЙ ILI9341 (на шине SPI0)
// ==========================================
#define PIN_ILI9341_CS  17  // Chip Select дисплея
#define PIN_ILI9341_DC  20  // Data / Command
#define PIN_ILI9341_RST 21  // Reset
#define PIN_ILI9341_BLK 14  // Подсветка (Backlight)
#define SPI0_BAUDRATE_ILI9341 (40 * 1000 * 1000) // 40 MHz для быстрой отрисовки UI

// ==========================================
// ТАЧСКРИН XPT2046 (на шине SPI0)
// ==========================================
#define PIN_XPT2046_CS  22  // Chip Select тачскрина
#define PIN_XPT2046_IRQ 15  // Прерывание тачскрина (PEN IRQ)
#define SPI0_BAUDRATE_XPT2046 (2 * 1000 * 1000)  // 2 MHz для стабильного чтения тача

// ==========================================
// РАДИОМОДУЛЬ SUB-GHZ CC1101 (на шине SPI0)
// ==========================================
#define PIN_CC1101_CS   13  // Chip Select CC1101 (ТРЕБУЕТ УТОЧНЕНИЯ НА ПЛАТЕ)
#define PIN_CC1101_GDO0 12  // Пин прерывания (RX/TX Packet) (ТРЕБУЕТ УТОЧНЕНИЯ НА ПЛАТЕ)
#define PIN_CC1101_GDO2 11  // Опциональный пин прерывания CC1101
#define SPI0_BAUDRATE_CC1101 (5 * 1000 * 1000)   // 5 MHz стандарт для CC1101

// ==========================================
// DSP ПРИЕМНИК Si4732 (I2C0)
// ==========================================
#define I2C_PORT        i2c0
#define PIN_I2C0_SDA    4   // I2C SDA (ТРЕБУЕТ УТОЧНЕНИЯ НА ПЛАТЕ)
#define PIN_I2C0_SCL    5   // I2C SCL (ТРЕБУЕТ УТОЧНЕНИЯ НА ПЛАТЕ)
#define I2C_BAUDRATE    (400 * 1000) // 400 kHz Fast Mode

// ==========================================
// ДЖАММЕР И ИНДИКАЦИЯ
// ==========================================
#define PIN_JAMMER_PWM  28  // Выход ШИМ-генератора помех
#define PIN_LED         25  // Индикаторный светодиод (на Pico - встроенный)


#endif // CONFIG_H
