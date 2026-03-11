# KELL31 Jammer Pico2

Многофункциональный RF-инструмент с сенсорным интерфейсом на базе **Raspberry Pi Pico 2** (RP2350). Устройство объединяет генерацию сигналов джаммера, приём/передачу данных через радиомодуль CC1101, DSP-приёмник Si4732 и интуитивный GUI с тачскрином.

![License](https://img.shields.io/badge/license-proprietary-blue.svg)
![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi%20Pico%202-orange.svg)
![SDK](https://img.shields.io/badge/Pico%20SDK-2.2.0-green.svg)

---

## 📋 Содержание

- [Возможности](#-возможности)
- [Аппаратная часть](#-аппаратная-часть)
- [Архитектура ПО](#-архитектура-по)
- [Структура проекта](#-структура-проекта)
- [Сборка и прошивка](#-сборка-и-прошивка)
- [API и использование](#-api-и-использование)
- [Отладка](#-отладка)
- [Важные замечания](#-важные-замечания)

---

## ✨ Возможности

### Основные функции

- **Сенсорный интерфейс** на базе дисплея ILI9341 (240×320) с тачскрином XPT2046
- **Генерация помех (Jammer)** с программируемой частотой через ШИМ
- **Приём/передача данных** через Sub-GHz радиомодуль CC1101
- **DSP-приёмник** Si4732 для обработки радиосигналов
- **Двухъядерная обработка** с разделением задач между ядрами RP2350

### Технические особенности

- **Анти-коллизия SPI** — безопасное разделение шины между 3 устройствами
- **Межъядерное взаимодействие (IPC)** через очереди pico_util
- **Энергоэффективная отрисовка** — обновление только изменённых областей экрана
- **Real-time обработка** радиоэфира без задержек UI

---

## 🔌 Аппаратная часть

### Микроконтроллер

| Параметр | Значение |
|----------|----------|
| **Модель** | Raspberry Pi Pico 2 |
| **Чип** | RP2350 (двухъядерный ARM Cortex-M33) |
| **Частота** | до 150 MHz |
| **Память** | 4 MB Flash, 520 KB SRAM |

### SPI0 — общая шина (3 устройства)

| Устройство | CS | DC/IRQ | RST | BLK | Частота SPI |
|------------|----|--------|-----|-----|-------------|
| **ILI9341** (дисплей) | GP17 | GP20 (DC) | GP21 | GP14 (BLK) | 40 MHz |
| **XPT2046** (тачскрин) | GP22 | GP15 (IRQ) | — | — | 2 MHz |
| **CC1101** (радио) | GP13 | GP12 (GDO0), GP11 (GDO2) | — | — | 5 MHz |

### I2C0 — DSP приёмник

| Устройство | SDA | SCL | Частота |
|------------|-----|-----|---------|
| **Si4732** | GP4 | GP5 | 400 kHz |

### Другие пины

| Функция | Пин | Описание |
|---------|-----|----------|
| **Джаммер (PWM)** | GP28 | Выход ШИМ-генератора помех |
| **LED** | GP25 | Встроенный индикатор состояния |

> ⚠️ **Внимание**: Пины CC1101 и Si4732 могут требовать уточнения для вашей платы. Проверьте схему подключения в файле [`include/config.h`](include/config.h).

---

## 🏗 Архитектура ПО

### Распределение задач по ядрам

```
┌─────────────────────────────────────────────────────────────┐
│                      RP2350 (Dual-Core)                     │
├─────────────────────────────────────────────────────────────┤
│  Core 0 (UI)                    │  Core 1 (Real-time)       │
│  ┌─────────────────────────┐    │  ┌─────────────────────┐  │
│  │ • Отрисовка GUI (50Hz)  │    │  │ • Обработка CC1101  │  │
│  │ • Опрос тачскрина       │◄───┼──┤ • Прерывания GDO0   │  │
│  │ • Обработка виджетов    │ IPC│  │ • Jammer PWM        │  │
│  │ • Чтение IPC-событий    │────┼──│ • Отправка в Core 0 │  │
│  └─────────────────────────┘    │  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Core 0 — UI и система

```c
int main() {
    stdio_init_all();
    ipc_init();              // Инициализация IPC
    spi_manager_init();      // Инициализация SPI-менеджера
    
    ui_context *pUI = InitUI();
    ILI9341_Init(...);       // Дисплей
    TouchInitCtl(...);       // Тачскрин
    jammer_pwm_init();       // ШИМ джаммера
    
    multicore_launch_core1(core1_entry);  // Запуск Core 1

    // Главный цикл UI (50 Hz)
    for(int tick = 0;;++tick) {
        tight_loop_contents();
        // Обработка тач-событий
        // Отрисовка фреймов
        // Чтение IPC от Core 1
    }
}
```

### Core 1 — Real-time задачи

```c
void core1_entry(void) {
    cc1101_init();           // Инициализация радиомодуля

    while(1) {
        // 1. Проверка команд от Core 0 (IPC)
        // 2. Опрос GDO0 CC1101 (приём пакета)
        // 3. Отправка данных в Core 0 (IPC)
        tight_loop_contents();
    }
}
```

### SPI-менеджер (Anti-Collision)

Для предотвращения коллизий на общей шине SPI используется мьютекс и принудительное отключение всех устройств:

```c
void spi_manager_acquire(uint target_cs_pin, uint baudrate) {
    mutex_enter_blocking(&spi_mutex);  // Блокировка
    set_all_cs_high();                 // Отключить все устройства
    spi_set_baudrate(SPI_PORT, baudrate); // Установить частоту
    gpio_put(target_cs_pin, 0);        // Активировать целевое устройство
}
```

### Межъядерное взаимодействие (IPC)

Используются очереди `queue_t` из `pico_util`:

```c
// Типы команд Core 0 → Core 1
typedef enum {
    CMD_JAMMER_START,
    CMD_JAMMER_STOP,
    CMD_JAMMER_SET_FREQ,
    CMD_RADIO_SCAN_START,
    CMD_RADIO_SCAN_STOP
} core0_to_core1_cmd_t;

// Типы событий Core 1 → Core 0
typedef enum {
    EVT_RADIO_PACKET_RX,
    EVT_JAMMER_STATUS
} core1_to_core0_evt_t;
```

---

## 📁 Структура проекта

```
jammer_pico2/
├── CMakeLists.txt              # Основной файл сборки CMake
├── pico_sdk_import.cmake       # Импорт Pico SDK
├── jammer.c                    # Заглушка (основной код в src/)
├── README.md                   # Этот файл
│
├── include/
│   ├── config.h                # Глобальные настройки пинов и частот
│   ├── cc1101_hal.h            # Драйвер радиомодуля CC1101
│   ├── spi_manager.h           # Менеджер SPI с защитой от коллизий
│   └── ipc_core.h              # Очереди IPC между ядрами
│
├── src/
│   ├── main.c                  # Основной код (Core 0 и Core 1)
│   ├── spi_manager.c           # Реализация SPI-менеджера и ШИМ
│   ├── cc1101_hal.c            # Драйвер CC1101
│   └── ipc_core.c              # Инициализация очередей IPC
│
├── lib/
│   ├── pico-touchscr-sdk/      # SDK для дисплея ILI9341 и тачскрина XPT2046
│   │   ├── ili9341/            # Драйвер дисплея с буфером 10800 байт
│   │   ├── touch/              # Драйвер тачскрина с калибровкой
│   │   └── lib/                # Вспомогательные функции
│   │
│   └── pico-widgets/           # GUI-фреймворк с виджетами
│       ├── frame/              # Базовая структура фреймов
│       ├── ui/                 # Управление UI контекстом
│       ├── widgets/            # Виджеты (TopBar, Settings, APRS...)
│       └── debug/              # TFT-логгер для отладки
│
├── legacy/                     # MicroPython-версия проекта (архив)
│   ├── config.py
│   ├── ili9341.py
│   ├── xpt2046.py
│   ├── jammer_signal.py
│   └── ui_manager.py
│
└── build/                      # Выходные файлы сборки
    ├── kelll31_jammer.uf2      # Для прошивки через bootloader
    ├── kelll31_jammer.bin      # Бинарный образ
    ├── kelll31_jammer.hex      # HEX-файл
    └── kelll31_jammer.elf      # Отладочный файл
```

---

## 🛠 Сборка и прошивка

### Требования

| Компонент | Версия | Примечание |
|-----------|--------|------------|
| **Pico SDK** | 2.2.0 | Настроена в `CMakeLists.txt` |
| **CMake** | ≥ 3.13 | Система сборки |
| **Toolchain** | RISCV_ZCB_RPI_2_2_0_3 | Компилятор GCC |
| **Picotool** | 2.2.0-a4 | Утилита для работы с UF2 |

### Пошаговая инструкция

#### 1. Установка Pico SDK

```bash
# Windows (PowerShell)
cd $HOME
git clone -b 2.2.0 https://github.com/raspberrypi/pico-sdk.git
cd pico-sdk
git submodule update --init
setx PICO_SDK_PATH "%USERPROFILE%\pico-sdk"

# Linux / macOS
cd ~
git clone -b 2.2.0 https://github.com/raspberrypi/pico-sdk.git
cd pico-sdk
git submodule update --init
export PICO_SDK_PATH=~/pico-sdk
echo "export PICO_SDK_PATH=~/pico-sdk" >> ~/.bashrc
```

#### 2. Установка toolchain

Скачайте и установите toolchain с официальной страницы:
- [RISCV ЗCB Toolchain](https://github.com/raspberrypi/pico-sdk-toolchain/releases)

#### 3. Сборка проекта

```bash
# Перейдите в директорию проекта
cd d:\kelll31scripts\jammer_pico2

# Создайте директорию сборки
mkdir build
cd build

# Конфигурация (укажите путь к Pico SDK, если не задан в среде)
cmake -DPICO_SDK_PATH="C:\Users\kupri\pico-sdk" ..

# Сборка
cmake --build .
```

#### 4. Прошивка устройства

1. Зажмите кнопку **BOOTSEL** на Raspberry Pi Pico 2
2. Подключите устройство к USB-порту
3. Отпустите кнопку — появится том `RPI-RP2350`
4. Скопируйте файл `kelll31_jammer.uf2` в этот том

Устройство автоматически перезагрузится и запустит прошивку.

---

## 📖 API и использование

### SPI-менеджер

```c
// Инициализация
spi_manager_init();

// Захват шины для работы с устройством
spi_manager_acquire(PIN_ILI9341_CS, SPI0_BAUDRATE_ILI9341);
spi_write_blocking(SPI_PORT, data, len);
spi_manager_release(PIN_ILI9341_CS);

// Или используйте вспомогательные функции
spi_manager_write_blocking(PIN_CC1101_CS, SPI0_BAUDRATE_CC1101, buffer, len);
```

### Jammer PWM

```c
// Инициализация
jammer_pwm_init();

// Установка частоты (Гц)
jammer_pwm_set_freq(433000000);  // 433 MHz

// Включение/выключение
jammer_pwm_enable(true);
jammer_pwm_enable(false);
```

### CC1101

```c
// Инициализация
cc1101_init();

// Запись в регистр
cc1101_write_reg(CC1101_CONFIG, value);

// Чтение из регистра
uint8_t status = cc1101_read_status_reg(CC1101_STATUS);

// Чтение/запись FIFO
cc1101_read_fifo(buffer, length);
cc1101_write_fifo(buffer, length);

// Отправка строб-команды
cc1101_strobe(CC1101_STROBE_TX);
```

### IPC (межъядерное взаимодействие)

```c
// Отправка команды из Core 0 в Core 1
core0_to_core1_msg_t msg;
msg.cmd = CMD_JAMMER_START;
msg.param1 = 433000000;  // Частота
queue_try_add(&q_core0_to_core1, &msg);

// Чтение события в Core 0 от Core 1
core1_to_core0_msg_t evt;
if (queue_try_remove(&q_core1_to_core0, &evt)) {
    if (evt.evt == EVT_RADIO_PACKET_RX) {
        // Обработка пакета
    }
}
```

### GUI (pico-widgets)

```c
// Инициализация UI
ui_context *pUI = InitUI();

// Получение активного фрейма
frame *pfActive = GetActiveFrame(pUI);

// Обработка событий виджета
pfActive->mpfEventProc(pfActive, kEventDraw, 0, 0, pUI);
pfActive->mpfEventProc(pfActive, kEventClickInside, x, y, pUI);
```

---

## 🐛 Отладка

### Вывод отладочной информации

Используйте `printf()` для вывода через USB CDC:

```c
printf("Debug message: value = %d\n", value);
```

### Подключение к консоли

| ОС | Устройство | Команда |
|----|------------|---------|
| **Windows** | COM-порт | Putty / Terminal |
| **Linux** | `/dev/ttyACM0` | `screen /dev/ttyACM0 115200` |
| **macOS** | `/dev/cu.usbmodem*` | `screen /dev/cu.usbmodem* 115200` |

> USB CDC не требует настройки baudrate — скорость определяется автоматически.

### Отладка через GDB

```bash
# Подключение Picoprobe
picoprobe -v

# Запуск GDB
riscv32-unknown-elf-gdb build/kelll31_jammer.elf
(gdb) target extended-remote :3333
(gdb) monitor reset init
(gdb) continue
```

---

## ⚠️ Важные замечания

1. **Не используйте `sleep_ms()` в Core 1** — это нарушит real-time обработку. Используйте `tight_loop_contents()`.

2. **Всегда вызывайте `spi_manager_acquire/release`** при работе с SPI в многопоточной среде.

3. **Инициализируйте IPC до запуска ядер** — иначе возможна гонка данных.

4. **Проверяйте пины на плате** — в `config.h` указаны значения, требующие уточнения (CC1101 CS/GDO, Si4732 I2C).

5. **Частота SPI для разных устройств**:
   - ILI9341: 40 MHz (максимальная скорость отрисовки)
   - XPT2046: 2 MHz (стабильное чтение тача)
   - CC1101: 5 MHz (стандартная частота для радиомодуля)

---

## 📚 Библиотеки

### pico-touchscr-sdk

- **Драйвер ILI9341** с энергоэффективным буфером (10800 байт)
- **Драйвер XPT2046** с калибровкой и фильтрацией нажатий
- **Селективная отрисовка** — обновляются только изменённые области

### pico-widgets

- **Легковесный GUI-фреймворк** на основе фреймов
- **Виджеты**: TopBar, Settings, APRS, PSK, Terminal, Phone, Callsign, Calibration
- **События**: `kEventDraw`, `kEventClickInside`, `kEventClickOutside`

---

## 🔗 Ссылки

- [Pico SDK Documentation](https://datasheets.raspberrypi.com/pico-sdk/)
- [pico-touchscr-sdk](https://github.com/RPiks/pico-touchscr-sdk)
- [pico-widgets](https://github.com/RPiks/pico-widgets)
- [CC1101 Datasheet](https://www.ti.com/lit/ds/symlink/cc1101.pdf)
- [ILI9341 Datasheet](https://cdn.sparkfun.com/datasheets/Display/ILI9341.pdf)
- [RP2350 Datasheet](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf)

---

## 📄 Лицензия

Проект распространяется под лицензией оригинального KELL31 Jammer.

---

**KELL31 Jammer Pico2** © 2026
