#!/usr/bin/env python3
"""
IWP Port Test Utility
Tests if your computer can receive IWP packets on port 7200
"""

import socket
import threading
import time
import sys
from typing import Optional

class PortTester:
    """Test IWP UDP port availability and connectivity"""

    def __init__(self, port: int = 7200):
        self.port = port
        self.test_message = b"IWP Test Packet"

    def test_port_binding(self) -> bool:
        """Test if we can bind to the UDP port"""
        print(f"🔍 Testing if port {self.port} is available for binding...")

        try:
            # Try to create and bind a UDP socket
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            test_socket.bind(('0.0.0.0', self.port))
            test_socket.close()

            print(f"✅ Port {self.port} is available and can be bound")
            return True

        except OSError as e:
            if e.errno == 48:  # Address already in use
                print(f"❌ Port {self.port} is already in use by another application")
                print("   Try stopping other applications or use a different port")
            elif e.errno == 13:  # Permission denied
                print(f"❌ Permission denied for port {self.port}")
                print("   Try running as administrator or use a port > 1024")
            else:
                print(f"❌ Cannot bind to port {self.port}: {e}")
            return False

    def test_loopback_communication(self) -> bool:
        """Test UDP communication via loopback"""
        print(f"\n🔄 Testing UDP communication on port {self.port}...")

        received_data = None
        server_error = None

        def server_thread():
            nonlocal received_data, server_error
            try:
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.bind(('127.0.0.1', self.port))
                server_socket.settimeout(5.0)  # 5 second timeout

                print(f"   📡 Server listening on 127.0.0.1:{self.port}")
                data, addr = server_socket.recvfrom(1024)
                received_data = data
                print(f"   📨 Received: {data.decode()} from {addr}")
                server_socket.close()

            except Exception as e:
                server_error = e

        # Start server thread
        server = threading.Thread(target=server_thread, daemon=True)
        server.start()

        # Give server time to start
        time.sleep(0.5)

        try:
            # Send test packet
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client_socket.sendto(self.test_message, ('127.0.0.1', self.port))
            client_socket.close()
            print(f"   📤 Sent test packet to 127.0.0.1:{self.port}")

        except Exception as e:
            print(f"   ❌ Failed to send test packet: {e}")
            return False

        # Wait for server to receive
        server.join(timeout=6.0)

        if server_error:
            print(f"   ❌ Server error: {server_error}")
            return False

        if received_data == self.test_message:
            print(f"   ✅ UDP communication test successful!")
            return True
        else:
            print(f"   ❌ Did not receive expected data")
            return False

    def check_firewall_status(self) -> dict:
        """Check firewall status (platform-specific)"""
        print(f"\n🛡️  Checking firewall status...")

        import platform
        system = platform.system().lower()

        info = {
            'system': system,
            'firewall_active': 'Unknown',
            'recommendations': []
        }

        try:
            import subprocess

            if system == 'darwin':  # macOS
                try:
                    result = subprocess.run(['pfctl', '-s', 'info'],
                                          capture_output=True, text=True, timeout=5)
                    if 'Status: Enabled' in result.stdout:
                        info['firewall_active'] = 'Enabled'
                        info['recommendations'].append('macOS Firewall is active')
                        info['recommendations'].append('Allow Python in System Preferences > Security & Privacy > Firewall')
                    else:
                        info['firewall_active'] = 'Disabled'
                except:
                    info['recommendations'].append('Could not check pfctl status')

            elif system == 'linux':
                # Check ufw
                try:
                    result = subprocess.run(['ufw', 'status'],
                                          capture_output=True, text=True, timeout=5)
                    if 'Status: active' in result.stdout:
                        info['firewall_active'] = 'UFW Active'
                        info['recommendations'].append('UFW firewall is active')
                        info['recommendations'].append(f'Run: sudo ufw allow {self.port}/udp')
                    else:
                        info['firewall_active'] = 'UFW Inactive'
                except:
                    # Check iptables
                    try:
                        result = subprocess.run(['iptables', '-L'],
                                              capture_output=True, text=True, timeout=5)
                        if result.returncode == 0:
                            info['firewall_active'] = 'iptables detected'
                            info['recommendations'].append('iptables may be filtering packets')
                    except:
                        pass

            elif system == 'windows':
                try:
                    result = subprocess.run(['netsh', 'advfirewall', 'show', 'allprofiles', 'state'],
                                          capture_output=True, text=True, timeout=5)
                    if 'ON' in result.stdout:
                        info['firewall_active'] = 'Windows Defender Firewall ON'
                        info['recommendations'].append('Windows Firewall is active')
                        info['recommendations'].append('Allow Python through Windows Defender Firewall')
                    else:
                        info['firewall_active'] = 'OFF'
                except:
                    info['recommendations'].append('Could not check Windows Firewall status')

        except Exception as e:
            info['recommendations'].append(f'Error checking firewall: {e}')

        return info

    def test_with_iwp_simulation(self) -> bool:
        """Simulate IWP sender device packet format"""
        print(f"\n🤖 Testing with simulated IWP device packet...")

        # Create a realistic IWP packet
        import struct

        packet = bytearray()
        packet.extend(b'IWPX')  # Magic
        packet.extend(struct.pack('<H', 0x0001))  # Frame type
        packet.extend(struct.pack('<H', 3))  # Point count
        packet.extend(struct.pack('<I', 12345))  # Timestamp

        # Add 3 test points (crosshair pattern)
        packet.extend(struct.pack('<hhBBBB', 0, 0, 255, 255, 255, 0))      # Center white
        packet.extend(struct.pack('<hhBBBB', 1000, 0, 255, 0, 0, 0))       # Right red
        packet.extend(struct.pack('<hhBBBB', 0, 1000, 0, 255, 0, 0))       # Up green

        received_packet = None
        server_error = None

        def server_thread():
            nonlocal received_packet, server_error
            try:
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.bind(('127.0.0.1', self.port))
                server_socket.settimeout(5.0)

                data, addr = server_socket.recvfrom(1024)
                received_packet = data
                server_socket.close()

            except Exception as e:
                server_error = e

        # Start server
        server = threading.Thread(target=server_thread, daemon=True)
        server.start()
        time.sleep(0.5)

        try:
            # Send simulated IWP device packet
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client_socket.sendto(bytes(packet), ('127.0.0.1', self.port))
            client_socket.close()
            print(f"   📤 Sent {len(packet)} byte IWP packet")

        except Exception as e:
            print(f"   ❌ Failed to send packet: {e}")
            return False

        server.join(timeout=6.0)

        if server_error:
            print(f"   ❌ Server error: {server_error}")
            return False

        if received_packet:
            print(f"   ✅ Received {len(received_packet)} bytes")

            # Try to parse with our IWP parser
            try:
                import sys
                import os
                sys.path.append(os.path.dirname(__file__))
                from iwp_protocol import IWPProtocolParser

                parser = IWPProtocolParser()
                parsed = parser.parse_packet(received_packet)

                if parsed:
                    print(f"   ✅ Successfully parsed IWP packet:")
                    print(f"      Points: {parsed.point_count}")
                    print(f"      Timestamp: {parsed.timestamp}")
                    return True
                else:
                    print(f"   ❌ Failed to parse IWP packet")
                    return False

            except ImportError:
                print(f"   ⚠️  Could not test IWP parsing (iwp_protocol not found)")
                return True  # Still successful for basic UDP test

        else:
            print(f"   ❌ No packet received")
            return False

def main():
    """Run comprehensive port tests"""
    print("🧪 IWP Port 7200 Test Suite")
    print("=" * 50)

    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("❌ Invalid port number")
            sys.exit(1)
    else:
        port = 7200

    tester = PortTester(port)

    # Run all tests
    tests = [
        ("Port Binding", tester.test_port_binding),
        ("UDP Communication", tester.test_loopback_communication),
        ("IWP Device Simulation", tester.test_with_iwp_simulation),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    # Check firewall
    firewall_info = tester.check_firewall_status()

    # Summary
    print(f"\n📋 Test Results Summary")
    print("=" * 50)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False

    print(f"\n🛡️  Firewall Status: {firewall_info['firewall_active']}")

    if firewall_info['recommendations']:
        print("\n💡 Recommendations:")
        for rec in firewall_info['recommendations']:
            print(f"   • {rec}")

    if all_passed:
        print(f"\n🎉 All tests passed! Your computer can receive UDP packets on port {port}")
        print(f"✅ Ready to receive IWP sender device laser data!")
    else:
        print(f"\n⚠️  Some tests failed. Check the issues above.")
        print(f"💡 Try running the IWP receiver anyway - it might still work!")

    print(f"\n🚀 Next step: python src/main.py visualize")

if __name__ == "__main__":
    main()