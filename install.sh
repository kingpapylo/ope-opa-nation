#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  OPE-OPA-NATION  —  Smart Installer
#  Supports: Termux (Android) and Linux
#  Usage:    bash install.sh
#  One-line: bash <(curl -fsSL https://raw.githubusercontent.com/YOUR/REPO/main/install.sh)
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Colors ──────────────────────────────────────────────────────────────────
RED='\033[1;31m'    YELLOW='\033[1;33m'  GREEN='\033[1;32m'
CYAN='\033[1;36m'   BLUE='\033[1;34m'   MAGENTA='\033[1;35m'
RESET='\033[0m'     BOLD='\033[1m'       DIM='\033[2m'

RAINBOW=("$RED" "$YELLOW" "$GREEN" "$CYAN" "$BLUE" "$MAGENTA")

rainbow_echo() {
    local text="$1"
    local out=""
    local i=0
    for (( c=0; c<${#text}; c++ )); do
        local ch="${text:$c:1}"
        local color="${RAINBOW[$((i % 6))]}"
        out+="${color}${ch}${RESET}"
        [[ "$ch" != " " ]] && (( i++ )) || true
    done
    echo -e "$out"
}

banner() {
    echo ""
    rainbow_echo "★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★"
    echo ""
    echo -e "${RED}${BOLD}  ██████╗ ██████╗ ███████╗      ██████╗ ██████╗  █████╗${RESET}"
    echo -e "${YELLOW}${BOLD}  ██╔══██╗██╔══██╗██╔════╝     ██╔═══██╗██╔══██╗██╔══██╗${RESET}"
    echo -e "${GREEN}${BOLD}  ██║  ██║██████╔╝█████╗       ██║   ██║██████╔╝███████║${RESET}"
    echo -e "${CYAN}${BOLD}  ██║  ██║██╔═══╝ ██╔══╝       ██║   ██║██╔═══╝ ██╔══██║${RESET}"
    echo -e "${BLUE}${BOLD}  ██████╔╝██║     ███████╗     ╚██████╔╝██║     ██║  ██║${RESET}"
    echo -e "${MAGENTA}${BOLD}  ╚═════╝ ╚═╝     ╚══════╝      ╚═════╝ ╚═╝     ╚═╝  ╚═╝${RESET}"
    echo ""
    echo -e "${RED}${BOLD}  ███╗  ██╗ █████╗ ████████╗██╗ ██████╗ ███╗  ██╗${RESET}"
    echo -e "${YELLOW}${BOLD}  ████╗ ██║██╔══██╗╚══██╔══╝██║██╔═══██╗████╗ ██║${RESET}"
    echo -e "${GREEN}${BOLD}  ██╔██╗██║███████║   ██║   ██║██║   ██║██╔██╗██║${RESET}"
    echo -e "${CYAN}${BOLD}  ██║╚████║██╔══██║   ██║   ██║██║   ██║██║╚████║${RESET}"
    echo -e "${BLUE}${BOLD}  ██║ ╚███║██║  ██║   ██║   ██║╚██████╔╝██║ ╚███║${RESET}"
    echo -e "${MAGENTA}${BOLD}  ╚═╝  ╚══╝╚═╝  ╚═╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚══╝${RESET}"
    echo ""
    rainbow_echo "  ✦  Rainbow AI-Powered Terminal Assistant  ✦"
    echo ""
    rainbow_echo "★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★"
    echo ""
}

info()    { echo -e "${CYAN}${BOLD}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}${BOLD}[ OK ]${RESET}  $*"; }
warn()    { echo -e "${YELLOW}${BOLD}[WARN]${RESET}  $*"; }
error()   { echo -e "${RED}${BOLD}[ERR ]${RESET}  $*" >&2; }
step()    { echo -e "\n${MAGENTA}${BOLD}══>${RESET}  $*"; }

# ── Detect environment ───────────────────────────────────────────────────────
detect_env() {
    if [[ -n "${TERMUX_VERSION:-}" ]] || [[ -d "/data/data/com.termux" ]] || \
       [[ "${PREFIX:-}" == /data/data/com.termux* ]]; then
        ENV_TYPE="termux"
        PYTHON="${PREFIX}/bin/python3"
        PIP="${PREFIX}/bin/pip3"
        INSTALL_DIR="${HOME}/ope-opa-nation"
        STORAGE_DIR="/sdcard/OPE-OPA-NATION"
        BIN_DIR="${PREFIX}/bin"
    else
        ENV_TYPE="linux"
        PYTHON="$(command -v python3 || command -v python)"
        PIP="$(command -v pip3 || command -v pip)"
        INSTALL_DIR="${HOME}/.local/share/ope-opa-nation"
        STORAGE_DIR="${HOME}/OPE-OPA-NATION"
        BIN_DIR="${HOME}/.local/bin"
    fi
}

# ── Install system dependencies ──────────────────────────────────────────────
install_system_deps() {
    step "Installing system dependencies ($ENV_TYPE)"

    if [[ "$ENV_TYPE" == "termux" ]]; then
        info "Updating Termux packages..."
        pkg update -y -o Dpkg::Options::="--force-confnew" 2>/dev/null || pkg update -y
        pkg install -y python git curl 2>/dev/null || true
        success "Termux packages ready"

    else
        # Linux — try common package managers
        if command -v apt-get &>/dev/null; then
            info "Using apt..."
            sudo apt-get update -qq
            sudo apt-get install -y python3 python3-pip python3-venv git curl
        elif command -v dnf &>/dev/null; then
            info "Using dnf..."
            sudo dnf install -y python3 python3-pip git curl
        elif command -v pacman &>/dev/null; then
            info "Using pacman..."
            sudo pacman -Sy --noconfirm python python-pip git curl
        else
            warn "Unknown package manager — skipping system deps (assuming Python is available)"
        fi
        success "System packages ready"
    fi
}

# ── Clone or copy project ────────────────────────────────────────────────────
install_project() {
    step "Installing OPE-OPA-NATION to $INSTALL_DIR"

    mkdir -p "$INSTALL_DIR"

    # If this script is running from inside the project dir, copy it
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    if [[ -f "$SCRIPT_DIR/pyproject.toml" ]]; then
        info "Copying project files from $SCRIPT_DIR..."
        cp -r "$SCRIPT_DIR/." "$INSTALL_DIR/"
        success "Files copied to $INSTALL_DIR"
    else
        # Not inside the project — clone from GitHub
        REPO_URL="${OON_REPO:-https://github.com/kingpapylo/ope-opa-nation.git}"
        info "Cloning from $REPO_URL..."
        git clone --depth=1 "$REPO_URL" "$INSTALL_DIR"
        success "Cloned to $INSTALL_DIR"
    fi
}

# ── Install Python packages ──────────────────────────────────────────────────
install_python_deps() {
    step "Installing Python dependencies"

    if [[ "$ENV_TYPE" == "termux" ]]; then
        # Termux: install directly (no venv needed, no system-package restrictions)
        info "Installing with pip (Termux mode — no venv)..."
        "$PIP" install --upgrade pip --quiet
        "$PIP" install openai==1.35.3 rich==13.7.1 --quiet
        success "Python packages installed"

    else
        # Linux: use a venv inside the install dir
        VENV_DIR="$INSTALL_DIR/.venv"
        info "Creating virtual environment at $VENV_DIR..."
        "$PYTHON" -m venv "$VENV_DIR"
        VENV_PYTHON="$VENV_DIR/bin/python"
        VENV_PIP="$VENV_DIR/bin/pip"

        info "Installing with pip (venv mode)..."
        "$VENV_PIP" install --upgrade pip --quiet
        "$VENV_PIP" install openai==1.35.3 rich==13.7.1 --quiet
        success "Python packages installed in venv"
    fi
}

# ── Create launcher script ───────────────────────────────────────────────────
create_launcher() {
    step "Creating launcher command: ope-opa-nation"

    mkdir -p "$BIN_DIR"

    if [[ "$ENV_TYPE" == "termux" ]]; then
        # Termux: simple launcher using system python
        cat > "$BIN_DIR/ope-opa-nation" <<EOF
#!/data/data/com.termux/files/usr/bin/env python3
import sys, os
sys.path.insert(0, '${INSTALL_DIR}')
os.chdir('${INSTALL_DIR}')
from src.cli import main
main()
EOF
    else
        # Linux: launcher that activates the venv
        cat > "$BIN_DIR/ope-opa-nation" <<EOF
#!/usr/bin/env bash
export VIRTUAL_ENV="${INSTALL_DIR}/.venv"
export PATH="\${VIRTUAL_ENV}/bin:\${PATH}"
exec python3 -c "
import sys, os
sys.path.insert(0, '${INSTALL_DIR}')
os.chdir('${INSTALL_DIR}')
from src.cli import main
main()
" "\$@"
EOF
    fi

    chmod +x "$BIN_DIR/ope-opa-nation"

    # Short aliases: oon and opa
    cp "$BIN_DIR/ope-opa-nation" "$BIN_DIR/oon"
    chmod +x "$BIN_DIR/oon"
    cp "$BIN_DIR/ope-opa-nation" "$BIN_DIR/opa"
    chmod +x "$BIN_DIR/opa"

    success "Launchers created: ope-opa-nation  |  oon  |  opa"
}

# ── Save project copy to phone storage (Termux only) ────────────────────────
save_to_phone_storage() {
    if [[ "$ENV_TYPE" != "termux" ]]; then
        return
    fi

    step "Saving project to phone storage: $STORAGE_DIR"

    # Check if sdcard is accessible (user may not have granted storage permission yet)
    if [[ ! -d "/sdcard" ]]; then
        warn "/sdcard not found. Requesting storage permission..."
        termux-setup-storage
        sleep 3
    fi

    if [[ -d "/sdcard" ]]; then
        mkdir -p "$STORAGE_DIR"
        # Copy source files (exclude venv and cache)
        rsync -a --exclude='.venv' --exclude='__pycache__' \
              --exclude='*.pyc' --exclude='.git' \
              "$INSTALL_DIR/" "$STORAGE_DIR/" 2>/dev/null \
        || cp -r "$INSTALL_DIR/." "$STORAGE_DIR/"

        success "Project saved to phone storage: $STORAGE_DIR"
        info "You can browse files in your Android Files app under 'OPE-OPA-NATION'"
    else
        warn "Could not access /sdcard — storage permission may not be granted."
        warn "Run 'termux-setup-storage' then re-run this installer."
    fi
}

# ── Add BIN_DIR to PATH in shell config ─────────────────────────────────────
add_to_path() {
    step "Ensuring $BIN_DIR is in PATH"

    local shell_rc=""
    if [[ -n "${BASH_VERSION:-}" ]] || [[ "$(basename "${SHELL:-bash}")" == "bash" ]]; then
        shell_rc="${HOME}/.bashrc"
    elif [[ "$(basename "${SHELL:-}")" == "zsh" ]]; then
        shell_rc="${HOME}/.zshrc"
    fi

    if [[ -n "$shell_rc" ]]; then
        local path_line="export PATH=\"${BIN_DIR}:\${PATH}\""
        if ! grep -qF "$BIN_DIR" "$shell_rc" 2>/dev/null; then
            echo "" >> "$shell_rc"
            echo "# OPE-OPA-NATION" >> "$shell_rc"
            echo "$path_line" >> "$shell_rc"
            success "Added $BIN_DIR to $shell_rc"
        else
            info "$BIN_DIR already in $shell_rc"
        fi
    fi

    # Also export for current shell session
    export PATH="${BIN_DIR}:${PATH}"
}

# ── Print final instructions ─────────────────────────────────────────────────
print_done() {
    echo ""
    rainbow_echo "★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★"
    echo ""
    echo -e "${GREEN}${BOLD}  Installation complete!${RESET}"
    echo ""
    echo -e "${CYAN}  Environment : ${BOLD}${ENV_TYPE}${RESET}"
    echo -e "${CYAN}  Install dir : ${BOLD}${INSTALL_DIR}${RESET}"
    if [[ "$ENV_TYPE" == "termux" ]]; then
    echo -e "${CYAN}  Phone storage: ${BOLD}${STORAGE_DIR}${RESET}"
    fi
    echo ""
    echo -e "${YELLOW}${BOLD}  Set your OpenAI API key:${RESET}"
    echo -e "  ${DIM}export OPENAI_API_KEY=\"sk-...\"${RESET}"
    echo -e "  ${DIM}(add to ~/.bashrc to make it permanent)${RESET}"
    echo ""
    echo -e "${YELLOW}${BOLD}  Start OPE-OPA-NATION:${RESET}"
    echo -e "  ${GREEN}${BOLD}opa${RESET}              ${DIM}# quickest way to start${RESET}"
    echo -e "  ${GREEN}${BOLD}oon${RESET}              ${DIM}# short alias${RESET}"
    echo -e "  ${GREEN}${BOLD}ope-opa-nation${RESET}   ${DIM}# full command${RESET}"
    echo ""
    echo -e "  ${DIM}If command not found, run:  source ~/.bashrc${RESET}"
    echo ""
    rainbow_echo "★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★"
    echo ""
}

# ── Main ─────────────────────────────────────────────────────────────────────
main() {
    banner
    detect_env
    info "Detected environment: ${BOLD}${ENV_TYPE}${RESET}"
    install_system_deps
    install_project
    install_python_deps
    create_launcher
    save_to_phone_storage
    add_to_path
    print_done
}

main "$@"
