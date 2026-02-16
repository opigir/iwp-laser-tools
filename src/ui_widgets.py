#!/usr/bin/env python3
"""
Pygame UI Widgets for IWP Visualizer
Provides reusable UI components for the laser visualizer interface
"""

import pygame
import re
from typing import Optional, Callable, Tuple, Any
from enum import Enum

# Modern Color System (shadcn/ui inspired)
# Backgrounds
BACKGROUND = (9, 9, 11)        # Dark background
SURFACE = (24, 24, 27)         # Panel/card background
SURFACE_HOVER = (39, 39, 42)   # Hover states

# Borders
BORDER = (39, 39, 42)          # Default borders
BORDER_SUBTLE = (63, 63, 70)   # Subtle borders

# Text
WHITE = (250, 250, 250)        # Primary text
TEXT_SECONDARY = (161, 161, 170) # Secondary text
TEXT_MUTED = (113, 113, 122)   # Muted text

# Legacy colors (keep for compatibility)
BLACK = (0, 0, 0)
GRAY = (113, 113, 122)         # Updated to muted text
DARK_GRAY = (39, 39, 42)       # Updated to surface hover
LIGHT_GRAY = (161, 161, 170)   # Updated to secondary text

# Accent colors (modern, less saturated)
BLUE = (59, 130, 246)          # Primary blue
LIGHT_BLUE = (147, 197, 253)   # Light blue
GREEN = (34, 197, 94)          # Success green
RED = (239, 68, 68)            # Error red
YELLOW = (245, 158, 11)        # Warning amber
ORANGE = (249, 115, 22)        # Orange accent

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

        # Modern button styling with rounded corners
        radius = 8

        # Button background with modern color states
        button_color = self.color
        border_color = BORDER

        if not self.enabled:
            button_color = DARK_GRAY
            border_color = BORDER_SUBTLE
        elif self.pressed:
            # Darker pressed state
            button_color = tuple(max(0, c - 30) for c in self.color)
            border_color = tuple(max(0, c - 20) for c in border_color)
        elif self.hover:
            # Lighter hover state with subtle glow effect
            button_color = tuple(min(255, c + 15) for c in self.color)
            border_color = tuple(min(255, c + 30) for c in self.color)

        # Draw subtle shadow first (offset slightly)
        shadow_rect = self.rect.copy()
        shadow_rect.x += 1
        shadow_rect.y += 2
        shadow_color = (0, 0, 0, 40)  # Semi-transparent black
        pygame.draw.rect(surface, shadow_color[:3], shadow_rect, border_radius=radius)

        # Draw main button with rounded corners
        pygame.draw.rect(surface, button_color, self.rect, border_radius=radius)
        pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=radius)

        # Button text with better typography
        text_color = WHITE if self.enabled else TEXT_MUTED
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

        radius = 6  # Rounded corners

        # Modern input field styling
        bg_color = SURFACE if self.enabled else DARK_GRAY
        border_color = BLUE if self.active else BORDER
        border_width = 2 if self.active else 1

        # Draw subtle shadow
        shadow_rect = self.rect.copy()
        shadow_rect.x += 1
        shadow_rect.y += 1
        pygame.draw.rect(surface, (0, 0, 0, 20), shadow_rect, border_radius=radius)

        # Draw input field background with rounded corners
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=radius)
        pygame.draw.rect(surface, border_color, self.rect, border_width, border_radius=radius)

        # Focus ring effect
        if self.active:
            focus_rect = self.rect.copy()
            focus_rect.inflate_ip(4, 4)
            pygame.draw.rect(surface, (*BLUE, 30), focus_rect, 3, border_radius=radius+2)

        # Text content with better typography
        display_text = self.text if self.text else self.placeholder
        text_color = WHITE if self.text else TEXT_MUTED

        if display_text:
            text_surface = self.font.render(display_text, True, text_color)
            text_x = self.rect.x + 12  # More padding
            text_y = self.rect.y + (self.rect.height - text_surface.get_height()) // 2
            surface.blit(text_surface, (text_x, text_y))

        # Modern cursor
        if self.active and self.cursor_visible and self.enabled:
            cursor_x = self.rect.x + 12
            if self.text:
                cursor_text = self.text[:self.cursor_pos]
                cursor_width = self.font.size(cursor_text)[0]
                cursor_x += cursor_width

            cursor_y1 = self.rect.y + 6
            cursor_y2 = self.rect.bottom - 6
            pygame.draw.line(surface, BLUE, (cursor_x, cursor_y1), (cursor_x, cursor_y2), 2)

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

        # Label with better typography
        if self.label:
            label_surface = self.small_font.render(self.label, True, TEXT_SECONDARY)
            surface.blit(label_surface, (self.rect.x, self.rect.y - 18))

        # Modern slider track
        track_y = self.rect.y + self.rect.height // 2
        track_start = (self.rect.x + self.handle_radius, track_y)
        track_end = (self.rect.right - self.handle_radius, track_y)

        # Background track
        pygame.draw.line(surface, BORDER, track_start, track_end, 4)

        # Filled portion (progress indicator)
        track_width = self.rect.width - 2 * self.handle_radius
        value_ratio = (self.value - self.min_value) / (self.max_value - self.min_value)
        fill_end_x = self.rect.x + self.handle_radius + track_width * value_ratio
        fill_end = (int(fill_end_x), track_y)
        pygame.draw.line(surface, BLUE, track_start, fill_end, 4)

        # Slider handle with modern styling
        handle_x = self.rect.x + self.handle_radius + track_width * value_ratio
        handle_pos = (int(handle_x), track_y)

        # Handle shadow
        shadow_pos = (int(handle_x) + 1, track_y + 1)
        pygame.draw.circle(surface, (0, 0, 0, 60), shadow_pos, self.handle_radius + 1)

        # Handle styling based on state
        if not self.enabled:
            handle_color = BORDER_SUBTLE
            border_color = BORDER
        elif self.dragging:
            handle_color = SURFACE_HOVER
            border_color = BLUE
            # Slightly larger when dragging
            pygame.draw.circle(surface, handle_color, handle_pos, self.handle_radius + 2)
            pygame.draw.circle(surface, border_color, handle_pos, self.handle_radius + 2, 2)
        else:
            handle_color = WHITE
            border_color = BORDER_SUBTLE
            pygame.draw.circle(surface, handle_color, handle_pos, self.handle_radius)
            pygame.draw.circle(surface, border_color, handle_pos, self.handle_radius, 2)

        # Value display with better positioning
        value_text = f"{self.value:.{self.decimal_places}f}"
        value_surface = self.small_font.render(value_text, True, TEXT_SECONDARY)
        value_x = self.rect.right - value_surface.get_width()
        surface.blit(value_surface, (value_x, self.rect.bottom + 4))

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
                 title: str = "", background_color: Tuple[int, int, int] = SURFACE):
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

        radius = 8

        # Panel shadow
        shadow_rect = self.rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 3
        pygame.draw.rect(surface, (0, 0, 0, 25), shadow_rect, border_radius=radius)

        # Modern panel background with rounded corners
        pygame.draw.rect(surface, self.background_color, self.rect, border_radius=radius)
        pygame.draw.rect(surface, BORDER, self.rect, 1, border_radius=radius)

        # Panel title with better typography
        if self.title:
            title_surface = self.font.render(self.title, True, WHITE)
            title_x = self.rect.x + 12  # More padding
            title_y = self.rect.y + 10
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

        # Label with better typography
        if self.label:
            label_surface = self.font.render(self.label, True, TEXT_SECONDARY)
            surface.blit(label_surface, (self.rect.x, self.rect.y - 22))

        # Modern iOS-style toggle switch
        radius = self.rect.height // 2

        # Track shadow
        shadow_rect = self.rect.copy()
        shadow_rect.x += 1
        shadow_rect.y += 2
        pygame.draw.rect(surface, (0, 0, 0, 30), shadow_rect, border_radius=radius)

        # Switch track with gradient-like effect
        if self.state:
            track_color = GREEN
            border_color = tuple(max(0, c - 40) for c in GREEN)
        else:
            track_color = BORDER_SUBTLE
            border_color = BORDER

        pygame.draw.rect(surface, track_color, self.rect, border_radius=radius)
        pygame.draw.rect(surface, border_color, self.rect, 1, border_radius=radius)

        # Switch handle with modern styling
        handle_radius = self.rect.height // 2 - 3
        handle_padding = 3

        if self.state:
            handle_x = self.rect.right - handle_radius - handle_padding
        else:
            handle_x = self.rect.x + handle_radius + handle_padding

        handle_y = self.rect.centery
        handle_pos = (handle_x, handle_y)

        # Handle shadow
        shadow_pos = (handle_x + 1, handle_y + 1)
        pygame.draw.circle(surface, (0, 0, 0, 40), shadow_pos, handle_radius + 1)

        # Handle with subtle border
        pygame.draw.circle(surface, WHITE, handle_pos, handle_radius)
        pygame.draw.circle(surface, BORDER_SUBTLE, handle_pos, handle_radius, 1)

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