# Changelog

All notable changes to the IWP Laser Visualizer project will be documented in this file.

## [1.0.0] - 2025-01-31

### Added
- Professional real-time IWP (ILDA Wave Protocol) visualization
- Full support for all IWP command types (TYPE_0-3)
- High-performance UDP server with connection management
- Real-time pygame-based visualization engine
- Network discovery and configuration tools
- Comprehensive type hints and error handling
- Professional logging system
- Complete documentation and examples

### Features
- **Protocol Support**: Compatible with IWPServer.cpp and iwp-ilda.py
- **Real-time Performance**: 30+ FPS laser pattern display
- **Network Tools**: Auto-discovery and port testing utilities
- **Professional Quality**: Production-ready code with comprehensive error handling
- **Cross-platform**: Works on Windows, macOS, and Linux

### Technical Details
- Port: 7200 (standard IWP port)
- Protocol: UDP with big-endian byte order
- Coordinate System: 16-bit unsigned (0-65535)
- Color Support: 8-bit and 16-bit RGB values
- Framework: Python 3.8+ with pygame 2.0+

### Compatibility
- ILDAWaveX16 hardware
- iwp-ilda.py sender
- IWPServer.cpp implementations
- All IWP-compatible devices