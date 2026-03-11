#include "screen_manager.h"

// Dummy implementation for now
static screen_manager_ctx_t s_ctx;

void screen_manager_init(void) {
    s_ctx.uptime_us = 0;
    s_ctx.battery_mv = 4200;
    s_ctx.core1_active = false;
    s_ctx.current_freq = 0;
}

screen_manager_ctx_t* screen_manager_get_ctx(void) {
    return &s_ctx;
}

void screen_manager_register(screen_descriptor_t *desc) {
}

void screen_manager_navigate(screen_id_t target_screen) {
}

void screen_manager_tick(ui_context *pUI) {
}
