# IWP Laser Tools - Quick Start Guide

## 1. Install and Setup

```bash
cd python-idn-receiver
python install_and_run.py
```

Or manually:

```bash
pip install -r requirements.txt
python src/main.py discover
```

## 2. Configure IWP Sender Device

1. Note the **Target IP** from the discovery output (e.g., `192.168.0.2`)
2. Connect your IWP-enabled sender device to the same WiFi network
3. Open the device web interface: `http://<DEVICE_IP>/`
4. Set **Target IP** to your computer's IP
5. Set **Target Port** to `7255`
6. Click "Update Configuration"

## 3. Start Receiving Data

### Option A: Full Visualizer (Recommended)
```bash
python src/main.py visualize
```

### Option B: Server Only (Console Output)
```bash
python src/main.py server
```

### Option C: Individual Components
```bash
# Network discovery
python src/network_discovery.py

# UDP server only
python src/udp_server.py

# Visualizer only (with integrated server)
python src/laser_visualizer.py
```

## 4. Verify Connection

- Device status LED should indicate WiFi connection
- Python application should show "CONNECTED" status
- You should see real-time laser patterns on screen

## Troubleshooting

### No Connection
1. Check both devices on same WiFi
2. Verify sender device Target IP matches your computer
3. Check firewall allows UDP port 7255

### Poor Performance
1. Move closer to WiFi router
2. Close other network applications
3. Use Ethernet connection if available

### Pygame Issues
```bash
pip install --upgrade pygame
```

## Controls (Visualizer)

- `G` - Toggle grid
- `C` - Toggle crosshair
- `P` - Toggle points
- `L` - Toggle lines
- `T` - Toggle trail mode
- `ESC` - Exit