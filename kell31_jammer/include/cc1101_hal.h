/**
 * @file cc1101_hal.h
 * @brief Аппаратный драйвер для Sub-GHz радиомодуля CC1101
 *        с использованием безопасного SPI (spi_manager).
 */

#ifndef CC1101_HAL_H
#define CC1101_HAL_H

#include <stdint.h>
#include <stdbool.h>

/**
 * @brief Инициализация радиомодуля CC1101
 * Выполняет сброс (Reset) чипа и начальную конфигурацию.
 */
void cc1101_init(void);

/**
 * @brief Чтение статусного регистра CC1101
 */
uint8_t cc1101_read_status_reg(uint8_t addr);

/**
 * @brief Запись значения в регистр CC1101
 */
void cc1101_write_reg(uint8_t addr, uint8_t value);

/**
 * @brief Чтение значения из регистра CC1101
 */
uint8_t cc1101_read_reg(uint8_t addr);

/**
 * @brief Запись команды-строба (Strobe Command)
 */
void cc1101_strobe(uint8_t cmd);

/**
 * @brief Чтение пакета из RX FIFO
 */
void cc1101_read_fifo(uint8_t *buffer, uint8_t length);

/**
 * @brief Запись пакета в TX FIFO
 */
void cc1101_write_fifo(const uint8_t *buffer, uint8_t length);

#endif // CC1101_HAL_H
