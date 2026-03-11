#include "stub_screen.h"
#include "home_screen.h"
#include "config.h"

// Заглушки для экранов APRS, PSK, Phone
// Заглушки для экранов APRS, PSK, Phone
static int s_aprs_screen = 0;
static int s_psk_screen = 0;
static int s_phone_screen = 0;

// Регистрация всех stub-экранов
void stub_screen_register_all(void)
{
    // Регистрируем APRS, PSK, Phone экраны
    stub_screen_register(&s_aprs_screen);
    stub_screen_register(&s_psk_screen);
    stub_screen_register(&s_phone_screen);
}
