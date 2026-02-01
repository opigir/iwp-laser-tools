#!/usr/bin/env python3
"""
Basic test script to verify all modules can be imported
"""

def test_imports():
    """Test that all modules can be imported"""
    print("Testing basic imports...")

    try:
        import pygame
        print("✅ pygame imported successfully")
    except ImportError as e:
        print(f"❌ pygame import failed: {e}")
        return False

    try:
        from src.ui_widgets import Button, TextInput, Slider, Panel
        print("✅ ui_widgets imported successfully")
    except ImportError as e:
        print(f"❌ ui_widgets import failed: {e}")
        return False

    try:
        from src.ilda_integration import IntegratedILDASystem
        print("✅ ilda_integration imported successfully")
    except ImportError as e:
        print(f"❌ ilda_integration import failed: {e}")
        return False

    try:
        from src.iwp_protocol import IWPPacket, IWPPoint
        print("✅ iwp_protocol imported successfully")
    except ImportError as e:
        print(f"❌ iwp_protocol import failed: {e}")
        return False

    try:
        from src.udp_server import UDPServer
        print("✅ udp_server imported successfully")
    except ImportError as e:
        print(f"❌ udp_server import failed: {e}")
        return False

    return True

def test_ilda_system():
    """Test basic ILDA system functionality"""
    print("\nTesting ILDA system...")

    try:
        from src.ilda_integration import IntegratedILDASystem

        # Create system
        system = IntegratedILDASystem()
        print("✅ ILDA system created")

        # Get status
        status = system.get_status()
        print(f"✅ Status: {status}")

        # Test player
        player = system.get_player()
        print(f"✅ Player created: {type(player).__name__}")

        return True

    except Exception as e:
        print(f"❌ ILDA system test failed: {e}")
        return False

def test_ui_widgets():
    """Test UI widgets without pygame display"""
    print("\nTesting UI widgets...")

    try:
        from src.ui_widgets import Button, TextInput, Slider, Panel

        # Create widgets (without display)
        button = Button(10, 10, 100, 30, "Test")
        print("✅ Button created")

        text_input = TextInput(10, 50, 100, 30, "test text")
        print("✅ TextInput created")

        slider = Slider(10, 90, 100, 20, 0, 100, 50)
        print("✅ Slider created")

        panel = Panel(0, 0, 200, 150, "Test Panel")
        panel.add_widget(button)
        panel.add_widget(text_input)
        panel.add_widget(slider)
        print("✅ Panel with widgets created")

        return True

    except Exception as e:
        print(f"❌ UI widgets test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Basic IWP Visualizer Test Suite")
    print("=" * 40)

    success = True

    success &= test_imports()
    success &= test_ilda_system()
    success &= test_ui_widgets()

    print("\n" + "=" * 40)
    if success:
        print("🎉 All basic tests passed!")
        print("Ready to test the full visualizer")
    else:
        print("❌ Some tests failed")
        print("Please fix the issues before running the visualizer")