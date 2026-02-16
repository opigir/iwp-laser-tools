#!/usr/bin/env python3
"""
ILDA File Integration for IWP Visualizer
Provides ILDA file loading and playback capabilities
"""

import struct
import time
import socket
from dataclasses import dataclass
from typing import List, Optional, Tuple

try:
    from iwp_protocol import IWPPacket
except ImportError:
    from .iwp_protocol import IWPPacket

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
        """Read ILDA header from buffer - exact match to iwp-ilda.py"""
        head = buf[offset:offset + ILDA_HEADER_SIZE]
        if len(head) < ILDA_HEADER_SIZE:
            return None, offset

        if head[0:4] != b"ILDA":
            return None, offset

        format_code = head[7]
        frame_name = head[8:16].rstrip(b"\x00").decode(errors="ignore")
        company_name = head[16:24].rstrip(b"\x00").decode(errors="ignore")
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
    """Convert ILDA frames to direct transmission format"""

    @staticmethod
    def convert_frame_to_points(frame: IldaFrame) -> List[Tuple[int, int, int, int, int, int, int]]:
        """Convert ILDA frame to point list for direct transmission matching iwp-ilda.py"""
        return frame.points

class ProjectorSender:
    """Network sender based on the proven iwp-ilda.py implementation"""

    def __init__(self, ip: str = "127.0.0.1", scan_rate: int = 1000, point_delay: float = 0.0):
        self.ip = ip
        self.port = 7200
        self.scan_period = max(1, min(4294967295, int(1000000/int(scan_rate))))
        self.point_delay = point_delay
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.connected = False
        self.error_count = 0
        self.packets_sent = 0
        self.bytes_sent = 0
        self.last_error = None
        self._setup_connection()

    def _setup_connection(self):
        """Send initial scan period setup packet"""
        try:
            self.sock.sendto(struct.pack(">B I", IW_TYPE_1, self.scan_period), (self.ip, self.port))
            self.connected = True
            self.last_error = None
        except Exception as e:
            self.last_error = str(e)
            self.connected = False

    @staticmethod
    def _u16(x: int) -> int:
        return x & 0xFFFF

    @staticmethod
    def _to_u16_from_u8(c: int) -> int:
        return (c & 0xFF) * 257

    def _transform_xy(self, x: int, y: int) -> Tuple[int, int]:
        xn = (x + 0x8000)
        yn = (-y + 0x8000)
        return self._u16(xn), self._u16(yn)

    def send_frame(self, points: List[Tuple[int, int, int, int, int, int, int]]):
        """Send frame using the exact same method as iwp-ilda.py"""
        if not self.connected:
            return False

        try:
            max_packet_size = 1023
            point_size = struct.calcsize(">B H H H H H")  # 11 bytes
            max_points_per_packet = max_packet_size // point_size

            samples = []
            for (x, y, _z, status, r8, g8, b8) in points:
                blanked = (status & STATUS_BLANKED_MASK) != 0

                x16, y16 = self._transform_xy(x, y)
                if blanked:
                    r16 = g16 = b16 = 0
                else:
                    r16 = self._to_u16_from_u8(r8)
                    g16 = self._to_u16_from_u8(g8)
                    b16 = self._to_u16_from_u8(b8)

                samples.append(struct.pack(
                    ">B H H H H H",
                    IW_TYPE_3,
                    x16, y16, r16, g16, b16
                ))

            # Chunk into packets
            for i in range(0, len(samples), max_points_per_packet):
                chunk = b"".join(samples[i:i + max_points_per_packet])
                if chunk:
                    self.sock.sendto(chunk, (self.ip, self.port))
                    self.bytes_sent += len(chunk)
                    if self.point_delay > 0:
                        time.sleep(self.point_delay)

            self.packets_sent += 1
            return True

        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            self.connected = False
            return False

    def connect(self) -> bool:
        """Establish UDP connection"""
        self._setup_connection()
        return self.connected

    def disconnect(self):
        """Close UDP connection"""
        if self.sock:
            try:
                # Send end frame
                end_packet = struct.pack(">B", IW_TYPE_0)
                self.sock.sendto(end_packet, (self.ip, self.port))
            except:
                pass
            finally:
                self.sock.close()
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.connected = False

    def set_target(self, ip: str, port: int = 7200):
        """Update target IP and port"""
        self.ip = ip
        self.port = port
        if self.connected:
            self.disconnect()

    def set_scan_rate(self, scan_rate: int):
        """Update scan rate"""
        self.scan_period = max(1, min(4294967295, int(1000000/int(scan_rate))))
        if self.connected:
            try:
                setup_packet = struct.pack(">B I", IW_TYPE_1, self.scan_period)
                self.sock.sendto(setup_packet, (self.ip, self.port))
            except:
                pass

    def set_point_delay(self, point_delay: float):
        """Set point delay for frame rate control"""
        self.point_delay = max(0.0, point_delay)

    def set_fps_delay(self, fps: float):
        """Set delay based on FPS like iwp-ilda.py"""
        if fps > 0:
            self.point_delay = 1.0 / fps
        else:
            self.point_delay = 0.0

    def get_stats(self) -> dict:
        """Get transmission statistics"""
        return {
            'connected': self.connected,
            'target_ip': self.ip,
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
        self.sender = ProjectorSender()
        self.current_frame_points = None
        self.current_packet = None
        self.transmission_enabled = False

    def load_file(self, filename: str) -> bool:
        """Load an ILDA file"""
        if self.loader.load_file(filename):
            self.player = ILDAPlayer(self.loader)  # Reset player
            self.current_frame_points = None  # Reset frame cache to force update
            self.current_packet = None  # Reset packet cache
            print(f"Loaded ILDA file: {filename}")
            print(f"  Frames: {self.loader.get_frame_count()}")
            if self.loader.frames:
                first_frame = self.loader.frames[0]
                print(f"  Points per frame: {len(first_frame.points)}")
                print(f"  Format: {first_frame.format}")
            return True
        return False

    def update(self) -> Optional[IWPPacket]:
        """Update and get current IWP packet for compatibility"""
        frame_changed = self.player.update()

        if frame_changed or self.current_frame_points is None:
            current_frame = self.player.get_current_frame()
            if current_frame:
                self.current_frame_points = self.converter.convert_frame_to_points(current_frame)

                # Send over network if transmission is enabled
                if self.transmission_enabled and self.current_frame_points:
                    self.sender.send_frame(self.current_frame_points)

                # Create IWP packet for compatibility with main program
                self.current_packet = self._create_iwp_packet_from_points(self.current_frame_points)
                return self.current_packet

        return self.current_packet

    def _create_iwp_packet_from_points(self, points: List[Tuple[int, int, int, int, int, int, int]]) -> IWPPacket:
        """Create IWP packet from point data for main program compatibility"""
        try:
            from iwp_protocol import IWPPoint
        except ImportError:
            from .iwp_protocol import IWPPoint

        iwp_points = []
        for x, y, z, status, r, g, b in points:
            blanking = bool(status & STATUS_BLANKED_MASK)
            iwp_point = IWPPoint(
                x=x,  # Keep original ILDA coordinates
                y=y,  # Keep original ILDA coordinates
                r=r,  # Keep original color values
                g=g,
                b=b,
                blanking=blanking
            )
            iwp_points.append(iwp_point)

        return IWPPacket(
            points=iwp_points,
            commands=[],
            point_count=len(iwp_points),
            scan_period=None,
            timestamp=int(time.time() * 1000000),
            raw_size=len(iwp_points) * 11
        )

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

    def get_sender(self) -> ProjectorSender:
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
                points = system.update()
                if points:
                    status = system.get_status()
                    print(f"Frame {status['current_frame']}/{status['total_frames']} - {len(points)} points")
                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\\nStopped.")
    else:
        print(f"Failed to load {filename}")

if __name__ == "__main__":
    main()