# Support for the EMC2101 I2C PWM fan controller
#
# Copyright (C) 2023  Vii <vii@gamecraft.tech>
#
# This file may be distributed under the terms of the GNU GPLv3 license.
import logging
from . import bus

EMC2101_CHIP_ADDR = 0x4C

EMC2101_CHIP_ID = 0x16
EMC2101_R_CHIP_ID = 0x28

EMC2101_REGS = {
    'WHOAMI': 0xFD,
    'CONFIG': 0x03,
    'DATA_RATE': 0x04,
    'TACH_LSB': 0x46,
    'TACH_MSB': 0x47,
    'FAN_CONFIG': 0x4A,
    'FAN_SPINUP': 0x4B,
    'FAN_SETTING': 0x4C,
    'PWM_FREQ': 0x4D,
    'PWM_DIV': 0x4E
}

# Conversion unit to convert chip readings to fan RPM
EMC2101_FAN_RPM_NUMERATOR = 5400000

class EMC2101:
    def __init__(self, config):
        self._printer = config.get_printer()
        self._name = config.get_name().split()[-1]
        self._i2c = bus.MCU_I2C_from_config(config, EMC2101_CHIP_ADDR)
        self._mcu = self._i2c.get_mcu()

        self._last_clock = 0

        self._printer.add_object('emc2101 ' + self._name, self)
        self._printer.register_event_handler("klippy:connect",
                                            self.handle_connect)
    
    def handle_connect(self):
        chipid = self._read_register('WHOAMI', 1)[0]
        if chipid != EMC2101_CHIP_ID and chipid != EMC2101_R_CHIP_ID:
            logging.error(f'emc2101 {self._name}: Unexpected chip ID {chipid:0x}')
        else:
            logging.info(f'emc2101 {self._name}: Chip ID {chipid:0x}')

        settings = self._read_register('CONFIG', 1)[0]
        settings |= 1 << 2 # enable tach input
        settings &= ~(1 << 4) # fan in PWM mode
        self._write_register('CONFIG', settings)
        
        settings = self._read_register('FAN_CONFIG', 1)[0]
        settings |= 1 # set tach to read 0xFFFF below min RPM
        settings &= ~(1 << 2) # no PWM clock freq override
        settings |= 1 << 3 # base PWM clock to 1.4kHz
        settings &= ~(1 << 4) # disable invert fan speed
        settings |= 1 << 5 # manual fan control
        self._write_register('FAN_CONFIG', settings)

        # no HW spinup, let Klipper handle it
        self._write_register('FAN_SPINUP', 0x0)

        # max PWM resolution
        self._write_register('PWM_FREQ', 0x1F)

        # lowest temperature meauserment rate
        self._write_register('DATA_RATE', 0x0)
    
    def set_fan_speed(self, print_time, value):
        clock = self._mcu.print_time_to_clock(print_time)
        minclock = self._last_clock
        self._last_clock = clock

        mapped_value = int(63 * value)
        self._write_register(
            'FAN_SETTING',
            mapped_value,
            minclock=minclock,
            reqclock=clock)
    
    def get_fan_rpm(self):
        lsb = self._read_register('TACH_LSB', 1)[0]
        msb = self._read_register('TACH_MSB', 1)[0]
        raw = (msb << 8) | lsb
        if raw == 0xFFFF or raw == 0:
            return 0
        
        return EMC2101_FAN_RPM_NUMERATOR / raw

    def get_mcu(self):
        return self._i2c.get_mcu()

    def _read_register(self, reg_name, read_len):
        regs = [EMC2101_REGS[reg_name]]
        params = self._i2c.i2c_read(regs, read_len)
        return bytearray(params['response'])
    
    def _write_register(self, reg_name, data, minclock=0, reqclock=0):
        if type(data) is not list:
            data = [data]
        reg = EMC2101_REGS[reg_name]
        data.insert(0, reg)
        self._i2c.i2c_write(data, minclock=minclock, reqclock=reqclock)

def load_config_prefix(config):
    return EMC2101(config)