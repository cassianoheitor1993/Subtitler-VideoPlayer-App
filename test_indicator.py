"""
Test SimpleProgressIndicator standalone
"""
import sys
from PyQt6.QtWidgets import QApplication
from src.simple_progress_indicator import SimpleProgressIndicator

app = QApplication(sys.argv)

# Create indicator
indicator = SimpleProgressIndicator(None)
indicator.update_status("50% - Testing indicator display")
indicator.show()

print(f"Indicator created:")
print(f"  - Visible: {indicator.isVisible()}")
print(f"  - Size: {indicator.width()}x{indicator.height()}")
print(f"  - Position: ({indicator.x()}, {indicator.y()})")
print(f"  - Screen geometry: {app.primaryScreen().geometry()}")
print(f"\nIf you can see a floating window with text, press Ctrl+C to close")

sys.exit(app.exec())
