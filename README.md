# vsb-to-can

Convert Intrepid Control Systems `.vsb` (Vehicle Spy binary) CAN log files to `.csv` format for analysis using Python.

## Overview

This tool reads binary CAN bus log files produced by Intrepid Control Systems hardware (neoVI, ValueCAN, RAD-Galaxy, etc.) and Vehicle Spy software, and converts them into a flat CSV file suitable for analysis in Python, MATLAB, Excel, or any data tool.

## Files

| File | Description |
|------|-------------|
| `NCAT_CAN_Logs.vsb` | Raw binary CAN log captured from HSCAN3 network |
| `NCAT_CAN_Logs.csv` | Converted CSV output (27,510 messages) |
| `vsb_to_csv.py` | Python conversion script |

## Data Summary

- **Messages:** 27,510 CAN frames
- **Network:** HSCAN3 (High-Speed CAN, channel 3)
- **Protocol:** CAN 2.0
- **Duration:** ~3 minutes 16 seconds (2026-03-29 18:59:06 to 19:02:23 UTC)
- **Unique Arbitration IDs:** 12 (range 0x010 to 0x041)

### Arbitration ID Breakdown

| ArbID | Count | DLC |
|-------|-------|-----|
| 0x010 | 1,965 | 1 |
| 0x011 | 1,965 | 1 |
| 0x014 | 1,965 | 8 |
| 0x020 | 1,965 | 3 |
| 0x021 | 1,965 | 8 |
| 0x022 | 1,965 | 5 |
| 0x023 | 1,965 | 8 |
| 0x024 | 1,965 | 5 |
| 0x030 | 3,930 | 3 |
| 0x031 | 3,930 | 7 |
| 0x040 | 1,965 | 3 |
| 0x041 | 1,965 | 7 |

## CSV Columns

| Column | Description |
|--------|-------------|
| `Timestamp_Sec` | Seconds since ICS epoch (Jan 1, 2007) |
| `DateTime_UTC` | Human-readable UTC timestamp |
| `Network` | CAN network name |
| `NetworkID` | Numeric network identifier |
| `Protocol` | Protocol type (CAN, CANFD, LIN, etc.) |
| `ArbID_Hex` | Arbitration ID in hexadecimal |
| `ArbID_Dec` | Arbitration ID in decimal |
| `Is_Extended` | 1 if 29-bit extended ID, 0 if 11-bit standard |
| `Is_Tx` | 1 if transmitted by logger, 0 if received |
| `Is_Error` | 1 if error frame |
| `DLC` | Data Length Code (number of data bytes) |
| `Data_Hex` | All data bytes as a hex string |
| `B0` - `B7` | Individual data bytes |

## Requirements

- Python 3.8+
- ICS-VSBIO library

Install the dependency:

```
pip install ICS-VSBIO
```

## Usage

Convert a `.vsb` file to `.csv`:

```
python3 vsb_to_csv.py <input.vsb> [output.csv]
```

If no output path is given, the CSV is written alongside the input file with the same base name.

Example:

```
python3 vsb_to_csv.py NCAT_CAN_Logs.vsb
```

## Possible Analyses

- **Message frequency and timing** -- verify cycle times and detect message dropouts
- **Signal trending** -- plot data byte values over time to observe sensor behavior
- **Bus load estimation** -- calculate CAN bus utilization percentage
- **Anomaly detection** -- identify error frames, missing messages, or out-of-range values
- **Signal correlation** -- find relationships between data on different CAN IDs
- **DBC decoding** -- if a database file is available, decode raw bytes into physical signals with units
- **Reverse engineering** -- classify bytes as counters, checksums, or physical signals based on statistical patterns

## License

MIT
