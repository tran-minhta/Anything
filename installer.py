import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional


class Installer:
    def __init__(self, json_path: str = None):
        if json_path is None:
            json_path = str(Path(__file__).parent / "packages.json")
        self.json_path = json_path
        self.system = platform.system().lower()
        if self.system == "linux":
            self.platform_key = "linux"
        elif self.system == "darwin":
            self.platform_key = "darwin"
        else:
            self.platform_key = "win32"
        self.data = self._load()

    def _load(self) -> dict:
        with open(self.json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self):
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def get_categories(self) -> list:
        return self.data.get("categories", [])

    def get_all_packages(self) -> list:
        result = []
        for cat in self.data.get("categories", []):
            for pkg in cat.get("packages", []):
                result.append({
                    "category_id": cat["id"],
                    "category_name": cat["name"],
                    **pkg,
                })
        return result

    def get_package(self, pkg_id: str) -> Optional[dict]:
        for cat in self.data.get("categories", []):
            for pkg in cat.get("packages", []):
                if pkg["id"] == pkg_id:
                    return {
                        "category_id": cat["id"],
                        "category_name": cat["name"],
                        **pkg,
                    }
        return None

    def is_installed(self, pkg_id: str) -> bool:
        pkg = self.get_package(pkg_id)
        if pkg is None:
            return False
        checks = pkg.get("check", {})
        cmd = checks.get(self.platform_key)
        if not cmd:
            return False
        try:
            shell = self.platform_key != "win32"
            result = subprocess.run(
                cmd, shell=shell, capture_output=True, timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def install(
        self,
        pkg_ids: list[str],
        callback: Optional[Callable[[int, str], None]] = None,
    ) -> bool:
        total = len(pkg_ids)
        success_count = 0

        for i, pkg_id in enumerate(pkg_ids):
            pkg = self.get_package(pkg_id)
            if pkg is None:
                if callback:
                    callback(self._progress(i, total), f"[SKIP] Khong tim thay: {pkg_id}")
                continue

            if callback:
                callback(self._progress(i, total), f"[...] Dang cai dat: {pkg['name']}")

            install_cmds = pkg.get("install", {})
            cmd = install_cmds.get(self.platform_key)
            if not cmd:
                if callback:
                    callback(self._progress(i, total), f"[SKIP] Khong ho tro nen {self.platform_key}: {pkg['name']}")
                continue

            ok = self._run_cmd(cmd, callback, f"  Cai {pkg['name']}")
            if not ok:
                if callback:
                    callback(self._progress(i, total), f"[FAIL] That bai: {pkg['name']}")
                continue

            post = pkg.get("post_install", {})
            post_cmd = post.get(self.platform_key)
            if post_cmd:
                self._run_cmd(post_cmd, callback, f"  Post-install {pkg['name']}")

            success_count += 1
            if callback:
                callback(self._progress(i, total), f"[OK] Da cai xong: {pkg['name']}")

        if callback:
            callback(100, f"Hoan tat! Da cai thanh cong {success_count}/{total} goi.")

        return success_count == total

    def _run_cmd(
        self,
        cmd: str,
        callback: Optional[Callable[[int, str], None]] = None,
        prefix: str = "",
    ) -> bool:
        shell = self.platform_key != "win32"
        try:
            process = subprocess.Popen(
                cmd,
                shell=shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=0,
            )
            buf = b""
            while True:
                chunk = process.stdout.read(1024)
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf or b"\r" in buf:
                    idx_newline = buf.find(b"\n")
                    idx_cr = buf.find(b"\r")
                    if idx_newline == -1:
                        idx = idx_cr
                    elif idx_cr == -1:
                        idx = idx_newline
                    else:
                        idx = min(idx_newline, idx_cr)
                    line = buf[:idx].decode("utf-8", errors="replace").rstrip()
                    if idx + 1 < len(buf):
                        buf = buf[idx + 1:]
                    else:
                        buf = b""
                    if line and callback:
                        callback(-1, f"{prefix} | {line}")

            if buf:
                line = buf.decode("utf-8", errors="replace").rstrip()
                if line and callback:
                    callback(-1, f"{prefix} | {line}")

            process.wait(timeout=600)
            return process.returncode == 0
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            if callback:
                callback(-1, f"{prefix} | TIMEOUT (killed after 600s)")
            return False
        except Exception as e:
            if callback:
                callback(-1, f"{prefix} | ERROR: {e}")
            return False

    def add_package(
        self,
        category_id: str,
        pkg_id: str,
        name: str,
        description: str,
        install_cmds: dict,
        check_cmds: dict,
        post_install_cmds: dict = None,
    ) -> bool:
        for cat in self.data.get("categories", []):
            if cat["id"] == category_id:
                for pkg in cat.get("packages", []):
                    if pkg["id"] == pkg_id:
                        return False
                new_pkg = {
                    "id": pkg_id,
                    "name": name,
                    "description": description,
                    "install": install_cmds,
                    "check": check_cmds,
                }
                if post_install_cmds:
                    new_pkg["post_install"] = post_install_cmds
                cat.setdefault("packages", []).append(new_pkg)
                self.save()
                return True
        return False

    def add_category(self, cat_id: str, name: str) -> bool:
        for cat in self.data.get("categories", []):
            if cat["id"] == cat_id:
                return False
        self.data.setdefault("categories", []).append({
            "id": cat_id,
            "name": name,
            "packages": [],
        })
        self.save()
        return True

    def remove_package(self, pkg_id: str) -> bool:
        for cat in self.data.get("categories", []):
            packages = cat.get("packages", [])
            for i, pkg in enumerate(packages):
                if pkg["id"] == pkg_id:
                    packages.pop(i)
                    self.save()
                    return True
        return False

    def remove_category(self, cat_id: str) -> bool:
        categories = self.data.get("categories", [])
        for i, cat in enumerate(categories):
            if cat["id"] == cat_id:
                categories.pop(i)
                self.save()
                return True
        return False

    def update_package(
        self,
        pkg_id: str,
        name: str = None,
        description: str = None,
        install_cmds: dict = None,
        check_cmds: dict = None,
        post_install_cmds: dict = None,
    ) -> bool:
        for cat in self.data.get("categories", []):
            for pkg in cat.get("packages", []):
                if pkg["id"] == pkg_id:
                    if name is not None:
                        pkg["name"] = name
                    if description is not None:
                        pkg["description"] = description
                    if install_cmds is not None:
                        pkg["install"] = install_cmds
                    if check_cmds is not None:
                        pkg["check"] = check_cmds
                    if post_install_cmds is not None:
                        pkg["post_install"] = post_install_cmds
                    self.save()
                    return True
        return False

    def _progress(self, current: int, total: int) -> int:
        if total == 0:
            return 100
        return int((current / total) * 100)
