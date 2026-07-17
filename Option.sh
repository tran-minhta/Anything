#!/bin/bash
set -e

echo "🚀 Chào mừng đến với trình thiết lập hệ thống Talon!"

# --- MẢNG LỰA CHỌN ---
options=("Cơ bản (Apt, Zsh, Common)" "Rust" "Golang" "Node.js" "Neovim (LazyVim)" "Tailscale" "Bắt đầu cài đặt")
selected=()

echo "Chọn các thành phần cần cài đặt (Gõ số tương ứng, chọn 'Bắt đầu cài đặt' để chạy):"
PS3='Lựa chọn của bạn: '

select opt in "${options[@]}"
do
    case $opt in
        "Cơ bản (Apt, Zsh, Common)") selected+=("BASE") ;;
        "Rust") selected+=("RUST") ;;
        "Golang") selected+=("GO") ;;
        "Node.js") selected+=("NODE") ;;
        "Neovim (LazyVim)") selected+=("NVIM") ;;
        "Tailscale") selected+=("TAILSCALE") ;;
        "Bắt đầu cài đặt") break ;;
        *) echo "Lựa chọn không hợp lệ!" ;;
    esac
done

# --- HÀM CÀI ĐẶT ---
# 1. CƠ BẢN
if [[ " ${selected[@]} " =~ " BASE " ]]; then
    echo "📦 Cài đặt gói cơ bản..."
    sudo apt update && sudo apt install -y zsh tmux fzf bat eza stow curl git build-essential unzip wget
    
    # Tạo commonrc
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
fi

# 2. RUST
if [[ " ${selected[@]} " =~ " RUST " ]]; then
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    grep -q ".cargo/bin" ~/.commonrc || echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.commonrc
fi

# 3. GOLANG
if [[ " ${selected[@]} " =~ " GO " ]]; then
    GO_VER=$(curl -s https://go.dev/VERSION?m=text | head -n 1)
    wget "https://dl.google.com/go/${GO_VER}.linux-arm64.tar.gz" -O /tmp/go.tar.gz
    sudo rm -rf /usr/local/go && sudo tar -C /usr/local -xzf /tmp/go.tar.gz
    grep -q "/usr/local/go/bin" ~/.commonrc || echo 'export PATH="$PATH:/usr/local/go/bin"' >> ~/.commonrc
fi

# 4. NODE.JS
if [[ " ${selected[@]} " =~ " NODE " ]]; then
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
fi

# 5. NEOVIM
if [[ " ${selected[@]} " =~ " NVIM " ]]; then
    wget -qO /tmp/nvim.tar.gz https://github.com/neovim/neovim/releases/latest/download/nvim-linux-arm64.tar.gz
    sudo tar -C /opt -xzf /tmp/nvim.tar.gz && sudo ln -sf /opt/nvim-linux-arm64/bin/nvim /usr/local/bin/nvim
    git clone https://github.com/LazyVim/starter ~/.config/nvim && rm -rf ~/.config/nvim/.git
fi

# 6. TAILSCALE
if [[ " ${selected[@]} " =~ " TAILSCALE " ]]; then
    curl -fsSL https://tailscale.com/install.sh | sh
fi

echo "✅ Hoàn tất thiết lập! Hãy chạy 'exec zsh' để áp dụng các thay đổi."
