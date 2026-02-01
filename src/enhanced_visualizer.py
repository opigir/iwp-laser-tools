#!/usr/bin/env python3
"""
Enhanced IWP Laser Visualizer - Unified Sender/Receiver with comprehensive GUI
Professional tool for visualizing and transmitting IWP laser patterns using pygame
"""

import pygame
import math
import time
import os
import re
from typing import List, Tuple, Optional
from iwp_protocol import IWPPoint, IWPPacket, iwp_to_screen_coords, ilda_to_screen_coords
from udp_server import UDPServer
from ilda_integration import IntegratedILDASystem
from ui_widgets import Panel, Button, TextInput, Slider, StatusIndicator, ToggleSwitch
from ui_widgets import WHITE, BLACK, GRAY, DARK_GRAY, GREEN, RED, BLUE, YELLOW, LIGHT_GRAY, ORANGE

class EnhancedLaserVisualizer:
    """Enhanced laser visualizer with unified sender/receiver functionality"""

    @staticmethod
    def _convert_color_to_8bit(r: int, g: int, b: int) -> tuple:
        """Convert IWP colors (which can be 8-bit or 16-bit) to 8-bit pygame colors"""
        r8 = min(255, r >> 8) if r > 255 else r
        g8 = min(255, g >> 8) if g > 255 else g
        b8 = min(255, b >> 8) if b > 255 else b
        return (r8, g8, b8)

    def __init__(self, width: int = 1200, height: int = 800, title: str = "IWP Laser Tools"):
        self.width = width
        self.height = height
        self.title = title

        # UI Layout dimensions
        self.left_panel_width = 260  # Increased for better spacing
        self.top_panel_height = 60   # Reduced for more space
        self.bottom_panel_height = 30 # Minimal bottom panel
        self.viz_x = self.left_panel_width + 10  # Add margin
        self.viz_y = self.top_panel_height + 10  # Add margin
        self.viz_width = self.width - self.left_panel_width - 30  # Account for margins
        self.viz_height = self.height - self.top_panel_height - self.bottom_panel_height - 20

        # Pygame initialization
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 16)

        # Application state
        self.app_mode = "receiver"  # "receiver" or "sender"
        self.running = True

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

        # Statistics
        self.fps = 0
        self.packet_count = 0
        self.last_packet_time = 0
        self.pattern_type = "Unknown"

        # Network components
        self.udp_server = None

        # ILDA Integration
        self.ilda_system = IntegratedILDASystem()
        self.ilda_packet = None
        self.ilda_file_path = ""
        self.show_file_browser = False
        self.file_browser_files = []
        self.file_browser_selected = 0
        self.current_directory = os.getcwd()

        # Initialize UI
        self._init_ui_panels()

        print(f"Enhanced laser visualizer initialized: {width}x{height}")

    def _init_ui_panels(self):
        """Initialize UI panels and widgets"""
        # Top panel - Mode selection and file operations
        self.top_panel = Panel(0, 0, self.width, self.top_panel_height, "")
        self.top_panel.background_color = (30, 30, 30)

        # Mode toggle button
        self.mode_button = Button(20, 15, 140, 35, "Receiver Mode", self._toggle_app_mode, BLUE)
        self.top_panel.add_widget(self.mode_button)

        # File browser button
        self.file_button = Button(180, 15, 120, 35, "Load ILDA", self._show_file_browser, GRAY)
        self.top_panel.add_widget(self.file_button)

        # Connection status indicator
        self.status_indicator = StatusIndicator(self.width - 120, 25, 12, "Network")
        self.top_panel.add_widget(self.status_indicator)

        # Left panel - Network configuration
        panel_y = self.top_panel_height
        panel_height = self.height - self.top_panel_height - self.bottom_panel_height
        self.left_panel = Panel(0, panel_y, self.left_panel_width, panel_height, "Control Panel")

        y_pos = 100  # Increased top margin
        spacing = 55  # Increased spacing between controls

        # IP address input
        self.ip_input = TextInput(20, y_pos, 210, 32, "192.168.1.100", "Target IP Address",
                                 r"^(\d{1,3}\.){0,3}\d{0,3}$")
        self.left_panel.add_widget(self.ip_input)
        y_pos += spacing

        # Port input
        self.port_input = TextInput(20, y_pos, 210, 32, "7200", "Port", r"^\d{0,5}$")
        self.left_panel.add_widget(self.port_input)
        y_pos += spacing

        # Scan rate slider
        self.scan_rate_slider = Slider(20, y_pos, 210, 28, 100, 100000, 1000,
                                      self._on_scan_rate_change, "Scan Rate (Hz)", 0)
        self.left_panel.add_widget(self.scan_rate_slider)
        y_pos += spacing + 5

        # FPS slider
        self.fps_slider = Slider(20, y_pos, 210, 28, 0.1, 120, 25,
                                self._on_fps_change, "FPS", 1)
        self.left_panel.add_widget(self.fps_slider)
        y_pos += spacing + 5

        # Playback controls section
        y_pos += 20  # Extra space before playback section

        # Play/Stop buttons on same row
        self.play_button = Button(20, y_pos, 100, 35, "Play", self._toggle_ilda_playback, GREEN)
        self.left_panel.add_widget(self.play_button)

        self.stop_button = Button(130, y_pos, 100, 35, "Stop", self._stop_ilda_playback, RED)
        self.left_panel.add_widget(self.stop_button)
        y_pos += 50

        # Frame navigation
        self.prev_button = Button(20, y_pos, 100, 32, "Previous", self._previous_frame, GRAY)
        self.left_panel.add_widget(self.prev_button)

        self.next_button = Button(130, y_pos, 100, 32, "Next", self._next_frame, GRAY)
        self.left_panel.add_widget(self.next_button)
        y_pos += 50

        # Speed slider
        self.speed_slider = Slider(20, y_pos, 210, 28, 0.1, 5.0, 1.0,
                                  self._on_speed_change, "Speed", 1)
        self.left_panel.add_widget(self.speed_slider)
        y_pos += spacing

        # Loop toggle
        self.loop_toggle = ToggleSwitch(20, y_pos, 100, 32, True,
                                       self._on_loop_toggle, "Loop")
        self.left_panel.add_widget(self.loop_toggle)

        # Network transmission toggle
        self.transmission_toggle = ToggleSwitch(130, y_pos, 100, 32, False,
                                               self._on_transmission_toggle, "Transmit")
        self.left_panel.add_widget(self.transmission_toggle)
        y_pos += 50

        # Connection button
        self.connect_button = Button(20, y_pos, 210, 35, "Start Server", self._test_connection, GREEN)
        self.left_panel.add_widget(self.connect_button)


        # Bottom panel - Status bar
        self.bottom_panel = Panel(0, self.height - self.bottom_panel_height,
                                 self.width, self.bottom_panel_height, "")
        self.bottom_panel.background_color = (25, 25, 25)

        # Update UI for current mode
        self._update_ui_for_mode()

    def _toggle_app_mode(self):
        """Toggle between receiver and sender mode"""
        self.app_mode = "sender" if self.app_mode == "receiver" else "receiver"
        self._update_ui_for_mode()
        print(f"Switched to {self.app_mode} mode")

    def _update_ui_for_mode(self):
        """Update UI elements based on current mode"""
        if self.app_mode == "receiver":
            self.mode_button.text = "📡 Receiver Mode"
            self.mode_button.color = BLUE
            self.transmission_toggle.enabled = False
            self.connect_button.text = "Start Server"
        else:  # sender mode
            self.mode_button.text = "📤 Sender Mode"
            self.mode_button.color = BLACK
            self.transmission_toggle.enabled = True
            self.connect_button.text = "Test Connection"

    def _show_file_browser(self):
        """Show file browser"""
        self.show_file_browser = True
        self._refresh_file_list()

    def _refresh_file_list(self):
        """Refresh file browser list"""
        try:
            files = []
            if self.current_directory != '/' and self.current_directory != os.path.dirname(self.current_directory):
                files.append('..')

            for item in sorted(os.listdir(self.current_directory)):
                item_path = os.path.join(self.current_directory, item)
                if os.path.isdir(item_path):
                    files.append(f"📁 {item}")
                elif item.lower().endswith('.ild'):
                    files.append(f"📄 {item}")

            self.file_browser_files = files
            self.file_browser_selected = 0
        except Exception as e:
            print(f"Error reading directory: {e}")
            self.file_browser_files = []

    # Event handler callbacks
    def _on_scan_rate_change(self, value: float):
        """Handle scan rate slider change"""
        if self.app_mode == "sender":
            self.ilda_system.get_sender().set_scan_rate(int(value))

    def _on_fps_change(self, value: float):
        """Handle FPS slider change"""
        self.ilda_system.get_player().set_fps(value)

    def _on_speed_change(self, value: float):
        """Handle speed slider change"""
        self.ilda_system.get_player().set_speed(value)

    def _on_loop_toggle(self, enabled: bool):
        """Handle loop toggle"""
        self.ilda_system.get_player().loop = enabled

    def _on_transmission_toggle(self, enabled: bool):
        """Handle transmission toggle"""
        if self.app_mode == "sender":
            if enabled:
                ip = self.ip_input.get_text()
                port = int(self.port_input.get_text() or "7200")
                scan_rate = int(self.scan_rate_slider.get_value())
                success = self.ilda_system.enable_transmission(ip, port, scan_rate)
                if success:
                    self.status_indicator.set_status("connected")
                    print(f"Transmission enabled to {ip}:{port}")
                else:
                    self.status_indicator.set_status("error")
                    self.transmission_toggle.set_state(False)
                    print("Failed to enable transmission")
            else:
                self.ilda_system.disable_transmission()
                self.status_indicator.set_status("disconnected")
                print("Transmission disabled")

    def _test_connection(self):
        """Test network connection"""
        if self.app_mode == "receiver":
            self._start_udp_server()
        else:
            # Test sender connection
            ip = self.ip_input.get_text()
            port = int(self.port_input.get_text() or "7200")
            print(f"Testing connection to {ip}:{port}")

    def _start_udp_server(self):
        """Start UDP server for receiving IWP data"""
        if not self.udp_server:
            port = int(self.port_input.get_text() or "7200")
            self.udp_server = UDPServer(port=port)
            self.udp_server.set_packet_callback(self.set_packet)
            if self.udp_server.start():
                self.status_indicator.set_status("connected")
                self.connect_button.text = "Stop Server"
                print(f"UDP server started on port {port}")
            else:
                self.status_indicator.set_status("error")
                print("Failed to start UDP server")
        else:
            self.udp_server.stop()
            self.udp_server = None
            self.status_indicator.set_status("disconnected")
            self.connect_button.text = "Start Server"
            print("UDP server stopped")

    def _toggle_ilda_playback(self):
        """Toggle ILDA playback"""
        player = self.ilda_system.get_player()
        if player.playing:
            player.pause()
            self.play_button.text = "Play"
        else:
            player.play()
            self.play_button.text = "Pause"

    def _stop_ilda_playback(self):
        """Stop ILDA playback"""
        self.ilda_system.get_player().stop()
        self.play_button.text = "Play"

    def _previous_frame(self):
        """Go to previous frame"""
        self.ilda_system.get_player().previous_frame()

    def _next_frame(self):
        """Go to next frame"""
        self.ilda_system.get_player().next_frame()

    def set_packet(self, packet: IWPPacket, source_address: str):
        """Update display with new packet data (for receiver mode)"""
        if self.app_mode == "receiver":
            self.current_packet = packet
            self.packet_count += 1
            self.last_packet_time = time.time()

            if len(self.packet_history) >= self.max_history:
                self.packet_history.pop(0)
            self.packet_history.append(packet)

    def _draw_visualization_area(self):
        """Draw the main visualization area"""
        # Create visualization surface
        viz_rect = pygame.Rect(self.viz_x, self.viz_y, self.viz_width, self.viz_height)
        pygame.draw.rect(self.screen, BLACK, viz_rect)
        pygame.draw.rect(self.screen, GRAY, viz_rect, 1)

        # Set clipping to visualization area for drawing
        self.screen.set_clip(viz_rect)

        # Draw grid relative to viz area
        if self.show_grid:
            self._draw_grid()

        # Draw crosshair
        if self.show_crosshair:
            self._draw_crosshair()

        # Draw laser patterns
        packet_to_draw = None
        if self.app_mode == "sender":
            self.ilda_packet = self.ilda_system.update()
            packet_to_draw = self.ilda_packet
        else:
            packet_to_draw = self.current_packet

        if packet_to_draw:
            self._draw_packet(packet_to_draw, viz_rect)

        # Remove clipping
        self.screen.set_clip(None)

    def _draw_grid(self):
        """Draw coordinate grid in visualization area"""
        grid_spacing = 40

        # Calculate grid relative to viz area
        start_x = self.viz_x
        start_y = self.viz_y
        end_x = self.viz_x + self.viz_width
        end_y = self.viz_y + self.viz_height
        center_x = self.viz_x + self.viz_width // 2
        center_y = self.viz_y + self.viz_height // 2

        # Vertical lines
        for x in range(start_x, end_x, grid_spacing):
            pygame.draw.line(self.screen, DARK_GRAY, (x, start_y), (x, end_y), 1)

        # Horizontal lines
        for y in range(start_y, end_y, grid_spacing):
            pygame.draw.line(self.screen, DARK_GRAY, (start_x, y), (end_x, y), 1)

        # Center lines
        pygame.draw.line(self.screen, GRAY, (center_x, start_y), (center_x, end_y), 2)
        pygame.draw.line(self.screen, GRAY, (start_x, center_y), (end_x, center_y), 2)

    def _draw_crosshair(self):
        """Draw crosshair in visualization area"""
        center_x = self.viz_x + self.viz_width // 2
        center_y = self.viz_y + self.viz_height // 2
        size = 20

        pygame.draw.line(self.screen, WHITE, (center_x - size, center_y), (center_x + size, center_y), 1)
        pygame.draw.line(self.screen, WHITE, (center_x, center_y - size), (center_x, center_y + size), 1)
        pygame.draw.circle(self.screen, WHITE, (center_x, center_y), 3, 1)

    def _draw_packet(self, packet: IWPPacket, viz_rect: pygame.Rect):
        """Draw packet points in visualization area"""
        if packet.point_count == 0:
            return

        screen_points = []
        for point in packet.points:
            # Use standard IWP coordinate transformation for visualization area
            sx, sy = iwp_to_screen_coords(point.x, point.y, viz_rect.width, viz_rect.height)
            # Offset to visualization area position
            screen_x = viz_rect.x + sx
            screen_y = viz_rect.y + sy
            screen_points.append((screen_x, screen_y, point))

        # Draw lines
        if self.show_lines and len(screen_points) > 1:
            line_points = []
            for sx, sy, point in screen_points:
                if not point.blanking:
                    line_points.append((sx, sy))
                else:
                    if len(line_points) > 1:
                        color = self._convert_color_to_8bit(point.r, point.g, point.b)
                        if color == (0, 0, 0):
                            color = GREEN
                        pygame.draw.lines(self.screen, color, False, line_points, 2)
                    line_points = []

            if len(line_points) > 1:
                pygame.draw.lines(self.screen, GREEN, False, line_points, 2)

        # Draw points
        if self.show_points:
            for sx, sy, point in screen_points:
                if point.blanking and not self.show_blanking:
                    continue

                if point.blanking:
                    color = DARK_GRAY
                    size = max(1, self.point_size - 1)
                else:
                    color = self._convert_color_to_8bit(point.r, point.g, point.b)
                    if color == (0, 0, 0):
                        color = WHITE
                    size = self.point_size

                pygame.draw.circle(self.screen, color, (sx, sy), size)


    def _draw_status_bar(self):
        """Draw status information in bottom panel"""
        status_y = self.height - self.bottom_panel_height + 15

        # Mode and connection status
        mode_text = f"Mode: {self.app_mode.title()}"
        text = self.small_font.render(mode_text, True, WHITE)
        self.screen.blit(text, (20, status_y))

        # Network stats
        if self.app_mode == "sender" and self.transmission_toggle.state:
            stats = self.ilda_system.get_network_stats()
            net_text = f"Transmitting to {stats['target_ip']}:{stats['port']} | Packets: {stats['packets_sent']}"
            text = self.small_font.render(net_text, True, GREEN)
            self.screen.blit(text, (200, status_y))
        elif self.app_mode == "receiver" and self.udp_server:
            recv_text = f"Listening on port {self.port_input.get_text()} | Packets received: {self.packet_count}"
            text = self.small_font.render(recv_text, True, BLUE)
            self.screen.blit(text, (200, status_y))

        # FPS
        fps_text = f"FPS: {self.fps:.1f}"
        text = self.small_font.render(fps_text, True, WHITE)
        self.screen.blit(text, (self.width - 100, status_y))

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
        self.screen.blit(title_text, (browser_x + 20, browser_y + 20))

        # Current directory
        dir_text = self.small_font.render(f"📁 {self.current_directory}", True, LIGHT_GRAY)
        self.screen.blit(dir_text, (browser_x + 20, browser_y + 50))

        # File list
        list_y = browser_y + 80
        line_height = 25
        visible_lines = (browser_height - 120) // line_height

        for i, filename in enumerate(self.file_browser_files[:visible_lines]):
            y_pos = list_y + i * line_height
            color = YELLOW if i == self.file_browser_selected else WHITE

            # Highlight selection
            if i == self.file_browser_selected:
                highlight_rect = pygame.Rect(browser_x + 15, y_pos - 2, browser_width - 30, line_height)
                pygame.draw.rect(self.screen, (80, 80, 80), highlight_rect)

            file_text = self.small_font.render(filename, True, color)
            self.screen.blit(file_text, (browser_x + 20, y_pos))

        # Instructions
        inst_y = browser_y + browser_height - 40
        instructions = "↑↓ Navigate | ENTER Select | ESC Cancel"
        inst_text = self.small_font.render(instructions, True, LIGHT_GRAY)
        self.screen.blit(inst_text, (browser_x + 20, inst_y))

    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            # UI panel event handling
            if self.show_file_browser:
                self._handle_file_browser_events(event)
            else:
                self.top_panel.handle_event(event)
                self.left_panel.handle_event(event)
                self.bottom_panel.handle_event(event)

            # Keyboard shortcuts
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    self._toggle_app_mode()
                elif event.key == pygame.K_F1:
                    self._show_file_browser()
                elif event.key == pygame.K_g:
                    self.show_grid = not self.show_grid
                elif event.key == pygame.K_c:
                    self.show_crosshair = not self.show_crosshair
                elif event.key == pygame.K_p:
                    self.show_points = not self.show_points
                elif event.key == pygame.K_l:
                    self.show_lines = not self.show_lines

    def _handle_file_browser_events(self, event):
        """Handle file browser specific events"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.show_file_browser = False
            elif event.key == pygame.K_UP:
                self.file_browser_selected = max(0, self.file_browser_selected - 1)
            elif event.key == pygame.K_DOWN:
                self.file_browser_selected = min(len(self.file_browser_files) - 1, self.file_browser_selected + 1)
            elif event.key == pygame.K_RETURN:
                self._select_file_from_browser()

    def _select_file_from_browser(self):
        """Select file from browser"""
        if not self.file_browser_files or self.file_browser_selected >= len(self.file_browser_files):
            return

        selected = self.file_browser_files[self.file_browser_selected]

        if selected == '..':
            # Go to parent directory
            self.current_directory = os.path.dirname(self.current_directory)
            self._refresh_file_list()
        elif selected.startswith('📁'):
            # Directory
            dir_name = selected[2:].strip()
            self.current_directory = os.path.join(self.current_directory, dir_name)
            self._refresh_file_list()
        elif selected.startswith('📄'):
            # ILDA file
            filename = selected[2:].strip()
            file_path = os.path.join(self.current_directory, filename)
            if self.ilda_system.load_file(file_path):
                self.ilda_file_path = file_path
                print(f"Loaded ILDA file: {filename}")
                self.show_file_browser = False
                # Auto-switch to sender mode if loading ILDA file
                if self.app_mode == "receiver":
                    self._toggle_app_mode()
            else:
                print(f"Failed to load ILDA file: {filename}")

    def update(self):
        """Update application state"""
        # Update UI widgets
        self.top_panel.update()
        self.left_panel.update()
        self.bottom_panel.update()

        # Update FPS calculation
        current_time = time.time()
        if hasattr(self, 'last_fps_time'):
            dt = current_time - self.last_fps_time
            if dt > 0:
                self.fps = 1.0 / dt
        self.last_fps_time = current_time

    def render(self):
        """Render the complete interface"""
        # Clear screen
        self.screen.fill(BLACK)

        # Draw main visualization area
        self._draw_visualization_area()

        # Draw UI panels
        self.top_panel.draw(self.screen)
        self.left_panel.draw(self.screen)
        self.bottom_panel.draw(self.screen)

        # Draw additional info
        self._draw_status_bar()

        # Draw file browser if active
        self._draw_file_browser()

        # Update display
        pygame.display.flip()

    def run(self):
        """Main application loop"""
        print("IWP Laser Tools started")
        print("Controls:")
        print("  TAB - Toggle Sender/Receiver mode")
        print("  F1 - Open file browser")
        print("  G - Toggle grid")
        print("  C - Toggle crosshair")
        print("  P - Toggle points")
        print("  L - Toggle lines")

        try:
            while self.running:
                self.handle_events()
                self.update()
                self.render()
                self.clock.tick(60)  # 60 FPS

        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()
            pygame.quit()

    def cleanup(self):
        """Clean up resources"""
        if self.udp_server:
            self.udp_server.stop()
        self.ilda_system.disable_transmission()
        print("IWP Laser Tools stopped")

def main():
    """Run the enhanced visualizer"""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='Enhanced IWP Visualizer with Sender/Receiver modes')
    parser.add_argument('--ilda-file', type=str, help='Load ILDA file on startup')
    parser.add_argument('--mode', choices=['sender', 'receiver'], default='receiver', help='Start in sender or receiver mode')
    parser.add_argument('--width', type=int, default=1200, help='Window width')
    parser.add_argument('--height', type=int, default=800, help='Window height')

    args = parser.parse_args()

    visualizer = EnhancedLaserVisualizer(width=args.width, height=args.height)

    # Set initial mode
    if args.mode == "sender":
        visualizer._toggle_app_mode()

    # Load ILDA file if provided
    if args.ilda_file:
        if visualizer.ilda_system.load_file(args.ilda_file):
            visualizer.ilda_file_path = args.ilda_file
            if args.mode != "sender":
                visualizer._toggle_app_mode()  # Switch to sender mode
            print(f"Loaded ILDA file: {args.ilda_file}")
        else:
            print(f"Warning: Could not load ILDA file {args.ilda_file}")

    visualizer.run()

if __name__ == "__main__":
    main()