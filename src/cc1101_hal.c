/**
 * @file cc1101_hal.c
 * @brief Реализация драйвера CC1101
 */

#include "cc1101_hal.h"
#include "config.h"
#include "spi_manager.h"

// Добавлены необходимые библиотеки Pico SDK
#include "pico/stdlib.h"
#include "hardware/gpio.h"
#include "hardware/spi.h"
#include "pico/time.h"

// Константы CC1101 SPI (Чтение/Запись/Берст маски)
#define CC1101_WRITE_BURST 0x40
#define CC1101_READ_SINGLE 0x80
#define CC1101_READ_BURST 0xC0

#define CC1101_SRES 0x30  // Reset chip
#define CC1101_SRX 0x34   // Enable RX
#define CC1101_STX 0x35   // Enable TX
#define CC1101_SIDLE 0x36 // Exit RX / TX
#define CC1101_SFRX 0x3A  // Flush the RX FIFO buffer
#define CC1101_SFTX 0x3B  // Flush the TX FIFO buffer

#define CC1101_RXFIFO 0x3F // RX FIFO Address
#define CC1101_TXFIFO 0x3F // TX FIFO Address

void cc1101_init(void)
{
    gpio_init(PIN_CC1101_CS);
    gpio_set_dir(PIN_CC1101_CS, GPIO_OUT);
    gpio_put(PIN_CC1101_CS, 1);

    // Инициализация пина GDO0 для прерываний от радио
    gpio_init(PIN_CC1101_GDO0);
    gpio_set_dir(PIN_CC1101_GDO0, GPIO_IN);

    // Сброс чипа (Manual Reset Sequence)
    gpio_put(PIN_CC1101_CS, 1);
    sleep_us(5);
    gpio_put(PIN_CC1101_CS, 0);
    sleep_us(10);
    gpio_put(PIN_CC1101_CS, 1);
    sleep_us(41);

    // Посылаем строб сброса SRES
    cc1101_strobe(CC1101_SRES);
}

void cc1101_strobe(uint8_t cmd)
{
    spi_manager_write_blocking(PIN_CC1101_CS, SPI0_BAUDRATE_CC1101, &cmd, 1);
}

void cc1101_write_reg(uint8_t addr, uint8_t value)
{
    uint8_t tx_buf[2] = {addr, value};
    spi_manager_write_blocking(PIN_CC1101_CS, SPI0_BAUDRATE_CC1101, tx_buf, 2);
}

uint8_t cc1101_read_reg(uint8_t addr)
{
    uint8_t tx_buf[2] = {addr | CC1101_READ_SINGLE, 0x00};
    uint8_t rx_buf[2] = {0, 0};
    spi_manager_write_read_blocking(PIN_CC1101_CS, SPI0_BAUDRATE_CC1101, tx_buf, rx_buf, 2);
    return rx_buf[1];
}

uint8_t cc1101_read_status_reg(uint8_t addr)
{
    uint8_t tx_buf[2] = {addr | CC1101_READ_BURST, 0x00};
    uint8_t rx_buf[2] = {0, 0};
    spi_manager_write_read_blocking(PIN_CC1101_CS, SPI0_BAUDRATE_CC1101, tx_buf, rx_buf, 2);
    return rx_buf[1];
}

void cc1101_write_fifo(const uint8_t *buffer, uint8_t length)
{
    spi_manager_acquire(PIN_CC1101_CS, SPI0_BAUDRATE_CC1101);

    uint8_t addr = CC1101_TXFIFO | CC1101_WRITE_BURST;
    spi_write_blocking(SPI_PORT, &addr, 1);
    spi_write_blocking(SPI_PORT, buffer, length);

    spi_manager_release(PIN_CC1101_CS);
}

void cc1101_read_fifo(uint8_t *buffer, uint8_t length)
{
    spi_manager_acquire(PIN_CC1101_CS, SPI0_BAUDRATE_CC1101);

    uint8_t addr = CC1101_RXFIFO | CC1101_READ_BURST;
    spi_write_blocking(SPI_PORT, &addr, 1);
spi_read_blocking(SPI_PORT, 0x00, buffer, length);

    spi_manager_release(PIN_CC1101_CS);
}