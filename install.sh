#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
#  MoodTracker — Instalador para Ubuntu/Debian
# ─────────────────────────────────────────────────────────────────────────────

set -e

INSTALL_DIR="$HOME/.local/share/moodtracker"
BIN_LINK="$HOME/.local/bin/moodtracker"
AUTOSTART="$HOME/.config/autostart/moodtracker.desktop"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="$SCRIPT_DIR/moodtracker.py"

GREEN="\033[0;32m"
CYAN="\033[0;36m"
YELLOW="\033[1;33m"
RESET="\033[0m"

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${CYAN}   MoodTracker — Instalador               ${RESET}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""

# ── 1. Python check ──────────────────────────────────────────────────────────
echo -e "${YELLOW}[1/4]${RESET} Verificando Python 3..."
if ! command -v python3 &>/dev/null; then
    echo "     Python 3 no encontrado. Instalando..."
    sudo apt-get install -y python3
fi
echo -e "     ${GREEN}✓ Python 3 disponible${RESET}"

# ── 2. Dependencies ──────────────────────────────────────────────────────────
echo -e "${YELLOW}[2/4]${RESET} Instalando dependencias..."

# tkinter
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "     Instalando python3-tk..."
    sudo apt-get install -y python3-tk
fi
echo -e "     ${GREEN}✓ tkinter${RESET}"

# matplotlib (optional but recommended)
if ! python3 -c "import matplotlib" 2>/dev/null; then
    echo "     Instalando matplotlib (para gráficos avanzados)..."
    pip3 install matplotlib --break-system-packages 2>/dev/null || \
    pip3 install matplotlib 2>/dev/null || \
    sudo apt-get install -y python3-matplotlib || \
    echo "     (matplotlib no disponible — se usará gráfico básico)"
else
    echo -e "     ${GREEN}✓ matplotlib${RESET}"
fi

# ── 3. Copy files ────────────────────────────────────────────────────────────
echo -e "${YELLOW}[3/4]${RESET} Instalando aplicación..."
mkdir -p "$INSTALL_DIR"
cp "$SOURCE" "$INSTALL_DIR/moodtracker.py"
chmod +x "$INSTALL_DIR/moodtracker.py"

mkdir -p "$HOME/.local/bin"
cat > "$BIN_LINK" <<EOF
#!/bin/bash
python3 $INSTALL_DIR/moodtracker.py "\$@"
EOF
chmod +x "$BIN_LINK"
echo -e "     ${GREEN}✓ Instalado en $INSTALL_DIR${RESET}"

# ── 4. Autostart ─────────────────────────────────────────────────────────────
echo -e "${YELLOW}[4/4]${RESET} Configurando inicio automático..."
mkdir -p "$(dirname "$AUTOSTART")"
cat > "$AUTOSTART" <<EOF
[Desktop Entry]
Type=Application
Name=MoodTracker
Exec=python3 $INSTALL_DIR/moodtracker.py
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Comment=Seguimiento diario de estado de ánimo
StartupNotify=false
EOF
echo -e "     ${GREEN}✓ Autostart configurado${RESET}"

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${GREEN}  ¡Instalación completada! ✓${RESET}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
echo "  Para ejecutar ahora:  moodtracker"
echo "  O directamente:       python3 $INSTALL_DIR/moodtracker.py"
echo ""
echo "  Se iniciará automáticamente al encender la PC."
echo ""

# Launch now?
read -r -p "  ¿Abrir MoodTracker ahora? [S/n]: " ans
ans=${ans:-S}
if [[ "$ans" =~ ^[Ss]$ ]]; then
    python3 "$INSTALL_DIR/moodtracker.py" &
fi
