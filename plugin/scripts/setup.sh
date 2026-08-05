#!/usr/bin/env bash
# Lawdog plugin bootstrap — configures LAWDOG_CASES_DIR and validates dependencies
set -euo pipefail

DEFAULT_DIR="$HOME/lawdog-cases"

# ── helpers ────────────────────────────────────────────────────────────────

print_header() { echo "=== $* ==="; }
print_ok()     { echo "✓ $*"; }
print_warn()   { echo "⚠  $*"; }

detect_profile() {
    if [ -f "$HOME/.zshrc" ]; then echo "$HOME/.zshrc"
    elif [ -f "$HOME/.bash_profile" ]; then echo "$HOME/.bash_profile"
    else echo "$HOME/.bashrc"
    fi
}

expand_tilde() {
    # Replace leading ~ with $HOME (handles cases where read gives literal ~)
    echo "${1/#\~/$HOME}"
}

read_cases_dir() {
    local INPUT
    echo "Onde o lawdog deve salvar os arquivos dos casos?" >&2
    echo "Pressione Enter para usar o padrão: $DEFAULT_DIR" >&2
    printf "> " >&2
    read -r INPUT
    if [ -z "$INPUT" ]; then
        echo "$DEFAULT_DIR"
    else
        expand_tilde "$INPUT"
    fi
}

write_to_profile() {
    local profile="$1"
    local cases_dir="$2"

    # Filter out any existing LAWDOG_CASES_DIR line, create file if absent
    grep -v "LAWDOG_CASES_DIR" "$profile" > "${profile}.tmp" 2>/dev/null || true
    printf 'export LAWDOG_CASES_DIR="%s"\n' "$cases_dir" >> "${profile}.tmp"
    mv "${profile}.tmp" "$profile"
}

check_ffmpeg() {
    if command -v ffmpeg >/dev/null 2>&1 || [ -n "${FFMPEG:-}" ]; then
        print_ok "ffmpeg encontrado"
    else
        print_warn "ffmpeg não encontrado. /lawdog:video2forum não funcionará."
        print_warn "Instale em: https://www.ffmpeg.org/download.html"
    fi
}

install_python_deps() {
    local req
    req="$(cd "$(dirname "${BASH_SOURCE[0]}")" && git rev-parse --show-toplevel 2>/dev/null)/requirements.txt"
    [ ! -f "$req" ] && { print_warn "requirements.txt não encontrado."; return; }
    echo ""
    echo "Instalando dependências Python..."
    if command -v uv >/dev/null 2>&1; then
        if uv pip install -r "$req" --system 2>/dev/null; then
            print_ok "Dependências instaladas com uv"
        elif command -v pip3 >/dev/null 2>&1; then
            pip3 install -r "$req" --user && print_ok "Dependências instaladas com pip3"
        else
            print_warn "uv falhou e pip3 não encontrado."
        fi
    elif command -v pip3 >/dev/null 2>&1; then
        pip3 install -r "$req" --user && print_ok "Dependências instaladas com pip3"
    else
        print_warn "uv e pip3 não encontrados. Instale o uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
    fi
}

write_pdf_size() {
    local profile="$1"
    touch "$profile"   # ensure profile exists before filtering
    grep -v "LAWDOG_PDF_SIZE" "$profile" > "${profile}.tmp" 2>/dev/null || true
    printf '# JEC file size limit in bytes — change here to update all skills\nexport LAWDOG_PDF_SIZE=4194304\n' \
        >> "${profile}.tmp"
    mv "${profile}.tmp" "$profile"
}

# ── main ───────────────────────────────────────────────────────────────────

print_header "Lawdog Plugin Setup"
echo ""

CASES_DIR="$(read_cases_dir)"

echo ""
echo "Criando $CASES_DIR..."
mkdir -p "$CASES_DIR"

PROFILE="$(detect_profile)"
write_to_profile "$PROFILE" "$CASES_DIR"
write_pdf_size "$PROFILE"
install_python_deps

check_ffmpeg

echo ""
print_header "Setup concluído"
echo "LAWDOG_CASES_DIR=$CASES_DIR"
echo "Perfil atualizado: $PROFILE"
echo ""
echo "Recarregue o shell ou execute: source $PROFILE"
