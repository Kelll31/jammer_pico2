/**
 * @file ipc_core.h
 * @brief Очереди для взаимодействия между ядрами (Inter-Process Communication)
 */

#ifndef IPC_CORE_H
#define IPC_CORE_H

#include <stdint.h>
#include <stdbool.h>
#include "pico/util/queue.h"

// Типы сообщений от Core 0 (UI) к Core 1 (Radio/Jammer)
typedef enum {
    CMD_JAMMER_START,
    CMD_JAMMER_STOP,
    CMD_JAMMER_SET_FREQ,
    CMD_RADIO_SCAN_START,
    CMD_RADIO_SCAN_STOP
} core0_to_core1_cmd_t;

// Структура сообщения от Core 0 к Core 1
typedef struct {
    core0_to_core1_cmd_t cmd;
    uint32_t param1;
    uint32_t param2;
} core0_to_core1_msg_t;

// Типы сообщений от Core 1 к Core 0
typedef enum {
    EVT_RADIO_PACKET_RX,
    EVT_JAMMER_STATUS
} core1_to_core0_evt_t;

// Структура сообщения от Core 1 к Core 0
typedef struct {
    core1_to_core0_evt_t evt;
    uint32_t data;
    uint8_t payload[16];
} core1_to_core0_msg_t;

// Глобальные очереди (должны быть инициализированы в main до запуска core1)
extern queue_t q_core0_to_core1;
extern queue_t q_core1_to_core0;

/**
 * @brief Инициализация очередей межъядерного взаимодействия
 */
void ipc_init(void);

#endif // IPC_CORE_H
