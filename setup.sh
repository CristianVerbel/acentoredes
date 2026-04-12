#!/usr/bin/env bash
# =============================================================================
# Setup Script - Acento Redes / OpenClaw + WhatsApp
# =============================================================================
set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

echo -e "${BOLD}"
echo "============================================="
echo "  Acento Redes - OpenClaw + WhatsApp Setup"
echo "============================================="
echo -e "${NC}"

# --- Verificar dependencias ---
info "Verificando dependencias..."

if ! command -v node &> /dev/null; then
    error "Node.js no esta instalado. Instala Node.js 22+ desde https://nodejs.org"
fi

NODE_VERSION=$(node -v | sed 's/v//' | cut -d. -f1)
if [ "$NODE_VERSION" -lt 22 ]; then
    error "Se requiere Node.js 22+. Version actual: $(node -v)"
fi
info "Node.js $(node -v) detectado"

if ! command -v npm &> /dev/null; then
    error "npm no esta instalado"
fi
info "npm $(npm -v) detectado"

# --- Instalar OpenClaw ---
info "Instalando OpenClaw..."
if ! command -v openclaw &> /dev/null; then
    npm install -g openclaw@latest
    info "OpenClaw instalado correctamente"
else
    CURRENT_VERSION=$(openclaw --version 2>/dev/null || echo "desconocida")
    info "OpenClaw ya instalado (version: $CURRENT_VERSION)"
    read -rp "Deseas actualizar a la ultima version? [s/N]: " UPDATE
    if [[ "$UPDATE" =~ ^[sS]$ ]]; then
        npm install -g openclaw@latest
        info "OpenClaw actualizado"
    fi
fi

# --- Configurar .env ---
if [ ! -f .env ]; then
    warn "Archivo .env no encontrado"
    cp .env.example .env
    info "Archivo .env creado desde .env.example"
    echo ""
    warn "IMPORTANTE: Edita el archivo .env con tu API key antes de continuar"
    warn "  nano .env  (o usa tu editor preferido)"
    echo ""
    read -rp "Presiona ENTER cuando hayas configurado tu .env..."
fi

# Cargar variables de entorno
source .env

# Verificar API key
if [[ "${ANTHROPIC_API_KEY:-}" == "sk-ant-xxxxxxxxxxxxxxxxxxxx" ]] || [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
    if [[ -z "${OPENAI_API_KEY:-}" ]]; then
        error "Configura al menos una API key en el archivo .env"
    fi
fi
info "API key configurada"

# --- Ejecutar onboarding de OpenClaw ---
info "Ejecutando configuracion inicial de OpenClaw..."
openclaw onboard --install-daemon 2>/dev/null || true

# --- Copiar configuracion ---
OPENCLAW_DIR="$HOME/.openclaw"
mkdir -p "$OPENCLAW_DIR"

if [ -f openclaw.config.yaml ]; then
    cp openclaw.config.yaml "$OPENCLAW_DIR/config.yaml"
    info "Configuracion copiada a $OPENCLAW_DIR/config.yaml"
fi

# --- Instalar plugin de WhatsApp ---
info "Instalando plugin de WhatsApp..."
openclaw plugins install @openclaw/whatsapp 2>/dev/null || \
    openclaw channels add --channel whatsapp 2>/dev/null || \
    warn "Plugin de WhatsApp podria ya estar instalado"

# --- Vincular WhatsApp ---
echo ""
echo -e "${BOLD}============================================="
echo "  Vinculacion de WhatsApp"
echo "=============================================${NC}"
echo ""
info "Se va a generar un codigo QR para vincular WhatsApp."
info "Preparate para escanear el codigo con tu telefono:"
info "  1. Abre WhatsApp en tu telefono"
info "  2. Ve a Configuracion > Dispositivos vinculados"
info "  3. Toca 'Vincular un dispositivo'"
info "  4. Escanea el codigo QR que aparecera"
echo ""
read -rp "Presiona ENTER cuando estes listo para escanear..."

openclaw channels login --channel whatsapp

echo ""
info "WhatsApp vinculado exitosamente!"

# --- Iniciar gateway ---
echo ""
echo -e "${BOLD}============================================="
echo "  Iniciando Gateway"
echo "=============================================${NC}"
echo ""
info "Iniciando OpenClaw Gateway en el puerto ${GATEWAY_PORT:-18789}..."
info "Presiona Ctrl+C para detener el gateway"
echo ""

openclaw gateway --port "${GATEWAY_PORT:-18789}" --verbose
