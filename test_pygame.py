#!/usr/bin/env python3
"""
Simple pygame test to check if basic GUI works
"""

import pygame
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_pygame():
    """Test basic pygame functionality"""
    print("Testing pygame...")

    try:
        pygame.init()
        print("✅ Pygame initialized")

        # Test screen creation
        screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Test")
        print("✅ Screen created")

        # Test font creation
        font = pygame.font.Font(None, 24)
        print("✅ Font created")

        # Simple test loop
        clock = pygame.time.Clock()
        running = True
        frames = 0

        print("✅ Running test window for 3 seconds...")

        while running and frames < 180:  # 3 seconds at 60fps
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Clear screen
            screen.fill((50, 50, 50))

            # Draw test text
            text = font.render(f"Frame: {frames}", True, (255, 255, 255))
            screen.blit(text, (10, 10))

            # Draw test shapes
            pygame.draw.circle(screen, (255, 0, 0), (400, 300), 50)
            pygame.draw.rect(screen, (0, 255, 0), (350, 250, 100, 100), 2)

            pygame.display.flip()
            clock.tick(60)
            frames += 1

        print("✅ Pygame test completed successfully")
        pygame.quit()
        return True

    except Exception as e:
        print(f"❌ Pygame test failed: {e}")
        pygame.quit()
        return False

if __name__ == "__main__":
    test_pygame()