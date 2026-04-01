#!/usr/bin/env python3
"""Convert Intrepid Control Systems .vsb CAN log files to .csv format."""

import csv
import sys
from datetime import datetime, timezone
from ICS_VSBIO.VSBReader import VSBReader
from ICS_VSBIO import VSBIOFlags as flags

ICS_EPOCH_UNIX = 1167609600.0  # Jan 1, 2007 00:00:00 UTC as Unix timestamp

NETWORK_NAMES = {
    flags.NETID_DEVICE: "DEVICE",
    flags.NETID_HSCAN: "HSCAN",
    flags.NETID_MSCAN: "MSCAN",
    flags.NETID_SWCAN: "SWCAN",
    flags.NETID_LSFTCAN: "LSFTCAN",
    flags.NETID_J1708: "J1708",
    flags.NETID_JVPW: "JVPW",
    flags.NETID_ISO: "ISO",
    flags.NETID_ISO2: "ISO2",
    flags.NETID_LIN: "LIN",
    flags.NETID_ISO3: "ISO3",
    flags.NETID_HSCAN2: "HSCAN2",
    flags.NETID_HSCAN3: "HSCAN3",
    flags.NETID_ISO4: "ISO4",
    flags.NETID_LIN2: "LIN2",
    flags.NETID_LIN3: "LIN3",
    flags.NETID_LIN4: "LIN4",
    flags.NETID_MOST: "MOST",
    flags.NETID_CGI: "CGI",
    flags.NETID_HSCAN4: "HSCAN4",
    flags.NETID_HSCAN5: "HSCAN5",
    flags.NETID_SWCAN2: "SWCAN2",
    flags.NETID_ETHERNET_DAQ: "ETHERNET_DAQ",
    flags.NETID_FLEXRAY1A: "FLEXRAY1A",
    flags.NETID_FLEXRAY1B: "FLEXRAY1B",
    flags.NETID_FLEXRAY2A: "FLEXRAY2A",
    flags.NETID_FLEXRAY2B: "FLEXRAY2B",
    flags.NETID_LIN5: "LIN5",
    flags.NETID_FLEXRAY: "FLEXRAY",
    flags.NETID_MOST25: "MOST25",
    flags.NETID_MOST50: "MOST50",
    flags.NETID_ETHERNET: "ETHERNET",
    flags.NETID_GMFSA: "GMFSA",
    flags.NETID_TCP: "TCP",
    flags.NETID_HSCAN6: "HSCAN6",
    flags.NETID_HSCAN7: "HSCAN7",
    flags.NETID_LIN6: "LIN6",
    flags.NETID_LSFTCAN2: "LSFTCAN2",
    flags.NETID_OP_ETHERNET1: "OP_ETHERNET1",
    flags.NETID_OP_ETHERNET2: "OP_ETHERNET2",
    flags.NETID_OP_ETHERNET3: "OP_ETHERNET3",
    flags.NETID_OP_ETHERNET4: "OP_ETHERNET4",
    flags.NETID_OP_ETHERNET5: "OP_ETHERNET5",
    flags.NETID_OP_ETHERNET6: "OP_ETHERNET6",
    flags.NETID_OP_ETHERNET7: "OP_ETHERNET7",
    flags.NETID_OP_ETHERNET8: "OP_ETHERNET8",
    flags.NETID_OP_ETHERNET9: "OP_ETHERNET9",
    flags.NETID_OP_ETHERNET10: "OP_ETHERNET10",
    flags.NETID_OP_ETHERNET11: "OP_ETHERNET11",
    flags.NETID_OP_ETHERNET12: "OP_ETHERNET12",
}

PROTOCOL_NAMES = {
    flags.SPY_PROTOCOL_CUSTOM: "CUSTOM",
    flags.SPY_PROTOCOL_CAN: "CAN",
    flags.SPY_PROTOCOL_GMLAN: "GMLAN",
    flags.SPY_PROTOCOL_J1850VPW: "J1850VPW",
    flags.SPY_PROTOCOL_J1850PWM: "J1850PWM",
    flags.SPY_PROTOCOL_ISO9141: "ISO9141",
    flags.SPY_PROTOCOL_Keyword2000: "KWP2000",
    flags.SPY_PROTOCOL_LIN: "LIN",
    flags.SPY_PROTOCOL_J1708: "J1708",
    flags.SPY_PROTOCOL_J1939: "J1939",
    flags.SPY_PROTOCOL_FLEXRAY: "FLEXRAY",
    flags.SPY_PROTOCOL_MOST: "MOST",
    flags.SPY_PROTOCOL_ETHERNET: "ETHERNET",
    flags.SPY_PROTOCOL_CANFD: "CANFD",
    flags.SPY_PROTOCOL_TCP: "TCP",
}


def convert_vsb_to_csv(vsb_path, csv_path):
    reader = VSBReader(vsb_path)

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Timestamp_Sec",
            "DateTime_UTC",
            "Network",
            "NetworkID",
            "Protocol",
            "ArbID_Hex",
            "ArbID_Dec",
            "Is_Extended",
            "Is_Tx",
            "Is_Error",
            "DLC",
            "Data_Hex",
            "B0", "B1", "B2", "B3", "B4", "B5", "B6", "B7",
        ])

        count = 0
        for msg in reader:
            m = msg.info
            timestamp = reader.get_message_time(msg)
            unix_ts = timestamp + ICS_EPOCH_UNIX
            try:
                dt = datetime.fromtimestamp(unix_ts, tz=timezone.utc)
                dt_str = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
            except (OSError, ValueError):
                dt_str = ""

            net_name = NETWORK_NAMES.get(m.NetworkID, f"NET_{m.NetworkID}")
            proto_name = PROTOCOL_NAMES.get(m.Protocol, f"PROTO_{m.Protocol}")
            is_extended = bool(m.StatusBitField & flags.SPY_STATUS_XTD_FRAME)
            is_tx = bool(m.StatusBitField & flags.SPY_STATUS_TX_MSG)
            is_error = bool(m.StatusBitField & flags.SPY_STATUS_GLOBAL_ERR)

            arb_id = m.ArbIDOrHeader
            dlc = m.NumberBytesData

            data_bytes = []
            for i in range(min(dlc, 8)):
                data_bytes.append(msg.get_byte_from_data(i))
            while len(data_bytes) < 8:
                data_bytes.append(None)

            data_hex = " ".join(f"{b:02X}" for b in data_bytes if b is not None)
            byte_cols = [f"0x{b:02X}" if b is not None else "" for b in data_bytes]

            writer.writerow([
                f"{timestamp:.6f}",
                dt_str,
                net_name,
                m.NetworkID,
                proto_name,
                f"0x{arb_id:03X}" if not is_extended else f"0x{arb_id:08X}",
                arb_id,
                int(is_extended),
                int(is_tx),
                int(is_error),
                dlc,
                data_hex,
                *byte_cols,
            ])
            count += 1
            if count % 5000 == 0:
                print(f"  Processed {count} messages...", file=sys.stderr)

    print(f"Done! Converted {count} messages to {csv_path}", file=sys.stderr)
    return count


if __name__ == "__main__":
    vsb_file = sys.argv[1] if len(sys.argv) > 1 else "/home/balulab/Downloads/NCAT_CAN_Logs.vsb"
    csv_file = vsb_file.rsplit(".", 1)[0] + ".csv"
    if len(sys.argv) > 2:
        csv_file = sys.argv[2]

    print(f"Converting: {vsb_file}", file=sys.stderr)
    print(f"Output:     {csv_file}", file=sys.stderr)
    convert_vsb_to_csv(vsb_file, csv_file)
