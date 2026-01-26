#!/bin/bash

# ============================================
# Copy Trade Dashboard - Setup Script
# Detecta o SO e instala todos os requisitos
# ============================================

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_banner() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════╗"
    echo "║     Copy Trade Dashboard Setup         ║"
    echo "╚════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_status() { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Detecta o Sistema Operacional
detect_os() {
    case "$(uname -s)" in
        Linux*)
            if [ -f /etc/debian_version ]; then
                echo "debian"
            elif [ -f /etc/redhat-release ]; then
                echo "redhat"
            else
                echo "linux"
            fi
            ;;
        Darwin*)    echo "macos";;
        MINGW*|MSYS*|CYGWIN*) echo "windows";;
        *)          echo "unknown";;
    esac
}

# Verifica se um comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Instala Docker baseado no SO
install_docker() {
    local os=$1

    if command_exists docker; then
        print_status "Docker ja esta instalado"
        return 0
    fi

    print_status "Instalando Docker para $os..."

    case $os in
        debian)
            sudo apt-get update
            sudo apt-get install -y ca-certificates curl gnupg
            sudo install -m 0755 -d /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
            sudo chmod a+r /etc/apt/keyrings/docker.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            sudo apt-get update
            sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            sudo usermod -aG docker $USER
            ;;
        redhat)
            sudo yum install -y yum-utils
            sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            sudo systemctl start docker
            sudo systemctl enable docker
            sudo usermod -aG docker $USER
            ;;
        linux)
            curl -fsSL https://get.docker.com | sh
            sudo usermod -aG docker $USER
            ;;
        macos)
            if command_exists brew; then
                print_status "Instalando Docker via Homebrew..."
                brew install --cask docker
                print_warning "Por favor, abra o Docker Desktop manualmente apos a instalacao"
                print_warning "Pressione Enter quando o Docker estiver rodando..."
                read -r
            else
                print_error "Homebrew nao encontrado. Instale Docker Desktop manualmente:"
                print_error "https://www.docker.com/products/docker-desktop"
                exit 1
            fi
            ;;
        windows)
            print_error "Por favor, instale Docker Desktop manualmente:"
            print_error "https://www.docker.com/products/docker-desktop"
            exit 1
            ;;
        *)
            print_error "Sistema operacional nao suportado"
            exit 1
            ;;
    esac
}

# Gera uma string aleatoria segura
generate_secret() {
    if command_exists openssl; then
        openssl rand -base64 32 | tr -d '/+=' | cut -c1-32
    else
        head -c 32 /dev/urandom | base64 | tr -d '/+=' | cut -c1-32
    fi
}

# Gera uma chave Fernet valida
generate_fernet_key() {
    if command_exists python3; then
        python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || \
        openssl rand -base64 32
    else
        openssl rand -base64 32
    fi
}

# Variavel global para controlar reset do banco
RESET_DATABASE=false

# Configura variaveis de ambiente
setup_env() {
    if [ -f .env ]; then
        print_warning "Arquivo .env ja existe. Deseja sobrescrever? (s/N)"
        read -r response
        if [[ ! "$response" =~ ^[Ss]$ ]]; then
            print_status "Mantendo .env existente"
            return 0
        fi
        
        # Se vai sobrescrever .env, precisa perguntar sobre o banco
        echo ""
        print_warning "ATENCAO: O .env sera recriado com novas credenciais do banco."
        print_warning "Para o sistema funcionar, o banco de dados precisa ser resetado."
        print_warning "Isso ira APAGAR todos os dados existentes!"
        echo ""
        echo -e "${RED}Deseja resetar o banco de dados? (sim/N)${NC}"
        read -r reset_response
        if [[ "$reset_response" == "sim" ]]; then
            RESET_DATABASE=true
            print_status "Banco de dados sera resetado."
        else
            print_error "Sem reset do banco, as novas credenciais nao funcionarao."
            print_error "Mantendo .env existente para evitar problemas."
            return 0
        fi
    fi

    print_status "Criando arquivo .env..."

    local db_password=$(generate_secret)
    local jwt_secret=$(generate_secret)
    local encryption_key=$(generate_fernet_key)
    local admin_password=$(generate_secret | cut -c1-16)

    cat > .env << EOF
# Database Configuration
DB_USER=copytrade
DB_PASSWORD=${db_password}
DATABASE_URL=postgresql://copytrade:${db_password}@db:5432/copytrade

# JWT Configuration
JWT_SECRET_KEY=${jwt_secret}
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Encryption Key (Fernet key for account passwords)
ENCRYPTION_KEY=${encryption_key}

# CORS Origins
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# API URL for frontend
VITE_API_URL=http://localhost:8000

# Admin user credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=${admin_password}
ADMIN_EMAIL=admin@copytrade.app
EOF

    chmod 600 .env
    print_status "Arquivo .env criado com sucesso!"
    echo ""
    print_warning "IMPORTANTE: Salve estas credenciais do admin:"
    echo -e "${YELLOW}  Usuario: admin${NC}"
    echo -e "${YELLOW}  Senha: ${admin_password}${NC}"
    echo ""
}

# Aguarda o servico ficar pronto
wait_for_service() {
    local url=$1
    local max_attempts=${2:-30}
    local attempt=1

    print_status "Aguardando servico em $url..."

    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            print_status "Servico disponivel!"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done

    print_error "Timeout aguardando servico"
    return 1
}

# Funcao principal
main() {
    print_banner

    # Detecta SO
    OS=$(detect_os)
    print_status "Sistema Operacional detectado: $OS"

    # Instala Docker se necessario
    install_docker "$OS"

    # Verifica se Docker esta rodando
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker nao esta rodando. Por favor, inicie o Docker e tente novamente."
        exit 1
    fi
    print_status "Docker esta rodando"

    # Verifica docker compose
    if docker compose version >/dev/null 2>&1; then
        DOCKER_COMPOSE="docker compose"
    elif command_exists docker-compose; then
        DOCKER_COMPOSE="docker-compose"
    else
        print_error "Docker Compose nao encontrado"
        exit 1
    fi
    print_status "Docker Compose disponivel"

    # Configura ambiente
    setup_env

    # Para containers existentes
    print_status "Parando containers existentes..."
    if [ "$RESET_DATABASE" = true ]; then
        print_warning "Removendo volumes (banco de dados)..."
        $DOCKER_COMPOSE down -v 2>/dev/null || true
    else
        $DOCKER_COMPOSE down 2>/dev/null || true
    fi

    # Build e start dos containers
    print_status "Construindo e iniciando containers..."
    $DOCKER_COMPOSE up -d --build

    # Aguarda backend ficar pronto
    sleep 5
    wait_for_service "http://localhost:8000/api/health" 60

    # Resultado final
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║         Setup Completo!                ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
    echo ""
    print_status "Frontend:  http://localhost:3000"
    print_status "Backend:   http://localhost:8000"
    print_status "API Docs:  http://localhost:8000/docs"
    echo ""
    print_warning "Credenciais do admin estao no arquivo .env"
    echo ""
    print_status "Para ver os logs: $DOCKER_COMPOSE logs -f"
    print_status "Para parar: $DOCKER_COMPOSE down"
}

# Executa
main "$@"
