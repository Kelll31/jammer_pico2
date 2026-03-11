/**
 * @file spi_manager.h
 * @brief Потокобезопасный менеджер SPI для предотвращения коллизий на общей шине
 */

#ifndef SPI_MANAGER_H
#define SPI_MANAGER_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include "hardware/spi.h"

/**
 * @brief Инициализация SPI, мьютекса и пинов CS (Chip Select)
 */
void spi_manager_init(void);

/**
 * @brief Захват шины SPI (Anti-Collision механизм).
 * Блокирует мьютекс, поднимает все CS в HIGH,
 * устанавливает нужную частоту (baudrate) и опускает целевой CS в LOW.
 *
 * @param target_cs_pin Целевой пин CS для общения с устройством
 * @param baudrate Требуемая частота для текущего устройства
 */
void spi_manager_acquire(uint target_cs_pin, uint baudrate);

/**
 * @brief Освобождение шины SPI.
 * Поднимает целевой CS в HIGH и освобождает мьютекс.
 *
 * @param target_cs_pin Целевой пин CS для общения с устройством
 */
void spi_manager_release(uint target_cs_pin);

/**
 * @brief Вспомогательная функция для записи данных с автоматическим захватом/освобождением
 */
void spi_manager_write_blocking(uint target_cs_pin, uint baudrate, const uint8_t *src, size_t len);

/**
 * @brief Вспомогательная функция для чтения данных с автоматическим захватом/освобождением
 */
void spi_manager_read_blocking(uint target_cs_pin, uint baudrate, uint8_t repeated_tx_data, uint8_t *dst, size_t len);

/**
 * @brief Вспомогательная функция для одновременной записи и чтения
 */
void spi_manager_write_read_blocking(uint target_cs_pin, uint baudrate, const uint8_t *src, uint8_t *dst, size_t len);

/**
 * @brief Инициализация ШИМ-генератора для джаммера
 */
void jammer_pwm_init(void);

/**
 * @brief Установка частоты ШИМ-генератора джаммера
 * @param freq_hz Желаемая частота в Гц
 */
void jammer_pwm_set_freq(uint32_t freq_hz);

/**
 * @brief Включение или выключение ШИМ
 * @param enable true для включения, false для выключения
 */
void jammer_pwm_enable(bool enable);

#endif // SPI_MANAGER_H
