#ifndef SCREEN_MANAGER_H
#define SCREEN_MANAGER_H

#include "config.h"
#include <ui_context.h>

// Context for screen manager
typedef struct {
    uint64_t uptime_us;
    int battery_mv;
    bool core1_active;
    int current_freq;
} screen_manager_ctx_t;

// Screen descriptor
typedef struct {
    screen_id_t id;
    const char *name;
    const char *title;
    const uint8_t *icon_data;
    int icon_width;
    int icon_height;
    color_t color;
    color_t ink;
    int (*on_event)(screen_id_t id, screen_event_t evt, void *data, void *ctx);
    void *data;
    bool initialized;
    bool visible;
    bool has_status_bar;
    bool has_info_bar;
} screen_descriptor_t;

void screen_manager_init(void);
screen_manager_ctx_t* screen_manager_get_ctx(void);
void screen_manager_register(screen_descriptor_t *desc);
void screen_manager_navigate(screen_id_t target_screen);
void screen_manager_tick(ui_context *pUI);

#endif // SCREEN_MANAGER_H
