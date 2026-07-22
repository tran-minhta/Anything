import json
import platform
import subprocess
import threading
import queue
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
                    callback(self._progress(i, total), f"[SKIP] Not found: {pkg_id}")
                continue

            if self.is_installed(pkg_id):
                success_count += 1
                if callback:
                    callback(self._progress(i, total), f"[SKIP] Already installed: {pkg['name']}")
                continue

            if callback:
                callback(self._progress(i, total), f"[...] Installing: {pkg['name']}")

            install_cmds = pkg.get("install", {})
            cmd = install_cmds.get(self.platform_key)
            if not cmd:
                if callback:
                    callback(self._progress(i, total), f"[SKIP] Not supported on {self.platform_key}: {pkg['name']}")
                continue

            ok = self._run_cmd(cmd, callback, f"  {pkg['name']}")
            if not ok:
                if callback:
                    callback(self._progress(i, total), f"[FAIL] Failed: {pkg['name']}")
                continue

            post = pkg.get("post_install", {})
            post_cmd = post.get(self.platform_key)
            if post_cmd:
                self._run_cmd(post_cmd, callback, f"  Post-install {pkg['name']}")

            success_count += 1
            if callback:
                callback(self._progress(i, total), f"[OK] Done: {pkg['name']}")

        if callback:
            callback(100, f"Finished! Installed {success_count}/{total} packages.")

        return success_count == total

    def _run_cmd(
        self,
        cmd: str,
        callback: Optional[Callable[[int, str], None]] = None,
        prefix: str = "",
        timeout: int = 900,
        heartbeat: int = 10,
    ) -> bool:
        shell = self.platform_key != "win32"
        process = None
        try:
            process = subprocess.Popen(
                cmd,
                shell=shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=0,
            )

            output_queue: queue.Queue = queue.Queue()

            def _reader():
                buf = b""
                try:
                    while True:
                        chunk = process.stdout.read(4096)
                        if not chunk:
                            break
                        buf += chunk
                        while b"\n" in buf or b"\r" in buf:
                            nl = buf.find(b"\n")
                            cr = buf.find(b"\r")
                            if nl == -1 and cr == -1:
                                break
                            candidates = [x for x in [nl, cr] if x != -1]
                            idx = min(candidates)
                            line = buf[:idx].decode("utf-8", errors="replace").rstrip()
                            buf = buf[idx + 1:]
                            if line:
                                output_queue.put(("line", line))
                finally:
                    if buf:
                        line = buf.decode("utf-8", errors="replace").rstrip()
                        if line:
                            output_queue.put(("line", line))
                    output_queue.put(("done", None))

            reader_thread = threading.Thread(target=_reader, daemon=True)
            reader_thread.start()

            elapsed = 0
            last_output_time = 0

            while True:
                try:
                    msg_type, data = output_queue.get(timeout=heartbeat)
                except queue.Empty:
                    elapsed += heartbeat
                    if elapsed >= timeout:
                        if callback:
                            callback(-1, f"{prefix} | TIMEOUT: no output for {timeout}s, killing...")
                        process.kill()
                        process.wait()
                        return False
                    if callback:
                        callback(-1, f"{prefix} | ... still running ({elapsed}s elapsed)")
                    continue

                if msg_type == "done":
                    break

                if msg_type == "line":
                    elapsed = 0
                    if callback:
                        callback(-1, f"{prefix} | {data}")

            process.wait(timeout=30)
            return process.returncode == 0

        except subprocess.TimeoutExpired:
            if process:
                process.kill()
                process.wait()
            if callback:
                callback(-1, f"{prefix} | TIMEOUT: process killed after {timeout}s")
            return False
        except Exception as e:
            if process and process.poll() is None:
                process.kill()
                process.wait()
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
