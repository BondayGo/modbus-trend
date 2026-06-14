# Changelog

## 0.2.0 - 2026-08-19

- Flush the CSV after every sample so an unplugged dongle loses at most
  one line.
- Count and report read errors on exit.
- Bump default baud rate to 19200 to match the bench dongles.

## 0.1.1 - 2026-07-02

- Fix CRC byte order in the request frame (low byte first, as on the wire).
- Handle short replies with a clear error instead of a stack trace.

## 0.1.0 - 2026-06-14

- First working version: FC03 polling, CSV append, Ctrl+C clean stop.
