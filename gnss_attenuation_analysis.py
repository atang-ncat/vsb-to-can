#!/usr/bin/env python3
"""
GNSS Attenuation Offline Analysis
===================================
Reads planning-control-test.bag, simulates the attenuator phases,
and generates figures + data for the GNSS attenuation report.

Outputs:
  - /tmp/attenuation_timeline.png   (phase timeline + stdev/drift)
  - /tmp/attenuation_trajectory.png (vehicle path with phase coloring)
  - /tmp/attenuation_stats.json     (per-phase error statistics)
"""

import rosbag
import math
import json
import random
import numpy as np

# Try matplotlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

BAG_PATH = "/home/autodrive/vehicle_planning_autodrive/rosbags/planning-control-test.bag"
OUT_DIR = "/tmp"

# ============================================================
# ATTENUATOR SIMULATION (mirrors gps_attenuator.py)
# ============================================================
INIT_NORMAL_DURATION = 10.0
CYCLE_PERIOD = 60.0
PHASE_DURATIONS = {
    "SLOW_DRIFT":   10.0,
    "GPS_DENIED":   20.0,
    "RECOVERY":      8.0,
    "NORMAL":        8.0,
    "MULTIPATH":     4.0,
    "GPS_DENIED_2": 10.0,
}
PHASE_ORDER = ["SLOW_DRIFT", "GPS_DENIED", "RECOVERY", "NORMAL", "MULTIPATH", "GPS_DENIED_2"]

def get_phase(elapsed):
    if elapsed < INIT_NORMAL_DURATION:
        return "INIT_NORMAL", 0.0
    cycle_time = (elapsed - INIT_NORMAL_DURATION) % CYCLE_PERIOD
    t = 0.0
    for name in PHASE_ORDER:
        dur = PHASE_DURATIONS[name]
        if cycle_time < t + dur:
            return name, (cycle_time - t) / dur
        t += dur
    return "NORMAL", 0.0

def get_attenuation(phase, progress):
    if phase in ["INIT_NORMAL", "NORMAL"]:
        return 1.0, 3, 0.0, False
    elif phase == "SLOW_DRIFT":
        return 1.0 + progress * 49.0, (3 if progress < 0.4 else (2 if progress < 0.7 else 6)), progress * 0.3, False
    elif phase in ["GPS_DENIED", "GPS_DENIED_2"]:
        return 100.0, 0, 0.5, False
    elif phase == "RECOVERY":
        return 100.0 * (1.0 - progress) + 1.0 * progress, (0 if progress < 0.3 else (2 if progress < 0.6 else 3)), 0.5 * (1.0 - progress), False
    elif phase == "MULTIPATH":
        return 2.0, 3, 0.0, True
    return 1.0, 3, 0.0, False

# ============================================================
# READ BAG
# ============================================================
print(f"Reading bag: {BAG_PATH}")

inspva_data = []
odom_data = []
insstdev_data = []

bag = rosbag.Bag(BAG_PATH, 'r')
bag_start = None

for topic, msg, t in bag.read_messages(topics=[
    '/novatel/oem7/inspva',
    '/novatel/oem7/odom',
    '/novatel/oem7/insstdev'
]):
    ts = t.to_sec()
    if bag_start is None:
        bag_start = ts
    
    elapsed = ts - bag_start
    
    if topic == '/novatel/oem7/inspva':
        inspva_data.append({
            'time': elapsed,
            'lat': msg.latitude,
            'lon': msg.longitude,
            'azimuth': msg.azimuth,
            'status': msg.status.status,
        })
    elif topic == '/novatel/oem7/odom':
        odom_data.append({
            'time': elapsed,
            'x': msg.pose.pose.position.x,
            'y': msg.pose.pose.position.y,
        })
    elif topic == '/novatel/oem7/insstdev':
        insstdev_data.append({
            'time': elapsed,
            'lat_stdev': msg.latitude_stdev,
            'lon_stdev': msg.longitude_stdev,
        })

bag.close()
bag_duration = inspva_data[-1]['time'] if inspva_data else 0
print(f"Read {len(inspva_data)} INSPVA, {len(odom_data)} odom, {len(insstdev_data)} INSSTDEV msgs")
print(f"Bag duration: {bag_duration:.1f}s")

# ============================================================
# SIMULATE ATTENUATION
# ============================================================
random.seed(42)

timeline = []
drift_x, drift_y = 0.0, 0.0
multipath_x, multipath_y = 0.0, 0.0

for d in inspva_data:
    elapsed = d['time']
    phase, progress = get_phase(elapsed)
    stdev_mult, ins_status, drift_rate, multipath = get_attenuation(phase, progress)
    
    if phase in ["INIT_NORMAL", "NORMAL"]:
        drift_x *= 0.95
        drift_y *= 0.95
        multipath_x *= 0.9
        multipath_y *= 0.9
    else:
        drift_x += random.gauss(0, drift_rate * 0.1)
        drift_y += random.gauss(0, drift_rate * 0.1)
        drift_x = max(-15, min(15, drift_x))
        drift_y = max(-15, min(15, drift_y))
    
    if multipath:
        multipath_x, multipath_y = 3.0, -2.5
    
    total_drift = math.sqrt((drift_x + multipath_x)**2 + (drift_y + multipath_y)**2)
    
    # Original stdev from bag
    orig_stdev = 0.01  # default
    for sd in insstdev_data:
        if abs(sd['time'] - elapsed) < 0.5:
            orig_stdev = math.sqrt(sd['lat_stdev']**2 + sd['lon_stdev']**2)
            break
    
    timeline.append({
        'time': elapsed,
        'phase': phase,
        'progress': progress,
        'stdev_mult': stdev_mult,
        'ins_status': ins_status,
        'drift_m': total_drift,
        'attenuated_stdev': orig_stdev * stdev_mult,
        'original_stdev': orig_stdev,
        'lat': d['lat'],
        'lon': d['lon'],
    })

# ============================================================
# COMPUTE PER-PHASE STATISTICS
# ============================================================
phase_stats = {}
for entry in timeline:
    phase = entry['phase']
    if phase not in phase_stats:
        phase_stats[phase] = {'drift': [], 'stdev': [], 'count': 0, 'duration': 0}
    phase_stats[phase]['drift'].append(entry['drift_m'])
    phase_stats[phase]['stdev'].append(entry['attenuated_stdev'])
    phase_stats[phase]['count'] += 1

for phase in phase_stats:
    s = phase_stats[phase]
    s['drift_mean'] = float(np.mean(s['drift']))
    s['drift_max'] = float(np.max(s['drift']))
    s['drift_p95'] = float(np.percentile(s['drift'], 95))
    s['stdev_mean'] = float(np.mean(s['stdev']))
    s['stdev_max'] = float(np.max(s['stdev']))
    del s['drift']
    del s['stdev']

with open(f"{OUT_DIR}/attenuation_stats.json", 'w') as f:
    json.dump(phase_stats, f, indent=2)
print(f"Saved stats to {OUT_DIR}/attenuation_stats.json")

# ============================================================
# FIGURE 1: ATTENUATION TIMELINE
# ============================================================
fig, axes = plt.subplots(3, 1, figsize=(10, 6), sharex=True)
fig.suptitle('GNSS Attenuation Profile — Planning-Control Test Bag', fontweight='bold', fontsize=13)

times = [e['time'] for e in timeline]
stdevs = [e['attenuated_stdev'] for e in timeline]
drifts = [e['drift_m'] for e in timeline]
ins_statuses = [e['ins_status'] for e in timeline]

# Phase coloring
phase_colors = {
    'INIT_NORMAL': '#22c55e', 'NORMAL': '#22c55e',
    'SLOW_DRIFT': '#f97316', 'RECOVERY': '#f97316',
    'GPS_DENIED': '#ef4444', 'GPS_DENIED_2': '#ef4444',
    'MULTIPATH': '#a855f7',
}

# Background shading for phases
prev_phase = None
phase_start = 0
for i, e in enumerate(timeline):
    if e['phase'] != prev_phase:
        if prev_phase is not None:
            for ax in axes:
                ax.axvspan(phase_start, e['time'], alpha=0.15, color=phase_colors.get(prev_phase, '#888'))
        prev_phase = e['phase']
        phase_start = e['time']
# Last phase
if prev_phase:
    for ax in axes:
        ax.axvspan(phase_start, times[-1], alpha=0.15, color=phase_colors.get(prev_phase, '#888'))

# Plot 1: Stdev multiplier
axes[0].semilogy(times, stdevs, color='#3b82f6', linewidth=1.2)
axes[0].set_ylabel('Position Stdev (m)', fontsize=10)
axes[0].set_ylim(0.001, 10)
axes[0].grid(True, alpha=0.3)
axes[0].axhline(y=0.5, color='orange', linestyle='--', alpha=0.5, label='Pose selector threshold')
axes[0].legend(fontsize=8)

# Plot 2: Position drift
axes[1].plot(times, drifts, color='#ef4444', linewidth=1.2)
axes[1].set_ylabel('Position Drift (m)', fontsize=10)
axes[1].grid(True, alpha=0.3)
axes[1].axhline(y=2.0, color='orange', linestyle='--', alpha=0.5, label='LIO switch threshold')
axes[1].legend(fontsize=8)

# Plot 3: INS status
axes[2].step(times, ins_statuses, color='#a855f7', linewidth=1.5, where='post')
axes[2].set_ylabel('INS Status', fontsize=10)
axes[2].set_xlabel('Time (s)', fontsize=10)
axes[2].set_yticks([0, 2, 3, 6])
axes[2].set_yticklabels(['INACTIVE', 'CONVERGING', 'GOOD', 'DEGRADED'])
axes[2].grid(True, alpha=0.3)

# Add phase labels at top
prev_phase = None
for e in timeline:
    if e['phase'] != prev_phase:
        prev_phase = e['phase']
        label = prev_phase.replace('_', '\n')
        axes[0].text(e['time'] + 1, 5, label, fontsize=6, va='top', fontweight='bold',
                     color=phase_colors.get(prev_phase, '#888'))

plt.tight_layout()
plt.savefig(f"{OUT_DIR}/attenuation_timeline.png", dpi=150, bbox_inches='tight')
print(f"Saved {OUT_DIR}/attenuation_timeline.png")

# ============================================================
# FIGURE 2: VEHICLE TRAJECTORY WITH PHASE COLORING
# ============================================================
origin_lat = inspva_data[0]['lat']
origin_lon = inspva_data[0]['lon']

fig2, ax2 = plt.subplots(1, 1, figsize=(8, 6))
fig2.suptitle('Vehicle Trajectory — Phase-Colored', fontweight='bold', fontsize=13)

for e in timeline:
    x = (e['lon'] - origin_lon) * 111320 * math.cos(math.radians(origin_lat))
    y = (e['lat'] - origin_lat) * 110540
    color = phase_colors.get(e['phase'], '#888')
    ax2.plot(x, y, '.', color=color, markersize=2)

ax2.set_xlabel('X (m)', fontsize=10)
ax2.set_ylabel('Y (m)', fontsize=10)
ax2.set_aspect('equal')
ax2.grid(True, alpha=0.3)

# Legend
patches = [
    mpatches.Patch(color='#22c55e', label='Normal GPS'),
    mpatches.Patch(color='#f97316', label='Degrading/Recovery'),
    mpatches.Patch(color='#ef4444', label='GPS Denied'),
    mpatches.Patch(color='#a855f7', label='Multipath'),
]
ax2.legend(handles=patches, loc='upper right', fontsize=9)

plt.tight_layout()
plt.savefig(f"{OUT_DIR}/attenuation_trajectory.png", dpi=150, bbox_inches='tight')
print(f"Saved {OUT_DIR}/attenuation_trajectory.png")

# ============================================================
# PRINT SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("PER-PHASE SUMMARY")
print("=" * 60)
for phase in ['INIT_NORMAL', 'SLOW_DRIFT', 'GPS_DENIED', 'NORMAL', 'RECOVERY', 'MULTIPATH', 'GPS_DENIED_2']:
    if phase in phase_stats:
        s = phase_stats[phase]
        print(f"  {phase:15s}: drift_mean={s['drift_mean']:.3f}m  "
              f"drift_max={s['drift_max']:.3f}m  "
              f"stdev_mean={s['stdev_mean']:.4f}m  "
              f"({s['count']} samples)")
print("=" * 60)
print("Done! Figures saved to /tmp/")
