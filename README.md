# CV Upload System

Sistema seguro de subida de CVs desarrollado como reto de ciberseguridad.

## Arquitectura

```
project/
├── backend/
│   └── app/
│       ├── main.py              # Aplicación FastAPI
│       ├── config.py            # Configuración
│       ├── database.py          # SQLAlchemy
│       ├── models/              # Modelos de BD
│       ├── schemas/             # Schemas Pydantic
│       ├── routers/             # Endpoints API
│       ├── services/            # Lógica de negocio
│       ├── security/            # JWT, passwords
│       ├── middleware/          # Headers, WAF, Rate Limiting
│       └── utils/               # Validación archivos, logging
├── frontend/                    # HTML + JS + CSS
├── tests/                       # Tests de seguridad
├── scripts/                     # Scripts de ejecución
├── Dockerfile
├── docker-compose.yml
└── Makefile
```

## Stack Tecnológico

- **Backend**: Python + FastAPI
- **Base de datos**: PostgreSQL
- **ORM**: SQLAlchemy
- **Validación**: Pydantic
- **Autenticación**: JWT (python-jose)
- **Hash contraseñas**: bcrypt
- **Frontend**: HTML + JavaScript vanilla

## Ejecución Rápida con Docker

```bash
# Clonar repositorio
git clone <repo>
cd cv-upload-system

# Ejecutar con Docker
./scripts/docker_run.sh

# O usando make
make docker-build
make docker-run
```

La aplicación estará disponible en: http://localhost:8000

## Comandos Disponibles

```bash
make help           # Ver todos los comandos
make install        # Instalar dependencias localmente
make run            # Ejecutar localmente
make test           # Ejecutar tests
make docker-build   # Construir imagen Docker
make docker-run     # Iniciar contenedores
make docker-stop    # Detener contenedores
make docker-logs    # Ver logs
make clean          # Limpiar archivos temporales
```

## API Endpoints

### Autenticación

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/auth/register` | Registrar usuario |
| POST | `/api/auth/login` | Iniciar sesión |
| GET | `/api/auth/me` | Obtener usuario actual |

### Gestión de CV

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/cv/upload` | Subir CV (PDF) |
| GET | `/api/cv/download` | Descargar CV propio |
| GET | `/api/cv/info` | Info del CV |
| DELETE | `/api/cv/delete` | Eliminar CV |

### Sistema

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/health` | Health check |

## Medidas de Seguridad Implementadas

### Autenticación y Autorización
- JWT con expiración configurable
- Hash de contraseñas con bcrypt (12 rounds)
- Validación de contraseñas fuertes (12+ caracteres, mayúsculas, minúsculas, números, símbolos)
- Verificación de ownership en cada operación

### Protección contra Ataques
- **SQL Injection**: ORM con queries parametrizadas
- **XSS**: CSP headers, sanitización de input
- **CSRF**: Tokens JWT, no cookies de sesión
- **Path Traversal**: Validación de rutas, nombres UUID
- **File Upload Attacks**: Validación de extensión, MIME, magic bytes
- **Brute Force**: Rate limiting, bloqueo de IP
- **Enumeration**: Mensajes de error genéricos

### Headers de Seguridad
- Content-Security-Policy
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- Strict-Transport-Security
- Referrer-Policy

### WAF (Web Application Firewall)
- Detección de patrones de SQL injection
- Detección de XSS
- Detección de path traversal
- Logging de intentos sospechosos

### Validación de Archivos
- Solo PDF permitidos
- Verificación de extensión (.pdf)
- Verificación de MIME type (application/pdf)
- Verificación de magic bytes (%PDF)
- Tamaño máximo: 5 MB
- Detección de contenido sospechoso (JavaScript embebido)
- Renombrado con UUID (sin usar nombre original)

### Logging Seguro
- Registro de intentos de login
- Registro de uploads/downloads
- Registro de eventos de seguridad
- NUNCA se registran contraseñas ni tokens

### Docker Seguro
- Imagen base mínima (python:slim)
- Usuario no root
- Health checks
- Volúmenes para persistencia
- Red interna para BD

## Variables de Entorno

```bash
# Base de datos
DATABASE_URL=postgresql://user:pass@host:5432/db

# JWT (CAMBIAR EN PRODUCCIÓN)
JWT_SECRET_KEY=your_very_long_random_secret_key

# Configuración
DEBUG=false
UPLOAD_DIR=/app/storage/cvs
```

## Tests de Seguridad

Los tests verifican:
- Acceso sin autenticación
- Acceso a CV de otro usuario
- Subida de archivo no PDF
- Subida de archivo demasiado grande
- Login incorrecto
- Protección contra enumeración
- Headers de seguridad
- Protección del WAF

```bash
make test
```

## Estructura de la Base de Datos

### Tabla: users
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | Primary key |
| email | VARCHAR(255) | Unique, indexed |
| password_hash | VARCHAR(255) | bcrypt hash |
| created_at | TIMESTAMP | Con timezone |
| updated_at | TIMESTAMP | Con timezone |

### Tabla: cvs
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Foreign key a users |
| filename | VARCHAR(255) | Nombre UUID del archivo |
| original_filename | VARCHAR(255) | Nombre original sanitizado |
| storage_path | VARCHAR(512) | Ruta completa |
| uploaded_at | TIMESTAMP | Con timezone |

## Notas de Seguridad

1. **Nunca** exponer la documentación de API en producción (DEBUG=false)
2. **Siempre** usar HTTPS en producción
3. **Cambiar** el JWT_SECRET_KEY con un valor aleatorio largo
4. **Revisar** los logs regularmente para detectar intentos de ataque
5. **Actualizar** las dependencias periódicamente

## Licencia

Proyecto educativo para reto de ciberseguridad.
