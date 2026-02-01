#!/usr/bin/env python3
"""
UDP Server for receiving IWP (ILDA Wave Protocol) packets
server implementation for real-time laser pattern streaming
"""

import socket
import threading
import time
import logging
from typing import Callable, Optional, Dict, Set, Any
from queue import Queue, Empty
try:
    from iwp_protocol import IWPProtocolParser, IWPPacket
except ImportError:
    from .iwp_protocol import IWPProtocolParser, IWPPacket

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UDPServer:
    """UDP server for receiving IWP (ILDA Wave Protocol) packets"""

    def __init__(self, port: int = 7200, bind_address: str = '0.0.0.0') -> None:
        """
        Initialize UDP server for IWP packet reception

        Args:
            port: UDP port to bind to (default: 7200)
            bind_address: IP address to bind to (default: '0.0.0.0')
        """
        self.port = port
        self.bind_address = bind_address
        self.socket: Optional[socket.socket] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.parser = IWPProtocolParser()
        self.packet_queue: Queue = Queue(maxsize=100)
        self.packet_callback: Optional[Callable[[IWPPacket, str], None]] = None
        self.error_callback: Optional[Callable[[Exception], None]] = None

        # Statistics
        self.bytes_received = 0
        self.connections_detected: Set[str] = set()
        self.last_packet_time = 0.0
        self.start_time = 0.0

    def set_packet_callback(self, callback: Callable[[IWPPacket, str], None]) -> None:
        """Set callback function to call when valid packet is received"""
        self.packet_callback = callback

    def set_error_callback(self, callback: Callable[[Exception], None]) -> None:
        """Set callback function to call when errors occur"""
        self.error_callback = callback

    def start(self) -> bool:
        """
        Start the UDP server in a separate thread

        Returns:
            bool: True if server started successfully, False otherwise
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.bind_address, self.port))
            self.socket.settimeout(1.0)  # 1 second timeout for clean shutdown

            self.running = True
            self.start_time = time.time()
            self.thread = threading.Thread(target=self._server_loop, daemon=True)
            self.thread.start()

            logger.info(f"IWP UDP Server listening on {self.bind_address}:{self.port}")
            return True

        except Exception as e:
            logger.error(f"Failed to start UDP server: {e}")
            if self.error_callback:
                self.error_callback(e)
            return False

    def stop(self) -> None:
        """Stop the UDP server gracefully"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                logger.warning(f"Error closing socket: {e}")
        logger.info("IWP UDP Server stopped")

    def _server_loop(self) -> None:
        """Main server loop running in separate thread"""
        logger.debug("IWP UDP server thread started")

        while self.running:
            try:
                # Receive UDP packet
                data, addr = self.socket.recvfrom(1024)  # Max packet size
                self.bytes_received += len(data)
                self.last_packet_time = time.time()

                # Track unique connections
                client_address = f"{addr[0]}:{addr[1]}"
                if client_address not in self.connections_detected:
                    self.connections_detected.add(client_address)
                    logger.info(f"New IWP device connection detected from: {client_address}")

                # Parse the packet
                packet = self.parser.parse_packet(data)
                if packet:
                    # Add to queue (drop old packets if full)
                    try:
                        self.packet_queue.put_nowait((packet, client_address))
                    except:
                        # Queue full, drop oldest packet
                        try:
                            self.packet_queue.get_nowait()
                            self.packet_queue.put_nowait((packet, client_address))
                        except Empty:
                            pass

                    # Call callback if set
                    if self.packet_callback:
                        self.packet_callback(packet, client_address)

            except socket.timeout:
                # Timeout is expected for clean shutdown
                continue
            except Exception as e:
                if self.running:  # Only report errors if we're supposed to be running
                    if self.error_callback:
                        self.error_callback(e)
                    else:
                        logger.error(f"UDP server error: {e}")

        logger.debug("IWP UDP server thread stopped")

    def get_latest_packet(self) -> Optional[tuple]:
        """Get the most recent packet from the queue (non-blocking)"""
        try:
            return self.packet_queue.get_nowait()
        except Empty:
            return None

    def get_all_packets(self) -> list:
        """Get all packets from the queue and clear it"""
        packets = []
        while True:
            try:
                packets.append(self.packet_queue.get_nowait())
            except Empty:
                break
        return packets

    def is_connected(self) -> bool:
        """Check if we've received packets recently (within last 5 seconds)"""
        return (time.time() - self.last_packet_time) < 5.0 if self.last_packet_time > 0 else False

    def get_statistics(self) -> Dict[str, Any]:
        """Get server and parser statistics"""
        uptime = time.time() - self.start_time if self.start_time > 0 else 0
        parser_stats = self.parser.get_statistics()

        return {
            'uptime_seconds': uptime,
            'bytes_received': self.bytes_received,
            'connections_detected': len(self.connections_detected),
            'connection_list': list(self.connections_detected),
            'packets_in_queue': self.packet_queue.qsize(),
            'last_packet_ago': time.time() - self.last_packet_time if self.last_packet_time > 0 else None,
            'is_connected': self.is_connected(),
            **parser_stats
        }

    def print_status(self):
        """Print current server status"""
        stats = self.get_statistics()
        print("\n=== UDP Server Status ===")
        print(f"Running: {self.running}")
        print(f"Address: {self.bind_address}:{self.port}")
        print(f"Uptime: {stats['uptime_seconds']:.1f}s")
        print(f"Bytes received: {stats['bytes_received']:,}")
        print(f"Connections: {stats['connections_detected']}")
        print(f"Connected now: {stats['is_connected']}")
        if stats['last_packet_ago'] is not None:
            print(f"Last packet: {stats['last_packet_ago']:.1f}s ago")
        print(f"Queue size: {stats['packets_in_queue']}")
        print(f"Valid packets: {stats['packets_valid']}/{stats['packets_received']} ({stats['success_rate']:.1f}%)")
        if stats['connection_list']:
            print(f"IWP devices: {', '.join(stats['connection_list'])}")
        print("========================")


def main():
    """Test the UDP server"""
    def on_packet_received(packet: IWPPacket, address: str):
        print(f"\nReceived from {address}:")
        print(f"  Timestamp: {packet.timestamp}")
        print(f"  Points: {packet.point_count}")
        for i, point in enumerate(packet.points[:3]):  # Show first 3 points
            status = "BLANKED" if point.blanking else "VISIBLE"
            print(f"    {i}: ({point.x:6d}, {point.y:6d}) RGB({point.r:3d}, {point.g:3d}, {point.b:3d}) {status}")
        if packet.point_count > 3:
            print(f"    ... and {packet.point_count - 3} more points")

    def on_error(error: Exception):
        print(f"Server error: {error}")

    # Create and start server
    server = UDPServer(port=7200)
    server.set_packet_callback(on_packet_received)
    server.set_error_callback(on_error)

    if not server.start():
        return

    try:
        print("\nUDP Server running. Waiting for IWP packets...")
        print("Press Ctrl+C to stop")

        # Status update loop
        while True:
            time.sleep(5)
            server.print_status()

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.stop()


if __name__ == "__main__":
    main()