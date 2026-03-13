#!/bin/bash
# Script para ejecutar con Docker

set -e

GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}CV Upload System - Docker${NC}"
echo "========================="

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker no está instalado${NC}"
    exit 1
fi

# Crear archivo .env si no existe
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creando archivo .env...${NC}"
    cp .env.example .env

    # Generar JWT secret aleatorio
    JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || openssl rand -base64 32)
    sed -i.bak "s/change_this_in_production_to_a_very_long_random_string/$JWT_SECRET/" .env
    rm -f .env.bak

    echo -e "${GREEN}Archivo .env creado con JWT_SECRET generado${NC}"
fi

# Construir y ejecutar
echo -e "${YELLOW}Construyendo imagen Docker...${NC}"
docker compose build

echo -e "${YELLOW}Iniciando contenedores...${NC}"
docker compose up -d

# Esperar a que la aplicación esté lista
echo -e "${YELLOW}Esperando a que la aplicación esté lista...${NC}"
sleep 5

# Verificar estado
if docker compose ps | grep -q "healthy\|running"; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Aplicación iniciada correctamente${NC}"
    echo -e "${GREEN}URL: http://localhost:8000${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Comandos útiles:"
    echo "  Ver logs:    docker compose logs -f"
    echo "  Detener:     docker compose down"
    echo "  Estado:      docker compose ps"
else
    echo -e "${RED}Error al iniciar la aplicación${NC}"
    docker compose logs
    exit 1
fi
