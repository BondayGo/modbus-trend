# modbus-trend

Polls a single holding register from a Modbus RTU slave on a serial
(RS-485) link and appends each sample to a CSV file. Written for the motor
test benches: we keep it running during alignment jobs and check the drive
temperature / speed trend afterwards instead of watching a live gauge.

No Modbus stack dependency — the RTU frame and CRC16 are hand-rolled, so
the only requirement is `pyserial`.

## Usage

```bash
pip install -r requirements.txt
python modbus_trend.py --port COM3 --slave 1 --register 40001 --interval 5 --out run42.csv
```

Register numbering uses the usual 4xxxx notation (`40001` = the first
holding register). Stop with Ctrl+C; the log is flushed after every sample,
so an unplugged dongle costs at most one line.

## Notes

- Defaults match our bench dongles: 19200 8N1, slave 1.
- Exception replies, short reads and CRC mismatches are reported to stderr
  and counted; the logging loop keeps going.
- The output is plain CSV (`timestamp,slave,register,value`), which plots
  fine in any spreadsheet.

## Sample

See `samples/sample-log.csv` for a short captured run.
