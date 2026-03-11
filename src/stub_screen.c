#include "stub_screen.h"
#include "home_screen.h"
#include "config.h"

// Заглушки для экранов APRS, PSK, Phone
// Заглушки для экранов APRS, PSK, Phone
static screen_descriptor_t s_aprs_screen = {0};
static screen_descriptor_t s_psk_screen = {0};
static screen_descriptor_t s_phone_screen = {0};

// Регистрация всех stub-экранов
void stub_screen_register_all(void)
{
    // Регистрируем APRS, PSK, Phone экраны
    screen_manager_register(&s_aprs_screen);
    screen_manager_register(&s_psk_screen);
    screen_manager_register(&s_phone_screen);
}
