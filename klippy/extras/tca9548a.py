# Support for the TCA9533A I2C multiplexer
#
# Copyright (C) 2023  Vii <vii@gamecraft.tech>
#
# This file may be distributed under the terms of the GNU GPLv3 license.
import logging
from . import bus

TCA9548A_CHIP_ADDR = 0x70

class TCA9548A:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.name = config.get_name().split()[-1]
        self.i2c = bus.MCU_I2C_from_config(config, default_addr=TCA9548A_CHIP_ADDR)

        self.printer.add_object("tca9548a " + self.name, self)

    def set_port_enabled(self, port, enabled):
        port = min(port, 7)
        params = self.i2c.i2c_read([TCA9548A_CHIP_ADDR], 1)
        settings = params['response']
        if enabled:
            settings |= (1 << port)
        else:
            settings &= ~(1 << port)
        
        self.i2c.i2c_write([TCA9548A_CHIP_ADDR, settings])