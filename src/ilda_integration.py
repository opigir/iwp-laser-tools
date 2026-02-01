#!/usr/bin/env python3
"""
ILDA File Integration for IWP Visualizer
Provides ILDA file loading and playback capabilities
"""

import struct
import time
import socket
import threading
from dataclasses import dataclass
from typing import List, Optional, Tuple, Generator, Callable
from pathlib import Path

try:
    from iwp_protocol import IWPPoint, IWPPacket
except ImportError:
    from .iwp_protocol import IWPPoint, IWPPacket

# ILDA constants
ILDA_HEADER_SIZE = 32
STATUS_BLANKED_MASK = 0b0100_0000

# IWP Protocol constants
IW_TYPE_0 = 0x00  # Turn off / end frame
IW_TYPE_1 = 0x01  # Period (us)
IW_TYPE_2 = 0x02  # 16b X/Y + 8b R/G/B
IW_TYPE_3 = 0x03  # 16b X/Y + 16b R/G/B

@dataclass
class IldaHeader:
    format: int
    frame_name: str
    company_name: str
    records: int
    frame_number: int
    total_frames: int
    projector_number: int

@dataclass
class IldaFrame:
    format: int
    points: List[Tuple[int, int, int, int, int, int, int]]
    header: IldaHeader

class ILDALoader:
    """Load and parse ILDA files"""

    def __init__(self):
        self.frames: List[IldaFrame] = []
        self.palette: List[Tuple[int, int, int]] = [(255, 255, 255)] * 256
        self.filename: Optional[str] = None

    def load_file(self, filename: str) -> bool:
        """Load an ILDA file and parse all frames"""
        try:
            with open(filename, "rb") as f:
                data = f.read()

            self.frames, self.palette = self._parse_ilda_data(data)
            self.filename = filename
            return len(self.frames) > 0

        except Exception as e:
            print(f"Failed to load ILDA file {filename}: {e}")
            return False

    def _read_ilda_header(self, buf: bytes, offset: int) -> Tuple[Optional[IldaHeader], int]:
        """Read ILDA header from buffer"""
        head = buf[offset:offset + ILDA_HEADER_SIZE]
        if len(head) < ILDA_HEADER_SIZE:
            return None, offset

        if head[0:4] != b"ILDA":
            return None, offset

        format_code = head[7]
        frame_name = head[8:16].rstrip(b"\\x00").decode(errors="ignore")
        company_name = head[16:24].rstrip(b"\\x00").decode(errors="ignore")
        records = struct.unpack(">H", head[24:26])[0]
        frame_number = struct.unpack(">H", head[26:28])[0]
        total_frames = struct.unpack(">H", head[28:30])[0]
        projector_number = head[30]

        hdr = IldaHeader(
            format=format_code,
            frame_name=frame_name,
            company_name=company_name,
            records=records,
            frame_number=frame_number,
            total_frames=total_frames,
            projector_number=projector_number,
        )
        return hdr, offset + ILDA_HEADER_SIZE

    def _parse_ilda_data(self, data: bytes) -> Tuple[List[IldaFrame], List[Tuple[int, int, int]]]:
        """Parse ILDA data and return frames and palette"""
        offset = 0
        frames: List[IldaFrame] = []
        palette: List[Tuple[int, int, int]] = [(255, 255, 255)] * 256

        while offset < len(data):
            hdr, offset = self._read_ilda_header(data, offset)
            if hdr is None:
                break

            fmt = hdr.format
            recs = hdr.records

            if fmt == 0:  # 3D coordinates + indexed color
                rec_size = 8
                points = []
                for _ in range(recs):
                    rec = data[offset:offset + rec_size]
                    if len(rec) < rec_size:
                        break
                    x, y, z, status, color_index = struct.unpack(">hhhBB", rec)
                    r, g, b = palette[color_index]
                    points.append((x, y, z, status, r, g, b))
                    offset += rec_size
                frames.append(IldaFrame(format=fmt, points=points, header=hdr))

            elif fmt == 1:  # 2D coordinates + indexed color
                rec_size = 6
                points = []
                for _ in range(recs):
                    rec = data[offset:offset + rec_size]
                    if len(rec) < rec_size:
                        break
                    x, y, status, color_index = struct.unpack(">hhBB", rec)
                    r, g, b = palette[color_index]
                    points.append((x, y, 0, status, r, g, b))
                    offset += rec_size
                frames.append(IldaFrame(format=fmt, points=points, header=hdr))

            elif fmt == 2:  # Color palette
                rec_size = 3
                for i in range(recs):
                    rec = data[offset:offset + rec_size]
                    if len(rec) < rec_size:
                        break
                    r, g, b = struct.unpack(">BBB", rec)
                    if i < 256:
                        palette[i] = (r, g, b)
                    offset += rec_size

            elif fmt == 4:  # 3D coordinates + truecolor
                rec_size = 10
                points = []
                for _ in range(recs):
                    rec = data[offset:offset + rec_size]
                    if len(rec) < rec_size:
                        break
                    x, y, z, status, b, g, r = struct.unpack(">hhhBBBB", rec)
                    points.append((x, y, z, status, r, g, b))
                    offset += rec_size
                frames.append(IldaFrame(format=fmt, points=points, header=hdr))

            elif fmt == 5:  # 2D coordinates + truecolor
                rec_size = 8
                points = []
                for _ in range(recs):
                    rec = data[offset:offset + rec_size]
                    if len(rec) < rec_size:
                        break
                    x, y, status, b, g, r = struct.unpack(">hhBBBB", rec)
                    points.append((x, y, 0, status, r, g, b))
                    offset += rec_size
                frames.append(IldaFrame(format=fmt, points=points, header=hdr))

            else:
                # Unsupported format, skip
                break

        return frames, palette

    def get_frame_count(self) -> int:
        """Get total number of frames"""
        return len(self.frames)

    def get_frame(self, index: int) -> Optional[IldaFrame]:
        """Get frame by index"""
        if 0 <= index < len(self.frames):
            return self.frames[index]
        return None

class ILDAPlayer:
    """Handle ILDA file playback"""

    def __init__(self, loader: ILDALoader):
        self.loader = loader
        self.current_frame = 0
        self.playing = False
        self.loop = True
        self.fps = 25.0
        self.last_frame_time = 0.0
        self.speed_multiplier = 1.0

    def play(self):
        """Start playback"""
        self.playing = True
        self.last_frame_time = time.time()

    def pause(self):
        """Pause playback"""
        self.playing = False

    def stop(self):
        """Stop playback and reset to beginning"""
        self.playing = False
        self.current_frame = 0

    def restart(self):
        """Restart from beginning"""
        self.current_frame = 0
        self.last_frame_time = time.time()

    def next_frame(self):
        """Advance to next frame"""
        if self.loader.get_frame_count() > 0:
            self.current_frame = (self.current_frame + 1) % self.loader.get_frame_count()
            if not self.loop and self.current_frame == 0:
                self.current_frame = self.loader.get_frame_count() - 1
                self.playing = False

    def previous_frame(self):
        """Go to previous frame"""
        if self.loader.get_frame_count() > 0:
            self.current_frame = (self.current_frame - 1) % self.loader.get_frame_count()

    def set_frame(self, index: int):
        """Set current frame by index"""
        if 0 <= index < self.loader.get_frame_count():
            self.current_frame = index

    def set_fps(self, fps: float):
        """Set playback frame rate"""
        self.fps = max(0.1, min(1000.0, fps))

    def set_speed(self, multiplier: float):
        """Set speed multiplier"""
        self.speed_multiplier = max(0.1, min(10.0, multiplier))

    def update(self) -> bool:
        """Update playback state. Returns True if frame changed."""
        if not self.playing or self.loader.get_frame_count() == 0:
            return False

        current_time = time.time()
        frame_duration = 1.0 / (self.fps * self.speed_multiplier)

        if current_time - self.last_frame_time >= frame_duration:
            self.next_frame()
            self.last_frame_time = current_time
            return True

        return False

    def get_current_frame(self) -> Optional[IldaFrame]:
        """Get the current frame"""
        return self.loader.get_frame(self.current_frame)

    def get_status(self) -> dict:
        """Get player status information"""
        return {
            'playing': self.playing,
            'current_frame': self.current_frame,
            'total_frames': self.loader.get_frame_count(),
            'fps': self.fps,
            'speed': self.speed_multiplier,
            'loop': self.loop,
            'filename': self.loader.filename
        }

class ILDAToIWPConverter:
    """Convert ILDA frames to IWP packets"""

    @staticmethod
    def _transform_coordinates(x: int, y: int) -> Tuple[int, int]:
        """Transform ILDA coordinates to IWP coordinates"""
        # ILDA uses signed 16-bit coordinates (-32768 to +32767)
        # IWP uses unsigned 16-bit coordinates (0 to 65535)
        # Match the transformation from original iwp-ilda.py
        xn = (x + 0x8000) & 0xFFFF  # Convert to unsigned 16-bit
        yn = (-y + 0x8000) & 0xFFFF  # Flip Y axis and convert to unsigned
        return xn, yn

    @staticmethod
    def convert_frame_to_packet(frame: IldaFrame, timestamp: Optional[int] = None) -> IWPPacket:
        """Convert an ILDA frame to an IWP packet"""
        if timestamp is None:
            timestamp = int(time.time() * 1000000)  # microseconds

        iwp_points = []

        for x, y, z, status, r, g, b in frame.points:
            # Transform coordinates
            iwp_x, iwp_y = ILDAToIWPConverter._transform_coordinates(x, y)

            # Handle blanking
            blanking = bool(status & STATUS_BLANKED_MASK)

            # Convert 8-bit colors to 16-bit if needed
            if r <= 255 and g <= 255 and b <= 255:
                r16 = r * 257 if not blanking else 0  # Convert 8-bit to 16-bit
                g16 = g * 257 if not blanking else 0
                b16 = b * 257 if not blanking else 0
            else:
                r16 = r if not blanking else 0
                g16 = g if not blanking else 0
                b16 = b if not blanking else 0

            iwp_point = IWPPoint(
                x=iwp_x,
                y=iwp_y,
                r=r16,
                g=g16,
                b=b16,
                blanking=blanking
            )
            iwp_points.append(iwp_point)

        return IWPPacket(
            points=iwp_points,
            commands=[],  # No commands for ILDA conversion
            point_count=len(iwp_points),
            scan_period=None,  # Will be set by caller if needed
            timestamp=timestamp,
            raw_size=len(iwp_points) * 11  # Estimate for TYPE_3 commands
        )

class NetworkSender:
    """Network sender for transmitting IWP packets via UDP"""

    def __init__(self, target_ip: str = "127.0.0.1", port: int = 7200, scan_rate: int = 1000):
        self.target_ip = target_ip
        self.port = port
        self.scan_period = max(1, min(4294967295, int(1000000 / scan_rate)))
        self.sock = None
        self.connected = False
        self.error_count = 0
        self.packets_sent = 0
        self.bytes_sent = 0
        self.last_error = None
        self._lock = threading.Lock()

    def connect(self) -> bool:
        """Establish UDP connection"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Send scan period setup packet
            setup_packet = struct.pack(">B I", IW_TYPE_1, self.scan_period)
            self.sock.sendto(setup_packet, (self.target_ip, self.port))
            self.connected = True
            self.last_error = None
            return True
        except Exception as e:
            self.last_error = str(e)
            self.connected = False
            return False

    def disconnect(self):
        """Close UDP connection"""
        with self._lock:
            if self.sock:
                try:
                    # Send end frame
                    end_packet = struct.pack(">B", IW_TYPE_0)
                    self.sock.sendto(end_packet, (self.target_ip, self.port))
                except:
                    pass
                finally:
                    self.sock.close()
                    self.sock = None
            self.connected = False

    def send_packet(self, packet: IWPPacket) -> bool:
        """Send an IWP packet over the network"""
        if not self.connected or not self.sock:
            return False

        try:
            with self._lock:
                # Convert packet to network format
                network_data = self._packet_to_network_data(packet)

                # Send in chunks if needed
                max_packet_size = 1023
                for i in range(0, len(network_data), max_packet_size):
                    chunk = network_data[i:i + max_packet_size]
                    self.sock.sendto(chunk, (self.target_ip, self.port))
                    self.bytes_sent += len(chunk)

                self.packets_sent += 1
                return True

        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            return False

    def _packet_to_network_data(self, packet: IWPPacket) -> bytes:
        """Convert IWP packet to network transmission format"""
        samples = []

        for point in packet.points:
            # Transform coordinates (ILDA to IWP)
            x16 = (point.x + 0x8000) & 0xFFFF
            y16 = (-point.y + 0x8000) & 0xFFFF

            # Handle blanking and colors
            if point.blanking:
                r16 = g16 = b16 = 0
            else:
                # Ensure 16-bit values
                r16 = point.r if point.r > 255 else point.r * 257
                g16 = point.g if point.g > 255 else point.g * 257
                b16 = point.b if point.b > 255 else point.b * 257

            # Pack as IW_TYPE_3 format (16-bit coordinates + 16-bit colors)
            sample = struct.pack(">B H H H H H", IW_TYPE_3, x16, y16, r16, g16, b16)
            samples.append(sample)

        return b"".join(samples)

    def set_target(self, ip: str, port: int):
        """Update target IP and port"""
        self.target_ip = ip
        self.port = port
        if self.connected:
            self.disconnect()

    def set_scan_rate(self, scan_rate: int):
        """Update scan rate"""
        self.scan_period = max(1, min(4294967295, int(1000000 / scan_rate)))
        if self.connected:
            # Send updated scan period
            try:
                setup_packet = struct.pack(">B I", IW_TYPE_1, self.scan_period)
                self.sock.sendto(setup_packet, (self.target_ip, self.port))
            except:
                pass

    def get_stats(self) -> dict:
        """Get transmission statistics"""
        return {
            'connected': self.connected,
            'target_ip': self.target_ip,
            'port': self.port,
            'packets_sent': self.packets_sent,
            'bytes_sent': self.bytes_sent,
            'error_count': self.error_count,
            'last_error': self.last_error
        }

class IntegratedILDASystem:
    """Main interface for ILDA integration with network transmission"""

    def __init__(self):
        self.loader = ILDALoader()
        self.player = ILDAPlayer(self.loader)
        self.converter = ILDAToIWPConverter()
        self.sender = NetworkSender()
        self.current_packet = None
        self.transmission_enabled = False

    def load_file(self, filename: str) -> bool:
        """Load an ILDA file"""
        if self.loader.load_file(filename):
            self.player = ILDAPlayer(self.loader)  # Reset player
            print(f"Loaded ILDA file: {filename}")
            print(f"  Frames: {self.loader.get_frame_count()}")
            if self.loader.frames:
                first_frame = self.loader.frames[0]
                print(f"  Points per frame: {len(first_frame.points)}")
                print(f"  Format: {first_frame.format}")
            return True
        return False

    def update(self) -> Optional[IWPPacket]:
        """Update and get current IWP packet"""
        frame_changed = self.player.update()

        if frame_changed or self.current_packet is None:
            current_frame = self.player.get_current_frame()
            if current_frame:
                self.current_packet = self.converter.convert_frame_to_packet(current_frame)

                # Send over network if transmission is enabled
                if self.transmission_enabled and self.current_packet:
                    self.sender.send_packet(self.current_packet)

                return self.current_packet

        return self.current_packet

    def enable_transmission(self, target_ip: str, port: int = 7200, scan_rate: int = 1000) -> bool:
        """Enable network transmission"""
        self.sender.set_target(target_ip, port)
        self.sender.set_scan_rate(scan_rate)
        if self.sender.connect():
            self.transmission_enabled = True
            return True
        return False

    def disable_transmission(self):
        """Disable network transmission"""
        self.transmission_enabled = False
        self.sender.disconnect()

    def get_network_stats(self) -> dict:
        """Get network transmission statistics"""
        return self.sender.get_stats()

    def get_player(self) -> ILDAPlayer:
        """Get the player for direct control"""
        return self.player

    def get_sender(self) -> NetworkSender:
        """Get the network sender for direct control"""
        return self.sender

    def get_status(self) -> dict:
        """Get system status"""
        status = self.player.get_status()
        status['loaded'] = self.loader.get_frame_count() > 0
        status['transmission_enabled'] = self.transmission_enabled
        status['network'] = self.sender.get_stats()
        return status

def main():
    """Test the ILDA integration system"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ilda_integration.py <ilda_file>")
        return

    filename = sys.argv[1]
    system = IntegratedILDASystem()

    if system.load_file(filename):
        system.player.play()
        print("Playing ILDA file. Press Ctrl+C to stop.")

        try:
            while True:
                packet = system.update()
                if packet:
                    status = system.get_status()
                    print(f"Frame {status['current_frame']}/{status['total_frames']} - {packet.point_count} points")
                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\\nStopped.")
    else:
        print(f"Failed to load {filename}")

if __name__ == "__main__":
    main()