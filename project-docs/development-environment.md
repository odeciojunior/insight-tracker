# Ambiente de Desenvolvimento para o Insight Tracker

## Visão Geral

Este documento detalha a configuração do ambiente de desenvolvimento para o projeto Insight Tracker, focando em uma abordagem containerizada com Docker e utilizando Windows com WSL2 (Windows Subsystem for Linux) como ambiente base. Esta configuração garante consistência entre ambientes de desenvolvimento e produção, além de facilitar a futura escalabilidade do projeto.

## Pré-requisitos

### Hardware Recomendado
- **CPU**: Processador de 64 bits com 4+ cores (Intel Core i5/i7 ou AMD Ryzen 5/7)
- **RAM**: 16GB+ (recomendado 32GB para execução simultânea de todos os containers)
- **Armazenamento**: SSD com pelo menos 100GB livres
- **GPU**: Opcional, mas recomendado para treinamento de modelos (NVIDIA com suporte a CUDA)

### Software de Base
- **Sistema Operacional**: Windows 10/11 Pro ou Enterprise (64 bits)
- **WSL2**: Ubuntu 20.04 LTS ou posterior
- **VS Code**: Última versão estável com extensões relevantes
- **Docker Desktop**: Configurado para integração com WSL2
- **Git**: Configurado tanto no Windows quanto no WSL2

## Configuração do WSL2

### Instalação

```powershell
# No PowerShell com privilégios administrativos
wsl --install -d Ubuntu-20.04
```

### Configuração Recomendada

Editar o arquivo `%UserProfile%\.wslconfig` no Windows:

```ini
[wsl2]
memory=8GB
processors=4
localhostForwarding=true
```

### Configuração do Ubuntu

```bash
# Atualizar o sistema
sudo apt update && sudo apt upgrade -y

# Instalar pacotes essenciais
sudo apt install -y build-essential curl wget git unzip python3-dev python3-pip

# Configurar Git
git config --global user.name "Seu Nome"
git config --global user.email "seu.email@exemplo.com"

# Configurar Python
echo 'alias python=python3' >> ~/.bashrc
echo 'alias pip=pip3' >> ~/.bashrc
source ~/.bashrc
```

## Instalação do Docker

### Docker Desktop

1. Baixar e instalar o Docker Desktop para Windows
2. Nas configurações do Docker Desktop, ativar a integração com WSL2
3. Reiniciar o Docker Desktop

### Verificação da Instalação

```bash
# No terminal WSL2
docker --version
docker-compose --version
```

## Configuração do VS Code

### Extensões Essenciais

- **Remote - WSL**: Desenvolvimento dentro do WSL
- **Remote - Containers**: Desenvolvimento dentro de containers
- **Docker**: Gerenciamento de Docker
- **Python**: Suporte a Python
- **Dart**: Suporte a Dart
- **Flutter**: Suporte a Flutter
- **MongoDB for VS Code**: Gerenciamento de MongoDB
- **Neo4j Cypher**: Suporte a linguagem Cypher

### Configuração para Desenvolvimento Remoto

1. Abrir o VS Code
2. Pressionar `F1` e selecionar "Remote-WSL: New Window"
3. No VS Code dentro do WSL, abrir a pasta do projeto

## Estrutura de Containers

### docker-compose.yml

O arquivo abaixo deve ser colocado na raiz do projeto:

```yaml
version: '3.8'

services:
  # Backend (Python/FastAPI)
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: insight-backend
    volumes:
      - ./backend:/app
      - backend_venv:/app/.venv
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URI=mongodb://mongodb:27017/insight
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=password
      - REDIS_URI=redis://redis:6379/0
      - ENVIRONMENT=development
      - LOG_LEVEL=DEBUG
    depends_on:
      - mongodb
      - neo4j
      - redis
    networks:
      - insight-network
    command: bash -c "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
  
  # Frontend (Flutter)
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: insight-frontend
    volumes:
      - ./frontend:/app
      - flutter_cache:/root/.pub-cache
    ports:
      - "3000:3000"
    depends_on:
      - backend
    networks:
      - insight-network
    command: flutter run -d web-server --web-port=3000 --web-hostname=0.0.0.0

  # MongoDB
  mongodb:
    image: mongo:latest
    container_name: insight-mongodb
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
      - ./infrastructure/docker/mongodb/init-mongo.js:/docker-entrypoint-initdb.d/init-mongo.js:ro
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=password
      - MONGO_INITDB_DATABASE=insight
    networks:
      - insight-network

  # Neo4j
  neo4j:
    image: neo4j:latest
    container_name: insight-neo4j
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
      - ./infrastructure/docker/neo4j/conf:/conf
    environment:
      - NEO4J_AUTH=neo4j/password
      - NEO4J_dbms_memory_heap_initial__size=512m
      - NEO4J_dbms_memory_heap_max__size=2G
    networks:
      - insight-network

  # Redis
  redis:
    image: redis:alpine
    container_name: insight-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - insight-network

  # Celery Worker
  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: insight-celery-worker
    volumes:
      - ./backend:/app
      - backend_venv:/app/.venv
    environment:
      - MONGODB_URI=mongodb://mongodb:27017/insight
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=password
      - REDIS_URI=redis://redis:6379/0
      - ENVIRONMENT=development
    depends_on:
      - backend
      - redis
      - mongodb
      - neo4j
    networks:
      - insight-network
    command: bash -c "celery -A app.tasks.worker worker --loglevel=info"

networks:
  insight-network:
    driver: bridge

volumes:
  mongodb_data:
  neo4j_data:
  neo4j_logs:
  redis_data:
  backend_venv:
  flutter_cache:
```

### Dockerfiles

#### Backend (Python/FastAPI)

Arquivo `backend/Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Configurar ambiente virtual Python
RUN python -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar o código da aplicação
COPY . .

# Expor porta da API
EXPOSE 8000

# Comando padrão
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Frontend (Flutter)

Arquivo `frontend/Dockerfile`:

```dockerfile
FROM ubuntu:20.04

# Evitar interações do usuário durante a instalação
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependências necessárias
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    unzip \
    xz-utils \
    libglu1-mesa \
    openjdk-8-jdk \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Instalar Flutter
WORKDIR /root
RUN git clone https://github.com/flutter/flutter.git -b stable

# Adicionar Flutter ao PATH
ENV PATH="/root/flutter/bin:${PATH}"

# Configurar Flutter para web
RUN flutter precache && \
    flutter config --enable-web

# Verificar instalação do Flutter
RUN flutter doctor -v

# Criar e configurar diretório de trabalho
WORKDIR /app

# Configurar ambiente para inicialização
COPY pubspec.yaml* ./
RUN if [ -f pubspec.yaml ]; then flutter pub get; fi

# Expor porta para o aplicativo web
EXPOSE 3000

# Comando padrão
CMD ["flutter", "run", "-d", "web-server", "--web-port=3000", "--web-hostname=0.0.0.0"]
```

## Scripts de Inicialização

### Script de Inicialização do Ambiente

Arquivo `tools/setup-dev.sh`:

```bash
#!/bin/bash

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null
then
    echo "Docker não encontrado. Por favor, instale o Docker antes de continuar."
    exit 1
fi

# Verificar se Docker Compose está instalado
if ! command -v docker-compose &> /dev/null
then
    echo "Docker Compose não encontrado. Por favor, instale o Docker Compose antes de continuar."
    exit 1
fi

# Criar arquivos necessários se não existirem
mkdir -p infrastructure/docker/mongodb
mkdir -p infrastructure/docker/neo4j/conf

# Criar script de inicialização do MongoDB
cat > infrastructure/docker/mongodb/init-mongo.js << 'EOF'
db = db.getSiblingDB('insight');

db.createUser({
  user: 'insight_user',
  pwd: 'insight_password',
  roles: [
    {
      role: 'readWrite',
      db: 'insight',
    },
  ],
});

db.createCollection('users');
db.createCollection('insights');
db.createCollection('categories');
db.createCollection('tags');
db.createCollection('embeddings');
EOF

# Criar arquivo de configuração para Neo4j (opcional)
touch infrastructure/docker/neo4j/conf/neo4j.conf

# Iniciar os containers
docker-compose up -d

echo "Ambiente de desenvolvimento iniciado com sucesso!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "MongoDB: mongodb://localhost:27017"
echo "Neo4j Browser: http://localhost:7474"
echo "Neo4j Bolt: bolt://localhost:7687"
```

### Script de Limpeza do Ambiente

Arquivo `tools/cleanup-dev.sh`:

```bash
#!/bin/bash

# Parar e remover containers
docker-compose down

# Opcional: Remover volumes para limpeza completa
read -p "Deseja remover todos os volumes (dados serão perdidos)? (s/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]
then
    docker-compose down -v
    echo "Todos os volumes foram removidos."
else
    echo "Volumes mantidos."
fi
```

## Configuração dos Bancos de Dados

### MongoDB

Para inicializar o MongoDB com usuários e coleções padrão, usar o script `init-mongo.js` mencionado acima.

Para conectar ao MongoDB manualmente:

```bash
# Conectar via shell
docker exec -it insight-mongodb mongosh -u admin -p password

# Ou usar MongoDB Compass com:
# mongodb://admin:password@localhost:27017/?authSource=admin
```

### Neo4j

Para conectar ao Neo4j manualmente:

```bash
# Via browser: http://localhost:7474
# Credenciais padrão: neo4j/password

# Ou via Cypher shell
docker exec -it insight-neo4j cypher-shell -u neo4j -p password
```

## Fluxo de Trabalho de Desenvolvimento

### Preparação do Ambiente

```bash
# Clonar o repositório
git clone https://github.com/odeciojunior/insight.git
cd insight

# Dar permissão de execução aos scripts
chmod +x tools/setup-dev.sh
chmod +x tools/cleanup-dev.sh

# Iniciar o ambiente
./tools/setup-dev.sh
```

### Desenvolvimento Backend

```bash
# Abrir VS Code no diretório do projeto dentro do WSL
code .

# O servidor FastAPI é iniciado automaticamente com hot reload
# Acessar a documentação da API em http://localhost:8000/docs
```

### Desenvolvimento Frontend

```bash
# O servidor Flutter Web é iniciado automaticamente
# Acessar a aplicação em http://localhost:3000

# Para trabalhos específicos no frontend
docker exec -it insight-frontend bash
```

### Teste de Banco de Dados

```bash
# Testar conexão com MongoDB
docker exec -it insight-backend python -c "from app.db.mongodb import connect_to_mongo; connect_to_mongo()"

# Testar conexão com Neo4j
docker exec -it insight-backend python -c "from app.db.neo4j import connect_to_neo4j; connect_to_neo4j()"
```

## Debug e Solução de Problemas

### Logs de Containers

```bash
# Visualizar logs do backend
docker logs insight-backend

# Visualizar logs do frontend
docker logs insight-frontend

# Seguir logs em tempo real
docker logs -f insight-backend
```

### Reiniciar Serviços

```bash
# Reiniciar um serviço específico
docker-compose restart backend

# Reconstruir um serviço após alterações no Dockerfile
docker-compose up -d --build backend
```

### Acessar Shell de Containers

```bash
# Acessar shell do backend
docker exec -it insight-backend bash

# Acessar shell do frontend
docker exec -it insight-frontend bash
```

## Configuração de VS Code para Desenvolvimento Remoto

Para uma experiência de desenvolvimento ideal, configure um arquivo `.devcontainer/devcontainer.json` na raiz do projeto:

```json
{
  "name": "Insight Tracker Development",
  "dockerComposeFile": ["../docker-compose.yml"],
  "service": "backend",
  "workspaceFolder": "/app",
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "dart-code.dart-code",
        "dart-code.flutter",
        "ms-azuretools.vscode-docker",
        "mongodb.mongodb-vscode",
        "neo4j.neo4j-vscode"
      ],
      "settings": {
        "python.defaultInterpreterPath": "/app/.venv/bin/python",
        "python.linting.enabled": true,
        "python.linting.pylintEnabled": true,
        "python.formatting.provider": "black",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
          "source.organizeImports": true
        }
      }
    }
  },
  "forwardPorts": [8000, 3000, 27017, 7474, 7687, 6379],
  "shutdownAction": "stopCompose"
}
```

## Ferramentas de Desenvolvimento Adicionais

### Backend

- **IPython**: Para experimentação interativa
- **PgAdmin**: Para administração do PostgreSQL (se aplicável)
- **pytest-cov**: Para relatórios de cobertura de teste
- **black, flake8, isort**: Para formatação e linting
- **FastAPI-Admin**: Para interface de administração 

### Frontend

- **DevTools**: Para debug e análise de performance
- **flutter_lints**: Para linting
- **flutter_test**: Para testes de widget
- **Lighthouse**: Para auditorias de web performance
- **Flutter Inspector**: Para debug de UI

## Integração com Serviços Externos

Para desenvolvimento local, use serviços "mock" ou versões locais de:

- **Serviços de Email**: Use MailHog para capturar emails localmente
- **Serviços de Armazenamento**: Use MinIO como alternativa local ao S3
- **Serviços de Autenticação**: Use versões locais de OAuth ou JWT 

## Considerações de Performance

- **Mapeamento de Volume**: Pode causar lentidão em Windows; considere técnicas como bindfs para melhorar performance
- **Hot Reload**: Configurado para ambos frontend e backend
- **Recursos do Docker**: Ajustar alocação no Docker Desktop para evitar gargalos
- **Memória e CPU**: Monitorar uso de recursos com Docker stats

## Práticas Recomendadas

1. **Controle de Versão**:
   - Uso de Git Flow para gerenciamento de branches
   - Pull Requests para todas as alterações significativas
   - Revisão de código antes de merge

2. **Testes**:
   - Testes unitários para cada nova funcionalidade
   - Testes de integração para componentes principais
   - Testes de UI para o frontend

3. **Documentação**:
   - Manter README atualizado
   - Documentar APIs com OpenAPI
   - Usar docstrings em funções e classes
   - Manter diagrama de arquitetura atualizado

4. **Segurança**:
   - Não armazenar segredos em código
   - Usar .env para variáveis de ambiente locais
   - Implementar rotação regular de credenciais

## Próximos Passos

Após a configuração do ambiente:

1. Configurar CI/CD com GitHub Actions para testes automáticos
2. Implementar linting e formatação automática
3. Configurar análise estática de código
4. Preparar ambiente de staging

Seguindo estas orientações, você terá um ambiente de desenvolvimento robusto, consistente e preparado para escalabilidade futura do projeto Insight Tracker.
