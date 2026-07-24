#!/bin/bash
set -e
echo "🚀 Bắt đầu quá trình thiết lập hệ thống..."

# 1. CÀI ĐẶT CƠ BẢN
APT_PACKAGES=(zsh tmux fzf bat eza stow curl git build-essential unzip wget apt-transport-https)
sudo apt update && sudo apt install -y "${APT_PACKAGES[@]}"

# Tạo symlink bat -> batcat (trên Ubuntu binary tên batcat)
if command -v batcat &>/dev/null && ! command -v bat &>/dev/null; then
    sudo ln -sf "$(which batcat)" /usr/local/bin/bat
fi

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

# 4. NVM & NODE.js
if [ ! -d "$HOME/.nvm" ]; then
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
fi
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Đồng bộ nvm vào .zshrc nếu chưa có
if ! grep -q 'NVM_DIR' ~/.zshrc 2>/dev/null; then
    cat << 'NVMEOF' >> ~/.zshrc

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
NVMEOF
fi

# Cài Node.js stable qua nvm
if command -v nvm &>/dev/null; then
    nvm install --lts
    nvm use --lts
    nvm alias default lts/*
fi

# 5. BUN
if ! command -v bun &> /dev/null; then
    curl -fsSL https://bun.sh/install | bash
fi
grep -q ".bun/bin" ~/.commonrc || echo 'export PATH="$HOME/.bun/bin:$PATH"' >> ~/.commonrc

# 6. UV (Python package manager)
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi
grep -q ".local/bin" ~/.commonrc || echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.commonrc

# 7. NEOVIM (Tối ưu cho ARM64)
if ! command -v nvim &> /dev/null; then
    wget -qO /tmp/nvim.tar.gz https://github.com/neovim/neovim/releases/latest/download/nvim-linux-arm64.tar.gz
    sudo tar -C /opt -xzf /tmp/nvim.tar.gz && sudo ln -sf /opt/nvim-linux-arm64/bin/nvim /usr/local/bin/nvim
fi

# 8. LAZYVIM (Neovim config distribution)
if [ ! -d "$HOME/.config/nvim" ]; then
    git clone https://github.com/LazyVim/starter "$HOME/.config/nvim"
    rm -rf "$HOME/.config/nvim/.git"
fi

# 9. ALIAS THÔNG MINH (Đặt vào .commonrc)
cat << 'EOF' > ~/.commonrc
# --- CẤU HÌNH DÙNG CHUNG ---
export PATH="$HOME/.cargo/bin:$HOME/.bun/bin:$PATH"
export PATH="$PATH:/usr/local/go/bin"

# Alias an toàn (bat --paging=never giúp tránh bị treo như cat cũ)
alias cat='batcat --paging=never'
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
# 10. DOCKER & DOCKER COMPOSE
if ! command -v docker >/dev/null; then
    echo "🐳 Đang cài đặt Docker và Docker Compose..."
    # Thêm GPG key chính thức của Docker
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/$(. /etc/os-release && echo "$ID")/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc

    # Thêm repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/$(. /etc/os-release && echo "$ID") \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Cấp quyền cho user hiện tại chạy docker không cần sudo
    sudo usermod -aG docker $USER
fi
# 11. ZSH, OH-MY-ZSH, PLUGINS & POWERLEVEL10K
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
fi

ZSH_CUSTOM="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}"

# Clone plugin zsh-autosuggestions (gợi ý code)
if [ ! -d "$ZSH_CUSTOM/plugins/zsh-autosuggestions" ]; then
    git clone https://github.com/zsh-users/zsh-autosuggestions "$ZSH_CUSTOM/plugins/zsh-autosuggestions"
fi

# Clone plugin zsh-syntax-highlighting (đổi màu chữ theo cú pháp)
if [ ! -d "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting" ]; then
    git clone https://github.com/zsh-users/zsh-syntax-highlighting "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting"
fi

# Clone theme Powerlevel10k
if [ ! -d "$ZSH_CUSTOM/themes/powerlevel10k" ]; then
    git clone --depth=1 https://github.com/romkatv/powerlevel10k "$ZSH_CUSTOM/themes/powerlevel10k"
fi

# Cấu hình theme và plugin trong .zshrc
sed -i 's/^ZSH_THEME=.*/ZSH_THEME="powerlevel10k\/powerlevel10k"/g' ~/.zshrc
sed -i 's/^plugins=.*/plugins=(git zsh-autosuggestions zsh-syntax-highlighting fzf)/g' ~/.zshrc

echo "✅ Hoàn tất! Chạy 'exec zsh' để áp dụng cấu hình."
