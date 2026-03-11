# Generated Cmake Pico project file - Merged for KELL31 Jammer

cmake_minimum_required(VERSION 3.13)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# == DO NOT EDIT THE FOLLOWING LINES for the Raspberry Pi Pico VS Code Extension to work ==
if(WIN32)
    set(USERHOME $ENV{USERPROFILE})
else()
    set(USERHOME $ENV{HOME})
endif()
set(sdkVersion 2.2.0)
set(toolchainVersion RISCV_ZCB_RPI_2_2_0_3)
set(picotoolVersion 2.2.0-a4)
set(picoVscode ${USERHOME}/.pico-sdk/cmake/pico-vscode.cmake)
if (EXISTS ${picoVscode})
    include(${picoVscode})
endif()
# ====================================================================================

# Устанавливаем целевую плату Pico 2 (RP2350)
set(PICO_BOARD pico2 CACHE STRING "Board type")

# Подключаем Pico SDK (файл pico_sdk_import.cmake должен лежать рядом в корне проекта)
include(pico_sdk_import.cmake OPTIONAL)

project(kelll31_jammer C CXX ASM)

if (COMMAND pico_sdk_init)
    pico_sdk_init()
else()
    message(WARNING "Pico SDK not found. Make sure PICO_SDK_PATH is set.")
endif()

# Исполняемый файл и исходники
# Мы просто скомпилируем их исходники напрямую в нашем target для удобства.
add_executable(kelll31_jammer
    src/main.c
    src/spi_manager.c
    src/cc1101_hal.c
    src/ipc_core.c
    src/home_screen.c
    src/stub_screen.c
    # Исходники pico-touchscr-sdk
    lib/pico-touchscr-sdk/lib/my_assert.c
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
    lib/pico-widgets/debug/tftlogger.c
    # src/core1_task.c # (раскомментировать при добавлении таски для второго ядра)
)

# Устанавливаем имя и версию программы
pico_set_program_name(kelll31_jammer "kelll31_jammer")
pico_set_program_version(kelll31_jammer "1.0")

# Подключаем директории с заголовочными файлами
target_include_directories(kelll31_jammer PRIVATE
    ${CMAKE_CURRENT_LIST_DIR}/include
    ${CMAKE_CURRENT_LIST_DIR}/lib/pico-touchscr-sdk
    ${CMAKE_CURRENT_LIST_DIR}/lib/pico-touchscr-sdk/ili9341
    ${CMAKE_CURRENT_LIST_DIR}/lib/pico-touchscr-sdk/touch
    ${CMAKE_CURRENT_LIST_DIR}/lib/pico-widgets/frame
    ${CMAKE_CURRENT_LIST_DIR}/lib/pico-widgets/ui
    ${CMAKE_CURRENT_LIST_DIR}/lib/pico-widgets/widgets
    ${CMAKE_CURRENT_LIST_DIR}/lib/pico-widgets/debug
    ${CMAKE_CURRENT_LIST_DIR}/lib/pico-touchscr-sdk/lib
    ${CMAKE_CURRENT_LIST_DIR}
)

# Подключаем необходимые библиотеки из Pico SDK и наши модули
target_link_libraries(kelll31_jammer PRIVATE
    pico_stdlib
    hardware_spi
    hardware_pwm
    hardware_i2c
    hardware_timer
    hardware_sync       # Необходим для mutex_t и spinlocks (Anti-Collision SPI)
    pico_multicore      # Необходим для работы со вторым ядром (Core 1)
    pico_util           # Необходим для очередей (queue_t) для IPC
)

# Включаем вывод стандартного потока (printf) через USB (виртуальный COM-порт) и отключаем UART
pico_enable_stdio_usb(kelll31_jammer 1)
pico_enable_stdio_uart(kelll31_jammer 0)

# Генерируем uf2, bin, hex файлы для прошивки

target_sources(kelll31_jammer PRIVATE  src/screen_manager.c src/screen_draw.c)
