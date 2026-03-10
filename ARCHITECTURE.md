# Jammer Pico2 Architecture Documentation

This project aims to convert the KELL31 Jammer from C to MicroPython, upgrading it into a high-end hardware multi-tool utilizing the Raspberry Pi Pico 2's specific features.

## Multicore Architecture

The architecture aims to solve standard issues where polling external modules freezes the display and user interface.

The RP2350 (Raspberry Pi Pico 2) utilizes its multi-core capabilities:
- **Core 0 (UI & System Management):** Solely dedicated to the GUI, polling touch inputs (XPT2046) and orchestrating rendering commands to the ILI9341 over SPI.
- **Core 1 (Real-time RF Tools):** Dedicated to the CC1101 and Si4732 modules. This core performs polling on module states, reacts to interrupts, captures high-speed RAW signal samples, and streams them efficiently to IPC buffers without dragging down the UI.

An `_thread.allocate_lock()` (IPC lock) mechanism coordinates read-write access to shared buffers to prevent synchronization issues between Core 0 and Core 1.

## SPI Device Management & Anti-Collision Guide

Since multiple high-speed devices are competing for the SPI bus (Display ILI9341, Touch Controller XPT2046, Sub-GHz Radio CC1101), correct CS (Chip Select) management is required to avoid collisions.

### Physical CS Guidelines:
- **ILI9341:** Requires its own dedicated CS pin.
- **XPT2046:** Requires its own dedicated CS pin.
- **CC1101:** Requires its own dedicated CS pin.
*(Si4732 communicates over I2C, avoiding this collision altogether).*

### Handling SPI Transfers Safely:

1. Before starting communication with a given device, **ensure all other devices' CS pins are set HIGH** (deactivated).
2. Set the active device's CS pin LOW (activated).
3. If necessary, change the SPI baud rate. The ILI9341 can often run at 40+ MHz, while the CC1101 or XPT2046 may require lower SPI speeds. Therefore, re-initializing the baudrate before communicating might be required.
4. Complete the transfer.
5. Bring the active device's CS pin back to HIGH immediately.

### Best Practice Implementation

For safe SPI operations, Python context managers should be used to wrap transactions.

```python
class SPIDeviceBlocker:
    def __init__(self, cs_pin, spi_bus, required_baudrate=None):
        self.cs_pin = cs_pin
        self.spi = spi_bus
        self.baudrate = required_baudrate
        self.old_baudrate = None

    def __enter__(self):
        # Change baudrate if necessary
        if self.baudrate:
            # Reconfigure baudrate
            pass
        self.cs_pin.value(0) # Drive CS LOW (Active)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cs_pin.value(1) # Drive CS HIGH (Inactive)
        # Restore baudrate if necessary
```

This prevents any concurrent reads/writes if one thread gets interrupted. In a multi-core environment, SPI locks should also be strictly maintained between Core 0 and Core 1 to prevent Core 0 from interrupting an ongoing Core 1 SPI block!
