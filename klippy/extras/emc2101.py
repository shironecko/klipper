# Support for the EMC2101 I2C PWM fan controller
#
# Copyright (C) 2023  Vii <vii@gamecraft.tech>
#
# This file may be distributed under the terms of the GNU GPLv3 license.
import logging
from . import bus

EMC2101_CHIP_ADDR = 0x4C

EMC2101_CHIP_ID = 0x16     # EMC2101 default device id from part id
EMC2101_ALT_CHIP_ID = 0x28 # EMC2101 alternate device id from part id

EMC2101_REGS = {
    'WHOAMI': 0xFD,
    'INTERNAL_TEMP': 0x00,
    'STATUS': 0x02,
    'REG_CONFIG': 0x03,
    'FAN_CONFIG': 0x4A
}

EMC2101_EXTERNAL_TEMP_MSB = 0x01 # high byte for the external temperature reading
EMC2101_EXTERNAL_TEMP_LSB = 0x10 # low byte for the external temperature reading

EMC2101_REG_DATA_RATE = 0x04 # Data rate config
EMC2101_TEMP_FORCE = 0x0C    # Temp force setting for LUT testing
EMC2101_TACH_LSB = 0x46      # Tach RPM data low byte
EMC2101_TACH_MSB = 0x47      # Tach RPM data high byte
EMC2101_TACH_LIMIT_LSB = 0x48 # Tach low-speed setting low byte. INVERSE OF THE SPEED
EMC2101_TACH_LIMIT_MSB = 0x49 # Tach low-speed setting high byte. INVERSE OF THE SPEED

EMC2101_FAN_SPINUP = 0x4B # Fan spinup behavior settings
EMC2101_REG_FAN_SETTING = 0x4C # Fan speed for non-LUT settings, as a % PWM duty cycle
EMC2101_PWM_FREQ = 0x4D # PWM frequency setting
EMC2101_PWM_DIV = 0x4E  # PWM frequency divisor
EMC2101_LUT_HYSTERESIS = 0x4F # The hysteresis value for LUT lookups when temp is decreasing

EMC2101_LUT_START = 0x50 # The first temp threshold register

EMC2101_TEMP_FILTER = 0xBF # The external temperature sensor filtering behavior
EMC2101_REG_PARTID = 0xFD # 0x16
EMC2101_REG_MFGID = 0xFE  # 0xFF16

MAX_LUT_SPEED = 0x3F # 6-bit value
MAX_LUT_TEMP = 0x7F  #  7-bit

EMC2101_I2C_ADDR = 0x4C # The default I2C address
EMC2101_FAN_RPM_NUMERATOR = 5400000 # Conversion unit to convert LSBs to fan RPM
_TEMP_LSB = 0.125 # single bit value for internal temperature readings


class EMC2101:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.name = config.get_name().split()[-1]
        self.i2c = bus.MCU_I2C_from_config(config, EMC2101_CHIP_ADDR)

        self.printer.add_object('emc2101 ' + self.name, self)
    
    def handle_connect(self):
        chipid = self._read_register('WHOAMI', 1)[0]
        if chipid != EMC2101_CHIP_ID and chipid != EMC2101_ALT_CHIP_ID:
            logging.error('emc2101: Unexpected chip ID %#x' % chipid)
        else:
            logging.info('emc2101: Chip ID %#x' % chipid)
    
    def set_fan_speed(self, value):
        logging.info(f'emc2101 {self.name} set fan speed {value}')

    def get_mcu(self):
        return self.i2c.get_mcu()

    def _read_register(self, reg_name, read_len):
        regs = [EMC2101_REGS[reg_name]]
        params = self.i2c.i2c_read(regs, read_len)
        return bytearray(params['response'])
    
    def _write_register(self, reg_name, data):
        if type(data) is not list:
            data = [data]
        reg = EMC2101_REGS[reg_name]
        data.insert(0, reg)
        self.i2c.i2c_write(data)