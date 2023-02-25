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
        self._i2c = bus.MCU_I2C_from_config(config, default_addr=TCA9548A_CHIP_ADDR, cmd_queue=self._cmd_queue)
        self._channels = [None] * 8
        self._active_channel = None

        self._printer.add_object("tca9548a " + self._name, self)

    def add_channel(self, config, i2c_address):
        channel = config.getint('i2c_mux_channel', minval=0, maxval=7)
        if self._channels[channel] is not None:
            raise self._printer.config_error(f"Channel {channel} of {self._name} is already taken")
        
        i2c = bus.MCU_I2C(self._i2c.get_mcu(), self._i2c.get_bus(), i2c_address, self._i2c.get_i2c_speed(), self._cmd_queue)
        self._channels[channel] = i2c.get_oid()
        return TCA9548A_Channel(self, i2c)
    
    def _open_channel(self, oid):
        if self._active_channel is not None:
            raise self._printer.command_error(f"Trying to open {self._name} channel before closing last one opened")
        
        channel = self._channels.index(oid)
        channel_mask = 1 << channel
        self._i2c.i2c_write([TCA9548A_CHIP_ADDR, channel_mask])
        self._active_channel = oid

    def _close_channel(self, oid):
        if self._active_channel != oid:
            raise self._printer.command_error(f"Trying to close a channel OID{oid} when channel OID{self._active_channel} is open")

        self._i2c.i2c_write([TCA9548A_CHIP_ADDR, 0x0])
        self._active_channel = None

def load_config_prefix(config):
    return TCA9548A(config)

class TCA9548A_Channel:
    def __init__(self, tca9548a, mcu_i2c):
        self._tca9548a = tca9548a
        self._mcu_i2c = mcu_i2c

    def i2c_write(self, data, minclock=0, reqclock=0):
        self._open()
        self._mcu_i2c.i2c_write(data, minclock, reqclock)
        self._close()
    def i2c_read(self, write, read_len):
        self._open()
        self._mcu_i2c.i2c_read(write, read_len)
        self._close()
    def i2c_modify_bits(self, reg, clear_bits, set_bits,
                        minclock=0, reqclock=0):
        self._open()
        self._mcu_i2c.i2c_modify_bits(reg, clear_bits, set_bits,
                        minclock, reqclock)
        self._close()

    def _open(self):
        self._tca9548a._open_channel(self.get_oid())
    def _close(self):
        self._tca9548a._close_channel(self.get_oid())

    def get_oid(self):
        return self._mcu_i2c.get_oid()
    def get_mcu(self):
        return self._mcu_i2c.get_mcu()
    def get_bus(self):
        return self._mcu_i2c.get_bus()
    def get_i2c_address(self):
        return self._mcu_i2c.get_i2c_address()
    def get_i2c_speed(self):
        return self._mcu_i2c.get_i2c_speed()
    def get_command_queue(self):
        return self._mcu_i2c.get_command_queue()