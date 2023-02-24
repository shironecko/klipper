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
        self.ports_status = 0

    def set_port_enabled(self, port, enabled):
        if enabled and self.ports_status != 0:
            logging.error(f'tca9548a error: enabling more than one port {self.ports_status:0b}')
        port = min(port, 7)
        params = self.i2c.i2c_read([TCA9548A_CHIP_ADDR], 1)
        settings = params['response'][0]
        if enabled:
            settings |= (1 << port)
        else:
            settings &= ~(1 << port)
        
        self.ports_status = settings
        self.i2c.i2c_write([TCA9548A_CHIP_ADDR, settings])

def load_config_prefix(config):
    return TCA9548A(config)