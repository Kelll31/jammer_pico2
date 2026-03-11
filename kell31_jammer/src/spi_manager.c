/**
 * @file spi_manager.c
 * @brief Реализация менеджера SPI и HAL для аппаратного ШИМ
 */

#include "spi_manager.h"
#include "config.h"
#include "hardware/gpio.h"
#include "hardware/sync.h"
#include "pico/mutex.h"
#include "hardware/pwm.h"
#include "hardware/clocks.h"

// Глобальный мьютекс для защиты шины SPI
static mutex_t spi_mutex;

// Вспомогательная функция для принудительного отключения всех устройств на шине
static void set_all_cs_high(void) {
    gpio_put(PIN_ILI9341_CS, 1);
    gpio_put(PIN_XPT2046_CS, 1);
    gpio_put(PIN_CC1101_CS, 1);
}

void spi_manager_init(void) {
    // Инициализируем мьютекс перед любыми операциями с SPI
    mutex_init(&spi_mutex);

    // Инициализация SPI на базовой частоте (будет меняться динамически)
    spi_init(SPI_PORT, 1000 * 1000);
    gpio_set_function(PIN_SPI0_MISO, GPIO_FUNC_SPI);
    gpio_set_function(PIN_SPI0_SCK, GPIO_FUNC_SPI);
    gpio_set_function(PIN_SPI0_MOSI, GPIO_FUNC_SPI);

    // Инициализируем пины CS и устанавливаем их в неактивное состояние (HIGH)
    gpio_init(PIN_ILI9341_CS);
    gpio_set_dir(PIN_ILI9341_CS, GPIO_OUT);
    gpio_put(PIN_ILI9341_CS, 1);

    gpio_init(PIN_XPT2046_CS);
    gpio_set_dir(PIN_XPT2046_CS, GPIO_OUT);
    gpio_put(PIN_XPT2046_CS, 1);

    gpio_init(PIN_CC1101_CS);
    gpio_set_dir(PIN_CC1101_CS, GPIO_OUT);
    gpio_put(PIN_CC1101_CS, 1);
}

void spi_manager_acquire(uint target_cs_pin, uint baudrate) {
    // Блокируем мьютекс (если шина занята другим ядром, мы подождем)
    mutex_enter_blocking(&spi_mutex);

    // Превентивно поднимаем все CS, чтобы исключить наложение сигналов
    set_all_cs_high();

    // Перенастраиваем частоту для текущего устройства
    spi_set_baudrate(SPI_PORT, baudrate);

    // Опускаем целевой CS, чтобы начать транзакцию
    gpio_put(target_cs_pin, 0);
}

void spi_manager_release(uint target_cs_pin) {
    // Поднимаем CS, завершая транзакцию
    gpio_put(target_cs_pin, 1);

    // Освобождаем мьютекс для других потоков/ядер
    mutex_exit(&spi_mutex);
}

void spi_manager_write_blocking(uint target_cs_pin, uint baudrate, const uint8_t *src, size_t len) {
    spi_manager_acquire(target_cs_pin, baudrate);
    spi_write_blocking(SPI_PORT, src, len);
    spi_manager_release(target_cs_pin);
}

void spi_manager_read_blocking(uint target_cs_pin, uint baudrate, uint8_t repeated_tx_data, uint8_t *dst, size_t len) {
    spi_manager_acquire(target_cs_pin, baudrate);
    spi_read_blocking(SPI_PORT, repeated_tx_data, dst, len);
    spi_manager_release(target_cs_pin);
}

void spi_manager_write_read_blocking(uint target_cs_pin, uint baudrate, const uint8_t *src, uint8_t *dst, size_t len) {
    spi_manager_acquire(target_cs_pin, baudrate);
    spi_write_read_blocking(SPI_PORT, src, dst, len);
    spi_manager_release(target_cs_pin);
}

// ==========================================
// ИНИЦИАЛИЗАЦИЯ ШИМ ДЛЯ ДЖАММЕРА (GP28)
// ==========================================

void jammer_pwm_init(void) {
    gpio_set_function(PIN_JAMMER_PWM, GPIO_FUNC_PWM);
    uint slice_num = pwm_gpio_to_slice_num(PIN_JAMMER_PWM);

    // Настраиваем ШИМ: без делителя для максимальной точности на высоких частотах
    pwm_config config = pwm_get_default_config();
    pwm_config_set_clkdiv(&config, 1.0f);
    pwm_init(slice_num, &config, false); // Инициализируем, но пока выключен
}

void jammer_pwm_set_freq(uint32_t freq_hz) {
    if (freq_hz == 0) return;

    uint slice_num = pwm_gpio_to_slice_num(PIN_JAMMER_PWM);
    uint32_t clock_freq = clock_get_hz(clk_sys); // Получаем текущую системную частоту (обычно 125 или 133 МГц)
    uint32_t wrap = clock_freq / freq_hz;

    // Устанавливаем период (wrap) и 50% заполнение (duty cycle)
    pwm_set_wrap(slice_num, wrap - 1);
    pwm_set_chan_level(slice_num, pwm_gpio_to_channel(PIN_JAMMER_PWM), wrap / 2);
}

void jammer_pwm_enable(bool enable) {
    uint slice_num = pwm_gpio_to_slice_num(PIN_JAMMER_PWM);
    pwm_set_enabled(slice_num, enable);
}
