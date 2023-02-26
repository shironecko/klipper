# Support for the TCA9533A I2C multiplexer
#
# Copyright (C) 2023  Vii <vii@gamecraft.tech>
#
# This file may be distributed under the terms of the GNU GPLv3 license.
import logging
from . import bus
import mcu

TCA9548A_CHIP_ADDR = 0x70

class TCA9548A:
    def __init__(self, config):
        self._printer = config.get_printer()
        self._name = config.get_name().split()[-1]
        i2c_mcu = mcu.get_printer_mcu(self._printer, config.get('i2c_mcu', 'mcu'))
        self._cmd_queue = i2c_mcu.alloc_command_queue()
        self._i2c = bus.MCU_I2C_from_config(
            config,
            default_addr=TCA9548A_CHIP_ADDR,
            cmd_queue=self._cmd_queue)
        self._channels = [None] * 8

        self._printer.add_object("tca9548a " + self._name, self)

    def claim_channel(self, config, i2c_address):
        channel = config.getint('i2c_mux_channel', minval=0, maxval=7)
        if self._channels[channel] is not None:
            raise config.error(
                f"Channel {channel} of {self._name} is already taken")
        
        i2c = bus.MCU_I2C(
            self._i2c.get_mcu(),
            self._i2c.get_bus(),
            i2c_address,
            self._i2c.get_i2c_speed(),
            self._cmd_queue)
        self._channels[channel] = i2c.get_oid()

        return TCA9548A_Channel(self, i2c)
    
    def _open_channel(self, oid):
        if oid not in self._channels:
            raise self._printer.command_error(
                f"No channel with OID {oid} in {self._name} I2C multiplexer")
        
        channel = self._channels.index(oid)
        channel_mask = 1 << channel
        self._i2c.i2c_write([TCA9548A_CHIP_ADDR, channel_mask])

class TCA9548A_Channel:
    def __init__(self, tca9548a, mcu_i2c):
        self._tca9548a = tca9548a
        self._mcu_i2c = mcu_i2c

        # Wrappers
        self.get_oid = self._mcu_i2c.get_oid
        self.get_mcu = self._mcu_i2c.get_mcu
        self.get_bus = self._mcu_i2c.get_bus
        self.get_i2c_address = self._mcu_i2c.get_i2c_address
        self.get_i2c_speed = self._mcu_i2c.get_i2c_speed
        self.get_command_queue = self._mcu_i2c.get_command_queue

    def i2c_write(self, data, minclock=0, reqclock=0):
        self._open()
        self._mcu_i2c.i2c_write(data, minclock, reqclock)
    def i2c_read(self, write, read_len):
        self._open()
        return self._mcu_i2c.i2c_read(write, read_len)
    def i2c_modify_bits(self, reg, clear_bits, set_bits,
                        minclock=0, reqclock=0):
        self._open()
        self._mcu_i2c.i2c_modify_bits(reg, clear_bits, set_bits,
                    minclock, reqclock)

    def _open(self):
        self._tca9548a._open_channel(self.get_oid())

def load_config_prefix(config):
    return TCA9548A(config)