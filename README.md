Để quản lý một danh sách công cụ đồ sộ gồm nhiều môi trường ngôn ngữ khác nhau (Rust, Go, Node.js, Python) và các công cụ mạng như Tailscale, chúng ta không thể chỉ phụ thuộc vào Aptfile. apt của Debian thường chứa các phiên bản phần mềm quá cũ, không phù hợp cho lập trình viên.
Chúng ta sẽ thiết kế một script theo dạng **Modular (Từng phần)**. Bạn có thể dễ dàng thêm hoặc xóa bất kỳ công cụ nào bằng cách comment/uncomment (thêm # vào đầu dòng) hoặc xóa thẳng block code đó đi.
Dưới đây là phiên bản setup.sh nâng cấp, tích hợp đầy đủ hệ sinh thái bạn yêu cầu:
```bash
#!/bin/bash
set -e
echo "🚀 Bắt đầu quá trình thiết lập hệ thống phát triển..."

# ==========================================
# 1. BIẾN MÔI TRƯỜNG & DANH SÁCH GÓI APT
# ==========================================
# Dễ dàng thêm/xóa các gói apt tại đây
APT_PACKAGES=(
    zsh tmux fzf bat eza stow curl git build-essential
    unzip wget apt-transport-https software-properties-common
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
if ! command -v cargo &> /dev/null; then
    echo "🦀 Đang cài đặt Rust & Cargo..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source "$HOME/.cargo/env"
fi

# Dễ dàng thêm các công cụ viết bằng Rust tại đây
RUST_TOOLS=(tealdeer)
for tool in "${RUST_TOOLS[@]}"; then
    if ! cargo install --list | grep -q "$tool"; then
        echo "   -> Biên dịch $tool bằng Cargo..."
        cargo install "$tool"
    fi
done


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
if ! command -v nvim &> /dev/null; then
    echo "📝 Đang cài đặt Neovim mới nhất..."
    wget -qO /tmp/nvim-linux64.tar.gz https://github.com/neovim/neovim/releases/latest/download/nvim-linux64.tar.gz
    sudo tar -C /opt -xzf /tmp/nvim-linux64.tar.gz
    sudo ln -sf /opt/nvim-linux64/bin/nvim /usr/local/bin/nvim
    rm /tmp/nvim-linux64.tar.gz
fi

# Clone LazyVim starter template nếu thư mục nvim chưa có
if [ ! -d "$HOME/.config/nvim" ]; then
    echo "💤 Khởi tạo LazyVim..."
    git clone https://github.com/LazyVim/starter ~/.config/nvim
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
# 9. ĐỒNG BỘ DOTFILES (GNU Stow)
# ==========================================
echo "🔗 Đang symlink file cấu hình qua GNU Stow..."
if [ -d "$HOME/dotfiles" ]; then
    cd ~/dotfiles
    # Thêm các thư mục bạn muốn stow tại đây
    # stow zsh tmux bin
fi


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

```
### Cách quản lý và chỉnh sửa script này:
 1. **Muốn xóa một công cụ (ví dụ: Go):** Chỉ cần tìm đến block số # 4. GOLANG và bôi đen xóa nó đi, hoặc thêm # vào đầu mỗi dòng trong block đó. Lần sau chạy script, Go sẽ bị bỏ qua.
 2. **Muốn thêm một công cụ CLI của Rust (ví dụ: ripgrep):** Tìm đến block số 3, sửa dòng mảng thành RUST_TOOLS=(tealdeer ripgrep).
 3. **Lưu ý về đường dẫn (PATH):** Các công cụ như Go, NVM, Cargo yêu cầu bạn cập nhật file ~/.zshrc để có thể gõ lệnh trực tiếp. Trong thư mục ~/dotfiles/zsh/ của bạn, hãy đảm bảo file .zshrc có chứa đoạn sau:
```bash
# Cargo / Rust
export PATH="$HOME/.cargo/bin:$PATH"

# Go
export PATH="/usr/local/go/bin:$HOME/go/bin:$PATH"

# NVM
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Pipx
export PATH="$HOME/.local/bin:$PATH"

```
Khi restore máy tính, bạn clone dotfiles về, chạy stow zsh để đưa .zshrc vào đúng vị trí, sau đó chạy setup.sh là toàn bộ công cụ và đường dẫn sẽ ăn khớp hoàn hảo.

