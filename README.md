# Anything

Bộ công cụ setup tự động cho máy tính mới. Chạy 1 lần là có ngay môi trường phát triển hoàn chỉnh.

## Cài nhanh

```bash
git clone git@github.com:tran-minhta/Anything.git ~/Anything
cd ~/Anything
chmod +x setup.sh
./setup.sh
```

Sau khi chạy xong, thực hiện `exec zsh` để áp dụng.

## 3 chế độ sử dụng

| File | Chức năng |
|------|-----------|
| `setup.sh` | Cài đặt **tất cả** tự động, không cần chọn |
| `Option.sh` | **Lựa chọn** theo số thứ tự trong terminal |
| `gui.py` | **GUI** với PyQt6, quản lý + cài đặt bằng giao diện đồ hoạ |

### Chế độ tuỳ chọn (Option.sh)

```
1) Cơ bản    - zsh, tmux, fzf, bat, eza, git, build-essential
2) Rust       - rustup + cargo
3) Golang     - Go mới nhất từ go.dev
4) Node.js    - NVM + Node.js
5) Neovim     - Neovim mới nhất + LazyVim
6) Tailscale  - VPN nội bộ
7) UV         - Python package installer siêu tốc
8) ZSH        - Oh My Zsh + zsh-autosuggestions + zsh-syntax-highlighting + Powerlevel10k
9) Docker     - Docker CE + Docker Compose
0) TẤT CẢ    - Cài hết
```

Nhập số, cách nhau bằng dấu cách. Ví dụ: `1 5 8` sẽ cài Cơ bản + Neovim + ZSH.

### Chế độ GUI (gui.py)

```bash
pip install PyQt6
python gui.py
```

**Tab Cai dat:** Chon package bang checkbox, bam nut "Cai dat da chon" de bat dau.

**Tab Quan ly:**
- Them package moi: bam "+ Them package", dien ten, lenh cai dat theo platform
- Them category moi: bam "+ Them category"
- Sua package: double-click vao package can sua
- Xoa package: chon package, bam "Xoa"

**Tab Log:** Xem output cai dat real-time.

**packages.json:** File cau hinh danh sach package. Co the sua truc tiep bang text editor hoac qua GUI.

## Chi tiet cai dat

### ZSH + Powerlevel10k

- **zsh-autosuggestions** — Goi y lenh khi ban go (nhan `→` de accept)
- **zsh-syntax-highlighting** — Doi mau chu theo cu phap lenh (xanh = dung, do = sai)
- **Powerlevel10k** — Theme prompt nhanh, dep, tu bien duoc. Chay `p10k configure` sau khi cai xong

### Cac alias co san

Duoc ghi vao `~/.commonrc`, dung duoc tren ca bash lan zsh:

```bash
alias cat='batcat --paging=never'    # cat dep hon
alias ls='eza --icons'               # ls co icon
alias ll='eza -lh --icons'           # ls chi tiet
alias gs='git status'
alias gp='git push'
alias gco='git checkout'
alias myenv='uv init . && uv venv'
alias act='source ./.venv/bin/activate'
```

### Docker

Cai tu repository chinh thuc. Sau khi cai xong, user se duoc them vao group `docker` de khong can `sudo`. **Can logout/login lai** de quyen co hieu luc.

## Cau truc

```
Anything/
├── setup.sh         # Cai tat ca (bash)
├── Option.sh        # Chon cai theo y muon (bash)
├── gui.py           # GUI PyQt6 (python gui.py)
├── installer.py     # Backend cai dat
├── packages.json    # Danh sach package (sua duoc)
├── .zshrc           # Cau hinh ZSH (oh-my-zsh + p10k + plugins)
├── .commonrc        # Alias & env dung chung bash/zsh
└── README.md
```

## Them/sua package

Mo file `packages.json`, them block moi:

```json
{
  "id": "mytool",
  "name": "My Tool",
  "description": "Mo ta cong cu",
  "install": {
    "linux": "sudo apt install -y mytool",
    "darwin": "brew install mytool",
    "win32": "winget install MyTool"
  },
  "check": {
    "linux": "command -v mytool",
    "darwin": "command -v mytool",
    "win32": "where mytool"
  }
}
```

Them vao category phu hop trong `categories`, hoac them category moi.
