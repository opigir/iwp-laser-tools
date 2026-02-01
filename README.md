# IWP Laser Tools

 Suite of tools for IWP (ILDA Wave Protocol) laser development and testing. Includes real-time visualization, ILDA file sending, and network analysis without requiring physical ILDAWaveX16 hardware.

## Features

- **Real-time Visualization**: High-performance laser pattern display using pygame
- **ILDA File Sender**: Load and transmit ILDA files as IWP packets over network
- **Dual Mode Interface**: Unified sender/receiver GUI with seamless mode switching
- **Full IWP Protocol Support**: Compatible with all IWP command types (TYPE_0-3)
- **Network Discovery**: Auto-detects IP configuration for IWP device setup
- **Performance Monitoring**: Packet rate, latency, and connection quality tracking
- **Interactive Controls**: Zoom, pan, trail mode, and display options
- **Professional Quality**: Production-ready code suitable for development and testing

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

**1. Enhanced Visualizer (Recommended)**
Run the full-featured enhanced visualizer with integrated sender/receiver:
```bash
python src/main.py
```

**2. Network Discovery**
Find your computer's IP address for IWP device configuration:
```bash
python src/iwp_visualizer_cli.py discover
```

**3. Command Line Tools**
Basic visualizer:
```bash
python src/iwp_visualizer_cli.py visualize
```

Server only (no GUI):
```bash
python src/iwp_visualizer_cli.py server
```

### Testing with iwp-ilda.py

Test the visualizer with ILDA files using the included iwp-ilda.py sender:
```bash
# Terminal 1: Start enhanced visualizer
python src/main.py

# Terminal 2: Send ILDA file (or use built-in ILDA loader in GUI)
python iwp-ilda.py --file "animation.ild" --ip 127.0.0.1 --scan 1000 --repeat 10
```

## IWP Protocol Support

Supports all IWP (ILDA Wave Protocol) command types:
- **TYPE_0 (0x00)**: Turn off/end frame
- **TYPE_1 (0x01)**: Scan period control (32-bit microseconds)
- **TYPE_2 (0x02)**: 16-bit coordinates + 8-bit RGB colors
- **TYPE_3 (0x03)**: 16-bit coordinates + 16-bit RGB colors

## Network Configuration

Default settings:
- **Port**: 7200 (standard IWP port)
- **Protocol**: UDP
- **Format**: Raw IWP commands (big-endian)
- **Coordinate System**: 16-bit unsigned (0-65535)

## Command Line Options

**Enhanced Visualizer:**
```bash
python src/main.py --help
```

**Command Line Tools:**
```bash
python src/iwp_visualizer_cli.py --help
```

Options:
- `--port PORT`: UDP port to listen on (default: 7200)
- `--width WIDTH`: Window width in pixels (default: 800)
- `--height HEIGHT`: Window height in pixels (default: 600)

## Architecture

- **`iwp_protocol.py`**: Professional IWP parser supporting all command types
- **`udp_server.py`**: High-performance UDP server with connection management
- **`main.py`**: Enhanced visualizer with integrated sender/receiver GUI
- **`iwp_visualizer_cli.py`**: Command-line interface tools
- **`laser_visualizer.py`**: Basic pygame-based visualization engine
- **`network_discovery.py`**: Network configuration and discovery utilities
- **`port_test.py`**: Network connectivity testing tools

## Contributing

This project is designed for contribution to the ILDAWaveX16 project. Code follows professional standards with:
- Comprehensive type hints
- Detailed docstrings
- Error handling
- Performance optimization
- Clean architecture

## Requirements

- Python 3.8+
- pygame 2.0+

## License

Compatible with ILDAWaveX16 project licensing.