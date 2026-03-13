#!/bin/bash
# Script para ejecutar tests

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Ejecutando tests de seguridad...${NC}"
echo "================================="

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Variables de entorno para tests
export DATABASE_URL="sqlite:///:memory:"
export JWT_SECRET_KEY="test_secret_key_for_testing_only_32chars!"
export UPLOAD_DIR="/tmp/test_cvs"
export DEBUG="false"

# Crear directorio temporal para tests
mkdir -p /tmp/test_cvs

# Ejecutar tests
cd backend
python -m pytest ../tests -v --tb=short

echo ""
echo -e "${GREEN}Tests completados exitosamente${NC}"
