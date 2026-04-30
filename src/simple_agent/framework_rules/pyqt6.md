# PyQt6 Rules

## Enum Syntax (CRITICAL)
PyQt6 uses fully-scoped enum names. The old PyQt5 short form does NOT work:
- WRONG: `QTabWidget.North`, `Qt.AlignCenter`, `QBoxLayout.TopToBottom`
- RIGHT: `QTabWidget.TabPosition.North`, `Qt.AlignmentFlag.AlignCenter`, `QBoxLayout.Direction.TopToBottom`

This applies to ALL Qt enums: `Qt.Orientation`, `Qt.GlobalColor`, `QSizePolicy.Policy`, etc.

## Imports
All imports MUST use `PyQt6`:
```python
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QFont
```
Do NOT import from `PyQt5`, `PySide2`, or `PySide6`.

## Signals
Signal connections use the new-style syntax:
```python
button.clicked.connect(self.on_click)  # correct
```
Do NOT use `pyqtSignal` with old-style `SIGNAL()`/`SLOT()` macros.

## Thread Safety
- Never modify UI from a background thread — use signals to communicate
- Use `QThread` with worker objects, not subclassing `QThread.run()`