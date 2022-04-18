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

import datetime
import struct

ENCODING = "UTF-8"
BYTE_ORDER_BIG_ENDIAN = 1
BYTE_ORDER_LITTLE_ENDIAN = 2

def read_byte(buffer, offset):
    return struct.unpack_from("B", buffer, offset)[0]

def read_short(buffer, offset):
    return struct.unpack_from("<H", buffer, offset)[0]

def read_int(buffer, offset):
    return struct.unpack_from("<I", buffer, offset)[0]

def read_string(buffer, offset, size):
    length = size

    for idx in range(0, size):
        if buffer[offset + idx] == 0x00:
            length = idx
            break

    return str(buffer[offset : offset + length], ENCODING)

def read_hex_string(buffer, offset, size, reverse_order = False):
    result = ""
    for idx in range(0, size):
        result += format(buffer[offset + (size - idx - 1 if reverse_order else idx)], "02x")

    return result

def read_timestamp(buffer, offset):
    year = read_short(buffer, offset)
    month = read_short(buffer, offset + 2)
    day = read_short(buffer, offset + 4)
    hour = read_short(buffer, offset + 6)
    minute = read_short(buffer, offset + 8)
    second = read_short(buffer, offset + 10)

    return int(datetime.datetime(2000 + year, month, day, hour, minute, second).timestamp())

def write_byte(buffer, offset, value):
    struct.pack_into("B", buffer, offset, value)

def write_short(buffer, offset, value, byte_order = BYTE_ORDER_LITTLE_ENDIAN):
    struct.pack_into("<H" if byte_order == BYTE_ORDER_LITTLE_ENDIAN else ">H", buffer, offset, value)

def write_int(buffer, offset, value, byte_order = BYTE_ORDER_LITTLE_ENDIAN):
    struct.pack_into("<I" if byte_order == BYTE_ORDER_LITTLE_ENDIAN else ">I", buffer, offset, value)

def checksum(buffer, start_offset, end_offset):
    return sum(buffer[start_offset : end_offset]) & 255
