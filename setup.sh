#!/bin/bash
set -e
echo "🚀 Bắt đầu quá trình thiết lập hệ thống phát triển..."

# ==========================================
# 1. BIẾN MÔI TRƯỜNG & DANH SÁCH GÓI APT
# ==========================================
# Dễ dàng thêm/xóa các gói apt tại đây
APT_PACKAGES=(
    zsh tmux fzf bat eza stow curl git build-essential
    unzip wget apt-transport-https
)

# Cập nhật và cài đặt gói hệ thống cơ bản
echo "📦 Cập nhật Debian và cài đặt các gói Apt cơ bản..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y "${APT_PACKAGES[@]}"


# ==========================================
# 2. CÀI ĐẶT TAILSCALE (VPN / Mạng nội bộ)
# ==========================================
if ! command -v tailscale &> /dev/null; then
    echo "🌐 Đang cài đặt Tailscale..."
    curl -fsSL https://tailscale.com/install.sh | sh
    # sudo tailscale up # (Chạy thủ công sau khi setup để login)
fi


# ==========================================
# 3. RUST ECOSYSTEM (rustup, cargo, công cụ CLI)
# ==========================================
# 3. RUST ECOSYSTEM
if ! command -v cargo >/dev/null 2>&1; then
    echo "🦀 Đang cài đặt Rust & Cargo..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
fi

# TỰ ĐỘNG SYNC PATH CHO CẢ BASH VÀ ZSH
# Kiểm tra nếu PATH đã tồn tại trong file thì không thêm nữa (tránh bị trùng lặp)
if ! grep -q ".cargo/bin" ~/.bashrc; then
    echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
fi

if ! grep -q ".cargo/bin" ~/.zshrc; then
    echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.zshrc
fi

# Cập nhật PATH cho phiên terminal hiện tại
source "$HOME/.cargo/env"


# ==========================================
# 4. GOLANG
# ==========================================
if ! command -v go &> /dev/null; then
    echo "🐹 Đang cài đặt Golang mới nhất..."
    # Lấy phiên bản Go mới nhất tự động
    GO_VERSION=$(curl -s https://go.dev/VERSION?m=text | head -n 1)
    wget "https://dl.google.com/go/${GO_VERSION}.linux-amd64.tar.gz" -O /tmp/go.tar.gz
    sudo rm -rf /usr/local/go
    sudo tar -C /usr/local -xzf /tmp/go.tar.gz
    rm /tmp/go.tar.gz
    # Thêm vào path tạm thời cho script này chạy
    export PATH=$PATH:/usr/local/go/bin
fi


# ==========================================
# 5. NODE.JS & NVM (Node Version Manager)
# ==========================================
if [ ! -d "$HOME/.nvm" ]; then
    echo "🟩 Đang cài đặt NVM, Node.js và npm..."
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    
    nvm install node # Cài bản mới nhất
    nvm use node
fi


# ==========================================
# 6. PYTHON ECOSYSTEM (pipx, uv)
# ==========================================
if ! command -v pipx &> /dev/null; then
    echo "🐍 Đang cài đặt pipx..."
    sudo apt install -y pipx
    pipx ensurepath
fi

if ! command -v uv &> /dev/null; then
    echo "⚡ Đang cài đặt uv (Python package installer siêu tốc)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi


# ==========================================
# 7. NEOVIM & LAZYVIM
# ==========================================
# Cài đặt Neovim từ binary mới nhất thay vì apt (vì apt nvim thường rất cũ)
# 7. NEOVIM & LAZYVIM
if ! command -v nvim &> /dev/null; then
    echo "📝 Đang cài đặt Neovim mới nhất cho ARM64..."
    # Tải bản build chính xác cho ARM64
    wget -qO /tmp/nvim.tar.gz https://github.com/neovim/neovim/releases/latest/download/nvim-linux-arm64.tar.gz
    
    # Xóa bản cũ nếu bị lỗi
    sudo rm -rf /opt/nvim-linux-arm64
    
    # Giải nén vào /opt
    sudo tar -C /opt -xzf /tmp/nvim.tar.gz
    
    # Tạo symlink
    sudo ln -sf /opt/nvim-linux-arm64/bin/nvim /usr/local/bin/nvim
    rm /tmp/nvim.tar.gz
    echo "✅ Đã cài đặt Neovim: $(nvim --version | head -n 1)"
fi

# Khởi tạo LazyVim nếu chưa có
if [ ! -d "$HOME/.config/nvim" ]; then
    echo "💤 Khởi tạo LazyVim..."
    git clone https://github.com/LazyVim/starter ~/.config/nvim
    # Xóa .git để nvim không nhận diện là project của người khác
    rm -rf ~/.config/nvim/.git
fi

# ==========================================
# 8. ZSH, OH-MY-ZSH & POWERLEVEL10K
# ==========================================
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    echo "🐚 Đang cài đặt Oh My Zsh..."
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
fi

if [ ! -d "${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/powerlevel10k" ]; then
    echo "🎨 Đang cài đặt Powerlevel10k Theme..."
    git clone --depth=1 https://github.com/romkatv/powerlevel10k.git ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/powerlevel10k
    
    # Ép zshrc sử dụng theme p10k
    sed -i 's/ZSH_THEME=".*"/ZSH_THEME="powerlevel10k\/powerlevel10k"/g' ~/.zshrc
fi
# ==========================================
# 8.2. CẤU HÌNH ZSH PLUGIN & THEME
# ==========================================
echo "🧩 Đang thiết lập Zsh Plugins và Theme..."

# Đường dẫn Zsh Custom
ZSH_CUSTOM=${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}

# 1. Cài đặt các plugin cần thiết
if [ ! -d "$ZSH_CUSTOM/plugins/zsh-autosuggestions" ]; then
    git clone https://github.com/zsh-users/zsh-autosuggestions "$ZSH_CUSTOM/plugins/zsh-autosuggestions"
fi

if [ ! -d "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting" ]; then
    git clone https://github.com/zsh-users/zsh-syntax-highlighting "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting"
fi

# 2. Cấu hình .zshrc
# Thêm plugin vào danh sách (đảm bảo không bị trùng lặp)
if grep -q "plugins=(git)" ~/.zshrc; then
    sed -i 's/plugins=(git)/plugins=(git zsh-autosuggestions zsh-syntax-highlighting)/g' ~/.zshrc
fi

# 3. Cấu hình màu sắc hiển thị (Terminal Color Scheme)
# Thêm các thiết lập này vào cuối .zshrc
cat << 'EOF' >> ~/.zshrc

# --- Cấu hình màu sắc và hiển thị ---
export TERM=xterm-256color
# Cấu hình highlight cho plugin
ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=8,bold'
EOF

echo "✅ Đã xong phần Zsh plugins và cấu hình màu!"

# ==========================================
# 8.3. CẤU HÌNH FZF CHO ZSH
# ==========================================
echo "🔍 Đang cấu hình FZF cho Zsh..."

# Kiểm tra nếu fzf đã cài đặt qua apt
if command -v fzf >/dev/null 2>&1; then
    # Thêm plugin fzf vào danh sách plugin hiện có nếu chưa có
    if grep -q "plugins=(.*)" ~/.zshrc && ! grep -q "fzf" ~/.zshrc; then
        sed -i 's/plugins=(/plugins=(fzf /' ~/.zshrc
    fi

    # Thêm cấu hình keybinding mặc định vào .zshrc nếu chưa tồn tại
    if ! grep -q "source <(fzf --zsh)" ~/.zshrc; then
        echo "source <(fzf --zsh)" >> ~/.zshrc
    fi
fi

# ==========================================
# 8.5. CẤU HÌNH DÙNG CHUNG BASH & ZSH
# ==========================================
echo "🔗 Cấu hình ~/.commonrc cho Bash và Zsh..."

# 1. Tạo file ~/.commonrc nếu chưa có
if [ ! -f ~/.commonrc ]; then
    touch ~/.commonrc
fi

# 2. Tự động source ~/.commonrc vào .bashrc và .zshrc
for rc in ~/.bashrc ~/.zshrc; do
    if [ -f "$rc" ] && ! grep -q "source ~/.commonrc" "$rc"; then
        echo "[ -f ~/.commonrc ] && source ~/.commonrc" >> "$rc"
    fi
done

# 3. Đưa các PATH quan trọng vào ~/.commonrc (ví dụ Rust & Go)
if ! grep -q ".cargo/bin" ~/.commonrc; then
    echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.commonrc
fi

if ! grep -q "/usr/local/go/bin" ~/.commonrc; then
    echo 'export PATH="/usr/local/go/bin:$PATH"' >> ~/.commonrc
fi


# ==========================================
# 9. ĐỒNG BỘ DOTFILES (GNU Stow)
# ==========================================
echo "🔗 Đang symlink file cấu hình qua GNU Stow..."
if [ -d "$HOME/dotfiles" ]; then
    cd ~/dotfiles
    # Thêm các thư mục bạn muốn stow tại đây
    # stow zsh tmux bin
fi

# ==========================================
# 8.4. THIẾT LẬP ALIAS DÙNG CHUNG
# ==========================================
echo "🛠 Đang thiết lập các lệnh alias hữu ích..."

cat << 'EOF' > ~/.commonrc
# --- ALIAS TÙY CHỈNH ---
# Quản lý Python Environment với UV
alias myenv='uv init . && uv venv'
alias act='source ./.venv/bin/activate'
alias deact='deactivate'
alias uv-pip='uv pip install'

# Công cụ tra cứu và lệnh nhanh
alias help='tldr'
alias cat='bat'
alias ls='eza --icons'
alias ll='eza -lh --icons'

# Git shortcuts
alias gco='git checkout'
alias gs='git status'
alias gp='git push'
EOF

# Đảm bảo các file cấu hình shell sẽ load file này
for rc in ~/.bashrc ~/.zshrc; do
    if [ -f "$rc" ] && ! grep -q "source ~/.commonrc" "$rc"; then
        echo "[ -f ~/.commonrc ] && source ~/.commonrc" >> "$rc"
    fi
done

echo "✅ Đã thiết lập xong toàn bộ alias!"

# ==========================================
# 10. CLEANUP & HOÀN TẤT
# ==========================================
echo "🧹 Dọn dẹp hệ thống..."
sudo apt autoremove -y

# Đổi shell mặc định sang zsh
if [ "$SHELL" != "$(which zsh)" ]; then
    echo "🔄 Đổi shell mặc định sang Zsh..."
    chsh -s $(which zsh)
fi

echo "✅ Hoàn tất! Hãy khởi động lại VM hoặc chạy 'exec zsh' để tận hưởng."
