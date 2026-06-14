#!/usr/bin/env python3
"""modbus-trend: poll a Modbus RTU slave and append values to a CSV log.

Built for the motor test benches: logs drive temperature / speed registers
over an RS-485 dongle so trends can be checked after a run.

Usage:
    python modbus_trend.py --port COM3 --slave 1 --register 40001 \
        --interval 5 --out log.csv

Requires pyserial (pip install -r requirements.txt). The script speaks
Modbus RTU (function code 03, holding registers) with a hand-rolled CRC,
so no further dependencies are needed.
"""

import argparse
import csv
import datetime
import serial
import sys
import time

# CRC16 lookup for the Modbus polynomial 0xA001 (reflected 0x8005).
_CRC_TABLE = []
for _b in range(256):
    _c = _b
    for _ in range(8):
        _c = (_c >> 1) ^ 0xA001 if _c & 1 else _c >> 1
    _CRC_TABLE.append(_c)


def crc16(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc = (crc >> 8) ^ _CRC_TABLE[(crc ^ byte) & 0xFF]
    return crc


def read_holding_registers(port, slave: int, register: int, count: int = 1):
    """Issue one FC03 request and return the register values as ints."""
    # Modbus addresses are 0-based; the 4xxxx notation offsets by 40001.
    address = register - 40001
    if not 0 <= address <= 0xFFFF - count:
        raise ValueError(f"register out of range: {register}")
    request = bytes([slave & 0xFF, 0x03,
                     (address >> 8) & 0xFF, address & 0xFF,
                     0x00, count & 0xFF])
    checksum = crc16(request)
    frame = request + bytes([checksum & 0xFF, (checksum >> 8) & 0xFF])

    port.reset_input_buffer()
    port.write(frame)

    # Response: slave, fc, bytecount, data..., crc16
    expected = 5 + 2 * count
    reply = port.read(expected)
    if len(reply) < expected:
        raise IOError(f"short reply ({len(reply)}/{expected} bytes)")
    if reply[1] & 0x80:
        raise IOError(f"slave returned exception code {reply[2]:#04x}")
    got = crc16(reply[:-2])
    if (reply[-2] | reply[-1] << 8) != got:
        raise IOError("CRC mismatch on reply")
    return [int.from_bytes(reply[3 + 2 * i:5 + 2 * i], "big") for i in range(count)]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port", required=True, help="serial device, e.g. COM3 or /dev/ttyUSB0")
    parser.add_argument("--slave", type=int, default=1, help="slave address (default 1)")
    parser.add_argument("--register", type=int, default=40001, help="holding register in 4xxxx notation")
    parser.add_argument("--interval", type=float, default=5.0, help="seconds between polls (default 5)")
    parser.add_argument("--out", default="log.csv", help="output CSV path")
    parser.add_argument("--baud", type=int, default=19200, help="baud rate (default 19200)")
    args = parser.parse_args()

    ser = serial.Serial(port=args.port, baudrate=args.baud,
                        bytesize=8, parity="N", stopbits=1,
                        timeout=1.0)
    new_file = not __import__("pathlib").Path(args.out).exists()
    csv_file = open(args.out, "a", newline="")
    writer = csv.writer(csv_file)
    if new_file:
        writer.writerow(["timestamp", "slave", "register", "value"])

    polls = errors = 0
    print(f"logging slave {args.slave} reg {args.register} every {args.interval:g}s -> {args.out}")
    print("press Ctrl+C to stop")
    try:
        while True:
            stamp = datetime.datetime.now().isoformat(timespec="seconds")
            try:
                values = read_holding_registers(ser, args.slave, args.register)
                writer.writerow([stamp, args.slave, args.register, values[0]])
                csv_file.flush()
                polls += 1
                print(f"{stamp}  {values[0]}")
            except (IOError, ValueError) as exc:
                errors += 1
                print(f"{stamp}  ERROR: {exc}", file=sys.stderr)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    finally:
        csv_file.close()
        ser.close()
        print(f"\nstopped: {polls} polls, {errors} errors")


if __name__ == "__main__":
    main()
