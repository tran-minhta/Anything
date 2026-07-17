#!/bin/bash
set -e

echo "🚀 Trình cài đặt hệ thống Talon (Tuần tự & Kiểm tra)"

# 1. Menu lựa chọn
echo "Chọn các gói muốn cài (nhập số, cách nhau bằng dấu cách, chọn '8' để cài tất cả):"
echo "1) Cơ bản | 2) Rust | 3) Golang | 4) Node.js | 5) Neovim | 6) Tailscale | 7) UV | 8) TẤT CẢ"
read -p "Lựa chọn của bạn (Enter để cài tất cả): " choices

if [ -z "$choices" ]; then choices="8"; fi

# 2. Hàng đợi
queue=()
if [[ $choices == *"8"* ]]; then
    queue=("BASE" "RUST" "GO" "NODE" "NVIM" "TAILSCALE" "UV")
else
    for i in $choices; do
        case $i in
            1) queue+=("BASE") ;; 2) queue+=("RUST") ;; 3) queue+=("GO") ;;
            4) queue+=("NODE") ;; 5) queue+=("NVIM") ;; 6) queue+=("TAILSCALE") ;; 7) queue+=("UV") ;;
        esac
    done
fi

# 3. Vòng lặp cài đặt
for task in "${queue[@]}"; do
    echo "--- Đang xử lý: $task ---"
    case $task in
        "BASE")
            sudo apt update && sudo apt install -y zsh tmux fzf bat eza stow curl git build-essential unzip wget
            touch ~/.commonrc
            for rc in ~/.bashrc ~/.zshrc; do
                if ! grep -q "source ~/.commonrc" "$rc"; then echo "[ -f ~/.commonrc ] && source ~/.commonrc" >> "$rc"; fi
            done
            # Chỉ ghi đè nếu file trống hoặc tạo mới
            cat << 'EOF' > ~/.commonrc
alias cat='bat --paging=never'
alias ls='eza --icons'
alias ll='eza -lh --icons'
alias gco='git checkout'
alias gs='git status'
alias gp='git push'
if [ -z "$SSH_AUTH_SOCK" ]; then eval $(ssh-agent -s) > /dev/null; ssh-add ~/.ssh/id_rsa 2>/dev/null; fi
EOF
            ;;
        "RUST")
            if ! command -v cargo &> /dev/null; then
                curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
            fi
            grep -q ".cargo/bin" ~/.commonrc || echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.commonrc
            ;;
        "GO")
            if ! command -v go &> /dev/null; then
                GO_VER=$(curl -s https://go.dev/VERSION?m=text | head -n 1)
                wget -q "https://dl.google.com/go/${GO_VER}.linux-arm64.tar.gz" -O /tmp/go.tar.gz
                sudo rm -rf /usr/local/go && sudo tar -C /usr/local -xzf /tmp/go.tar.gz
            fi
            grep -q "/usr/local/go/bin" ~/.commonrc || echo 'export PATH="$PATH:/usr/local/go/bin"' >> ~/.commonrc
            ;;
        "NODE")
            if [ ! -d "$HOME/.nvm" ]; then
                curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
            fi
            ;;
        "NVIM")
            if ! command -v nvim &> /dev/null; then
                wget -qO /tmp/nvim.tar.gz https://github.com/neovim/neovim/releases/latest/download/nvim-linux-arm64.tar.gz
                sudo tar -C /opt -xzf /tmp/nvim.tar.gz && sudo ln -sf /opt/nvim-linux-arm64/bin/nvim /usr/local/bin/nvim
            fi
            if [ ! -d "$HOME/.config/nvim" ]; then
                git clone https://github.com/LazyVim/starter ~/.config/nvim && rm -rf ~/.config/nvim/.git
            fi
            ;;
        "TAILSCALE")
            if ! command -v tailscale &> /dev/null; then
                curl -fsSL https://tailscale.com/install.sh | sh
            fi
            ;;
        "UV")
            if ! command -v uv &> /dev/null; then
                curl -LsSf https://astral.sh/uv/install.sh | sh
            fi
            ;;
    esac
    echo "✅ Đã kiểm tra/xong: $task"
    sleep 1
done

echo "🎉 Hoàn tất! Hãy chạy 'exec zsh' để áp dụng các thay đổi."
