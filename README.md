# NCAT AutoDrive Challenge -- CAN Log and GNSS Attenuation Analysis

North Carolina A&T State University submission for the AutoDrive Challenge data analysis component. This repository contains the raw CAN bus logs, decoded perception data, GNSS attenuation analysis, and the Jupyter notebooks that serve as the written reports.

## Submission Notebooks

The two Jupyter notebooks below constitute the team's written report and can be downloaded and reviewed directly:

| Notebook | Purpose |
|----------|---------|
| `NCAT_CAN_Analysis.ipynb` | Perception analysis of the scored run CAN logs (object detection, traffic signals, traffic signs, autonomy state, GPS track, and score estimation) |
| `NCAT_GNSS_Attenuation_Analysis.ipynb` | GNSS attenuation testing writeup (how attenuation was achieved, observed effects, and mitigation strategies) |

## Note on the GNSS Attenuation Analysis

The GNSS attenuation testing was performed separately from the scored Design Your Own Challenge run. During the attenuation test, no NeoVI CAN bus logs were recorded -- the data was captured as a ROS bag (`planning-control-test.bag`) on the vehicle's onboard compute platform using the Novatel OEM7 GNSS/INS driver topics (`/novatel/oem7/inspva`, `/novatel/oem7/insstdev`, `/novatel/oem7/odom`).

The original analysis was written as a standalone Python script (`gnss_attenuation_analysis.py`). For this submission, we converted it into a Jupyter notebook (`NCAT_GNSS_Attenuation_Analysis.ipynb`) to match the expected submission format and to embed the narrative writeup alongside the code and visualizations.

To execute the GNSS notebook, it must be run on the vehicle PC where the ROS bag file and `rosbag` Python library are available.

## Repository Contents

### Raw Data

| File | Description |
|------|-------------|
| `NCAT_CAN_Logs.vsb` | Raw binary CAN log captured from the NeoVI logger on HSCAN3 (scoring bus) during the scored challenge run. Intrepid Control Systems binary format (icsbin v0x104). |
| `NCAT_CAN_Logs.csv` | Converted CSV containing all 27,510 raw CAN frames with timestamps, arbitration IDs, network info, and individual data bytes. Produced by `vsb_to_csv.py`. |
| `NCAT_CAN_Logs_decoded.csv` | Fully decoded CSV where raw CAN bytes have been translated into named physical signals (e.g., VehicleLatitude, ObjObjectType, IllumLtGreenBall) using the ADC2 scoring DBC database. Produced by `analyze_can.py`. |

### DBC Database Files

| File | Description |
|------|-------------|
| `dbc/ADC2_SC_2024.2.dbc` | **Scoring CAN** database -- this is the primary DBC used for decoding the CAN logs. Defines perception messages: AVState, AVLight, VehicleLocation, Objects, TrafficSignalHeads, TrafficSigns, and their associated track messages. |
| `dbc/ADC2_HS_2024.2.dbc` | High-Speed CAN database -- defines vehicle platform messages (steering, braking, propulsion, chassis sensors). Not used in this analysis since the scoring bus carries the perception data. |
| `dbc/ADC2_CE_2024.2.dbc` | CAN Extended database -- defines additional vehicle interface messages. Included for completeness. |
| `dbc/ADC2_LS_2024.2.dbc` | Low-Speed CAN database -- defines body/comfort messages. Included for completeness. |

### Analysis Notebooks

| File | Description |
|------|-------------|
| `NCAT_CAN_Analysis.ipynb` | Full perception analysis of the scored run. Sections: data loading, GPS track visualization, autonomy engagement timeline, object detection analysis (types, confidence, sensor sources, bird's-eye view), traffic signal recognition (light states, state transitions), traffic sign recognition (detected types, confidence), perception quality summary, and score estimation. Pre-executed with all outputs and plots embedded. |
| `NCAT_GNSS_Attenuation_Analysis.ipynb` | GNSS attenuation writeup answering the three required questions: (1) how attenuation was achieved via a software-based attenuator cycling through drift, denial, recovery, multipath phases; (2) observed effects on position stdev, drift, and INS status; (3) mitigation via pose selector threshold, LIO fallback, smooth recovery blending, and multipath cross-checking. Must be executed on the vehicle PC with ROS and the bag file. |

### Scripts

| File | Description |
|------|-------------|
| `vsb_to_csv.py` | Converts Intrepid `.vsb` binary CAN logs to CSV format. Uses the `ICS-VSBIO` library to parse the binary file and extracts timestamps, network info, arbitration IDs, status flags, and data bytes. |
| `analyze_can.py` | Decodes raw CAN CSV data using a DBC file via the `cantools` library. Reads `NCAT_CAN_Logs.csv`, applies signal definitions from `dbc/ADC2_SC_2024.2.dbc`, and outputs `NCAT_CAN_Logs_decoded.csv` with all signals expanded into named columns. Also prints a per-signal summary (min, max, sample count, units). |
| `gnss_attenuation_analysis.py` | Original standalone Python script for the GNSS attenuation analysis. Reads the ROS bag, simulates the attenuator phases, computes per-phase drift/stdev statistics, and generates timeline and trajectory plots. This is the source script that was converted into the Jupyter notebook. |

### Generated Plots

These plot images are produced by `NCAT_CAN_Analysis.ipynb` and are also embedded in the notebook outputs:

| File | Description |
|------|-------------|
| `gps_track.png` | Vehicle GPS trajectory (lat/lon scatter colored by elapsed time) and coordinates over time |
| `autonomy_timeline.png` | Autonomy engagement status, control subsystem activation, and AV indicator light state over the run |
| `object_detection.png` | Object count, detected types, and detection confidence over time |
| `object_birdseye.png` | Bird's-eye view of all object detections in the vehicle's reference frame |
| `traffic_signals.png` | Traffic signal count, light states (green/yellow/red), distance, and confidence |
| `traffic_signs.png` | Traffic sign count, detected types, and distance over time |

## Data Summary

- **Scored run duration:** 196.4 seconds (~3.3 minutes)
- **CAN messages:** 27,510 frames on HSCAN3 (scoring bus)
- **12 unique message types** across arbitration IDs 0x010 to 0x041
- **Capture date:** 2026-03-29 18:59:06 to 19:02:23 UTC
- **Location:** NC A&T State University campus area (lat ~36.08, lon ~-79.77)

## Requirements

```
pip install ICS-VSBIO cantools pandas matplotlib numpy
```

For the GNSS attenuation notebook (vehicle PC only):

```
pip install rosbag numpy matplotlib
```

## Usage

Convert VSB to CSV:

```
python3 vsb_to_csv.py NCAT_CAN_Logs.vsb
```

Decode CAN signals using DBC:

```
python3 analyze_can.py
```

Run the CAN analysis notebook:

```
jupyter notebook NCAT_CAN_Analysis.ipynb
```

## License

MIT
