/**
 * @file ipc_core.c
 * @brief Реализация очередей межъядерного взаимодействия
 */

#include "ipc_core.h"

queue_t q_core0_to_core1;
queue_t q_core1_to_core0;

void ipc_init(void) {
    // Инициализация очередей.
    // Очереди используют spinlocks (аппаратные блокировки) для потокобезопасности
    queue_init(&q_core0_to_core1, sizeof(core0_to_core1_msg_t), 10);
    queue_init(&q_core1_to_core0, sizeof(core1_to_core0_msg_t), 10);
}
