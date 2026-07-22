import sys

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTreeWidget, QTreeWidgetItem, QPushButton, QLabel,
    QProgressBar, QTextEdit, QGroupBox, QLineEdit, QComboBox,
    QMessageBox, QCheckBox, QScrollArea, QGridLayout, QFrame,
    QInputDialog,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QTextCursor, QCloseEvent

from installer import Installer


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


class ManagePackageDialog(QWidget):
    saved = pyqtSignal()

    def __init__(self, installer: Installer, parent=None, edit_pkg=None):
        super().__init__(parent)
        self.installer = installer
        self.edit_pkg = edit_pkg
        self.setWindowTitle("Edit Package" if edit_pkg else "Add Package")
        self.setMinimumSize(620, 520)
        self.resize(620, 520)
        self._build_ui()
        if edit_pkg:
            self._fill_data()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        container = QWidget()
        form = QGridLayout(container)
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(8)

        form.addWidget(QLabel("Category:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        self.combo_cat = QComboBox()
        for cat in self.installer.get_categories():
            self.combo_cat.addItem(cat["name"], cat["id"])
        form.addWidget(self.combo_cat, 0, 1)

        form.addWidget(QLabel("ID:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        self.input_id = QLineEdit()
        self.input_id.setPlaceholderText("e.g. rust, docker, tailscale...")
        form.addWidget(self.input_id, 1, 1)

        form.addWidget(QLabel("Name:"), 2, 0, Qt.AlignmentFlag.AlignRight)
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Display name")
        form.addWidget(self.input_name, 2, 1)

        form.addWidget(QLabel("Description:"), 3, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        self.input_desc = QLineEdit()
        self.input_desc.setPlaceholderText("Short description")
        form.addWidget(self.input_desc, 3, 1)

        grp_install = QGroupBox("Install command (per platform)")
        grp_install.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ccc;
                border-radius: 4px;
                margin-top: 10px;
                padding: 12px 8px 8px 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
        """)
        grp_install_layout = QGridLayout(grp_install)
        grp_install_layout.setSpacing(6)
        self.inputs_install = {}
        for row_idx, plat in enumerate(["linux", "darwin", "win32"]):
            lbl = QLabel(f"{plat}:")
            lbl.setFixedWidth(55)
            grp_install_layout.addWidget(lbl, row_idx, 0)
            le = QLineEdit()
            le.setPlaceholderText(f"Install command for {plat}")
            grp_install_layout.addWidget(le, row_idx, 1)
            self.inputs_install[plat] = le
        form.addWidget(grp_install, 4, 0, 1, 2)

        grp_check = QGroupBox("Check command (per platform)")
        grp_check.setStyleSheet(grp_install.styleSheet())
        grp_check_layout = QGridLayout(grp_check)
        grp_check_layout.setSpacing(6)
        self.inputs_check = {}
        for row_idx, plat in enumerate(["linux", "darwin", "win32"]):
            lbl = QLabel(f"{plat}:")
            lbl.setFixedWidth(55)
            grp_check_layout.addWidget(lbl, row_idx, 0)
            le = QLineEdit()
            le.setPlaceholderText(f"Check command for {plat}")
            grp_check_layout.addWidget(le, row_idx, 1)
            self.inputs_check[plat] = le
        form.addWidget(grp_check, 5, 0, 1, 2)

        scroll.setWidget(container)
        root.addWidget(scroll, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_save = QPushButton("  Save  ")
        btn_save.setMinimumWidth(100)
        btn_save.setStyleSheet("""
            QPushButton { background-color: #4CAF50; color: white; border: none;
                          border-radius: 4px; padding: 8px 16px; font-weight: bold; }
            QPushButton:hover { background-color: #45a049; }
        """)
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_save)

        btn_cancel = QPushButton("  Cancel  ")
        btn_cancel.setMinimumWidth(100)
        btn_cancel.setStyleSheet("""
            QPushButton { background-color: #9e9e9e; color: white; border: none;
                          border-radius: 4px; padding: 8px 16px; }
            QPushButton:hover { background-color: #757575; }
        """)
        btn_cancel.clicked.connect(self.close)
        btn_row.addWidget(btn_cancel)
        root.addLayout(btn_row)

    def _fill_data(self):
        pkg = self.edit_pkg
        self.input_id.setText(pkg.get("id", ""))
        self.input_id.setReadOnly(True)
        self.input_id.setStyleSheet("background-color: #f0f0f0; color: #999;")
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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.installer = Installer()
        self.install_thread = None
        self.checkboxes = {}
        self._build_ui()
        self._load_packages()

    def _build_ui(self):
        self.setWindowTitle("Anything Setup Tool")
        self.setMinimumSize(860, 640)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        header = QLabel("Anything Setup Tool")
        header.setFont(QFont("Sans Serif", 20, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #1976D2; padding: 8px 0;")
        header.setFixedHeight(48)
        main_layout.addWidget(header)

        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Sans Serif", 11))
        main_layout.addWidget(self.tabs, 1)

        self.tab_install = self._build_install_tab()
        self.tab_manage = self._build_manage_tab()
        self.tab_log = self._build_log_tab()

        self.tabs.addTab(self.tab_install, "  Install  ")
        self.tabs.addTab(self.tab_manage, "  Manage  ")
        self.tabs.addTab(self.tab_log, "  Log  ")

        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(8)

        self.btn_install = QPushButton("  Install Selected  ")
        self.btn_install.setFont(QFont("Sans Serif", 11, QFont.Weight.Bold))
        self.btn_install.setFixedHeight(38)
        self.btn_install.setMinimumWidth(180)
        self.btn_install.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_install.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; color: white; border: none;
                border-radius: 6px; padding: 0 20px;
            }
            QPushButton:hover { background-color: #43A047; }
            QPushButton:pressed { background-color: #388E3C; }
            QPushButton:disabled { background-color: #BDBDBD; color: #757575; }
        """)
        self.btn_install.clicked.connect(self._start_install)
        bottom_bar.addWidget(self.btn_install)

        self.btn_select_all = QPushButton("Select All")
        self.btn_select_all.setFixedHeight(38)
        self.btn_select_all.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_select_all.setStyleSheet("""
            QPushButton { border: 1px solid #ccc; border-radius: 4px; padding: 0 12px; }
            QPushButton:hover { background-color: #e3f2fd; }
        """)
        self.btn_select_all.clicked.connect(self._select_all)
        bottom_bar.addWidget(self.btn_select_all)

        self.btn_deselect_all = QPushButton("Deselect All")
        self.btn_deselect_all.setFixedHeight(38)
        self.btn_deselect_all.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_deselect_all.setStyleSheet(self.btn_select_all.styleSheet())
        self.btn_deselect_all.clicked.connect(self._deselect_all)
        bottom_bar.addWidget(self.btn_deselect_all)

        bottom_bar.addStretch()
        main_layout.addLayout(bottom_bar)

        progress_row = QHBoxLayout()
        progress_row.setSpacing(8)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(22)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: 1px solid #ccc; border-radius: 4px; text-align: center; }
            QProgressBar::chunk { background-color: #4CAF50; border-radius: 3px; }
        """)
        progress_row.addWidget(self.progress_bar, 1)

        self.status_label = QLabel("Ready")
        self.status_label.setFixedHeight(22)
        self.status_label.setStyleSheet("color: #666; padding: 2px 6px;")
        progress_row.addWidget(self.status_label)
        main_layout.addLayout(progress_row)

    def _build_install_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        info_bar = QHBoxLayout()
        info_label = QLabel(
            f"Platform: {self.installer.platform_key}  |  "
            f"Total: {len(self.installer.get_all_packages())} packages"
        )
        info_label.setStyleSheet("color: #888; padding: 2px;")
        info_bar.addWidget(info_label)
        info_bar.addStretch()
        layout.addLayout(info_bar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.StyledPanel)
        scroll_content = QWidget()
        self.packages_layout = QVBoxLayout(scroll_content)
        self.packages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.packages_layout.setSpacing(8)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)

        return widget

    def _build_manage_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        btn_add_pkg = QPushButton("+ Add Package")
        btn_add_pkg.setFixedHeight(34)
        btn_add_pkg.setStyleSheet("""
            QPushButton { background-color: #2196F3; color: white; border: none;
                          border-radius: 4px; padding: 0 14px; font-weight: bold; }
            QPushButton:hover { background-color: #1E88E5; }
        """)
        btn_add_pkg.clicked.connect(self._add_package)
        btn_row.addWidget(btn_add_pkg)

        btn_add_cat = QPushButton("+ Add Category")
        btn_add_cat.setFixedHeight(34)
        btn_add_cat.setStyleSheet("""
            QPushButton { background-color: #9C27B0; color: white; border: none;
                          border-radius: 4px; padding: 0 14px; }
            QPushButton:hover { background-color: #AB47BC; }
        """)
        btn_add_cat.clicked.connect(self._add_category)
        btn_row.addWidget(btn_add_cat)

        btn_edit = QPushButton("Edit")
        btn_edit.setFixedHeight(34)
        btn_edit.setStyleSheet("""
            QPushButton { background-color: #FF9800; color: white; border: none;
                          border-radius: 4px; padding: 0 14px; }
            QPushButton:hover { background-color: #FB8C00; }
        """)
        btn_edit.clicked.connect(self._edit_package)
        btn_row.addWidget(btn_edit)

        btn_remove = QPushButton("Delete")
        btn_remove.setFixedHeight(34)
        btn_remove.setStyleSheet("""
            QPushButton { background-color: #f44336; color: white; border: none;
                          border-radius: 4px; padding: 0 14px; }
            QPushButton:hover { background-color: #E53935; }
        """)
        btn_remove.clicked.connect(self._remove_package)
        btn_row.addWidget(btn_remove)

        btn_reload = QPushButton("Reload")
        btn_reload.setFixedHeight(34)
        btn_reload.setStyleSheet("""
            QPushButton { border: 1px solid #ccc; border-radius: 4px; padding: 0 14px; }
            QPushButton:hover { background-color: #f5f5f5; }
        """)
        btn_reload.clicked.connect(self._reload_manage)
        btn_row.addWidget(btn_reload)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.manage_tree = QTreeWidget()
        self.manage_tree.setHeaderLabels(["ID", "Name", "Description", "Category", "Installed"])
        self.manage_tree.setColumnWidth(0, 110)
        self.manage_tree.setColumnWidth(1, 140)
        self.manage_tree.setColumnWidth(2, 260)
        self.manage_tree.setColumnWidth(3, 100)
        self.manage_tree.setColumnWidth(4, 80)
        self.manage_tree.setAlternatingRowColors(True)
        self.manage_tree.setRootIsDecorated(False)
        self.manage_tree.itemDoubleClicked.connect(self._edit_package)
        self.manage_tree.setStyleSheet("""
            QTreeWidget { border: 1px solid #ddd; border-radius: 4px; }
            QTreeWidget::item { padding: 4px 2px; }
            QTreeWidget::item:selected { background-color: #bbdefb; color: black; }
        """)
        layout.addWidget(self.manage_tree, 1)

        self._reload_manage()
        return widget

    def _build_log_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Monospace", 10))
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e; color: #d4d4d4;
                border: 1px solid #333; border-radius: 4px;
                padding: 8px; selection-background-color: #264f78;
            }
        """)
        layout.addWidget(self.log_text, 1)

        btn_clear = QPushButton("Clear Log")
        btn_clear.setFixedHeight(32)
        btn_clear.setStyleSheet("""
            QPushButton { border: 1px solid #ccc; border-radius: 4px; padding: 0 12px; }
            QPushButton:hover { background-color: #f5f5f5; }
        """)
        btn_clear.clicked.connect(self.log_text.clear)
        layout.addWidget(btn_clear)

        return widget

    def _load_packages(self):
        for i in reversed(range(self.packages_layout.count())):
            item = self.packages_layout.itemAt(i)
            if item and item.widget():
                item.widget().setParent(None)

        self.checkboxes.clear()

        for cat in self.installer.get_categories():
            cat_group = QGroupBox(cat["name"])
            cat_group.setFont(QFont("Sans Serif", 12, QFont.Weight.Bold))
            cat_group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    border: 1px solid #ddd;
                    border-radius: 6px;
                    margin-top: 14px;
                    padding: 18px 10px 10px 10px;
                    background-color: #fafafa;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 14px;
                    padding: 0 6px;
                    background-color: #fafafa;
                }
            """)
            cat_layout = QVBoxLayout()
            cat_layout.setSpacing(4)

            for pkg in cat.get("packages", []):
                row = QFrame()
                row.setStyleSheet("""
                    QFrame { border: 1px solid #eee; border-radius: 4px;
                             background-color: white; padding: 2px; }
                    QFrame:hover { background-color: #f5f5f5; }
                """)
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(8, 4, 8, 4)
                row_layout.setSpacing(10)

                cb = QCheckBox()
                cb.setChecked(True)
                cb.stateChanged.connect(self._update_status)
                self.checkboxes[pkg["id"]] = cb
                row_layout.addWidget(cb)

                name_label = QLabel(f"<b>{pkg['name']}</b>")
                name_label.setFixedWidth(140)
                row_layout.addWidget(name_label)

                desc_label = QLabel(pkg.get("description", ""))
                desc_label.setStyleSheet("color: #555;")
                desc_label.setWordWrap(False)
                row_layout.addWidget(desc_label, 1)

                installed = self.installer.is_installed(pkg["id"])
                status_text = "[Installed]" if installed else "[Not installed]"
                status_color = "#4CAF50" if installed else "#f44336"
                status = QLabel(status_text)
                status.setFixedWidth(110)
                status.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                status.setStyleSheet(f"color: {status_color}; font-weight: bold;")
                row_layout.addWidget(status)

                cat_layout.addWidget(row)

            cat_group.setLayout(cat_layout)
            self.packages_layout.addWidget(cat_group)

        self._update_status()

    def _update_status(self):
        total = len(self.checkboxes)
        selected = sum(1 for cb in self.checkboxes.values() if cb.isChecked())
        self.status_label.setText(f"Selected: {selected}/{total}")

    def _select_all(self):
        for cb in self.checkboxes.values():
            cb.setChecked(True)

    def _deselect_all(self):
        for cb in self.checkboxes.values():
            cb.setChecked(False)

    def _start_install(self):
        selected = [pid for pid, cb in self.checkboxes.items() if cb.isChecked()]
        if not selected:
            QMessageBox.information(self, "Notice", "Select at least one package to install!")
            return

        reply = QMessageBox.question(
            self, "Confirm",
            f"Install {len(selected)} package(s):\n{', '.join(selected)}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.btn_install.setEnabled(False)
        self.progress_bar.setValue(0)
        self.tabs.setCurrentWidget(self.tab_log)
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
            self._log("[DONE] All packages installed successfully!")
            self.status_label.setText("All installed!")
        else:
            self._log("[DONE] Some packages failed, check log above.")
            self.status_label.setText("Failed - check log!")
        self._load_packages()

    def _log(self, msg):
        self.log_text.append(msg)
        self.log_text.moveCursor(QTextCursor.MoveOperation.End)

    def _reload_manage(self):
        self.manage_tree.clear()
        for cat in self.installer.get_categories():
            cat_item = QTreeWidgetItem([cat["name"], "", "", "", ""])
            cat_item.setFont(0, QFont("Sans Serif", 11, QFont.Weight.Bold))
            cat_item.setBackground(0, QColor("#e3f2fd"))
            self.manage_tree.addTopLevelItem(cat_item)
            for pkg in cat.get("packages", []):
                installed = self.installer.is_installed(pkg["id"])
                child = QTreeWidgetItem([
                    pkg.get("id", ""),
                    pkg.get("name", ""),
                    pkg.get("description", ""),
                    cat["name"],
                    "Yes" if installed else "No",
                ])
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
    app.setStyle("Fusion")

    palette = app.palette()
    palette.setColor(palette.ColorRole.Window, QColor("#ffffff"))
    palette.setColor(palette.ColorRole.WindowText, QColor("#333333"))
    palette.setColor(palette.ColorRole.Base, QColor("#ffffff"))
    palette.setColor(palette.ColorRole.AlternateBase, QColor("#f9f9f9"))
    palette.setColor(palette.ColorRole.Text, QColor("#333333"))
    palette.setColor(palette.ColorRole.Button, QColor("#f0f0f0"))
    palette.setColor(palette.ColorRole.ButtonText, QColor("#333333"))
    palette.setColor(palette.ColorRole.Highlight, QColor("#bbdefb"))
    palette.setColor(palette.ColorRole.HighlightedText, QColor("#000000"))
    app.setPalette(palette)

    font = QFont("Sans Serif", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
