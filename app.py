import json
import os
import subprocess
import sys
import tempfile
import webbrowser
from pathlib import Path

from PySide6.QtCore import QPoint, QLockFile, QStandardPaths, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QCursor, QIcon, QPixmap, QRegion
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSystemTrayIcon,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

APP_NAME = "DragonTop"
APP_ID = "Vivek.DragonTop"
BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
ASSET_DIR = BASE_DIR / "assets"
DEFAULT_FILE = BASE_DIR / "default_settings.json"


def config_dir() -> Path:
    base = QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)
    path = Path(base) if base else Path(os.environ.get("APPDATA", Path.home())) / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


CONFIG_FILE = config_dir() / "settings.json"


def load_settings() -> dict:
    defaults = json.loads(DEFAULT_FILE.read_text(encoding="utf-8"))
    if not CONFIG_FILE.exists():
        save_settings(defaults)
        return defaults

    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        save_settings(defaults)
        return defaults

    changed = False
    for key, value in defaults.items():
        if key not in data:
            data[key] = value
            changed = True

    # Version 2 assets are already prepared at their native display size.
    # Migrate earlier installs away from fractional runtime scaling, which
    # caused uneven pixel edges and reduced clarity.
    if int(data.get("asset_version", 0)) < int(defaults.get("asset_version", 2)):
        data["asset_version"] = defaults.get("asset_version", 2)
        data["sprite_scale"] = defaults.get("sprite_scale", 1.0)
        changed = True

    if changed:
        save_settings(data)
    return data


def save_settings(data: dict) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def executable_path() -> str:
    return str(Path(sys.executable).resolve())


def set_launch_at_login(enabled: bool) -> None:
    """Add/remove DragonTop in the current user's Windows Run registry key."""
    if sys.platform != "win32":
        return
    import winreg

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{executable_path()}"')
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass


def open_application(value: str) -> None:
    if not value:
        return
    target = os.path.expandvars(os.path.expanduser(value))
    if sys.platform == "win32":
        os.startfile(target)  # type: ignore[attr-defined]
    else:
        subprocess.Popen([target])


class SettingsDialog(QDialog):
    TYPES = ["application", "url", "command", "settings", "quit"]

    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("DragonTop Settings")
        self.resize(720, 440)

        root = QVBoxLayout(self)
        intro = QLabel("Configure the shortcuts shown when you click the dragon.")
        intro.setWordWrap(True)
        root.addWidget(intro)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Action name", "Type", "Value"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        root.addWidget(self.table)
        for action in settings.get("actions", []):
            self.add_row(action)

        controls = QHBoxLayout()
        add = QPushButton("Add action")
        add.clicked.connect(lambda: self.add_row({"name": "New action", "type": "url", "value": "https://"}))
        remove = QPushButton("Remove selected")
        remove.clicked.connect(self.remove_selected)
        browse = QPushButton("Browse application…")
        browse.clicked.connect(self.browse_application)
        controls.addWidget(add)
        controls.addWidget(remove)
        controls.addWidget(browse)
        controls.addStretch()
        root.addLayout(controls)

        options = QHBoxLayout()
        options.addWidget(QLabel("Animation speed"))
        self.speed = QSpinBox()
        self.speed.setRange(70, 500)
        self.speed.setSuffix(" ms")
        self.speed.setValue(settings.get("animation_speed_ms", 140))
        options.addWidget(self.speed)
        self.login = QCheckBox("Start DragonTop when I sign in")
        self.login.setChecked(settings.get("launch_at_login", False))
        options.addWidget(self.login)
        options.addStretch()
        root.addLayout(options)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        save = QPushButton("Save")
        save.setDefault(True)
        save.clicked.connect(self.save)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        root.addLayout(buttons)

    def add_row(self, action: dict) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(action.get("name", "")))
        combo = QComboBox()
        combo.addItems(self.TYPES)
        combo.setCurrentText(action.get("type", "url"))
        self.table.setCellWidget(row, 1, combo)
        self.table.setItem(row, 2, QTableWidgetItem(action.get("value", "")))

    def remove_selected(self) -> None:
        for row in sorted({item.row() for item in self.table.selectedIndexes()}, reverse=True):
            self.table.removeRow(row)

    def browse_application(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select an action", "Select a table row first.")
            return
        path, _ = QFileDialog.getOpenFileName(self, "Choose an application", "C:/", "Programs (*.exe *.bat *.cmd);;All files (*.*)")
        if path:
            combo = self.table.cellWidget(row, 1)
            combo.setCurrentText("application")
            self.table.setItem(row, 2, QTableWidgetItem(path))

    def save(self) -> None:
        actions = []
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            value_item = self.table.item(row, 2)
            actions.append(
                {
                    "name": (name_item.text().strip() if name_item else "") or "Action",
                    "type": self.table.cellWidget(row, 1).currentText(),
                    "value": value_item.text().strip() if value_item else "",
                }
            )
        self.settings["actions"] = actions
        self.settings["animation_speed_ms"] = self.speed.value()
        self.settings["launch_at_login"] = self.login.isChecked()
        try:
            save_settings(self.settings)
            set_launch_at_login(self.login.isChecked())
        except OSError as exc:
            QMessageBox.warning(self, "Could not save settings", str(exc))
            return
        self.accept()


class ActionPanel(QWidget):
    def __init__(self, dragon):
        super().__init__(None, Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.dragon = dragon
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(6)
        self.setStyleSheet(
            "QWidget{background:rgba(18,28,20,242);border:1px solid #315d38;border-radius:14px;}"
            "QPushButton{color:white;background:#25472b;border:0;padding:9px 15px;border-radius:8px;text-align:left;}"
            "QPushButton:hover{background:#397044;}"
        )
        self.rebuild()

    def rebuild(self) -> None:
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for action in self.dragon.settings.get("actions", []):
            button = QPushButton(action.get("name", "Action"))
            button.clicked.connect(lambda _=False, a=action: self.run_action(a))
            self.layout.addWidget(button)
        self.adjustSize()

    def run_action(self, action: dict) -> None:
        action_type = action.get("type")
        value = action.get("value", "")
        try:
            if action_type == "application":
                open_application(value)
            elif action_type == "url" and value:
                webbrowser.open(value)
            elif action_type == "command" and value:
                subprocess.Popen(value, shell=True)
            elif action_type == "settings":
                self.dragon.open_settings()
            elif action_type == "quit":
                QApplication.quit()
        except Exception as exc:
            QMessageBox.warning(self, "Action failed", str(exc))
        self.hide()


class DragonWindow(QWidget):
    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.settings = load_settings()
        self.state = "idle"
        self.frame_index = 0
        self.dragging = False
        self.moved = False

        self.frames = {
            state: [QPixmap(str(path)) for path in sorted(ASSET_DIR.glob(f"{state}_*.png"))]
            for state in ("idle", "hover", "click")
        }
        self.label = QLabel(self)
        self.label.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(self.settings.get("animation_speed_ms", 140))
        self.panel = ActionPanel(self)
        self.update_frame()
        self.position_top_center()
        self.create_tray()

    def create_tray(self) -> None:
        self.tray = QSystemTrayIcon(QIcon(str(ASSET_DIR / "dragon_icon.ico")), self)
        self.tray.setToolTip("DragonTop")
        menu = QMenu()
        show = QAction("Show Dragon", self)
        show.triggered.connect(self.show_dragon)
        menu.addAction(show)
        settings = QAction("Settings…", self)
        settings.triggered.connect(self.open_settings)
        menu.addAction(settings)
        menu.addSeparator()
        quit_action = QAction("Quit DragonTop", self)
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(quit_action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.tray_activated)
        self.tray.show()

    def tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.Trigger:
            self.show_dragon()

    def show_dragon(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

    def position_top_center(self) -> None:
        screen = QApplication.primaryScreen().availableGeometry()
        self.adjustSize()
        self.move(screen.center().x() - self.width() // 2, screen.top() + 8)

    def update_frame(self) -> None:
        frames = self.frames.get(self.state, [])
        if not frames:
            return
        pixmap = frames[self.frame_index % len(frames)]
        scale = float(self.settings.get("sprite_scale", 1.0))
        if abs(scale - 1.0) > 0.001:
            pixmap = pixmap.scaled(
                max(1, int(pixmap.width() * scale)),
                max(1, int(pixmap.height() * scale)),
                Qt.KeepAspectRatio,
                Qt.FastTransformation,
            )

        self.label.setPixmap(pixmap)
        self.label.setFixedSize(pixmap.size())
        self.resize(pixmap.size())

        # Restrict interactions to visible pixels instead of the transparent
        # rectangular canvas around the dragon and its fire animation.
        alpha_mask = pixmap.mask()
        visible_region = QRegion(alpha_mask)
        self.content_rect = visible_region.boundingRect()
        self.setMask(visible_region)

    def tick(self) -> None:
        self.frame_index += 1
        if self.state == "click" and self.frame_index >= len(self.frames["click"]):
            self.state = "hover" if self.underMouse() else "idle"
            self.frame_index = 0
        self.update_frame()

    def enterEvent(self, event) -> None:
        if self.state != "click":
            self.state = "hover"
            self.frame_index = 0
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        if self.state != "click":
            self.state = "idle"
            self.frame_index = 0
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.moved = False
            point = event.globalPosition().toPoint()
            self.drag_offset = point - self.frameGeometry().topLeft()
            self.press_pos = point

    def mouseMoveEvent(self, event) -> None:
        if self.dragging:
            point = event.globalPosition().toPoint()
            if (point - self.press_pos).manhattanLength() > 5:
                self.moved = True
            self.move(point - self.drag_offset)
            if self.panel.isVisible():
                self.panel.hide()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.dragging = False
            if not self.moved:
                self.state = "click"
                self.frame_index = 0
                self.update_frame()
                self.toggle_panel()

    def toggle_panel(self) -> None:
        if self.panel.isVisible():
            self.panel.hide()
            return
        self.panel.rebuild()
        self.panel.adjustSize()
        content = getattr(self, "content_rect", self.rect())
        panel_y = max(0, content.top() + 8)
        point = self.mapToGlobal(QPoint(content.right() + 6, panel_y))
        screen = QApplication.screenAt(QCursor.pos()).availableGeometry()
        if point.x() + self.panel.width() > screen.right():
            point = self.mapToGlobal(QPoint(content.left() - self.panel.width() - 6, panel_y))
        if point.y() + self.panel.height() > screen.bottom():
            point.setY(screen.bottom() - self.panel.height())
        self.panel.move(point)
        self.panel.show()
        self.panel.raise_()

    def open_settings(self) -> None:
        self.panel.hide()
        dialog = SettingsDialog(dict(self.settings), self)
        if dialog.exec():
            self.settings = load_settings()
            self.timer.setInterval(self.settings.get("animation_speed_ms", 140))
            self.panel.rebuild()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("Vivek")
    app.setQuitOnLastWindowClosed(False)

    lock_path = Path(tempfile.gettempdir()) / "DragonTop.lock"
    lock = QLockFile(str(lock_path))
    lock.setStaleLockTime(0)
    if not lock.tryLock(100):
        QMessageBox.information(None, "DragonTop", "DragonTop is already running in the system tray.")
        sys.exit(0)

    dragon = DragonWindow()
    dragon.show()
    sys.exit(app.exec())
