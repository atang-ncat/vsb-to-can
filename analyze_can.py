#!/usr/bin/env python3
"""Decode NCAT CAN logs using ADC2 DBC files and produce decoded CSV + summary."""

import csv
import sys
import os
import cantools

DBC_PATH = os.path.join(os.path.dirname(__file__),
                        "..", "ADC2_IntegrationGuide_v2024.2", "ADC2_SC_2024.2.dbc")
CSV_INPUT = os.path.join(os.path.dirname(__file__), "NCAT_CAN_Logs.csv")
CSV_OUTPUT = os.path.join(os.path.dirname(__file__), "NCAT_CAN_Logs_decoded.csv")


def load_raw_messages(csv_path):
    """Load raw CAN messages from the converter output CSV."""
    messages = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            arb_id = int(row["ArbID_Dec"])
            dlc = int(row["DLC"])
            data = bytearray()
            for i in range(dlc):
                b = row.get(f"B{i}", "")
                if b:
                    data.append(int(b, 16))
                else:
                    data.append(0)
            messages.append({
                "timestamp": row["Timestamp_Sec"],
                "datetime": row["DateTime_UTC"],
                "arb_id": arb_id,
                "dlc": dlc,
                "data": bytes(data),
                "data_hex": row["Data_Hex"],
            })
    return messages


def main():
    dbc_path = sys.argv[1] if len(sys.argv) > 1 else DBC_PATH
    csv_in = sys.argv[2] if len(sys.argv) > 2 else CSV_INPUT
    csv_out = sys.argv[3] if len(sys.argv) > 3 else CSV_OUTPUT

    dbc_path = os.path.realpath(dbc_path)
    print(f"DBC file:  {dbc_path}", file=sys.stderr)
    print(f"Input CSV: {csv_in}", file=sys.stderr)
    print(f"Output:    {csv_out}", file=sys.stderr)

    db = cantools.database.load_file(dbc_path)
    dbc_ids = {msg.frame_id: msg for msg in db.messages}
    print(f"DBC defines {len(dbc_ids)} messages", file=sys.stderr)

    raw = load_raw_messages(csv_in)
    print(f"Loaded {len(raw)} raw CAN messages", file=sys.stderr)

    all_signal_names = set()
    for msg_def in dbc_ids.values():
        for sig in msg_def.signals:
            all_signal_names.add(f"{msg_def.name}.{sig.name}")
    all_signal_names = sorted(all_signal_names)

    decode_errors = 0
    decoded_rows = []
    summaries = {}

    for m in raw:
        row = {
            "Timestamp_Sec": m["timestamp"],
            "DateTime_UTC": m["datetime"],
            "ArbID_Hex": f"0x{m['arb_id']:03X}",
            "Message_Name": "",
            "Data_Hex": m["data_hex"],
        }
        for sn in all_signal_names:
            row[sn] = ""

        if m["arb_id"] in dbc_ids:
            msg_def = dbc_ids[m["arb_id"]]
            row["Message_Name"] = msg_def.name
            try:
                decoded = msg_def.decode(m["data"], decode_choices=False)
                for sig_name, value in decoded.items():
                    full_name = f"{msg_def.name}.{sig_name}"
                    row[full_name] = value

                    if full_name not in summaries:
                        summaries[full_name] = {
                            "min": value if isinstance(value, (int, float)) else None,
                            "max": value if isinstance(value, (int, float)) else None,
                            "count": 0,
                            "unit": "",
                        }
                        for s in msg_def.signals:
                            if s.name == sig_name:
                                summaries[full_name]["unit"] = s.unit or ""
                                break

                    s = summaries[full_name]
                    s["count"] += 1
                    if isinstance(value, (int, float)) and s["min"] is not None:
                        s["min"] = min(s["min"], value)
                        s["max"] = max(s["max"], value)
            except Exception:
                decode_errors += 1

        decoded_rows.append(row)

    header = ["Timestamp_Sec", "DateTime_UTC", "ArbID_Hex", "Message_Name",
              "Data_Hex"] + all_signal_names
    with open(csv_out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(decoded_rows)

    print(f"\nDecoded {len(decoded_rows)} messages ({decode_errors} errors) -> {csv_out}",
          file=sys.stderr)

    print("\n" + "=" * 80, file=sys.stderr)
    print("SIGNAL SUMMARY", file=sys.stderr)
    print("=" * 80, file=sys.stderr)

    current_msg = ""
    for name in sorted(summaries.keys()):
        s = summaries[name]
        msg_name = name.split(".")[0]
        if msg_name != current_msg:
            current_msg = msg_name
            print(f"\n--- {msg_name} ---", file=sys.stderr)
        unit_str = f" [{s['unit']}]" if s["unit"] else ""
        if s["min"] is not None:
            print(f"  {name}: min={s['min']}, max={s['max']}, "
                  f"samples={s['count']}{unit_str}", file=sys.stderr)
        else:
            print(f"  {name}: samples={s['count']}{unit_str}", file=sys.stderr)


if __name__ == "__main__":
    main()
