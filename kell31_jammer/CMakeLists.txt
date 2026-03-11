cmake_minimum_required(VERSION 3.13)

# Подключаем Pico SDK (файл pico_sdk_import.cmake должен лежать рядом в корне проекта)
include(pico_sdk_import.cmake OPTIONAL)

project(kell31_jammer C CXX ASM)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

if (COMMAND pico_sdk_init)
    pico_sdk_init()
else()
    message(WARNING "Pico SDK not found. Make sure PICO_SDK_PATH is set.")
endif()

# Мы не добавляем add_subdirectory, потому что у этих библиотек свои CMakeLists
# компилируют исполняемые файлы (test.c) вместо того, чтобы создавать static library.
# Мы просто скомпилируем их исходники напрямую в нашем target.

add_executable(kell31_jammer
    src/main.c
    src/spi_manager.c
    src/cc1101_hal.c
    src/ipc_core.c
    # Исходники pico-touchscr-sdk
    lib/pico-touchscr-sdk/lib/assert.c
    lib/pico-touchscr-sdk/ili9341/ili9341.c
    lib/pico-touchscr-sdk/touch/msp2807_touch.c
    lib/pico-touchscr-sdk/touch/msp2807_calibration.c
    # Исходники pico-widgets
    lib/pico-widgets/ui/ui_init.c
    lib/pico-widgets/ui/ui_manage.c
    lib/pico-widgets/widgets/widgets_utility.c
    lib/pico-widgets/widgets/TopBarEventProc.c
    lib/pico-widgets/widgets/SettingsEventProc.c
    lib/pico-widgets/widgets/APRSEventProc.c
    lib/pico-widgets/widgets/PSKEventProc.c
    lib/pico-widgets/widgets/PhoneEventProc.c
    lib/pico-widgets/widgets/CallsignEventProc.c
    lib/pico-widgets/widgets/CalibrationEventProc.c
    lib/pico-widgets/widgets/TerminalEventProc.c
    # src/core1_task.c
)

target_include_directories(kell31_jammer PRIVATE
    ${CMAKE_CURRENT_LIST_DIR}/include
    ${CMAKE_CURRENT_LIST_DIR}/lib/pico-touchscr-sdk
    ${CMAKE_CURRENT_LIST_DIR}/lib/pico-touchscr-sdk/ili9341
    ${CMAKE_CURRENT_LIST_DIR}/lib/pico-touchscr-sdk/touch
    ${CMAKE_CURRENT_LIST_DIR}/lib/pico-widgets/frame
    ${CMAKE_CURRENT_LIST_DIR}/lib/pico-widgets/ui
    ${CMAKE_CURRENT_LIST_DIR}/lib/pico-widgets/widgets
    ${CMAKE_CURRENT_LIST_DIR}/lib/pico-touchscr-sdk/lib
)

# Подключаем необходимые библиотеки из Pico SDK и наши локальные
target_link_libraries(kell31_jammer PRIVATE
    pico_stdlib
    hardware_spi
    hardware_pwm
    hardware_i2c
    hardware_timer
    hardware_sync       # Необходим для mutex_t и spinlocks (Anti-Collision SPI)
    pico_multicore      # Необходим для работы со вторым ядром (Core 1)
    pico_util           # Необходим для очередей (queue_t) для IPC
    # Либы из pico-widgets
)

# Включаем вывод стандартного потока (printf) через USB (виртуальный COM-порт)
pico_enable_stdio_usb(kell31_jammer 1)
pico_enable_stdio_uart(kell31_jammer 0)

# Генерируем uf2, bin, hex файлы для прошивки
pico_add_extra_outputs(kell31_jammer)
