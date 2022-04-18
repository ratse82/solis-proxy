"""
Solis-Proxy
Copyright (C) 2021 rATse

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import time
import array
import util

class Solarman:
    """ Class used to parse data received from Data Logging Stick """

    FRAME_TYPE_INFORMATION = 0x01
    FRAME_TYPE_DATA = 0x02

    __DATA_START_CODE = 0xa5
    __DATA_END_CODE = 0x15

    __DATA_TYPE_REAL_TIME = "real-time"
    __DATA_TYPE_HISTORICAL = "historical"

    __sequence_no = {}

    def __init__(self, rawdata):
        self.rawdata = rawdata

    @property
    def rawdata(self):
        return self.__rawdata

    @rawdata.setter
    def rawdata(self, value):
        value_length = len(value)

        if value_length == 0:
            raise Solarman.ValidationError("No data")

        if value[0] != Solarman.__DATA_START_CODE:
            raise Solarman.ValidationError("Data start code validation error")

        data_length = util.read_short(value, 1)
        if data_length > value_length - 13:
            raise Solarman.ValidationError("Wrong data size")

        checksum = util.checksum(value, 1, value_length - 2)
        if value[value_length - 2] != checksum:
            raise Solarman.ValidationError("Checksum error")

        if value[value_length - 1] != Solarman.__DATA_END_CODE:
            raise Solarman.ValidationError("Data end code validation error")

        self.__rawdata = value

    def get_payload(self):
        frame_type = self.get_frame_type()

        if frame_type == Solarman.FRAME_TYPE_INFORMATION:
            return self.__parse_information_frame()
        if frame_type == Solarman.FRAME_TYPE_DATA:
            return self.__parse_data_frame()

        raise Solarman.UnsupportedFrameTypeError(frame_type)

    def __parse_information_frame(self):
        rawdata = self.rawdata

        return {
            "data_logger_sn": str(self.get_data_logger_serial_no()),
            "total_working_time": util.read_int(rawdata, 12),
            "signal_quality": util.read_byte(rawdata, 28),
            "firmware": util.read_string(rawdata, 30, 15),
            "mac_address": util.read_hex_string(rawdata, 70, 6),
            "ip_address": util.read_string(rawdata, 76, 16)
        }

    def __parse_data_frame(self):
        rawdata = self.rawdata

        return {
            "dts": util.read_timestamp(rawdata, 146),
            "data_type": Solarman.__DATA_TYPE_HISTORICAL if self.__get_command_type() & 0b10000000 > 0 else Solarman.__DATA_TYPE_REAL_TIME,
            "data_logger_sn": str(self.get_data_logger_serial_no()),
            "total_working_time": util.read_int(rawdata, 14),
            "inverter_sn": util.read_string(rawdata, 32, 15),
            "temperature": util.read_short(rawdata, 48) / 10,
            "v_dc1": util.read_short(rawdata, 50) / 10,
            "i_dc1": util.read_short(rawdata, 54) / 10,
            "v_dc2": util.read_short(rawdata, 52) / 10,
            "i_dc2": util.read_short(rawdata, 56) / 10,
            "v_ac1": util.read_short(rawdata, 64) / 10,
            "i_ac1": util.read_short(rawdata, 58) / 10,
            "v_ac2": util.read_short(rawdata, 66) / 10,
            "i_ac2": util.read_short(rawdata, 60) / 10,
            "v_ac3": util.read_short(rawdata, 68) / 10,
            "i_ac3": util.read_short(rawdata, 62) / 10,
            "f_grid": util.read_short(rawdata, 70) / 100,
            "power": util.read_short(rawdata, 72),
            "kwh_today": util.read_int(rawdata, 76) / 100,
            "kwh_yesterday": util.read_short(rawdata, 128) / 10,
            "kwh_this_month": util.read_int(rawdata, 120),
            "kwh_last_month": util.read_int(rawdata, 124),
            "kwh_this_year": util.read_int(rawdata, 130),
            "kwh_last_year": util.read_int(rawdata, 134),
            "kwh_total": util.read_int(rawdata, 80) / 10,
            "inverter_model": util.read_hex_string(rawdata, 158, 2, True),
            "firmware_slave": util.read_hex_string(rawdata, 160, 2, True),
            "firmware_main": util.read_hex_string(rawdata, 162, 2, True),
            "status": util.read_short(rawdata, 242)
        }

    def is_response_needed(self):
        return util.read_byte(self.rawdata, 4) & 0b01000000 > 0

    def get_response(self):
        if not self.is_response_needed():
            return None

        now = time.localtime()
        response_data = array.array('b', b' ' * 23)

        # Start code
        util.write_byte  (response_data,  0, Solarman.__DATA_START_CODE)
        # Header
        util.write_short (response_data,  1, 0x0a)
        util.write_short (response_data,  3, (self.__get_protocol_version() << 12) + (1 << 4) + self.get_frame_type(), util.BYTE_ORDER_BIG_ENDIAN)
        util.write_short (response_data,  5, (self.__seq_next_value() << 8) + self.__get_client_seq(), util.BYTE_ORDER_BIG_ENDIAN)
        util.write_int   (response_data,  7, self.get_data_logger_serial_no())
        # Data
        util.write_byte  (response_data, 11, self.__get_command_type())
        util.write_byte  (response_data, 12, 0x01)
        util.write_int   (response_data, 13, int(time.mktime(now)))
        util.write_short (response_data, 17, int(now.tm_gmtoff / 60))
        util.write_short (response_data, 19, 0x00)
        # Checksum
        util.write_byte  (response_data, 21, util.checksum(response_data, 1, 21))
        # End code
        util.write_byte  (response_data, 22, Solarman.__DATA_END_CODE)

        return response_data

    def get_data_logger_serial_no(self):
        return util.read_int(self.rawdata, 7)

    def get_frame_type(self):
        return util.read_byte(self.rawdata, 4) & 0b00001111

    def __get_protocol_version(self):
        return (util.read_byte(self.rawdata, 3) & 0b11110000) >> 4

    def __get_command_type(self):
        return util.read_byte(self.rawdata, 11)

    def __get_client_seq(self):
        return util.read_byte(self.rawdata, 6)

    def __seq_next_value(self):
        data_logger_sn = self.get_data_logger_serial_no()
        seq_value = Solarman.__sequence_no.get(data_logger_sn)
        if seq_value is None:
            seq_value = 0

        seq_value = (seq_value + 1) & 255
        if seq_value == 0:
            seq_value = 1

        Solarman.__sequence_no[data_logger_sn] = seq_value
        return seq_value


    #
    # Exceptions
    #
    class ValidationError(Exception):
        """ Raised when received data can't pass validation """

    class UnsupportedFrameTypeError(Exception):
        """ Raised when received data can't be parsed """

        def __init__(self, frame_type):
            super().__init__(frame_type)
            self.frame_type = frame_type
