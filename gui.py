import sys

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QPushButton, QLabel,
    QProgressBar, QTextEdit, QGroupBox, QLineEdit, QComboBox,
    QMessageBox, QCheckBox, QScrollArea, QFrame,
    QInputDialog, QSplitter, QStackedWidget, QSizePolicy,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QColor, QTextCursor, QCloseEvent, QIcon, QPixmap

from installer import Installer


# ─── Color Palette ──────────────────────────────────────────────
C = {
    "bg":           "#0f172a",
    "bg_card":      "#1e293b",
    "bg_card_alt":  "#334155",
    "bg_input":     "#1e293b",
    "bg_sidebar":   "#0f172a",
    "bg_header":    "#0f172a",
    "border":       "#334155",
    "border_light": "#475569",
    "text":         "#f1f5f9",
    "text_dim":     "#94a3b8",
    "text_muted":   "#64748b",
    "accent":       "#38bdf8",
    "accent_hover": "#7dd3fc",
    "green":        "#4ade80",
    "green_bg":     "#166534",
    "red":          "#f87171",
    "red_bg":       "#991b1b",
    "orange":       "#fb923c",
    "orange_bg":    "#9a3412",
    "purple":       "#c084fc",
    "purple_bg":    "#6b21a8",
    "yellow":       "#facc15",
    "sidebar_w":    200,
}

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {C['bg']};
    color: {C['text']};
}}
QLabel {{
    color: {C['text']};
    background: transparent;
}}
QLineEdit {{
    background-color: {C['bg_input']};
    color: {C['text']};
    border: 1px solid {C['border']};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: {C['accent']};
}}
QLineEdit:focus {{
    border: 1px solid {C['accent']};
}}
QLineEdit::placeholder {{
    color: {C['text_muted']};
}}
QPushButton {{
    background-color: {C['bg_card']};
    color: {C['text']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 13px;
}}
QPushButton:hover {{
    background-color: {C['bg_card_alt']};
    border-color: {C['border_light']};
}}
QPushButton:pressed {{
    background-color: {C['border']};
}}
QComboBox {{
    background-color: {C['bg_input']};
    color: {C['text']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {C['text_dim']};
    margin-right: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {C['bg_card']};
    color: {C['text']};
    border: 1px solid {C['border']};
    selection-background-color: {C['accent']};
    selection-color: {C['bg']};
    outline: none;
}}
QProgressBar {{
    background-color: {C['bg_card']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    text-align: center;
    color: {C['text']};
    font-size: 12px;
    height: 22px;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {C['accent']}, stop:1 {C['purple']});
    border-radius: 5px;
}}
QTextEdit {{
    background-color: #0c0c14;
    color: #c8d6e5;
    border: 1px solid {C['border']};
    border-radius: 8px;
    padding: 8px;
    font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
    font-size: 12px;
    selection-background-color: #264f78;
}}
QScrollArea {{
    border: none;
    background: transparent;
}}
QScrollBar:vertical {{
    background: {C['bg']};
    width: 8px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {C['border']};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {C['border_light']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {C['bg']};
    height: 8px;
}}
QScrollBar::handle:horizontal {{
    background: {C['border']};
    border-radius: 4px;
    min-width: 30px;
}}
QCheckBox {{
    spacing: 6px;
    color: {C['text']};
    background: transparent;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {C['border_light']};
    border-radius: 4px;
    background: {C['bg_input']};
}}
QCheckBox::indicator:checked {{
    background-color: {C['accent']};
    border-color: {C['accent']};
}}
QCheckBox::indicator:hover {{
    border-color: {C['accent']};
}}
QTreeWidget {{
    background-color: {C['bg_card']};
    color: {C['text']};
    border: 1px solid {C['border']};
    border-radius: 8px;
    outline: none;
    font-size: 13px;
}}
QTreeWidget::item {{
    padding: 6px 4px;
    border-bottom: 1px solid {C['border']};
}}
QTreeWidget::item:selected {{
    background-color: {C['accent']};
    color: {C['bg']};
}}
QTreeWidget::item:hover {{
    background-color: {C['bg_card_alt']};
}}
QHeaderView::section {{
    background-color: {C['bg_card_alt']};
    color: {C['text']};
    border: none;
    border-bottom: 2px solid {C['border']};
    padding: 8px 6px;
    font-weight: bold;
    font-size: 12px;
}}
QSplitter::handle {{
    background-color: {C['border']};
    width: 1px;
}}
"""


class InstallThread(QThread):
    progress = pyqtSignal(int, str)
    finished_signal = pyqtSignal(bool)

    def __init__(self, installer: Installer, pkg_ids: list):
        super().__init__()
        self.installer = installer
        self.pkg_ids = pkg_ids
        self._stop = False

    def run(self):
        ok = self.installer.install(self.pkg_ids, callback=self._on_progress)
        self.finished_signal.emit(ok)

    def _on_progress(self, percent, message):
        if not self._stop:
            self.progress.emit(percent, message)

    def stop(self):
        self._stop = True


# ─── Sidebar Button ─────────────────────────────────────────────
class SideButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(42)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {C['text_dim']};
                border: none;
                border-radius: 8px;
                padding: 0 16px;
                text-align: left;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {C['bg_card']};
                color: {C['text']};
            }}
        """)
        self._active = False

    def set_active(self, active):
        self._active = active
        if active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {C['bg_card']};
                    color: {C['accent']};
                    border: none;
                    border-radius: 8px;
                    padding: 0 16px;
                    text-align: left;
                    font-size: 13px;
                    font-weight: 600;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {C['text_dim']};
                    border: none;
                    border-radius: 8px;
                    padding: 0 16px;
                    text-align: left;
                    font-size: 13px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: {C['bg_card']};
                    color: {C['text']};
                }}
            """)


# ─── Package Card ───────────────────────────────────────────────
class PackageCard(QFrame):
    def __init__(self, pkg: dict, installed: bool, parent=None):
        super().__init__(parent)
        self.pkg = pkg
        self.pkg_id = pkg["id"]
        self.setFixedHeight(64)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hover = False
        self._update_style(installed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(12)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(True)
        self.checkbox.setFixedSize(20, 20)
        layout.addWidget(self.checkbox, 0, Qt.AlignmentFlag.AlignVCenter)

        info_col = QVBoxLayout()
        info_col.setSpacing(2)

        name_row = QHBoxLayout()
        name_row.setSpacing(8)

        name_lbl = QLabel(f"<b>{pkg['name']}</b>")
        name_lbl.setStyleSheet(f"font-size: 14px; color: {C['text']};")
        name_row.addWidget(name_lbl)

        id_lbl = QLabel(pkg["id"])
        id_lbl.setStyleSheet(f"font-size: 11px; color: {C['text_muted']}; font-family: monospace;")
        name_row.addWidget(id_lbl)
        name_row.addStretch()

        if installed:
            status = QLabel("\u2713 Installed")
            status.setStyleSheet(f"""
                color: {C['green']};
                background-color: {C['green_bg']};
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: bold;
            """)
            name_row.addWidget(status, 0, Qt.AlignmentFlag.AlignVCenter)
        else:
            status = QLabel("\u2717 Not installed")
            status.setStyleSheet(f"""
                color: {C['red']};
                background-color: {C['red_bg']};
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 11px;
            """)
            name_row.addWidget(status, 0, Qt.AlignmentFlag.AlignVCenter)

        info_col.addLayout(name_row)

        desc = pkg.get("description", "")
        if desc:
            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet(f"font-size: 12px; color: {C['text_muted']};")
            info_col.addWidget(desc_lbl)

        layout.addLayout(info_col, 1)

    def _update_style(self, installed):
        self.setStyleSheet(f"""
            PackageCard {{
                background-color: {C['bg_card']};
                border: 1px solid {C['border']};
                border-radius: 10px;
            }}
            PackageCard:hover {{
                border-color: {C['accent']};
                background-color: {C['bg_card_alt']};
            }}
        """)

    def isChecked(self):
        return self.checkbox.isChecked()

    def setChecked(self, val):
        self.checkbox.setChecked(val)


# ─── Manage Package Dialog ──────────────────────────────────────
class ManagePackageDialog(QWidget):
    saved = pyqtSignal()

    def __init__(self, installer: Installer, parent=None, edit_pkg=None):
        super().__init__(parent)
        self.installer = installer
        self.edit_pkg = edit_pkg
        self.setWindowTitle("Edit Package" if edit_pkg else "Add Package")
        self.setMinimumSize(640, 540)
        self.resize(640, 540)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {C['bg']};
                color: {C['text']};
            }}
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {C['border']};
                border-radius: 8px;
                margin-top: 12px;
                padding: 14px 10px 10px 10px;
                color: {C['accent']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }}
        """)
        self._build_ui()
        if edit_pkg:
            self._fill_data()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        title = QLabel("Edit Package" if self.edit_pkg else "Add New Package")
        title.setFont(QFont("Sans Serif", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C['accent']};")
        root.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        container = QWidget()
        form = QVBoxLayout(container)
        form.setSpacing(12)

        row1 = QHBoxLayout()
        row1.setSpacing(12)
        cat_lbl = QLabel("Category:")
        cat_lbl.setFixedWidth(70)
        cat_lbl.setStyleSheet(f"color: {C['text_dim']};")
        row1.addWidget(cat_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
        self.combo_cat = QComboBox()
        self.combo_cat.setMinimumHeight(36)
        for cat in self.installer.get_categories():
            self.combo_cat.addItem(cat["name"], cat["id"])
        row1.addWidget(self.combo_cat, 1)
        form.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(12)
        id_lbl = QLabel("ID:")
        id_lbl.setFixedWidth(70)
        id_lbl.setStyleSheet(f"color: {C['text_dim']};")
        row2.addWidget(id_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
        self.input_id = QLineEdit()
        self.input_id.setPlaceholderText("e.g. rust, docker, tailscale...")
        self.input_id.setMinimumHeight(36)
        row2.addWidget(self.input_id, 1)
        form.addLayout(row2)

        row3 = QHBoxLayout()
        row3.setSpacing(12)
        name_lbl = QLabel("Name:")
        name_lbl.setFixedWidth(70)
        name_lbl.setStyleSheet(f"color: {C['text_dim']};")
        row3.addWidget(name_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Display name")
        self.input_name.setMinimumHeight(36)
        row3.addWidget(self.input_name, 1)
        form.addLayout(row3)

        row4 = QHBoxLayout()
        row4.setSpacing(12)
        desc_lbl = QLabel("Description:")
        desc_lbl.setFixedWidth(70)
        desc_lbl.setStyleSheet(f"color: {C['text_dim']};")
        row4.addWidget(desc_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
        self.input_desc = QLineEdit()
        self.input_desc.setPlaceholderText("Short description")
        self.input_desc.setMinimumHeight(36)
        row4.addWidget(self.input_desc, 1)
        form.addLayout(row4)

        grp_install = QGroupBox("Install command (per platform)")
        gi_layout = QVBoxLayout(grp_install)
        gi_layout.setSpacing(8)
        self.inputs_install = {}
        for plat in ["linux", "darwin", "win32"]:
            row = QHBoxLayout()
            row.setSpacing(8)
            lbl = QLabel(f"{plat}:")
            lbl.setFixedWidth(60)
            lbl.setStyleSheet(f"color: {C['text_dim']}; font-family: monospace;")
            row.addWidget(lbl)
            le = QLineEdit()
            le.setPlaceholderText(f"Install command for {plat}")
            le.setMinimumHeight(32)
            row.addWidget(le, 1)
            self.inputs_install[plat] = le
            gi_layout.addLayout(row)
        form.addWidget(grp_install)

        grp_check = QGroupBox("Check command (per platform)")
        gc_layout = QVBoxLayout(grp_check)
        gc_layout.setSpacing(8)
        self.inputs_check = {}
        for plat in ["linux", "darwin", "win32"]:
            row = QHBoxLayout()
            row.setSpacing(8)
            lbl = QLabel(f"{plat}:")
            lbl.setFixedWidth(60)
            lbl.setStyleSheet(f"color: {C['text_dim']}; font-family: monospace;")
            row.addWidget(lbl)
            le = QLineEdit()
            le.setPlaceholderText(f"Check command for {plat}")
            le.setMinimumHeight(32)
            row.addWidget(le, 1)
            self.inputs_check[plat] = le
            gc_layout.addLayout(row)
        form.addWidget(grp_check)

        scroll.setWidget(container)
        root.addWidget(scroll, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setFixedHeight(40)
        btn_cancel.setMinimumWidth(100)
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: {C['bg_card']};
                color: {C['text_dim']};
                border: 1px solid {C['border']};
                border-radius: 8px;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background-color: {C['bg_card_alt']};
                color: {C['text']};
            }}
        """)
        btn_cancel.clicked.connect(self.close)
        btn_row.addWidget(btn_cancel)

        btn_save = QPushButton("\u2713 Save")
        btn_save.setFixedHeight(40)
        btn_save.setMinimumWidth(120)
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setStyleSheet(f"""
            QPushButton {{
                background-color: {C['accent']};
                color: {C['bg']};
                border: none;
                border-radius: 8px;
                padding: 0 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {C['accent_hover']};
            }}
        """)
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_save)
        root.addLayout(btn_row)

    def _fill_data(self):
        pkg = self.edit_pkg
        self.input_id.setText(pkg.get("id", ""))
        self.input_id.setReadOnly(True)
        self.input_id.setStyleSheet(f"background-color: {C['bg_card_alt']}; color: {C['text_muted']}; border: 1px solid {C['border']}; border-radius: 8px; padding: 8px 12px;")
        self.input_name.setText(pkg.get("name", ""))
        self.input_desc.setText(pkg.get("description", ""))
        cat_id = pkg.get("category_id", "")
        idx = self.combo_cat.findData(cat_id)
        if idx >= 0:
            self.combo_cat.setCurrentIndex(idx)
        install = pkg.get("install", {})
        for plat, le in self.inputs_install.items():
            le.setText(install.get(plat, ""))
        check = pkg.get("check", {})
        for plat, le in self.inputs_check.items():
            le.setText(check.get(plat, ""))

    def _save(self):
        cat_id = self.combo_cat.currentData()
        pkg_id = self.input_id.text().strip()
        name = self.input_name.text().strip()
        desc = self.input_desc.text().strip()

        if not pkg_id or not name:
            QMessageBox.warning(self, "Error", "ID and Name cannot be empty!")
            return

        install = {}
        for plat, le in self.inputs_install.items():
            val = le.text().strip()
            if val:
                install[plat] = val

        check = {}
        for plat, le in self.inputs_check.items():
            val = le.text().strip()
            if val:
                check[plat] = val

        if not install:
            QMessageBox.warning(self, "Error", "Need at least one install command!")
            return

        if self.edit_pkg:
            self.installer.update_package(
                pkg_id, name=name, description=desc,
                install_cmds=install, check_cmds=check,
            )
        else:
            ok = self.installer.add_package(
                cat_id, pkg_id, name, desc, install, check
            )
            if not ok:
                QMessageBox.warning(self, "Error", f"Package '{pkg_id}' already exists!")
                return

        self.saved.emit()
        self.close()


# ─── Main Window ────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.installer = Installer()
        self.install_thread = None
        self.cards: dict[str, PackageCard] = {}
        self.sidebar_buttons: list[SideButton] = []
        self.current_page = 0
        self._build_ui()
        self._load_packages()
        self._set_active_page(0)

    def _build_ui(self):
        self.setWindowTitle("Anything Setup Tool")
        self.setMinimumSize(1000, 700)
        self.resize(1060, 720)

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ──
        sidebar = QWidget()
        sidebar.setFixedWidth(C["sidebar_w"])
        sidebar.setStyleSheet(f"""
            QWidget {{
                background-color: {C['bg_sidebar']};
                border-right: 1px solid {C['border']};
            }}
        """)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(12, 20, 12, 20)
        sb_layout.setSpacing(4)

        logo = QLabel("Anything")
        logo.setFont(QFont("Sans Serif", 18, QFont.Weight.Bold))
        logo.setStyleSheet(f"color: {C['accent']}; padding: 0 4px 12px 4px;")
        sb_layout.addWidget(logo)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {C['border']};")
        sb_layout.addWidget(sep)
        sb_layout.addSpacing(8)

        page_names = [
            "\u2022  Install Packages",
            "\u2022  Manage Packages",
            "\u2022  Install Log",
        ]
        self.page_buttons = []
        for i, name in enumerate(page_names):
            btn = SideButton(name)
            btn.clicked.connect(lambda checked, idx=i: self._set_active_page(idx))
            sb_layout.addWidget(btn)
            self.page_buttons.append(btn)

        sb_layout.addStretch()

        info_box = QFrame()
        info_box.setStyleSheet(f"""
            QFrame {{
                background-color: {C['bg_card']};
                border-radius: 8px;
                padding: 4px;
            }}
        """)
        info_layout = QVBoxLayout(info_box)
        info_layout.setContentsMargins(12, 10, 12, 10)
        info_layout.setSpacing(4)

        platform_lbl = QLabel(f"Platform: {self.installer.platform_key}")
        platform_lbl.setStyleSheet(f"font-size: 11px; color: {C['text_dim']};")
        info_layout.addWidget(platform_lbl)

        total = len(self.installer.get_all_packages())
        count_lbl = QLabel(f"Packages: {total}")
        count_lbl.setStyleSheet(f"font-size: 11px; color: {C['text_dim']};")
        info_layout.addWidget(count_lbl)

        sb_layout.addWidget(info_box)
        root.addWidget(sidebar)

        # ── Main content ──
        content = QWidget()
        content.setStyleSheet(f"background-color: {C['bg']};")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 20, 24, 16)
        content_layout.setSpacing(14)

        # Header
        header_row = QHBoxLayout()
        header_row.setSpacing(12)
        self.page_title = QLabel("Install Packages")
        self.page_title.setFont(QFont("Sans Serif", 20, QFont.Weight.Bold))
        self.page_title.setStyleSheet(f"color: {C['text']};")
        header_row.addWidget(self.page_title)
        header_row.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("\U0001F50D  Search packages...")
        self.search_input.setFixedWidth(280)
        self.search_input.setFixedHeight(36)
        self.search_input.textChanged.connect(self._filter_packages)
        header_row.addWidget(self.search_input)

        self.platform_filter = QComboBox()
        self.platform_filter.setFixedHeight(36)
        self.platform_filter.setFixedWidth(130)
        self.platform_filter.addItem("All", "all")
        self.platform_filter.addItem("\U0001F427 Linux", "linux")
        self.platform_filter.addItem("\U0001F34E macOS", "darwin")
        self.platform_filter.addItem("\U0001F5A5  Windows", "win32")
        self.platform_filter.currentIndexChanged.connect(self._filter_packages)
        header_row.addWidget(self.platform_filter)

        content_layout.addLayout(header_row)

        # Stacked pages
        self.stack = QStackedWidget()

        # Page 0: Install
        self.page_install = self._build_install_page()
        self.stack.addWidget(self.page_install)

        # Page 1: Manage
        self.page_manage = self._build_manage_page()
        self.stack.addWidget(self.page_manage)

        # Page 2: Log
        self.page_log = self._build_log_page()
        self.stack.addWidget(self.page_log)

        content_layout.addWidget(self.stack, 1)

        # Bottom bar
        self.bottom_bar = QWidget()
        self.bottom_bar.setFixedHeight(56)
        self.bottom_bar.setStyleSheet(f"""
            QWidget {{
                background-color: {C['bg']};
                border-top: 1px solid {C['border']};
            }}
        """)
        bb_layout = QHBoxLayout(self.bottom_bar)
        bb_layout.setContentsMargins(0, 0, 0, 0)
        bb_layout.setSpacing(10)

        self.btn_install = QPushButton("\u25B6  Install Selected")
        self.btn_install.setFixedHeight(40)
        self.btn_install.setMinimumWidth(180)
        self.btn_install.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_install.setFont(QFont("Sans Serif", 12, QFont.Weight.Bold))
        self.btn_install.setStyleSheet(f"""
            QPushButton {{
                background-color: {C['accent']};
                color: {C['bg']};
                border: none;
                border-radius: 8px;
                padding: 0 24px;
            }}
            QPushButton:hover {{
                background-color: {C['accent_hover']};
            }}
            QPushButton:disabled {{
                background-color: {C['border']};
                color: {C['text_muted']};
            }}
        """)
        self.btn_install.clicked.connect(self._start_install)
        bb_layout.addWidget(self.btn_install)

        btn_sel = QPushButton("Select All")
        btn_sel.setFixedHeight(36)
        btn_sel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_sel.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {C['text_dim']};
                border: 1px solid {C['border']};
                border-radius: 6px;
                padding: 0 14px;
            }}
            QPushButton:hover {{ color: {C['text']}; border-color: {C['accent']}; }}
        """)
        btn_sel.clicked.connect(self._select_all)
        bb_layout.addWidget(btn_sel)

        btn_desel = QPushButton("Deselect All")
        btn_desel.setFixedHeight(36)
        btn_desel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_desel.setStyleSheet(btn_sel.styleSheet())
        btn_desel.clicked.connect(self._deselect_all)
        bb_layout.addWidget(btn_desel)

        bb_layout.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(22)
        self.progress_bar.setFixedWidth(220)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        bb_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready")
        self.status_label.setFixedHeight(22)
        self.status_label.setStyleSheet(f"color: {C['text_muted']}; padding: 2px 6px; font-size: 12px;")
        bb_layout.addWidget(self.status_label)

        content_layout.addWidget(self.bottom_bar)
        root.addWidget(content, 1)

    # ── Install Page ──
    def _build_install_page(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.packages_container = QWidget()
        self.packages_layout = QVBoxLayout(self.packages_container)
        self.packages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.packages_layout.setSpacing(16)
        scroll.setWidget(self.packages_container)
        layout.addWidget(scroll, 1)

        return widget

    # ── Manage Page ──
    def _build_manage_page(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        btn_add_pkg = QPushButton("+ Add Package")
        btn_add_pkg.setFixedHeight(38)
        btn_add_pkg.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add_pkg.setStyleSheet(f"""
            QPushButton {{
                background-color: {C['accent']};
                color: {C['bg']};
                border: none;
                border-radius: 8px;
                padding: 0 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {C['accent_hover']}; }}
        """)
        btn_add_pkg.clicked.connect(self._add_package)
        btn_row.addWidget(btn_add_pkg)

        btn_add_cat = QPushButton("+ Add Category")
        btn_add_cat.setFixedHeight(38)
        btn_add_cat.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add_cat.setStyleSheet(f"""
            QPushButton {{
                background-color: {C['purple']};
                color: {C['bg']};
                border: none;
                border-radius: 8px;
                padding: 0 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #d8b4fe; }}
        """)
        btn_add_cat.clicked.connect(self._add_category)
        btn_row.addWidget(btn_add_cat)

        btn_edit = QPushButton("Edit")
        btn_edit.setFixedHeight(38)
        btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_edit.setStyleSheet(f"""
            QPushButton {{
                background-color: {C['orange']};
                color: {C['bg']};
                border: none;
                border-radius: 8px;
                padding: 0 16px;
            }}
            QPushButton:hover {{ background-color: #fdba74; }}
        """)
        btn_edit.clicked.connect(self._edit_package)
        btn_row.addWidget(btn_edit)

        btn_remove = QPushButton("Delete")
        btn_remove.setFixedHeight(38)
        btn_remove.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_remove.setStyleSheet(f"""
            QPushButton {{
                background-color: {C['red']};
                color: {C['bg']};
                border: none;
                border-radius: 8px;
                padding: 0 16px;
            }}
            QPushButton:hover {{ background-color: #fca5a5; }}
        """)
        btn_remove.clicked.connect(self._remove_package)
        btn_row.addWidget(btn_remove)

        btn_reload = QPushButton("\u21BB Reload")
        btn_reload.setFixedHeight(38)
        btn_reload.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reload.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {C['text_dim']};
                border: 1px solid {C['border']};
                border-radius: 8px;
                padding: 0 16px;
            }}
            QPushButton:hover {{ color: {C['text']}; border-color: {C['accent']}; }}
        """)
        btn_reload.clicked.connect(self._reload_manage)
        btn_row.addWidget(btn_reload)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.manage_tree = QTreeWidget()
        self.manage_tree.setHeaderLabels(["ID", "Name", "Description", "Category", "Status"])
        self.manage_tree.setColumnWidth(0, 120)
        self.manage_tree.setColumnWidth(1, 160)
        self.manage_tree.setColumnWidth(2, 280)
        self.manage_tree.setColumnWidth(3, 120)
        self.manage_tree.setColumnWidth(4, 90)
        self.manage_tree.setAlternatingRowColors(True)
        self.manage_tree.setRootIsDecorated(False)
        self.manage_tree.itemDoubleClicked.connect(self._edit_package)
        layout.addWidget(self.manage_tree, 1)

        self._reload_manage()
        return widget

    # ── Log Page ──
    def _build_log_page(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_clear = QPushButton("Clear Log")
        btn_clear.setFixedHeight(34)
        btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clear.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {C['text_dim']};
                border: 1px solid {C['border']};
                border-radius: 6px;
                padding: 0 16px;
            }}
            QPushButton:hover {{ color: {C['text']}; border-color: {C['accent']}; }}
        """)
        btn_clear.clicked.connect(self.log_text.clear)
        btn_row.addWidget(btn_clear)
        layout.addLayout(btn_row)

        return widget

    # ── Page navigation ──
    def _set_active_page(self, idx):
        self.current_page = idx
        self.stack.setCurrentIndex(idx)
        titles = ["Install Packages", "Manage Packages", "Install Log"]
        self.page_title.setText(titles[idx])
        for i, btn in enumerate(self.page_buttons):
            btn.set_active(i == idx)

        self.search_input.setVisible(idx == 0)
        self.platform_filter.setVisible(idx == 0)

    # ── Load packages ──
    def _load_packages(self):
        for i in reversed(range(self.packages_layout.count())):
            item = self.packages_layout.itemAt(i)
            if item and item.widget():
                item.widget().setParent(None)

        self.cards.clear()

        for cat in self.installer.get_categories():
            packages = cat.get("packages", [])
            if not packages:
                continue

            cat_group = QGroupBox(f"  {cat['name']}  ({len(packages)})")
            cat_group.setFont(QFont("Sans Serif", 13, QFont.Weight.Bold))
            cat_group.setStyleSheet(f"""
                QGroupBox {{
                    font-weight: bold;
                    border: 1px solid {C['border']};
                    border-radius: 10px;
                    margin-top: 16px;
                    padding: 20px 10px 10px 10px;
                    color: {C['accent']};
                    background-color: transparent;
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 16px;
                    padding: 0 8px;
                }}
            """)
            cat_layout = QVBoxLayout()
            cat_layout.setSpacing(6)

            for pkg in packages:
                installed = self.installer.is_installed(pkg["id"])
                card = PackageCard(pkg, installed)
                card.checkbox.setChecked(True)
                self.cards[pkg["id"]] = card
                cat_layout.addWidget(card)

            cat_group.setLayout(cat_layout)
            self.packages_layout.addWidget(cat_group)

        self._update_status()

    def _filter_packages(self):
        query = self.search_input.text().strip().lower()
        plat_filter = self.platform_filter.currentData()

        for cat_idx in range(self.packages_layout.count()):
            item = self.packages_layout.itemAt(cat_idx)
            if not item:
                continue
            group = item.widget()
            if not group or not isinstance(group, QGroupBox):
                continue

            visible_count = 0
            cat_layout = group.layout()
            if not cat_layout:
                continue

            for card_idx in range(cat_layout.count()):
                card_item = cat_layout.itemAt(card_idx)
                if not card_item:
                    continue
                card = card_item.widget()
                if not card or not isinstance(card, PackageCard):
                    continue

                pkg = card.pkg
                match_query = not query or query in pkg["name"].lower() or query in pkg["id"].lower() or query in pkg.get("description", "").lower()

                match_plat = plat_filter == "all" or plat_filter in pkg.get("install", {})

                visible = match_query and match_plat
                card.setVisible(visible)
                if visible:
                    visible_count += 1

            cat_name = group.title()
            base_name = cat_name.split("(")[0].strip()
            group.setTitle(f"  {base_name}  ({visible_count})")
            group.setVisible(visible_count > 0)

    def _update_status(self):
        total = len(self.cards)
        selected = sum(1 for c in self.cards.values() if c.isChecked())
        self.status_label.setText(f"Selected: {selected}/{total}")

    def _select_all(self):
        for card in self.cards.values():
            if card.isVisible():
                card.setChecked(True)
        self._update_status()

    def _deselect_all(self):
        for card in self.cards.values():
            if card.isVisible():
                card.setChecked(False)
        self._update_status()

    # ── Install ──
    def _start_install(self):
        selected = [cid for cid, card in self.cards.items() if card.isChecked()]
        if not selected:
            QMessageBox.information(self, "Notice", "Select at least one package to install!")
            return

        reply = QMessageBox.question(
            self, "Confirm",
            f"Install {len(selected)} package(s)?\n\n{', '.join(selected[:10])}{'...' if len(selected) > 10 else ''}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.btn_install.setEnabled(False)
        self.progress_bar.setValue(0)
        self._set_active_page(2)
        self.log_text.clear()
        self._log(f"[START] Installing {len(selected)} package(s)...")

        self.install_thread = InstallThread(self.installer, selected)
        self.install_thread.progress.connect(self._on_install_progress)
        self.install_thread.finished_signal.connect(self._on_install_done)
        self.install_thread.start()

    def _on_install_progress(self, percent, message):
        if percent >= 0:
            self.progress_bar.setValue(percent)
        self._log(message)

    def _on_install_done(self, success):
        self.btn_install.setEnabled(True)
        if success:
            self.progress_bar.setValue(100)
            self._log("\n[DONE] All packages installed successfully!")
            self.status_label.setText("All installed!")
        else:
            self._log("\n[DONE] Some packages failed, check log.")
            self.status_label.setText("Failed - check log!")
        self._load_packages()

    def _log(self, msg):
        self.log_text.append(msg)
        self.log_text.moveCursor(QTextCursor.MoveOperation.End)

    # ── Manage ──
    def _reload_manage(self):
        self.manage_tree.clear()
        for cat in self.installer.get_categories():
            cat_item = QTreeWidgetItem([cat["name"], "", "", "", ""])
            cat_item.setFont(0, QFont("Sans Serif", 11, QFont.Weight.Bold))
            cat_item.setBackground(0, QColor(C["bg_card_alt"]))
            cat_item.setForeground(0, QColor(C["accent"]))
            self.manage_tree.addTopLevelItem(cat_item)
            for pkg in cat.get("packages", []):
                installed = self.installer.is_installed(pkg["id"])
                child = QTreeWidgetItem([
                    pkg.get("id", ""),
                    pkg.get("name", ""),
                    pkg.get("description", ""),
                    cat["name"],
                    "\u2713 Yes" if installed else "\u2717 No",
                ])
                if installed:
                    child.setForeground(4, QColor(C["green"]))
                else:
                    child.setForeground(4, QColor(C["red"]))
                cat_item.addChild(child)
            cat_item.setExpanded(True)

    def _add_package(self):
        dlg = ManagePackageDialog(self.installer, self)
        dlg.saved.connect(self._on_manage_changed)
        dlg.show()

    def _add_category(self):
        name, ok = QInputDialog.getText(self, "Add Category", "Category name:")
        if ok and name.strip():
            cat_id = name.strip().lower().replace(" ", "_")
            if not self.installer.add_category(cat_id, name.strip()):
                QMessageBox.warning(self, "Error", "Category already exists!")
            else:
                self._on_manage_changed()

    def _edit_package(self):
        item = self.manage_tree.currentItem()
        if item is None or item.parent() is None:
            QMessageBox.information(self, "Notice", "Select a package to edit!")
            return
        pkg_id = item.text(0)
        pkg = self.installer.get_package(pkg_id)
        if pkg:
            dlg = ManagePackageDialog(self.installer, self, edit_pkg=pkg)
            dlg.saved.connect(self._on_manage_changed)
            dlg.show()

    def _remove_package(self):
        item = self.manage_tree.currentItem()
        if item is None or item.parent() is None:
            QMessageBox.information(self, "Notice", "Select a package to delete!")
            return
        pkg_id = item.text(0)
        pkg_name = item.text(1)
        reply = QMessageBox.question(
            self, "Confirm",
            f"Delete package '{pkg_name}' ({pkg_id})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.installer.remove_package(pkg_id)
            self._on_manage_changed()

    def _on_manage_changed(self):
        self.installer = Installer()
        self._reload_manage()
        self._load_packages()

    def closeEvent(self, event: QCloseEvent):
        if self.install_thread and self.install_thread.isRunning():
            reply = QMessageBox.question(
                self, "Confirm",
                "An install is still running. Quit anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.install_thread.stop()
            self.install_thread.wait(3000)
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
