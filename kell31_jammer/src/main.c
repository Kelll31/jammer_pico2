#include <stdio.h>
#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "config.h"
#include "spi_manager.h"
#include "cc1101_hal.h"
#include "ipc_core.h"

#include <ili9341.h>
#include <msp2807_touch.h>
#include <msp2807_calibration.h>
#include <ui_context.h>
#include <ui_protos.h>

// Прототип функции второго ядра (будет реализована на Этапе 4)
void core1_entry(void);

int main() {
    stdio_init_all();

    // Инициализация очередей межъядерного взаимодействия (IPC) до запуска ядер
    ipc_init();

    // 1. Инициализируем наш безопасный менеджер SPI
    spi_manager_init();

    // 2. Инициализируем UI контекст (pico-widgets)
    ui_context *pUI = InitUI();
    screen_control_t *pScrCtl = &pUI->mScreenCtl;
    touch_control_t *pTouchCtl= &pUI->mTouchCtl;

    // 3. Инициализируем дисплей ILI9341
    ili9341_config_t ili9341_hw_config;
    pScrCtl->mpHWConfig = &ili9341_hw_config;
    ILI9341_Init(pScrCtl->mpHWConfig, SPI_PORT, SPI0_BAUDRATE_ILI9341,
                 PIN_SPI0_MISO, PIN_ILI9341_CS, PIN_SPI0_SCK, PIN_SPI0_MOSI,
                 PIN_ILI9341_RST, PIN_ILI9341_DC);

    TftClearScreenBuffer(pScrCtl, kBlack, kWhite);
    TftSetCursor(pScrCtl, 0, 20);

    // 4. Инициализируем тачскрин XPT2046
    touch_hwconfig_t touch_hwc;
    TouchInitHW(&touch_hwc, SPI_PORT, SPI0_BAUDRATE_XPT2046,
                PIN_SPI0_MISO, PIN_XPT2046_CS, PIN_SPI0_SCK, PIN_SPI0_MOSI,
                PIN_XPT2046_IRQ);
    TouchInitCtl(pTouchCtl, &touch_hwc, 1000, 50000, 5);

    // Заглушка: базовые точки для калибровки (нужно будет делать реальную калибровку)
    const int16_t refpoints[] = { 0, 0, 240, 0, 0, 320, 240, 320 };
    const int16_t smplpoints[] = { 10, 120, 119, 119, 9, 11, 118, 12 };
    CalculateCalibrationMat(refpoints, smplpoints, 4, &pUI->mTouchCalMat);

    // 5. Инициализируем ШИМ джаммера
    jammer_pwm_init();

    // 6. Запускаем второе ядро (для CC1101 и Real-Time)
    multicore_launch_core1(core1_entry);

    // Основной цикл UI (Core 0)
    for(int tick = 0;;++tick)
    {
        tight_loop_contents();

        static uint64_t sLastTm = 0;
        const uint64_t ktm64_now = time_us_64();

        /* Prevent flicker / Limit frame rate to 50 Hz (20000 us) */
        if(ktm64_now - 20000ULL < sLastTm)
        {
            continue;
        }
        sLastTm = ktm64_now;

        frame *pfActive = GetActiveFrame(pUI);
        static frame *spfActiveM1 = NULL;
        if(!pfActive)
        {
            continue;
        }

        // Если сменился активный фрейм - отрисовать его полностью
        if(pfActive != spfActiveM1)
        {
            pfActive->mpfEventProc(pfActive, kEventDraw, 0, 0, pUI);
            spfActiveM1 = pfActive;
            continue;
        }

        // Эквивалент UItick из pico-widgets (без использования прерываний)
        // Обновляем состояние тачскрина
        bool kbnew_touch = GetTouchData(pUI, &pUI->mLastX, &pUI->mLastY);
        if(kbnew_touch) { pUI->mLastTouchTm = time_us_64(); }

        // Обработка кликов внутри/снаружи виджета
        if(pUI->mLastReleaseTm > pUI->mLastTouchTm)
        {
            if(pfActive->mpfEventProc)
            {
                IsInsideRect(&pfActive->mRegion, pUI->mLastX, pUI->mLastY)
                    ? pfActive->mpfEventProc(pfActive, kEventClickInside, pUI->mLastX, pUI->mLastY, pUI)
                    : pfActive->mpfEventProc(pfActive, kEventClickOutside, pUI->mLastX, pUI->mLastY, pUI);
            }
            pUI->mLastTouchTm = ktm64_now;
        }

        // Обновление экрана (частичная перерисовка)
        TftFullScreenSelectiveWrite(pScrCtl, 8);

        // Неблокирующее чтение событий от Core 1 (Радио/Джаммер)
        core1_to_core0_msg_t rx_msg;
        if (queue_try_remove(&q_core1_to_core0, &rx_msg)) {
            // Обработка данных пакета с CC1101 в UI или статуса джаммера
            // if (rx_msg.evt == EVT_RADIO_PACKET_RX) { ... }
        }
    }

    return 0;
}

// ==========================================
// КОД ВТОРОГО ЯДРА (Core 1) - Real-time & Radio
// ==========================================
void core1_entry(void) {
    // 1. Инициализируем радиомодуль (через безопасный SPI)
    cc1101_init();

    // Структура для приема команд от Core 0
    core0_to_core1_msg_t rx_cmd;

    // Бесконечный цикл Core 1 без sleep_ms!
    while(1) {
        // 1. Проверяем новые команды от UI
        if (queue_try_remove(&q_core0_to_core1, &rx_cmd)) {
            switch(rx_cmd.cmd) {
                case CMD_JAMMER_START:
                    jammer_pwm_set_freq(rx_cmd.param1);
                    jammer_pwm_enable(true);
                    break;
                case CMD_JAMMER_STOP:
                    jammer_pwm_enable(false);
                    break;
                case CMD_RADIO_SCAN_START:
                    // Запуск поллинга или прерываний CC1101
                    break;
                default:
                    break;
            }
        }

        // 2. Пример поллинга прерывания GDO0 CC1101 (пакет принят)
        if (gpio_get(PIN_CC1101_GDO0)) {
            // Читаем пакет
            uint8_t buffer[16];
            cc1101_read_fifo(buffer, sizeof(buffer));

            // Отправляем UI (Core 0)
            core1_to_core0_msg_t tx_msg;
            tx_msg.evt = EVT_RADIO_PACKET_RX;
            tx_msg.data = 16;
            for(int i=0; i<16; i++) tx_msg.payload[i] = buffer[i];

            queue_try_add(&q_core1_to_core0, &tx_msg);

            // Ждем пока пин не опустится (упрощенно)
            while(gpio_get(PIN_CC1101_GDO0)) { tight_loop_contents(); }
        }

        // Выполняем tight_loop_contents() вместо sleep_ms(),
        // чтобы ядро не простаивало, но могло экономить энергию, если нужно.
        tight_loop_contents();
    }
}
