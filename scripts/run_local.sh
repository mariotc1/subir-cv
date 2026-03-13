#!/bin/bash
# Script para ejecutar la aplicación localmente

set -e

GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}CV Upload System - Ejecución Local${NC}"
echo "======================================="

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 no está instalado${NC}"
    exit 1
fi

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creando entorno virtual...${NC}"
    python3 -m venv venv
fi

# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
echo -e "${YELLOW}Instalando dependencias...${NC}"
pip install -r backend/requirements.txt

# Variables de entorno para desarrollo local
export DATABASE_URL="sqlite:///./test.db"
export JWT_SECRET_KEY="development_secret_key_change_in_production"
export DEBUG="true"
export UPLOAD_DIR="./storage/cvs"

# Crear directorio de uploads
mkdir -p storage/cvs

echo -e "${GREEN}Iniciando servidor...${NC}"
echo -e "${GREEN}Aplicación disponible en: http://localhost:8000${NC}"
echo ""

cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
