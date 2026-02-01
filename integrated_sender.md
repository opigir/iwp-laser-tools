# Integrated ILDA Sender Feature

## Overview

The IWP Visualizer now includes integrated ILDA file playback capability, allowing you to load and visualize ILDA laser animation files directly without requiring external hardware. This feature combines the ILDA parsing functionality from `iwp-ilda.py` with the real-time visualization capabilities of the main visualizer.

## Features

- **Local Testing**: Test ILDA animations without needing physical laser hardware
- **File Preview**: Visualize ILDA files before sending to actual projectors
- **Development Tool**: Debug and validate ILDA animations during development
- **Comparison Mode**: Compare ILDA files against live IWP data streams
- **Educational Use**: Learn ILDA format structure and laser programming concepts

## Usage

### Loading ILDA Files

1. **Via Command Line**:
   ```bash
   python src/main.py --ilda-file "path/to/animation.ild"
   ```

2. **Via Interactive Mode**:
   - Start the enhanced visualizer: `python src/main.py`
   - Click "Load ILDA" button or press `F1`
   - Navigate and select your `.ild` file

### Playback Controls

### Enhanced Visualizer (main.py)
| Control | Action |
|---------|--------|
| `F1` | Open ILDA file browser |
| `TAB` | Toggle Sender/Receiver mode |
| Play/Pause Button | Control playback |
| Next/Previous Buttons | Frame navigation |
| Speed Slider | Adjust playback speed |
| Loop Toggle | Enable/disable loop |
| Transmit Toggle | Send to network |

### Basic Controls
| Key | Action |
|-----|--------|
| `G` | Toggle grid |
| `C` | Toggle crosshair |
| `P` | Toggle points |
| `L` | Toggle lines |

### Display Modes

- **ILDA Only**: Shows only the loaded ILDA animation
- **Live Only**: Shows only incoming IWP data (default mode)
- **Overlay**: Shows both ILDA and live data simultaneously
- **Split Screen**: ILDA on left, live data on right

## Technical Implementation

### ILDA Parser Integration

The visualizer incorporates the ILDA parsing logic from `iwp-ilda.py`:

- Supports ILDA formats 0, 1, 4, and 5
- Handles color palettes (format 2)
- Preserves blanking information
- Maintains frame timing

### Data Flow

```
ILDA File → Parser → IWP Packet Conversion → Visualizer Pipeline
```

### Memory Management

- Lazy loading for large ILDA files
- Frame caching with configurable limits
- Automatic garbage collection of unused frames

## Configuration

### Frame Rate Settings

```python
# In config.yaml or via command line
ilda_playback:
  fps: 25                    # Default playback FPS
  loop: true                 # Auto-loop animations
  preload_frames: 100        # Frames to preload
  max_cached_frames: 1000    # Memory limit
```

### Quality Settings

```python
# Interpolation and smoothing
rendering:
  ilda_interpolation: true   # Smooth point transitions
  point_density: 1.0         # Point density multiplier
  blanking_visible: true     # Show blanked points
```

## Supported ILDA Formats

| Format | Description | Support Status |
|--------|-------------|----------------|
| 0 | 3D Coordinates + Indexed Color | ✅ Full |
| 1 | 2D Coordinates + Indexed Color | ✅ Full |
| 2 | Color Palette | ✅ Full |
| 3 | Truecolor Palette | ⚠️ Partial |
| 4 | 3D Coordinates + Truecolor | ✅ Full |
| 5 | 2D Coordinates + Truecolor | ✅ Full |

## Use Cases

### 1. Local Development
```bash
# Test your ILDA animation locally
python src/main.py --ilda-file "my_animation.ild" --mode sender
```

### 2. Hardware Comparison
```bash
# Load ILDA file and receive live data simultaneously
python src/main.py --mode receiver
# Then load ILDA file via GUI for comparison
```

### 3. Educational Demo
```bash
# Use enhanced GUI for interactive exploration
python src/main.py --ilda-file "demo.ild"
```

## Troubleshooting

### Common Issues

1. **File Not Loading**
   - Check file path and permissions
   - Verify ILDA format compatibility
   - Check file size limits

2. **Slow Playback**
   - Reduce preload_frames setting
   - Lower visualization quality
   - Check available memory

3. **Color Issues**
   - Verify color palette in ILDA file
   - Check format compatibility
   - Adjust color mapping settings

### Debug Mode

Enable debug output to see parsing details:
```bash
python src/main.py --ilda-file "file.ild" --mode sender
```

Or use the command-line version:
```bash
python src/iwp_visualizer_cli.py visualize --help
```

## Performance Considerations

- **Large Files**: Files >100MB may require adjusted memory settings
- **High Frame Rates**: Consider reducing visualization quality for >60fps
- **Complex Animations**: Multi-thousand point frames may impact real-time performance

## Future Enhancements

- [ ] ILDA file editing capabilities
- [ ] Export visualizer output to ILDA
- [ ] Advanced interpolation modes
- [ ] Multi-file playlist support
- [ ] Frame-by-frame analysis tools
- [ ] Performance profiling integration

## Integration with Existing Features

This feature seamlessly integrates with all existing visualizer capabilities:

- All display options (grid, crosshair, trails) work with ILDA data
- Statistics and analysis tools function normally
- Export and recording features remain available
- Network discovery and IWP reception continue working

The integrated sender makes the IWP Visualizer a complete development and testing environment for laser programming workflows.