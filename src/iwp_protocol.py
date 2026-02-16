#!/usr/bin/env python3
"""
IWP (ILDA Wave Protocol) Parser - Professional Implementation
Supports all IWP command types for real-time laser pattern streaming
Based on IWPServer.cpp and iwp-ilda.py specifications
"""

import struct
from dataclasses import dataclass
from typing import List, Optional, Tuple

# IWP Protocol constants (from IWPServer.h)
IW_TYPE_0 = 0x00  # Turn off
IW_TYPE_1 = 0x01  # Period (32-bit)
IW_TYPE_2 = 0x02  # 16-bit X/Y + 8-bit R/G/B
IW_TYPE_3 = 0x03  # 16-bit X/Y + 16-bit R/G/B

# Status bit flags (from ILDA spec)
STATUS_BLANKING_BIT = 0x40  # Bit 6 = blanking (1 means laser off)

@dataclass
class IWPPoint:
    """Single laser point from IWP commands"""
    x: int           # X coordinate (0-65535)
    y: int           # Y coordinate (0-65535)
    r: int           # Red (0-65535 for TYPE_3, 0-255 for TYPE_2)
    g: int           # Green (0-65535 for TYPE_3, 0-255 for TYPE_2)
    b: int           # Blue (0-65535 for TYPE_3, 0-255 for TYPE_2)
    blanking: bool   # True = laser off, False = laser on

@dataclass
class IWPCommand:
    """Single IWP command"""
    cmd_type: int
    data: any

@dataclass
class IWPPacket:
    """Parsed IWP packet from raw UDP stream"""
    points: List[IWPPoint]
    commands: List[IWPCommand]
    point_count: int
    scan_period: Optional[int]  # From TYPE_1 commands
    timestamp: float  # Receive timestamp
    raw_size: int

class IWPProtocolParser:
    """Professional parser for raw IWP (ILDA Wave Protocol) commands"""

    def __init__(self):
        self.packets_received = 0
        self.packets_valid = 0
        self.packets_invalid = 0

    def parse_packet(self, data: bytes) -> Optional[IWPPacket]:
        """
        Parse incoming UDP packet with raw IWP commands

        Supports IWP command types from IWPServer.h:
        - TYPE_0 (0x00): Turn off (1 byte)
        - TYPE_1 (0x01): Period (1 + 4 bytes, big-endian)
        - TYPE_2 (0x02): 16b X/Y + 8b R/G/B (8 bytes, big-endian)
        - TYPE_3 (0x03): 16b X/Y + 16b R/G/B (11 bytes, big-endian)
        """
        import time
        self.packets_received += 1

        if len(data) == 0:
            self.packets_invalid += 1
            return None

        points = []
        commands = []
        scan_period = None
        offset = 0

        try:
            while offset < len(data):
                if offset >= len(data):
                    break

                cmd_type = data[offset]

                if cmd_type == IW_TYPE_0:
                    # TYPE_0: Turn off (1 byte)
                    commands.append(IWPCommand(cmd_type=IW_TYPE_0, data=None))
                    offset += 1

                elif cmd_type == IW_TYPE_1:
                    # TYPE_1: Period (1 + 4 bytes, big-endian)
                    if offset + 5 > len(data):
                        break
                    period_bytes = data[offset + 1:offset + 5]
                    period = struct.unpack('>I', period_bytes)[0]  # Big-endian uint32
                    scan_period = period
                    commands.append(IWPCommand(cmd_type=IW_TYPE_1, data=period))
                    offset += 5

                elif cmd_type == IW_TYPE_2:
                    # TYPE_2: 16b X/Y + 8b R/G/B (8 bytes, big-endian)
                    if offset + 8 > len(data):
                        break
                    x, y, r, g, b = struct.unpack('>HHBBB', data[offset + 1:offset + 8])
                    points.append(IWPPoint(x=x, y=y, r=r, g=g, b=b, blanking=False))
                    commands.append(IWPCommand(cmd_type=IW_TYPE_2, data=(x, y, r, g, b)))
                    offset += 8

                elif cmd_type == IW_TYPE_3:
                    # TYPE_3: 16b X/Y + 16b R/G/B (11 bytes, big-endian)
                    if offset + 11 > len(data):
                        break
                    x, y, r, g, b = struct.unpack('>HHHHH', data[offset + 1:offset + 11])
                    # Check for blanking (all colors zero indicates blanked point)
                    blanking = (r == 0 and g == 0 and b == 0)
                    points.append(IWPPoint(x=x, y=y, r=r, g=g, b=b, blanking=blanking))
                    commands.append(IWPCommand(cmd_type=IW_TYPE_3, data=(x, y, r, g, b)))
                    offset += 11

                else:
                    # Unknown command type, stop parsing
                    break

            self.packets_valid += 1

            return IWPPacket(
                points=points,
                commands=commands,
                point_count=len(points),
                scan_period=scan_period,
                timestamp=time.time(),
                raw_size=len(data)
            )

        except (struct.error, IndexError) as e:
            self.packets_invalid += 1
            return None

    def get_statistics(self) -> dict:
        """Get parser statistics"""
        return {
            'packets_received': self.packets_received,
            'packets_valid': self.packets_valid,
            'packets_invalid': self.packets_invalid,
            'success_rate': (self.packets_valid / max(1, self.packets_received)) * 100.0
        }

    def reset_statistics(self):
        """Reset packet statistics"""
        self.packets_received = 0
        self.packets_valid = 0
        self.packets_invalid = 0

def iwp_to_screen_coords(x: int, y: int, screen_width: int, screen_height: int) -> Tuple[int, int]:
    """
    Convert IWP coordinates (0 to 65535) to screen pixel coordinates
    IWP uses unsigned 16-bit coordinates from iwp-ilda.py transformation
    """
    # Map IWP range to screen coordinates
    screen_x = int(x * screen_width / 65536)
    screen_y = int(y * screen_height / 65536)

    # Clamp to screen bounds
    screen_x = max(0, min(screen_width - 1, screen_x))
    screen_y = max(0, min(screen_height - 1, screen_y))

    return screen_x, screen_y

def screen_to_iwp_coords(screen_x: int, screen_y: int, screen_width: int, screen_height: int) -> Tuple[int, int]:
    """
    Convert screen pixel coordinates back to IWP coordinates
    """
    x = int(screen_x * 65536 / screen_width)
    y = int(screen_y * 65536 / screen_height)

    # Clamp to IWP bounds
    x = max(0, min(65535, x))
    y = max(0, min(65535, y))

    return x, y

def ilda_to_screen_coords(x: int, y: int, screen_width: int, screen_height: int) -> Tuple[int, int]:
    """
    Convert ILDA coordinates (-32768 to 32767) to screen pixel coordinates
    Matches the coordinate transformation used in transmission for accurate preview
    """
    # Apply the same transformation as ProjectorSender._transform_xy():
    # xn = (x + 0x8000) and yn = (-y + 0x8000)
    # Match exactly what the working transmission does
    transformed_x = (x + 32768)   # Same as transmission: x + 0x8000
    transformed_y = (-y + 32768)  # Same as transmission: -y + 0x8000

    # Map transformed coordinates to screen coordinates
    screen_x = int(transformed_x * screen_width / 65536)
    screen_y = int(transformed_y * screen_height / 65536)

    # Clamp to screen bounds
    screen_x = max(0, min(screen_width - 1, screen_x))
    screen_y = max(0, min(screen_height - 1, screen_y))

    return screen_x, screen_y

def screen_to_ilda_coords(screen_x: int, screen_y: int, screen_width: int, screen_height: int) -> Tuple[int, int]:
    """
    Legacy function for backward compatibility
    Convert screen pixel coordinates back to ILDA coordinates
    """
    x = int((screen_x * 65536 / screen_width) - 32768)
    y = int((screen_y * 65536 / screen_height) - 32768)

    # Clamp to ILDA bounds
    x = max(-32768, min(32767, x))
    y = max(-32768, min(32767, y))

    return x, y

if __name__ == "__main__":
    # Test the parser with sample IWP commands
    parser = IWPProtocolParser()

    # Create test packet with IWP commands
    test_packet = bytearray()

    # Add TYPE_1 command (scan period)
    test_packet.append(IW_TYPE_1)
    test_packet.extend(struct.pack('>I', 1000))  # 1000 microseconds period

    # Add TYPE_3 command (16-bit coordinates + 16-bit colors)
    test_packet.append(IW_TYPE_3)
    test_packet.extend(struct.pack('>HHHHH', 32768, 32768, 65535, 0, 0))  # Red point at center

    # Add another TYPE_3 command (blanked point - all colors zero)
    test_packet.append(IW_TYPE_3)
    test_packet.extend(struct.pack('>HHHHH', 45000, 45000, 0, 0, 0))  # Blanked point

    # Add TYPE_2 command (8-bit colors)
    test_packet.append(IW_TYPE_2)
    test_packet.extend(struct.pack('>HHBBB', 16384, 49152, 0, 255, 0))  # Green point

    # Add TYPE_0 command (turn off)
    test_packet.append(IW_TYPE_0)

    # Parse the test packet
    result = parser.parse_packet(bytes(test_packet))

    if result:
        print(f"Parsed IWP packet successfully:")
        print(f"  Point count: {result.point_count}")
        print(f"  Commands: {len(result.commands)}")
        print(f"  Scan period: {result.scan_period}")
        print(f"  Timestamp: {result.timestamp}")
        print(f"  Raw size: {result.raw_size}")
        print(f"  Points:")
        for i, point in enumerate(result.points):
            status = "BLANKED" if point.blanking else "VISIBLE"
            print(f"    {i}: ({point.x:5d}, {point.y:5d}) RGB({point.r:5d}, {point.g:5d}, {point.b:5d}) {status}")

        print(f"  Commands:")
        for i, cmd in enumerate(result.commands):
            if cmd.cmd_type == IW_TYPE_0:
                print(f"    {i}: TYPE_0 (Turn off)")
            elif cmd.cmd_type == IW_TYPE_1:
                print(f"    {i}: TYPE_1 (Period: {cmd.data}µs)")
            elif cmd.cmd_type == IW_TYPE_2:
                print(f"    {i}: TYPE_2 (Point: {cmd.data})")
            elif cmd.cmd_type == IW_TYPE_3:
                print(f"    {i}: TYPE_3 (Point: {cmd.data})")

        print(f"\nStatistics: {parser.get_statistics()}")
    else:
        print("Failed to parse test packet")