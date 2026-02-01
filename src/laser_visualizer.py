#!/usr/bin/env python3
"""
IWP Laser Visualizer - Real-time ILDA Wave Protocol visualization
Professional tool for visualizing IWP laser patterns using pygame
"""

import pygame
import math
import time
import os
from typing import List, Tuple, Optional
from iwp_protocol import IWPPoint, IWPPacket, iwp_to_screen_coords, ilda_to_screen_coords
from udp_server import UDPServer
from ilda_integration import IntegratedILDASystem

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)

class LaserVisualizer:
    """Professional real-time IWP laser pattern visualizer using pygame"""

    @staticmethod
    def _convert_color_to_8bit(r: int, g: int, b: int) -> tuple:
        """Convert IWP colors (which can be 8-bit or 16-bit) to 8-bit pygame colors"""
        r8 = min(255, r >> 8) if r > 255 else r
        g8 = min(255, g >> 8) if g > 255 else g
        b8 = min(255, b >> 8) if b > 255 else b
        return (r8, g8, b8)

    def __init__(self, width: int = 800, height: int = 600, title: str = "IWP Laser Visualizer"):
        self.width = width
        self.height = height
        self.title = title

        # Pygame initialization
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)

        # Visualization state
        self.current_packet = None
        self.packet_history = []
        self.max_history = 10

        # Display options
        self.show_crosshair = True
        self.show_grid = True
        self.show_blanking = True
        self.show_points = True
        self.show_lines = True
        self.show_info = True
        self.trail_mode = False
        self.point_size = 2
        self.zoom_factor = 1.0
        self.pan_x = 0
        self.pan_y = 0

        # Statistics
        self.fps = 0
        self.packet_count = 0
        self.last_packet_time = 0

        # Pattern analysis
        self.pattern_type = "Unknown"

        # ILDA Integration
        self.ilda_system = IntegratedILDASystem()
        self.ilda_mode = False
        self.ilda_packet = None
        self.show_ilda_info = False
        self.ilda_file_path = ""
        self.show_file_browser = False
        self.file_browser_files = []
        self.file_browser_selected = 0
        self.file_browser_scroll = 0
        self.current_directory = os.getcwd()

        print(f"Laser visualizer initialized: {width}x{height}")

    def set_packet(self, packet: IWPPacket, source_address: str):
        """Update display with new packet data"""
        self.current_packet = packet
        self.packet_count += 1
        self.last_packet_time = time.time()

        # Add to history for trail mode
        if len(self.packet_history) >= self.max_history:
            self.packet_history.pop(0)
        self.packet_history.append(packet)

        # Analyze pattern type
        self._analyze_pattern(packet)

    def _analyze_pattern(self, packet: IWPPacket):
        """Analyze packet to determine pattern type"""
        if packet.point_count == 0:
            self.pattern_type = "Empty"
            return

        points = packet.points

        # Check for crosshair pattern (typically has perpendicular lines)
        if packet.point_count >= 4:
            # Look for horizontal and vertical lines
            has_horizontal = False
            has_vertical = False

            for i in range(len(points) - 1):
                p1, p2 = points[i], points[i + 1]
                if not p1.blanking and not p2.blanking:
                    dx = abs(p2.x - p1.x)
                    dy = abs(p2.y - p1.y)

                    if dx > dy * 3:  # Mostly horizontal
                        has_horizontal = True
                    elif dy > dx * 3:  # Mostly vertical
                        has_vertical = True

            if has_horizontal and has_vertical:
                self.pattern_type = "Crosshair"
            elif self._is_circle_pattern(points):
                self.pattern_type = "Level Circle"
            else:
                self.pattern_type = "Complex"
        else:
            self.pattern_type = "Simple"

    def _is_circle_pattern(self, points: List[IWPPoint]) -> bool:
        """Check if points form a rough circle"""
        if len(points) < 8:
            return False

        # Calculate center
        cx = sum(p.x for p in points) / len(points)
        cy = sum(p.y for p in points) / len(points)

        # Calculate distances from center
        distances = []
        for p in points:
            if not p.blanking:
                dist = math.sqrt((p.x - cx)**2 + (p.y - cy)**2)
                distances.append(dist)

        if len(distances) < 4:
            return False

        # Check if distances are roughly consistent (circle)
        avg_dist = sum(distances) / len(distances)
        variance = sum((d - avg_dist)**2 for d in distances) / len(distances)
        std_dev = math.sqrt(variance)

        # If standard deviation is less than 20% of average, it's likely a circle
        return std_dev < avg_dist * 0.2

    def _draw_grid(self):
        """Draw coordinate grid"""
        if not self.show_grid:
            return

        # Grid spacing (in screen pixels)
        grid_spacing = 50

        # Draw vertical lines
        for x in range(0, self.width, grid_spacing):
            pygame.draw.line(self.screen, DARK_GRAY, (x, 0), (x, self.height), 1)

        # Draw horizontal lines
        for y in range(0, self.height, grid_spacing):
            pygame.draw.line(self.screen, DARK_GRAY, (0, y), (self.width, y), 1)

        # Draw center lines
        cx = self.width // 2
        cy = self.height // 2
        pygame.draw.line(self.screen, GRAY, (cx, 0), (cx, self.height), 2)
        pygame.draw.line(self.screen, GRAY, (0, cy), (self.width, cy), 2)

    def _draw_crosshair(self):
        """Draw screen crosshair for reference"""
        if not self.show_crosshair:
            return

        cx = self.width // 2
        cy = self.height // 2
        size = 20

        # Draw crosshair
        pygame.draw.line(self.screen, WHITE, (cx - size, cy), (cx + size, cy), 1)
        pygame.draw.line(self.screen, WHITE, (cx, cy - size), (cx, cy + size), 1)

        # Draw center dot
        pygame.draw.circle(self.screen, WHITE, (cx, cy), 3, 1)

    def _draw_packet(self, packet: IWPPacket, alpha: int = 255):
        """Draw a single packet's points"""
        if packet.point_count == 0:
            return

        points = packet.points

        # Convert ILDA coordinates to screen coordinates
        screen_points = []
        for point in points:
            sx, sy = iwp_to_screen_coords(point.x, point.y, self.width, self.height)
            screen_points.append((sx, sy, point))

        # Draw lines between non-blanked points
        if self.show_lines and len(screen_points) > 1:
            line_points = []
            for sx, sy, point in screen_points:
                if not point.blanking:
                    line_points.append((sx, sy))
                else:
                    # Draw accumulated line points
                    if len(line_points) > 1:
                        color = self._convert_color_to_8bit(point.r, point.g, point.b)
                        if color == (0, 0, 0):
                            color = RED
                        if alpha < 255:
                            color = tuple(min(255, max(0, int(c * alpha / 255))) for c in color)

                        # Create surface for alpha blending
                        if alpha < 255:
                            surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                            pygame.draw.lines(surf, (*color, alpha), False, line_points, 2)
                            self.screen.blit(surf, (0, 0))
                        else:
                            pygame.draw.lines(self.screen, color, False, line_points, 2)
                    line_points = []

            # Draw remaining line points
            if len(line_points) > 1:
                color = RED if alpha == 255 else (min(255, int(255 * alpha / 255)), 0, 0)
                if alpha < 255:
                    surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                    pygame.draw.lines(surf, (*color, alpha), False, line_points, 2)
                    self.screen.blit(surf, (0, 0))
                else:
                    pygame.draw.lines(self.screen, color, False, line_points, 2)

        # Draw individual points
        if self.show_points:
            for sx, sy, point in screen_points:
                if point.blanking and not self.show_blanking:
                    continue

                # Point color (convert from 16-bit to 8-bit if needed)
                if point.blanking:
                    color = GRAY
                    size = max(1, self.point_size - 1)
                else:
                    color = self._convert_color_to_8bit(point.r, point.g, point.b)
                    if color == (0, 0, 0):
                        color = WHITE
                    size = self.point_size

                if alpha < 255:
                    color = tuple(min(255, max(0, int(c * alpha / 255))) for c in color)

                pygame.draw.circle(self.screen, color, (sx, sy), size)

    def _draw_info_panel(self):
        """Draw information panel"""
        if not self.show_info:
            return

        # Background for info panel
        info_rect = pygame.Rect(10, 10, 250, 150)
        pygame.draw.rect(self.screen, (0, 0, 0, 180), info_rect)
        pygame.draw.rect(self.screen, WHITE, info_rect, 1)

        y_offset = 25
        line_height = 18

        def draw_text(text: str, color=WHITE):
            nonlocal y_offset
            surface = self.small_font.render(text, True, color)
            self.screen.blit(surface, (15, y_offset))
            y_offset += line_height

        # Title
        title = "ILDA Visualizer" if self.ilda_mode else "IWP Laser Visualizer"
        draw_text(title, YELLOW)

        # Connection status
        time_since_packet = time.time() - self.last_packet_time if self.last_packet_time > 0 else 999
        connected = time_since_packet < 2.0

        status_color = GREEN if connected else RED
        status_text = "CONNECTED" if connected else "DISCONNECTED"
        draw_text(f"Status: {status_text}", status_color)

        # Current packet info
        if self.ilda_mode:
            status = self.ilda_system.get_status()
            if status['loaded']:
                draw_text(f"ILDA Frame: {status['current_frame']}/{status['total_frames']}")
                draw_text(f"Playing: {'Yes' if status['playing'] else 'No'}")
                draw_text(f"FPS: {status['fps']:.1f}")
                draw_text(f"Speed: {status['speed']:.1f}x")
                if self.ilda_packet:
                    draw_text(f"Points: {self.ilda_packet.point_count}")
            else:
                draw_text("No ILDA file loaded")
                draw_text("Press O to load file")
        elif self.current_packet:
            draw_text(f"Points: {self.current_packet.point_count}")
            draw_text(f"Pattern: {self.pattern_type}")
            draw_text(f"Timestamp: {self.current_packet.timestamp}")

        # Statistics
        draw_text(f"FPS: {self.fps:.1f}")
        draw_text(f"Packets: {self.packet_count}")

    def _draw_controls_help(self):
        """Draw controls help in bottom right"""
        base_controls = [
            "Controls:",
            "G - Toggle Grid",
            "C - Toggle Crosshair",
            "P - Toggle Points",
            "L - Toggle Lines",
            "B - Toggle Blanking",
            "I - Toggle Info",
            "T - Toggle Trail Mode",
            "+/- - Point Size",
            "S - Switch IWP/ILDA Mode",
            "ESC - Exit"
        ]

        ilda_controls = [
            "O - Open ILDA File",
            "SPACE - Play/Pause",
            "R - Restart",
            "N - Next Frame",
            "M - Previous Frame",
            "1/2 - Speed Up/Down"
        ]

        help_lines = base_controls
        if self.ilda_mode:
            help_lines.extend(ilda_controls)

        # Calculate position
        max_width = max(len(line) for line in help_lines) * 8
        x = self.width - max_width - 15
        y = self.height - len(help_lines) * 16 - 15

        # Background
        help_rect = pygame.Rect(x - 5, y - 5, max_width + 10, len(help_lines) * 16 + 10)
        pygame.draw.rect(self.screen, (0, 0, 0, 128), help_rect)
        pygame.draw.rect(self.screen, GRAY, help_rect, 1)

        # Draw text
        for i, line in enumerate(help_lines):
            color = YELLOW if i == 0 else WHITE
            surface = self.small_font.render(line, True, color)
            self.screen.blit(surface, (x, y + i * 16))

    def _handle_events(self) -> bool:
        """Handle pygame events. Returns False to quit."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_g:
                    self.show_grid = not self.show_grid
                elif event.key == pygame.K_c:
                    self.show_crosshair = not self.show_crosshair
                elif event.key == pygame.K_p:
                    self.show_points = not self.show_points
                elif event.key == pygame.K_l:
                    self.show_lines = not self.show_lines
                elif event.key == pygame.K_b:
                    self.show_blanking = not self.show_blanking
                elif event.key == pygame.K_i:
                    self.show_info = not self.show_info
                elif event.key == pygame.K_t:
                    self.trail_mode = not self.trail_mode
                elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                    self.point_size = min(10, self.point_size + 1)
                elif event.key == pygame.K_MINUS:
                    self.point_size = max(1, self.point_size - 1)
                elif event.key == pygame.K_s:
                    self._toggle_mode()
                elif event.key == pygame.K_o and self.ilda_mode:
                    self._show_file_browser()
                elif event.key == pygame.K_SPACE and self.ilda_mode:
                    self._toggle_ilda_playback()
                elif event.key == pygame.K_r and self.ilda_mode:
                    self.ilda_system.get_player().restart()
                elif event.key == pygame.K_n and self.ilda_mode:
                    self.ilda_system.get_player().next_frame()
                elif event.key == pygame.K_m and self.ilda_mode:
                    self.ilda_system.get_player().previous_frame()
                elif event.key == pygame.K_1 and self.ilda_mode:
                    player = self.ilda_system.get_player()
                    player.set_speed(player.speed_multiplier * 1.2)
                elif event.key == pygame.K_2 and self.ilda_mode:
                    player = self.ilda_system.get_player()
                    player.set_speed(player.speed_multiplier / 1.2)
                elif event.key == pygame.K_RETURN and self.show_file_browser:
                    self._select_file_from_browser()
                elif event.key == pygame.K_UP and self.show_file_browser:
                    self.file_browser_selected = max(0, self.file_browser_selected - 1)
                elif event.key == pygame.K_DOWN and self.show_file_browser:
                    self.file_browser_selected = min(len(self.file_browser_files) - 1, self.file_browser_selected + 1)
                elif event.key == pygame.K_ESCAPE and self.show_file_browser:
                    self.show_file_browser = False

        return True

    def _toggle_mode(self):
        """Toggle between IWP and ILDA mode"""
        self.ilda_mode = not self.ilda_mode
        print(f"Switched to {'ILDA' if self.ilda_mode else 'IWP'} mode")

    def _toggle_ilda_playback(self):
        """Toggle ILDA playback"""
        player = self.ilda_system.get_player()
        if player.playing:
            player.pause()
        else:
            player.play()

    def _show_file_browser(self):
        """Show simple file browser"""
        self.show_file_browser = True
        self._refresh_file_list()

    def _refresh_file_list(self):
        """Refresh the file list for current directory"""
        try:
            files = []
            if self.current_directory != '/':
                files.append('..')  # Parent directory

            for item in sorted(os.listdir(self.current_directory)):
                item_path = os.path.join(self.current_directory, item)
                if os.path.isdir(item_path):
                    files.append(f"[{item}]")
                elif item.lower().endswith('.ild'):
                    files.append(item)

            self.file_browser_files = files
            self.file_browser_selected = 0
        except Exception as e:
            print(f"Error reading directory: {e}")
            self.file_browser_files = []

    def _select_file_from_browser(self):
        """Select file from browser"""
        if not self.file_browser_files or self.file_browser_selected >= len(self.file_browser_files):
            return

        selected = self.file_browser_files[self.file_browser_selected]

        if selected == '..':
            # Go to parent directory
            self.current_directory = os.path.dirname(self.current_directory)
            self._refresh_file_list()
        elif selected.startswith('[') and selected.endswith(']'):
            # Directory
            dir_name = selected[1:-1]
            self.current_directory = os.path.join(self.current_directory, dir_name)
            self._refresh_file_list()
        elif selected.lower().endswith('.ild'):
            # ILDA file
            file_path = os.path.join(self.current_directory, selected)
            if self.ilda_system.load_file(file_path):
                self.ilda_file_path = file_path
                print(f"Loaded ILDA file: {selected}")
            else:
                print(f"Failed to load ILDA file: {selected}")
            self.show_file_browser = False

    def _draw_file_browser(self):
        """Draw file browser overlay"""
        if not self.show_file_browser:
            return

        # Semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        # Browser window
        browser_width = min(600, self.width - 100)
        browser_height = min(400, self.height - 100)
        browser_x = (self.width - browser_width) // 2
        browser_y = (self.height - browser_height) // 2

        browser_rect = pygame.Rect(browser_x, browser_y, browser_width, browser_height)
        pygame.draw.rect(self.screen, (40, 40, 40), browser_rect)
        pygame.draw.rect(self.screen, WHITE, browser_rect, 2)

        # Title
        title_text = self.font.render("Select ILDA File", True, WHITE)
        self.screen.blit(title_text, (browser_x + 10, browser_y + 10))

        # Current directory
        dir_text = self.small_font.render(f"Directory: {self.current_directory}", True, GRAY)
        self.screen.blit(dir_text, (browser_x + 10, browser_y + 35))

        # File list
        list_y = browser_y + 60
        line_height = 20
        visible_lines = (browser_height - 80) // line_height

        for i, filename in enumerate(self.file_browser_files[:visible_lines]):
            y_pos = list_y + i * line_height
            color = YELLOW if i == self.file_browser_selected else WHITE

            # Highlight selection
            if i == self.file_browser_selected:
                highlight_rect = pygame.Rect(browser_x + 5, y_pos - 2, browser_width - 10, line_height)
                pygame.draw.rect(self.screen, (60, 60, 60), highlight_rect)

            file_text = self.small_font.render(filename, True, color)
            self.screen.blit(file_text, (browser_x + 10, y_pos))

        # Instructions
        inst_y = browser_y + browser_height - 40
        inst_text = self.small_font.render("↑↓ Navigate, ENTER Select, ESC Cancel", True, GRAY)
        self.screen.blit(inst_text, (browser_x + 10, inst_y))

    def render(self):
        """Render one frame"""
        # Clear screen
        self.screen.fill(BLACK)

        # Draw grid
        self._draw_grid()

        # Draw crosshair
        self._draw_crosshair()

        # Update ILDA if in ILDA mode
        if self.ilda_mode:
            self.ilda_packet = self.ilda_system.update()

        # Draw packets
        if self.trail_mode:
            # Draw packet history with fading effect
            if self.ilda_mode and self.ilda_packet:
                self._draw_packet(self.ilda_packet)
            else:
                for i, packet in enumerate(self.packet_history):
                    alpha = int(255 * (i + 1) / len(self.packet_history))
                    self._draw_packet(packet, alpha)
        else:
            # Draw current packet
            packet_to_draw = self.ilda_packet if self.ilda_mode else self.current_packet
            if packet_to_draw:
                self._draw_packet(packet_to_draw)

        # Draw info panel
        self._draw_info_panel()

        # Draw help
        self._draw_controls_help()

        # Draw file browser if active
        self._draw_file_browser()

        # Update display
        pygame.display.flip()

    def load_ilda_file(self, filename: str) -> bool:
        """Load an ILDA file and switch to ILDA mode"""
        if self.ilda_system.load_file(filename):
            self.ilda_mode = True
            self.ilda_file_path = filename
            print(f"Loaded ILDA file: {filename}")
            return True
        return False

    def run_with_server(self, port: int = 7200, ilda_file: str = None):
        """Run visualizer with integrated UDP server"""
        # Load ILDA file if provided
        if ilda_file:
            if self.load_ilda_file(ilda_file):
                self.ilda_system.get_player().play()  # Auto-start playback
            else:
                print(f"Warning: Could not load ILDA file {ilda_file}")

        # Create and start UDP server (even in ILDA mode for potential switching)
        server = UDPServer(port=port)
        server.set_packet_callback(self.set_packet)

        if not server.start():
            print("Failed to start UDP server")
            return

        if self.ilda_mode:
            print(f"\nLaser Visualizer running in ILDA mode")
            print(f"ILDA file: {self.ilda_file_path}")
            print("Press S to switch to IWP mode")
        else:
            print(f"\nLaser Visualizer running on port {port}")
            print("Waiting for IWP sender device connection...")
            print("Press S to switch to ILDA mode")
        print("Press ESC to exit\n")

        # Main visualization loop
        running = True
        frame_count = 0
        start_time = time.time()

        try:
            while running:
                # Handle events
                running = self._handle_events()

                # Render frame
                self.render()

                # Update FPS
                frame_count += 1
                if frame_count % 30 == 0:
                    current_time = time.time()
                    self.fps = 30 / (current_time - start_time)
                    start_time = current_time

                # Limit frame rate
                self.clock.tick(60)

        except KeyboardInterrupt:
            pass
        finally:
            server.stop()
            pygame.quit()

    def run_standalone(self):
        """Run visualizer without UDP server (for testing)"""
        print("Laser Visualizer running in standalone mode")
        print("Press ESC to exit")

        running = True
        frame_count = 0
        start_time = time.time()

        try:
            while running:
                # Handle events
                running = self._handle_events()

                # Render frame
                self.render()

                # Update FPS
                frame_count += 1
                if frame_count % 30 == 0:
                    current_time = time.time()
                    self.fps = 30 / (current_time - start_time)
                    start_time = current_time

                # Limit frame rate
                self.clock.tick(60)

        except KeyboardInterrupt:
            pass
        finally:
            pygame.quit()


def main():
    """Run the laser visualizer"""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='IWP Laser Visualizer with ILDA support')
    parser.add_argument('--standalone', action='store_true', help='Run without UDP server')
    parser.add_argument('--ilda-file', type=str, help='Load ILDA file on startup')
    parser.add_argument('--port', type=int, default=7200, help='UDP port for IWP data')

    args = parser.parse_args()

    visualizer = LaserVisualizer()

    if args.standalone:
        if args.ilda_file:
            visualizer.load_ilda_file(args.ilda_file)
            visualizer.ilda_system.get_player().play()
        visualizer.run_standalone()
    else:
        visualizer.run_with_server(port=args.port, ilda_file=args.ilda_file)


if __name__ == "__main__":
    main()