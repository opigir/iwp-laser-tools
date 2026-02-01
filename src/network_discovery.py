#!/usr/bin/env python3
"""
Network Discovery for IWP Laser Visualizer
Auto-discovers computer's IP address for IWP device configuration
"""

import socket
import subprocess
import platform
import ipaddress
from typing import List, Dict, Optional

class NetworkDiscovery:
    """Discover network interfaces and provide IWP device configuration guidance"""

    def __init__(self):
        self.system = platform.system().lower()

    def get_local_ip_addresses(self) -> List[Dict[str, str]]:
        """Get all local IP addresses and interface information"""
        interfaces = []

        try:
            # Get hostname and resolve all IPs
            hostname = socket.gethostname()

            # Method 1: Use socket.getaddrinfo for reliable detection
            for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
                ip = info[4][0]
                if not ip.startswith('127.'):
                    interfaces.append({
                        'interface': 'hostname_resolve',
                        'ip': ip,
                        'type': 'IPv4',
                        'status': 'active',
                        'description': f'Resolved from hostname: {hostname}'
                    })

        except Exception as e:
            pass

        # Method 2: Connect to external address to find default route IP
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                # Connect to Google DNS (doesn't actually send data)
                s.connect(('8.8.8.8', 80))
                default_ip = s.getsockname()[0]
                interfaces.append({
                    'interface': 'default_route',
                    'ip': default_ip,
                    'type': 'IPv4',
                    'status': 'active',
                    'description': 'Default route interface (recommended for IWP sender)'
                })
        except Exception as e:
            pass

        # Method 3: Platform-specific interface detection
        platform_interfaces = self._get_platform_interfaces()
        interfaces.extend(platform_interfaces)

        # Remove duplicates while preserving order
        seen_ips = set()
        unique_interfaces = []
        for iface in interfaces:
            if iface['ip'] not in seen_ips and not iface['ip'].startswith('127.'):
                seen_ips.add(iface['ip'])
                unique_interfaces.append(iface)

        return unique_interfaces

    def _get_platform_interfaces(self) -> List[Dict[str, str]]:
        """Get network interfaces using platform-specific commands"""
        interfaces = []

        try:
            if self.system == 'windows':
                interfaces = self._get_windows_interfaces()
            elif self.system == 'darwin':  # macOS
                interfaces = self._get_macos_interfaces()
            elif self.system == 'linux':
                interfaces = self._get_linux_interfaces()
        except Exception as e:
            print(f"Warning: Could not get platform-specific interfaces: {e}")

        return interfaces

    def _get_windows_interfaces(self) -> List[Dict[str, str]]:
        """Get Windows network interfaces using ipconfig"""
        interfaces = []

        try:
            result = subprocess.run(['ipconfig'], capture_output=True, text=True)
            lines = result.stdout.split('\n')

            current_adapter = None
            for line in lines:
                line = line.strip()
                if 'adapter' in line.lower() and ':' in line:
                    current_adapter = line.split(':')[0].strip()
                elif 'IPv4 Address' in line and current_adapter:
                    ip = line.split(':')[-1].strip()
                    if self._is_valid_ip(ip):
                        interfaces.append({
                            'interface': current_adapter,
                            'ip': ip,
                            'type': 'IPv4',
                            'status': 'active',
                            'description': f'Windows adapter: {current_adapter}'
                        })
        except Exception as e:
            pass

        return interfaces

    def _get_macos_interfaces(self) -> List[Dict[str, str]]:
        """Get macOS network interfaces using ifconfig"""
        interfaces = []

        try:
            result = subprocess.run(['ifconfig'], capture_output=True, text=True)
            lines = result.stdout.split('\n')

            current_interface = None
            for line in lines:
                if line and not line.startswith(' ') and not line.startswith('\t'):
                    # New interface
                    current_interface = line.split(':')[0]
                elif 'inet ' in line and current_interface:
                    # IPv4 address line
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'inet' and i + 1 < len(parts):
                            ip = parts[i + 1]
                            if self._is_valid_ip(ip) and not ip.startswith('127.'):
                                # Determine interface type
                                iface_type = self._classify_interface(current_interface)
                                interfaces.append({
                                    'interface': current_interface,
                                    'ip': ip,
                                    'type': 'IPv4',
                                    'status': 'active',
                                    'description': f'macOS {iface_type}: {current_interface}'
                                })
                            break
        except Exception as e:
            pass

        return interfaces

    def _get_linux_interfaces(self) -> List[Dict[str, str]]:
        """Get Linux network interfaces using ip command"""
        interfaces = []

        try:
            # Try 'ip addr' first (modern Linux)
            result = subprocess.run(['ip', 'addr'], capture_output=True, text=True)
            lines = result.stdout.split('\n')

            current_interface = None
            for line in lines:
                if ':' in line and not line.startswith(' '):
                    # New interface line
                    parts = line.split()
                    if len(parts) >= 2:
                        current_interface = parts[1].rstrip(':')
                elif 'inet ' in line and current_interface:
                    # IPv4 address line
                    parts = line.strip().split()
                    for i, part in enumerate(parts):
                        if part == 'inet' and i + 1 < len(parts):
                            ip_cidr = parts[i + 1]
                            ip = ip_cidr.split('/')[0]
                            if self._is_valid_ip(ip) and not ip.startswith('127.'):
                                iface_type = self._classify_interface(current_interface)
                                interfaces.append({
                                    'interface': current_interface,
                                    'ip': ip,
                                    'type': 'IPv4',
                                    'status': 'active',
                                    'description': f'Linux {iface_type}: {current_interface}'
                                })
                            break
        except:
            # Fallback to ifconfig on older systems
            try:
                result = subprocess.run(['ifconfig'], capture_output=True, text=True)
                # Parse ifconfig output (similar to macOS)
                interfaces = self._parse_ifconfig_linux(result.stdout)
            except:
                pass

        return interfaces

    def _parse_ifconfig_linux(self, output: str) -> List[Dict[str, str]]:
        """Parse ifconfig output for Linux"""
        interfaces = []
        lines = output.split('\n')

        current_interface = None
        for line in lines:
            if line and not line.startswith(' '):
                current_interface = line.split(':')[0]
            elif 'inet ' in line and current_interface:
                # Look for inet addr:
                if 'addr:' in line:
                    ip = line.split('addr:')[1].split()[0]
                else:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'inet' and i + 1 < len(parts):
                            ip = parts[i + 1]
                            break
                    else:
                        continue

                if self._is_valid_ip(ip) and not ip.startswith('127.'):
                    iface_type = self._classify_interface(current_interface)
                    interfaces.append({
                        'interface': current_interface,
                        'ip': ip,
                        'type': 'IPv4',
                        'status': 'active',
                        'description': f'Linux {iface_type}: {current_interface}'
                    })

        return interfaces

    def _classify_interface(self, interface_name: str) -> str:
        """Classify network interface by name"""
        name_lower = interface_name.lower()

        if 'wifi' in name_lower or 'wlan' in name_lower or 'wireless' in name_lower:
            return 'WiFi'
        elif 'eth' in name_lower or 'ethernet' in name_lower:
            return 'Ethernet'
        elif 'en' in name_lower:
            return 'Network'
        elif 'ww' in name_lower or 'cellular' in name_lower:
            return 'Cellular'
        elif 'docker' in name_lower:
            return 'Docker'
        elif 'vm' in name_lower or 'virtual' in name_lower:
            return 'Virtual'
        else:
            return 'Unknown'

    def _is_valid_ip(self, ip_str: str) -> bool:
        """Check if string is a valid IPv4 address"""
        try:
            ipaddress.IPv4Address(ip_str)
            return True
        except ipaddress.AddressValueError:
            return False

    def get_recommended_ip(self) -> Optional[str]:
        """Get the recommended IP address for IWP sender device configuration"""
        interfaces = self.get_local_ip_addresses()

        # Priority order for recommendation
        priorities = ['default_route', 'wifi', 'network', 'ethernet']

        for priority in priorities:
            for iface in interfaces:
                if priority in iface['description'].lower():
                    return iface['ip']

        # Fallback to first available IP
        return interfaces[0]['ip'] if interfaces else None

    def generate_device_config(self, target_ip: str) -> str:
        """Generate IWP sender device configuration snippet"""
        config = f"""
// IWP Sender Device Configuration for Python IWP Receiver
// Add this to your device configuration:

#define TARGET_IP "{target_ip}"
#define TARGET_PORT 7200

// Or update via web interface at: http://<DEVICE_IP>/
// Set Target IP to: {target_ip}
// Set Target Port to: 7200

// Make sure both devices are on the same WiFi network!
"""
        return config

    def print_discovery_results(self):
        """Print formatted discovery results"""
        print("\n" + "="*60)
        print("    NETWORK DISCOVERY FOR IWP SENDER CONFIGURATION")
        print("="*60)

        interfaces = self.get_local_ip_addresses()
        recommended_ip = self.get_recommended_ip()

        if not interfaces:
            print("\n❌ No network interfaces found!")
            print("   Make sure your computer is connected to WiFi.")
            return

        print(f"\n📡 Found {len(interfaces)} network interface(s):")
        print("-" * 60)

        for i, iface in enumerate(interfaces, 1):
            marker = "⭐ RECOMMENDED" if iface['ip'] == recommended_ip else "  "
            print(f"{marker} {i}. {iface['ip']}")
            print(f"      Interface: {iface['interface']}")
            print(f"      Type: {iface['description']}")
            print()

        if recommended_ip:
            print("🎯 CONFIGURATION FOR IWP SENDER DEVICE:")
            print("-" * 60)
            print(f"Target IP: {recommended_ip}")
            print(f"Target Port: 7200")
            print()
            print("📋 Copy this IP address and configure your IWP sender device:")
            print(f"   1. Connect sender device to the same WiFi network")
            print(f"   2. Open web interface: http://<DEVICE_IP>/")
            print(f"   3. Set Target IP to: {recommended_ip}")
            print(f"   4. Set Target Port to: 7200")
            print(f"   5. Click 'Update Configuration'")

            print("\n🔧 Alternative - Update device configuration:")
            print(self.generate_device_config(recommended_ip))

        print("="*60)


def main():
    """Test the network discovery"""
    discovery = NetworkDiscovery()
    discovery.print_discovery_results()

    print("\n💡 Next steps:")
    print("   1. Note the recommended IP address above")
    print("   2. Configure your IWP sender device with this IP")
    print("   3. Run: python udp_server.py")
    print("   4. Run: python laser_visualizer.py")
    print("   5. Power on your device and watch the magic! ✨")


if __name__ == "__main__":
    main()