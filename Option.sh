#!/bin/bash
set -e

echo "🚀 Trình cài đặt hệ thống Talon (Tuần tự & An toàn)"

# 1. Menu lựa chọn
echo "Chọn các gói muốn cài (nhập số, cách nhau bằng dấu cách, chọn '8' để cài tất cả):"
echo "1) Cơ bản | 2) Rust | 3) Golang | 4) Node.js | 5) Neovim | 6) Tailscale | 7) UV | 8) TẤT CẢ"
read -p "Lựa chọn của bạn (Enter để cài tất cả): " choices

# Mặc định cài tất cả nếu người dùng chỉ nhấn Enter
if [ -z "$choices" ]; then
    choices="8"
fi

# 2. Xử lý lựa chọn vào hàng đợi (Queue)
queue=()
if [[ $choices == *"8"* ]]; then
    queue=("BASE" "RUST" "GO" "NODE" "NVIM" "TAILSCALE" "UV")
else
    for i in $choices; do
        case $i in
            1) queue+=("BASE") ;;
            2) queue+=("RUST") ;;
            3) queue+=("GO") ;;
            4) queue+=("NODE") ;;
            5) queue+=("NVIM") ;;
            6) queue+=("TAILSCALE") ;;
            7) queue+=("UV") ;;
        esac
    done
fi

# 3. Vòng lặp cài đặt tuần tự
for task in "${queue[@]}"; do
    echo "--- Đang cài đặt: $task ---"
    case $task in
        "BASE")
            sudo apt update && sudo apt install -y zsh tmux fzf bat eza stow curl git build-essential unzip wget
            touch ~/.commonrc
            for rc in ~/.bashrc ~/.zshrc; do
                if ! grep -q "source ~/.commonrc" "$rc"; then echo "[ -f ~/.commonrc ] && source ~/.commonrc" >> "$rc"; fi
            done
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
            curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
            grep -q ".cargo/bin" ~/.commonrc || echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.commonrc
            ;;
        "GO")
            GO_VER=$(curl -s https://go.dev/VERSION?m=text | head -n 1)
            wget -q "https://dl.google.com/go/${GO_VER}.linux-arm64.tar.gz" -O /tmp/go.tar.gz
            sudo rm -rf /usr/local/go && sudo tar -C /usr/local -xzf /tmp/go.tar.gz
            grep -q "/usr/local/go/bin" ~/.commonrc || echo 'export PATH="$PATH:/usr/local/go/bin"' >> ~/.commonrc
            ;;
        "NODE")
            curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
            ;;
        "NVIM")
            wget -qO /tmp/nvim.tar.gz https://github.com/neovim/neovim/releases/latest/download/nvim-linux-arm64.tar.gz
            sudo tar -C /opt -xzf /tmp/nvim.tar.gz && sudo ln -sf /opt/nvim-linux-arm64/bin/nvim /usr/local/bin/nvim
            git clone https://github.com/LazyVim/starter ~/.config/nvim && rm -rf ~/.config/nvim/.git
            ;;
        "TAILSCALE")
            curl -fsSL https://tailscale.com/install.sh | sh
            ;;
        "UV")
            curl -LsSf https://astral.sh/uv/install.sh | sh
            ;;
    esac
    echo "✅ Đã xong: $task"
    sleep 1
done

echo "🎉 Hoàn tất! Hãy chạy 'exec zsh' để áp dụng các thay đổi."
