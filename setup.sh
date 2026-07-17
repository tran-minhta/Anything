#!/bin/bash
set -e
echo "🚀 Bắt đầu quá trình thiết lập hệ thống..."

# 1. CÀI ĐẶT CƠ BẢN
APT_PACKAGES=(zsh tmux fzf bat eza stow curl git build-essential unzip wget apt-transport-https)
sudo apt update && sudo apt install -y "${APT_PACKAGES[@]}"

# 2. KHỞI TẠO ~/.commonrc (Làm sớm để các bước sau ghi vào)
if [ ! -f ~/.commonrc ]; then
    touch ~/.commonrc
    for rc in ~/.bashrc ~/.zshrc; do
        if [ -f "$rc" ] && ! grep -q "source ~/.commonrc" "$rc"; then
            echo "[ -f ~/.commonrc ] && source ~/.commonrc" >> "$rc"
        fi
    done
fi

# 3. RUST & GOLANG (Dùng hàm kiểm tra PATH)
if ! command -v cargo >/dev/null; then
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
fi
grep -q ".cargo/bin" ~/.commonrc || echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.commonrc

if ! command -v go >/dev/null; then
    GO_VERSION=$(curl -s https://go.dev/VERSION?m=text | head -n 1)
    wget "https://dl.google.com/go/${GO_VERSION}.linux-arm64.tar.gz" -O /tmp/go.tar.gz
    sudo rm -rf /usr/local/go && sudo tar -C /usr/local -xzf /tmp/go.tar.gz
fi
grep -q "/usr/local/go/bin" ~/.commonrc || echo 'export PATH="$PATH:/usr/local/go/bin"' >> ~/.commonrc

# 4. NEOVIM (Tối ưu cho ARM64)
if ! command -v nvim &> /dev/null; then
    wget -qO /tmp/nvim.tar.gz https://github.com/neovim/neovim/releases/latest/download/nvim-linux-arm64.tar.gz
    sudo tar -C /opt -xzf /tmp/nvim.tar.gz && sudo ln -sf /opt/nvim-linux-arm64/bin/nvim /usr/local/bin/nvim
fi

# 5. ALIAS THÔNG MINH (Đặt vào .commonrc)
cat << 'EOF' > ~/.commonrc
# --- CẤU HÌNH DÙNG CHUNG ---
export PATH="$HOME/.cargo/bin:$PATH"
export PATH="$PATH:/usr/local/go/bin"

# Alias an toàn (bat --paging=never giúp tránh bị treo như cat cũ)
alias cat='bat --paging=never'
alias myenv='uv init . && uv venv'
alias act='source ./.venv/bin/activate'
alias deact='deactivate'
alias uv-pip='uv pip install'
alias help='tldr'
alias ls='eza --icons'
alias ll='eza -lh --icons'
alias gco='git checkout'
alias gs='git status'
alias gp='git push'

# SSH AGENT
if [ -z "$SSH_AUTH_SOCK" ]; then
    eval $(ssh-agent -s) > /dev/null
    ssh-add ~/.ssh/id_rsa 2>/dev/null
fi
EOF

# 6. HOÀN TẤT ZSH
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
fi

# Cấu hình plugin
sed -i 's/plugins=(git)/plugins=(git zsh-autosuggestions zsh-syntax-highlighting fzf)/g' ~/.zshrc

echo "✅ Hoàn tất! Chạy 'exec zsh' để áp dụng cấu hình."
