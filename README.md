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

## Hai chế độ

| File | Chức năng |
|------|-----------|
| `setup.sh` | Cài đặt **tất cả** tự động, không cần chọn |
| `Option.sh` | **Lựa chọn** từng gói muốn cài |

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

## Chi tiết cài đặt

### ZSH + Powerlevel10k

- **zsh-autosuggestions** — Gợi ý lệnh khi bạn gõ (nhấn `→` để accept)
- **zsh-syntax-highlighting** — Đổi màu chữ theo cú pháp lệnh (xanh = đúng, đỏ = sai)
- **Powerlevel10k** — Theme prompt nhanh, đẹp, tuỳ biến được. Chạy `p10k configure` sau khi cài xong

### Các alias có sẵn

Được ghi vào `~/.commonrc`, dùng được trên cả bash lẫn zsh:

```bash
alias cat='batcat --paging=never'    # cat đẹp hơn
alias ls='eza --icons'            # ls có icon
alias ll='eza -lh --icons'        # ls chi tiết
alias gs='git status'
alias gp='git push'
alias gco='git checkout'
alias myenv='uv init . && uv venv'
alias act='source ./.venv/bin/activate'
```

### Docker

Cài từ repository chính thức. Sau khi cài xong, user sẽ được thêm vào group `docker` để chạy không cần `sudo`. **Cần logout/login lại** để quyền có hiệu lực.

## Cấu trúc

```
Anything/
├── setup.sh       # Cài tất cả
├── Option.sh      # Chọn cài theo ý muốn
├── .zshrc         # Cấu hình ZSH (oh-my-zsh + p10k + plugins)
├── .commonrc      # Alias & env dùng chung bash/zsh
└── README.md
```
