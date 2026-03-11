# KELL31 Jammer — Проект прошивки для Raspberry Pi Pico/Pico 2

## Обзор проекта

**KELL31 Jammer** — это проект прошивки для микроконтроллера **Raspberry Pi Pico/Pico 2**, предназначенный для управления устройством генерации сигналов с графическим интерфейсом на базе TFT-дисплея ILI9341 (240x320) с тачскрином XPT2046.

Проект состоит из **двух независимых реализаций**:
1. **C-версия** — нативная прошивка на C/C++ с использованием Raspberry Pi Pico SDK
2. **MicroPython-версия** — порт на MicroPython для быстрой разработки и отладки

### Основные возможности

- ✅ **Генерация сигналов** в диапазонах WiFi, Bluetooth, Cellular
- ✅ **4 режима работы**: Continuous, Sweep, Burst, Noise
- ✅ **Графический интерфейс** с тачскрином и аппаратными кнопками
- ✅ **Сохранение настроек** во flash-память (C) или JSON файл (MicroPython)
- ✅ **Антидребезг кнопок** программный
- ✅ **LED индикация** состояния
- ✅ **UART/USB отладка**

---

## Структура проекта

```
kelll31_jammer/
├── C/                          # C-версия прошивки (Pico SDK)
│   ├── kelll31_jammer.cpp      # Главный файл, основной цикл
│   ├── ili9341.c/h             # Драйвер дисплея ILI9341 (SPI)
│   ├── xpt2046.c/h             # Драйвер тачскрина XPT2046
│   ├── jammer_signal.c/h       # Генерация сигналов (PWM)
│   ├── ui_manager.c/h          # Пользовательский интерфейс
│   ├── button.c/h              # Обработка кнопок (debounce)
│   ├── font.c/h                # Шрифт 8x12
│   ├── settings.c/h            # Сохранение настроек (Flash)
│   ├── CMakeLists.txt          # Конфигурация сборки
│   └── pico_sdk_import.cmake   # Импорт Pico SDK
│
├── micropython/                # MicroPython-версия
│   ├── main.py                 # Главный файл приложения
│   ├── config.py               # Конфигурация оборудования
│   ├── ili9341.py              # Драйвер дисплея
│   ├── xpt2046.py              # Драйвер тачскрина
│   ├── jammer_signal.py        # Генерация сигналов
│   ├── ui_manager.py           # UI менеджер
│   ├── button.py               # Обработка кнопок
│   ├── settings.py             # Сохранение настроек (JSON)
│   └── README.md               # Документация MicroPython-версии
│
├── test_big_tft_touch.py       # Тест тачскрина (standalone)
├── .vscode/                    # Настройки VS Code
└── QWEN.md                     # Этот файл
```

---

## Модули и компоненты

### C-версия (Pico SDK)

| Модуль | Описание | Основные функции |
|--------|----------|------------------|
| `jammer_signal` | Генерация сигналов через PWM | `jammer_signal_init()`, `jammer_signal_enable()`, `jammer_signal_set_frequency()` |
| `ili9341` | Драйвер дисплея: SPI-коммуникация, графические примитивы, текст | `ili9341_init()`, `ili9341_draw_string()`, `ili9341_fill_rect()` |
| `xpt2046` | Драйвер тачскрина: чтение координат, калибровка | `xpt2046_init()`, `xpt2046_read_touch()`, `xpt2046_convert_coordinates()` |
| `ui_manager` | Отрисовка экранов, обработка навигации | `ui_init()`, `ui_process()`, `ui_set_page()` |
| `button` | Обработка кнопок с debounce и long press | `button_init()`, `button_process()`, `button_set_callback()` |
| `settings` | Сохранение/загрузка настроек из flash | `settings_init()`, `settings_save()`, `settings_load()` |
| `font` | Шрифт 8x12 для отображения текста | `font_get_char_data()` |

### MicroPython-версия

| Модуль | Описание |
|--------|----------|
| `main.py` | Основной класс `KELL31Jammer`, цикл обработки |
| `config.py` | Конфигурация пинов, частот, параметров |
| `ili9341.py` | Драйвер дисплея с двойной буферизацией |
| `xpt2046.py` | Драйвер тачскрина с калибровкой |
| `jammer_signal.py` | Класс генерации сигналов (4 режима) |
| `ui_manager.py` | UI менеджер с тач-интерфейсом |
| `settings.py` | Сохранение настроек в JSON |

---

## Режимы работы джаммера

### Режимы частоты

| Режим | Частотный диапазон | Описание |
|-------|-------------------|----------|
| `JAMMER_FREQ_WIFI_24GHZ` | 2400–2483,5 МГц | WiFi 2,4 ГГц |
| `JAMMER_FREQ_WIFI_5GHZ` | 5150–5825 МГц | WiFi 5 ГГц |
| `JAMMER_FREQ_BLUETOOTH` | 2402–2480 МГц | Bluetooth |
| `JAMMER_FREQ_CELLULAR` | 700–2600 МГц | Сотовая связь (GSM/3G/LTE) |
| `JAMMER_FREQ_CUSTOM` | Пользовательская | Любая частота |

### Режимы генерации

| Режим | Описание |
|-------|----------|
| `JAMMER_MODE_CONTINUOUS` | Непрерывное излучение на одной частоте |
| `JAMMER_MODE_SWEEP` | Сканирование по диапазону (шаг 1 МГц) |
| `JAMMER_MODE_BURST` | Импульсный режим (100 мс вкл / 50 мс выкл) |
| `JAMMER_MODE_NOISE` | Псевдослучайная частота (LFSR генератор) |

---

## Аппаратная конфигурация

### Дисплей ILI9341 (SPI)

| Функция | Пин Pico | GPIO |
|---------|----------|------|
| DC (Data/Command) | Pin 26 | GP20 |
| CS (Chip Select) | Pin 22 | GP17 |
| SCK (SPI Clock) | Pin 24 | GP18 |
| MOSI (SPI Data) | Pin 25 | GP19 |
| MISO | Pin 21 | GP16 |
| BLK (Backlight) | Pin 19 | GP14 |
| RST (Reset) | Pin 27 | GP21 |

### Тачскрин XPT2046

| Функция | Пин Pico | GPIO |
|---------|----------|------|
| CS | Pin 29 | GP22 |
| IRQ | Pin 20 | GP15 |

### Управление

| Функция | Пин Pico | GPIO | Активный уровень |
|---------|----------|------|------------------|
| JAMMER_SIGNAL | Pin 34 | GP28 | — |
| LED_STATUS | Pin 25 | GP25 | Высокий |
| BUTTON_UP | Pin 32 | GP27 | Низкий |
| BUTTON_DOWN | Pin 31 | GP26 | Низкий |
| BUTTON_ENTER | Pin 30 | GP24 | Низкий |

---

## Сборка и запуск

### C-версия (Pico SDK)

#### Требования

| Компонент | Версия |
|-----------|--------|
| Raspberry Pi Pico SDK | 2.2.0 |
| GCC ARM Embedded | 14.2 |
| CMake | 3.13+ |
| Генератор | Ninja |
| Плата | Raspberry Pi Pico / Pico 2 |

#### Переменные окружения (Windows PowerShell)

```powershell
$env:PICO_SDK_PATH = "$env:USERPROFILE/.pico-sdk/sdk/2.2.0"
$env:PICO_TOOLCHAIN_PATH = "$env:USERPROFILE/.pico-sdk/toolchain/14_2_Rel1"
```

#### Команды сборки

```bash
cd C
mkdir build && cd build
cmake -G Ninja ..
cmake --build .
```

#### Развёртывание

1. Подключите Pico в режиме **BOOTSEL** (удерживая кнопку BOOTSEL при подключении USB)
2. Скопируйте файл `kelll31_jammer.uf2` из `build/` на устройство
3. Устройство автоматически перезагрузится и запустит прошивку

### MicroPython-версия

#### Установка

```bash
# Копирование файлов на устройство
ampy --port COMx put micropython/
```

#### Запуск

```python
# На устройстве MicroPython
import main
main.main()
```

#### Тестирование

```python
import test_project
test_project.run_all_tests()
```

---

## Использование

### Главный экран

```
┌────────────────────────┐
│    KELL31 JAMMER       │
├────────────────────────┤
│     ┌──────────┐       │
│     │  ACTIVE  │       │  ← Статус (красный/зелёный)
│     └──────────┘       │
│   FREQ: WiFi 2.4GHz    │
│   MODE: Continuous     │
│   POWER: 50%           │
│                        │
│  [START]    [MODE]     │
│  [-] [+]    [SETUP]    │
├────────────────────────┤
│ STATUS: ACTIVE  WiFi   │  ← Статус бар
└────────────────────────┘
```

### Управление

| Элемент | Действие |
|---------|----------|
| **START/STOP** | Вкл/Выкл джаммер |
| **MODE** | Переключение режима |
| **+** | Увеличить мощность +5% |
| **-** | Уменьшить мощность -5% |
| **SETUP** | Меню настроек |

### Аппаратные кнопки

| Кнопка | Короткое нажатие | Долгое нажатие (>1 сек) |
|--------|------------------|-------------------------|
| **UP** | Увеличить мощность +5% | Следующая частота |
| **DOWN** | Уменьшить мощность -5% | Следующий режим |
| **ENTER** | Вкл/Выкл джаммер | Меню настроек |

---

## Структура состояний

### Состояния джаммера

```c
typedef enum {
    JAMMER_STATE_OFF = 0,      // Выключено
    JAMMER_STATE_ON,           // Активно
    JAMMER_STATE_STANDBY,      // Ожидание
    JAMMER_STATE_ERROR         // Ошибка
} jammer_state_t;
```

### Ошибки

```c
typedef enum {
    JAMMER_ERROR_NONE = 0,
    JAMMER_ERROR_INVALID_FREQ,   // Неверная частота
    JAMMER_ERROR_INVALID_POWER,  // Неверная мощность
    JAMMER_ERROR_INVALID_MODE,   // Неверный режим
    JAMMER_ERROR_HARDWARE        // Ошибка оборудования
} jammer_error_t;
```

---

## Отладка

### Вывод через UART

- **TX:** GP0 (Pin 1)
- **RX:** GP1 (Pin 2)
- **Скорость:** 115200 бод

### Вывод через USB (CDC)

```c
printf("State: %s | Freq: %s | Power: %d%%\r\n", ...);
```

### Формат логов

```
KELL31 Jammer v1.0.0 started
Jammer initialized successfully
Settings loaded from flash
State: OFF | Freq: WiFi 2.4GHz | Mode: Continuous | Power: 50%
```

---

## Конвенции разработки

### Стиль кода

| Элемент | Стиль | Пример |
|---------|-------|--------|
| Функции | `snake_case` | `jammer_signal_init` |
| Типы | `snake_case_t` | `jammer_state_t` |
| Макросы | `UPPER_CASE` | `ST7789_BLACK` |
| Глобальные переменные | `g_` префикс | `g_settings` |

### Стандарты

- **C:** C11
- **C++:** C++17
- **Python:** Python 3.x (MicroPython)
- **Комментарии:** на русском языке

### Организация кода

- Заголовочные файлы используют include guards
- `extern "C"` для совместимости C/C++
- Конфигурационные структуры передаются по указателю

---

## Версионирование

Формат: `MAJOR.MINOR.PATCH`

- **MAJOR:** Несовместимые изменения API
- **MINOR:** Новые функции (обратная совместимость)
- **PATCH:** Исправления ошибок

Текущая версия: **1.0.0**

---

## Зависимости Pico SDK (C-версия)

```cmake
target_link_libraries(kelll31_jammer
    pico_stdlib
    pico_multicore
    hardware_spi
    hardware_gpio
    hardware_pwm
    hardware_clocks
    hardware_irq
    hardware_timer
    hardware_flash
)
```

---

## Расширения VS Code

Рекомендуемые расширения (`.vscode/extensions.json`):

- `ms-python.python` — поддержка Python
- `ms-python.vscode-pylance` — языковой сервер Python
- `visualstudioexptteam.vscodeintellicode` — IntelliCode
- `paulober.pico-w-go` — разработка для Pico

---

## Примечания

⚠️ **Внимание:** Использование данного устройства может быть незаконным в вашей стране. Убедитесь, что вы имеете право на использование генераторов сигналов в вашем регионе. Данное устройство предназначено только для образовательных целей и тестирования собственного оборудования.

---

## Ссылки

- [Документация C-версии](C/QWEN.md)
- [Документация MicroPython-версии](micropython/README.md)
