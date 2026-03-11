/**
 * @file home_screen.h
 * @brief Главный экран с сеткой иконок в стиле Flipper Zero
 */

#ifndef HOME_SCREEN_H
#define HOME_SCREEN_H

#include "config.h"
#include "screen_manager.h"

// ==========================================
// ТИПЫ ДАННЫХ
// ==========================================

/**
 * @brief ID модулей на главном экране
 */
typedef enum {
    MODULE_JAMMER = 0,      // Джаммер
    MODULE_SUBGHZ,          // Sub-GHz (CC1101)
    MODULE_RADIO,           // Radio (Si4732)
    MODULE_SPECTRUM,        // Спектральный анализ
    MODULE_SETTINGS,        // Настройки
    MODULE_COUNT            // Количество модулей
} module_id_t;

/**
 * @brief Состояние модуля
 */
typedef enum {
    MODULE_STATE_IDLE = 0,  // Неактивен
    MODULE_STATE_RUNNING,   // Активен в фоне
    MODULE_STATE_BUSY       // Заблокирован
} module_state_t;

// ==========================================
// ФУНКЦИИ
// ==========================================

/**
 * @brief Получить дескриптор главного экрана
 * @return Указатель на дескриптор
 */
screen_descriptor_t* home_screen_get_descriptor(void);

/**
 * @brief Обновление статуса модуля
 * @param id ID модуля
 * @param state Новое состояние
 */
void home_screen_set_module_state(module_id_t id, module_state_t state);

#endif // HOME_SCREEN_H
