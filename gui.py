import sys
import platform
import subprocess
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTreeWidget, QTreeWidgetItem, QPushButton, QLabel,
    QProgressBar, QTextEdit, QGroupBox, QLineEdit, QComboBox,
    QMessageBox, QCheckBox, QScrollArea, QGridLayout,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QTextCursor

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
        self.setWindowTitle("Packages edit" if edit_pkg else "Add packages")
        self.setMinimumSize(500, 450)
        self._build_ui()
        if edit_pkg:
            self._fill_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        form = QGridLayout()
        form.setSpacing(10)

        form.addWidget(QLabel("Category:"), 0, 0)
        self.combo_cat = QComboBox()
        for cat in self.installer.get_categories():
            self.combo_cat.addItem(cat["name"], cat["id"])
        form.addWidget(self.combo_cat, 0, 1)

        form.addWidget(QLabel("ID:"), 1, 0)
        self.input_id = QLineEdit()
        self.input_id.setPlaceholderText("e.g. rust, docker, tailscale...")
        form.addWidget(self.input_id, 1, 1)

        form.addWidget(QLabel("Name:"), 2, 0)
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Display name")
        form.addWidget(self.input_name, 2, 1)

        form.addWidget(QLabel("Description:"), 3, 0)
        self.input_desc = QLineEdit()
        self.input_desc.setPlaceholderText("Short description")
        form.addWidget(self.input_desc, 3, 1)

        grp_install = QGroupBox("Install command (per platform)")
        grp_layout = QVBoxLayout()
        self.inputs_install = {}
        for plat in ["linux", "darwin", "win32"]:
            row = QHBoxLayout()
            row.addWidget(QLabel(f"{plat}:"))
            le = QLineEdit()
            le.setPlaceholderText(f"Install command for {plat}")
            row.addWidget(le)
            grp_layout.addLayout(row)
            self.inputs_install[plat] = le
        grp_install.setLayout(grp_layout)
        form.addWidget(grp_install, 4, 0, 1, 2)

        grp_check = QGroupBox("Check command (per platform)")
        grp_layout2 = QVBoxLayout()
        self.inputs_check = {}
        for plat in ["linux", "darwin", "win32"]:
            row = QHBoxLayout()
            row.addWidget(QLabel(f"{plat}:"))
            le = QLineEdit()
            le.setPlaceholderText(f"Check command for {plat}")
            row.addWidget(le)
            grp_layout2.addLayout(row)
            self.inputs_check[plat] = le
        grp_check.setLayout(grp_layout2)
        form.addWidget(grp_check, 5, 0, 1, 2)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_save = QPushButton("Save")
        btn_save.clicked.connect(self._save)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.close)
        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

    def _fill_data(self):
        pkg = self.edit_pkg
        self.input_id.setText(pkg.get("id", ""))
        self.input_id.setReadOnly(True)
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
        self.setMinimumSize(800, 600)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        header = QLabel("Anything Setup Tool")
        header.setFont(QFont("Sans Serif", 18, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #2196F3; padding: 10px;")
        main_layout.addWidget(header)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.tab_install = self._build_install_tab()
        self.tab_manage = self._build_manage_tab()
        self.tab_log = self._build_log_tab()

        self.tabs.addTab(self.tab_install, "  Apply  ")
        self.tabs.addTab(self.tab_manage, "  Manager  ")
        self.tabs.addTab(self.tab_log, "  Log  ")

        bottom = QHBoxLayout()

        self.btn_install = QPushButton("  Install Selected  ")
        self.btn_install.setFont(QFont("Sans Serif", 11, QFont.Weight.Bold))
        self.btn_install.setMinimumHeight(40)
        self.btn_install.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:pressed { background-color: #3d8b40; }
            QPushButton:disabled { background-color: #ccc; color: #666; }
        """)
        self.btn_install.clicked.connect(self._start_install)
        bottom.addWidget(self.btn_install)

        self.btn_select_all = QPushButton("Select All")
        self.btn_select_all.clicked.connect(self._select_all)
        bottom.addWidget(self.btn_select_all)

        self.btn_deselect_all = QPushButton("Deselect All")
        self.btn_deselect_all.clicked.connect(self._deselect_all)
        bottom.addWidget(self.btn_deselect_all)

        main_layout.addLayout(bottom)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(25)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #666; padding: 2px;")
        main_layout.addWidget(self.status_label)

    def _build_install_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        info = QLabel(f"Platform: {self.installer.platform_key}  |  Total: {len(self.installer.get_all_packages())} packages")
        info.setStyleSheet("color: #888; padding: 5px;")
        layout.addWidget(info)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.packages_layout = QVBoxLayout(scroll_content)
        self.packages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        return widget

    def _build_manage_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        btn_row = QHBoxLayout()

        btn_add_pkg = QPushButton("  + Add package  ")
        btn_add_pkg.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        btn_add_pkg.clicked.connect(self._add_package)
        btn_row.addWidget(btn_add_pkg)

        btn_add_cat = QPushButton("  + Add category  ")
        btn_add_cat.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #7B1FA2; }
        """)
        btn_add_cat.clicked.connect(self._add_category)
        btn_row.addWidget(btn_add_cat)

        btn_edit = QPushButton("  Edit  ")
        btn_edit.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #F57C00; }
        """)
        btn_edit.clicked.connect(self._edit_package)
        btn_row.addWidget(btn_edit)

        btn_remove = QPushButton("  Delete  ")
        btn_remove.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #D32F2F; }
        """)
        btn_remove.clicked.connect(self._remove_package)
        btn_row.addWidget(btn_remove)

        btn_reload = QPushButton("  Reload  ")
        btn_reload.clicked.connect(self._reload_manage)
        btn_row.addWidget(btn_reload)

        layout.addLayout(btn_row)

        self.manage_tree = QTreeWidget()
        self.manage_tree.setHeaderLabels(["ID", "Name", "Info", "Category", "Exist"])
        self.manage_tree.setColumnWidth(0, 120)
        self.manage_tree.setColumnWidth(1, 150)
        self.manage_tree.setColumnWidth(2, 250)
        self.manage_tree.setColumnWidth(3, 100)
        self.manage_tree.setAlternatingRowColors(True)
        self.manage_tree.itemDoubleClicked.connect(self._edit_package)
        layout.addWidget(self.manage_tree)

        self._reload_manage()

        return widget

    def _build_log_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Monospace", 10))
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #333;
                padding: 8px;
            }
        """)
        layout.addWidget(self.log_text)

        btn_clear = QPushButton("Clear log")
        btn_clear.clicked.connect(self.log_text.clear)
        layout.addWidget(btn_clear)

        return widget

    def _load_packages(self):
        for i in reversed(range(self.packages_layout.count())):
            child = self.packages_layout.itemAt(i)
            if child.widget():
                child.widget().setParent(None)

        self.checkboxes.clear()

        for cat in self.installer.get_categories():
            cat_group = QGroupBox(f"  {cat['name']}  ")
            cat_group.setFont(QFont("Sans Serif", 12, QFont.Weight.Bold))
            cat_group.setStyleSheet("""
                QGroupBox {
                    border: 1px solid #ddd;
                    border-radius: 6px;
                    margin-top: 12px;
                    padding-top: 15px;
                    background-color: #fafafa;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 12px;
                    padding: 0 6px;
                }
            """)
            cat_layout = QVBoxLayout()

            for pkg in cat.get("packages", []):
                row = QHBoxLayout()
                cb = QCheckBox()
                cb.setChecked(True)
                cb.stateChanged.connect(self._update_status)
                self.checkboxes[pkg["id"]] = cb
                row.addWidget(cb)

                name_label = QLabel(f"<b>{pkg['name']}</b>")
                name_label.setMinimumWidth(150)
                row.addWidget(name_label)

                desc_label = QLabel(pkg.get("description", ""))
                desc_label.setStyleSheet("color: #666;")
                row.addWidget(desc_label)

                installed = self.installer.is_installed(pkg["id"])
                status = QLabel("  [Installed]  " if installed else "  [Not installed]  ")
                status.setStyleSheet(
                    "color: #4CAF50; font-weight: bold;" if installed
                    else "color: #f44336;"
                )
                row.addWidget(status)

                cat_layout.addLayout(row)

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
            f"Install {len(selected)} package(s): {', '.join(selected)}?",
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
            self._log("[DONE] Success!")
            self.status_label.setText("Success!")
        else:
            self._log("[DONE] Failed, check log.")
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
        from PyQt6.QtWidgets import QInputDialog
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


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    palette = app.palette()
    palette.setColor(palette.ColorRole.Window, QColor("#ffffff"))
    palette.setColor(palette.ColorRole.WindowText, QColor("#333333"))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
