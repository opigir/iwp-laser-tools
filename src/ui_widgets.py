#!/usr/bin/env python3
"""
Pygame UI Widgets for IWP Visualizer
Provides reusable UI components for the laser visualizer interface
"""

import pygame
import re
from typing import Optional, Callable, Tuple, Any
from enum import Enum

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (192, 192, 192)
BLUE = (0, 100, 255)
LIGHT_BLUE = (100, 150, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 128, 0)

class UIWidget:
    """Base class for UI widgets"""

    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.visible = True
        self.enabled = True
        self.font = pygame.font.Font(None, 18)
        self.small_font = pygame.font.Font(None, 14)

    def draw(self, surface: pygame.Surface):
        """Draw the widget"""
        pass

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle pygame events. Return True if event was consumed."""
        return False

    def update(self):
        """Update widget state"""
        pass

class Button(UIWidget):
    """Clickable button widget"""

    def __init__(self, x: int, y: int, width: int, height: int, text: str,
                 callback: Optional[Callable] = None, color: Tuple[int, int, int] = GRAY):
        super().__init__(x, y, width, height)
        self.text = text
        self.callback = callback
        self.color = color
        self.pressed = False
        self.hover = False

    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return

        # Button background
        button_color = self.color
        if not self.enabled:
            button_color = DARK_GRAY
        elif self.pressed:
            button_color = tuple(max(0, c - 40) for c in self.color)
        elif self.hover:
            button_color = tuple(min(255, c + 20) for c in self.color)

        pygame.draw.rect(surface, button_color, self.rect)
        pygame.draw.rect(surface, WHITE, self.rect, 1)

        # Button text
        text_color = WHITE if self.enabled else GRAY
        text_surface = self.font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible or not self.enabled:
            return False

        mouse_pos = pygame.mouse.get_pos()
        self.hover = self.rect.collidepoint(mouse_pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.pressed = True
                return True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.pressed and self.rect.collidepoint(event.pos):
                self.pressed = False
                if self.callback:
                    self.callback()
                return True
            self.pressed = False

        return False

class TextInput(UIWidget):
    """Text input field widget"""

    def __init__(self, x: int, y: int, width: int, height: int,
                 initial_text: str = "", placeholder: str = "",
                 validation_pattern: Optional[str] = None):
        super().__init__(x, y, width, height)
        self.text = initial_text
        self.placeholder = placeholder
        self.validation_pattern = validation_pattern
        self.active = False
        self.cursor_pos = len(self.text)
        self.cursor_visible = True
        self.cursor_timer = 0
        self.max_length = 50

    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return

        # Input field background
        bg_color = WHITE if self.enabled else LIGHT_GRAY
        border_color = BLUE if self.active else GRAY
        border_width = 2 if self.active else 1

        pygame.draw.rect(surface, bg_color, self.rect)
        pygame.draw.rect(surface, border_color, self.rect, border_width)

        # Text content
        display_text = self.text if self.text else self.placeholder
        text_color = BLACK if self.text else GRAY

        if display_text:
            text_surface = self.font.render(display_text, True, text_color)
            text_x = self.rect.x + 5
            text_y = self.rect.y + (self.rect.height - text_surface.get_height()) // 2
            surface.blit(text_surface, (text_x, text_y))

        # Cursor
        if self.active and self.cursor_visible and self.enabled:
            cursor_x = self.rect.x + 5
            if self.text:
                cursor_text = self.text[:self.cursor_pos]
                cursor_width = self.font.size(cursor_text)[0]
                cursor_x += cursor_width

            cursor_y1 = self.rect.y + 3
            cursor_y2 = self.rect.bottom - 3
            pygame.draw.line(surface, BLACK, (cursor_x, cursor_y1), (cursor_x, cursor_y2))

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible or not self.enabled:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(event.pos)
            return self.active

        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                if self.cursor_pos > 0:
                    self.text = self.text[:self.cursor_pos-1] + self.text[self.cursor_pos:]
                    self.cursor_pos -= 1
                return True

            elif event.key == pygame.K_DELETE:
                if self.cursor_pos < len(self.text):
                    self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos+1:]
                return True

            elif event.key == pygame.K_LEFT:
                self.cursor_pos = max(0, self.cursor_pos - 1)
                return True

            elif event.key == pygame.K_RIGHT:
                self.cursor_pos = min(len(self.text), self.cursor_pos + 1)
                return True

            elif event.key == pygame.K_HOME:
                self.cursor_pos = 0
                return True

            elif event.key == pygame.K_END:
                self.cursor_pos = len(self.text)
                return True

            elif event.unicode and len(self.text) < self.max_length:
                if self.is_valid_char(event.unicode):
                    self.text = self.text[:self.cursor_pos] + event.unicode + self.text[self.cursor_pos:]
                    self.cursor_pos += 1
                return True

        return False

    def update(self):
        """Update cursor blink animation"""
        self.cursor_timer += 1
        if self.cursor_timer >= 30:  # Blink every 30 frames (~0.5s at 60fps)
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

    def is_valid_char(self, char: str) -> bool:
        """Check if character is valid for this input field"""
        if not char.isprintable() or char == '\r' or char == '\n':
            return False

        if self.validation_pattern:
            # Test if adding this character would still match pattern
            test_text = self.text[:self.cursor_pos] + char + self.text[self.cursor_pos:]
            return bool(re.match(self.validation_pattern, test_text))

        return True

    def get_text(self) -> str:
        """Get current text value"""
        return self.text

    def set_text(self, text: str):
        """Set text value"""
        self.text = text
        self.cursor_pos = len(text)

class Slider(UIWidget):
    """Horizontal slider widget"""

    def __init__(self, x: int, y: int, width: int, height: int,
                 min_value: float, max_value: float, initial_value: float,
                 callback: Optional[Callable[[float], None]] = None,
                 label: str = "", decimal_places: int = 1):
        super().__init__(x, y, width, height)
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial_value
        self.callback = callback
        self.label = label
        self.decimal_places = decimal_places
        self.dragging = False
        self.handle_radius = 8

    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return

        # Label
        if self.label:
            label_surface = self.small_font.render(self.label, True, WHITE)
            surface.blit(label_surface, (self.rect.x, self.rect.y - 15))

        # Slider track
        track_y = self.rect.y + self.rect.height // 2
        track_start = (self.rect.x + self.handle_radius, track_y)
        track_end = (self.rect.right - self.handle_radius, track_y)
        pygame.draw.line(surface, GRAY, track_start, track_end, 3)

        # Slider handle
        track_width = self.rect.width - 2 * self.handle_radius
        value_ratio = (self.value - self.min_value) / (self.max_value - self.min_value)
        handle_x = self.rect.x + self.handle_radius + track_width * value_ratio
        handle_pos = (int(handle_x), track_y)

        handle_color = LIGHT_BLUE if self.enabled else GRAY
        pygame.draw.circle(surface, handle_color, handle_pos, self.handle_radius)
        pygame.draw.circle(surface, WHITE, handle_pos, self.handle_radius, 2)

        # Value display
        value_text = f"{self.value:.{self.decimal_places}f}"
        value_surface = self.small_font.render(value_text, True, WHITE)
        value_x = self.rect.right - value_surface.get_width()
        surface.blit(value_surface, (value_x, self.rect.bottom + 2))

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible or not self.enabled:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self._update_value_from_mouse(event.pos)
                return True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.dragging = False
                return True

        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._update_value_from_mouse(event.pos)
            return True

        return False

    def _update_value_from_mouse(self, mouse_pos: Tuple[int, int]):
        """Update slider value based on mouse position"""
        track_start = self.rect.x + self.handle_radius
        track_width = self.rect.width - 2 * self.handle_radius
        relative_x = max(0, min(track_width, mouse_pos[0] - track_start))
        value_ratio = relative_x / track_width

        new_value = self.min_value + (self.max_value - self.min_value) * value_ratio
        self.set_value(new_value)

    def set_value(self, value: float):
        """Set slider value"""
        self.value = max(self.min_value, min(self.max_value, value))
        if self.callback:
            self.callback(self.value)

    def get_value(self) -> float:
        """Get current slider value"""
        return self.value

class StatusIndicator(UIWidget):
    """Status indicator widget with color-coded states"""

    def __init__(self, x: int, y: int, radius: int, label: str = ""):
        super().__init__(x, y, radius * 2, radius * 2)
        self.radius = radius
        self.label = label
        self.status = "disconnected"  # disconnected, connecting, connected, error

    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return

        # Status colors
        status_colors = {
            "disconnected": GRAY,
            "connecting": ORANGE,
            "connected": GREEN,
            "error": RED
        }

        color = status_colors.get(self.status, GRAY)
        center = self.rect.center

        # Outer ring
        pygame.draw.circle(surface, WHITE, center, self.radius + 2, 2)
        # Inner filled circle
        pygame.draw.circle(surface, color, center, self.radius)

        # Label
        if self.label:
            label_surface = self.small_font.render(self.label, True, WHITE)
            label_x = self.rect.right + 5
            label_y = self.rect.centery - label_surface.get_height() // 2
            surface.blit(label_surface, (label_x, label_y))

    def set_status(self, status: str):
        """Set status: disconnected, connecting, connected, error"""
        self.status = status

class Panel:
    """Container for grouping widgets with background"""

    def __init__(self, x: int, y: int, width: int, height: int,
                 title: str = "", background_color: Tuple[int, int, int] = (20, 20, 20)):
        self.rect = pygame.Rect(x, y, width, height)
        self.title = title
        self.background_color = background_color
        self.widgets = []
        self.visible = True
        self.font = pygame.font.Font(None, 20)

    def add_widget(self, widget: UIWidget):
        """Add a widget to the panel"""
        self.widgets.append(widget)

    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return

        # Panel background
        pygame.draw.rect(surface, self.background_color, self.rect)
        pygame.draw.rect(surface, GRAY, self.rect, 1)

        # Panel title
        if self.title:
            title_surface = self.font.render(self.title, True, WHITE)
            title_x = self.rect.x + 5
            title_y = self.rect.y + 5
            surface.blit(title_surface, (title_x, title_y))

        # Draw all widgets
        for widget in self.widgets:
            widget.draw(surface)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle events for all widgets in panel"""
        if not self.visible:
            return False

        # Handle in reverse order so top widgets get priority
        for widget in reversed(self.widgets):
            if widget.handle_event(event):
                return True
        return False

    def update(self):
        """Update all widgets in panel"""
        if self.visible:
            for widget in self.widgets:
                widget.update()

class ToggleSwitch(UIWidget):
    """Toggle switch widget"""

    def __init__(self, x: int, y: int, width: int, height: int,
                 initial_state: bool = False, callback: Optional[Callable[[bool], None]] = None,
                 label: str = ""):
        super().__init__(x, y, width, height)
        self.state = initial_state
        self.callback = callback
        self.label = label

    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return

        # Label
        if self.label:
            label_surface = self.font.render(self.label, True, WHITE)
            surface.blit(label_surface, (self.rect.x, self.rect.y - 20))

        # Switch track
        track_color = GREEN if self.state else DARK_GRAY
        pygame.draw.rect(surface, track_color, self.rect, border_radius=self.rect.height//2)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=self.rect.height//2)

        # Switch handle
        handle_radius = self.rect.height // 2 - 2
        handle_x = self.rect.right - handle_radius - 2 if self.state else self.rect.x + handle_radius + 2
        handle_y = self.rect.centery
        pygame.draw.circle(surface, WHITE, (handle_x, handle_y), handle_radius)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible or not self.enabled:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.toggle()
                return True
        return False

    def toggle(self):
        """Toggle the switch state"""
        self.state = not self.state
        if self.callback:
            self.callback(self.state)

    def set_state(self, state: bool):
        """Set switch state"""
        self.state = state