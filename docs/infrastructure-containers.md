# Infraestrutura de Containers para o Insight Tracker

## Visão Geral

Este documento detalha a estratégia de containerização do Insight Tracker, descrevendo como os diferentes componentes da aplicação são empacotados, orquestrados e escalados usando tecnologias de containers. A infraestrutura é projetada para ser consistente entre ambientes de desenvolvimento, teste e produção, garantindo reprodutibilidade e facilitando a escalabilidade.

## Arquitetura de Containers

### Componentes Principais

A aplicação Insight Tracker é dividida nos seguintes componentes containerizados:

1. **Backend (FastAPI)**: Serviço de API REST em Python
2. **Frontend (Flutter Web)**: Interface do usuário servida como aplicação web
3. **MongoDB**: Banco de dados primário para documentos (insights)
4. **Neo4j**: Banco de dados de grafos para relacionamentos
5. **Redis**: Cache e broker de mensagens
6. **Celery Workers**: Processamento assíncrono de tarefas
7. **Celery Beat**: Agendamento de tarefas periódicas

### Diagrama de Arquitetura

```

## Configuração Kubernetes

Para ambientes de produção em escala, o Insight Tracker pode ser implantado em um cluster Kubernetes. Abaixo estão os manifestos essenciais.

### Namespace

```yaml
# kubernetes/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: insight-tracker
```

### ConfigMap

```yaml
# kubernetes/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: insight-config
  namespace: insight-tracker
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  MONGODB_URI: "mongodb://mongodb-service.insight-tracker.svc.cluster.local:27017/insight"
  NEO4J_URI: "bolt://neo4j-service.insight-tracker.svc.cluster.local:7687"
  REDIS_URI: "redis://redis-service.insight-tracker.svc.cluster.local:6379/0"
```

### Secrets

```yaml
# kubernetes/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: insight-secrets
  namespace: insight-tracker
type: Opaque
data:
  # Valores devem ser codificados em base64
  SECRET_KEY: "YmFzZTY0X2VuY29kZWRfc2VjcmV0X2tleQ=="
  NEO4J_USER: "bmVvNGo="  # neo4j
  NEO4J_PASSWORD: "cGFzc3dvcmQ="  # password
  MONGO_ROOT_USER: "YWRtaW4="  # admin
  MONGO_ROOT_PASSWORD: "cGFzc3dvcmQ="  # password
```

### Backend Deployment

```yaml
# kubernetes/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: insight-tracker
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: insight-backend:latest
        ports:
        - containerPort: 8000
        resources:
          limits:
            cpu: "500m"
            memory: "512Mi"
          requests:
            cpu: "200m"
            memory: "256Mi"
        envFrom:
        - configMapRef:
            name: insight-config
        - secretRef:
            name: insight-secrets
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: insight-tracker
spec:
  selector:
    app: backend
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

### Frontend Deployment

```yaml
# kubernetes/frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: insight-tracker
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: insight-frontend:latest
        ports:
        - containerPort: 80
        resources:
          limits:
            cpu: "200m"
            memory: "256Mi"
          requests:
            cpu: "100m"
            memory: "128Mi"
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
  namespace: insight-tracker
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
```

### MongoDB StatefulSet

```yaml
# kubernetes/mongodb-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mongodb
  namespace: insight-tracker
spec:
  serviceName: mongodb-service
  replicas: 3
  selector:
    matchLabels:
      app: mongodb
  template:
    metadata:
      labels:
        app: mongodb
    spec:
      containers:
      - name: mongodb
        image: mongo:latest
        command:
        - mongod
        - "--replSet"
        - "rs0"
        - "--bind_ip_all"
        ports:
        - containerPort: 27017
        volumeMounts:
        - name: mongodb-data
          mountPath: /data/db
        env:
        - name: MONGO_INITDB_ROOT_USERNAME
          valueFrom:
            secretKeyRef:
              name: insight-secrets
              key: MONGO_ROOT_USER
        - name: MONGO_INITDB_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: insight-secrets
              key: MONGO_ROOT_PASSWORD
        - name: MONGO_INITDB_DATABASE
          value: "insight"
        resources:
          limits:
            cpu: "1"
            memory: "2Gi"
          requests:
            cpu: "500m"
            memory: "1Gi"
  volumeClaimTemplates:
  - metadata:
      name: mongodb-data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: mongodb-service
  namespace: insight-tracker
spec:
  selector:
    app: mongodb
  ports:
  - port: 27017
    targetPort: 27017
  clusterIP: None  # Headless service para StatefulSet
```

### Neo4j StatefulSet

```yaml
# kubernetes/neo4j-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: neo4j
  namespace: insight-tracker
spec:
  serviceName: neo4j-service
  replicas: 1
  selector:
    matchLabels:
      app: neo4j
  template:
    metadata:
      labels:
        app: neo4j
    spec:
      containers:
      - name: neo4j
        image: neo4j:latest
        ports:
        - containerPort: 7474
          name: http
        - containerPort: 7687
          name: bolt
        volumeMounts:
        - name: neo4j-data
          mountPath: /data
        - name: neo4j-logs
          mountPath: /logs
        env:
        - name: NEO4J_AUTH
          value: "$(NEO4J_USER)/$(NEO4J_PASSWORD)"
          valueFrom:
            secretKeyRef:
              name: insight-secrets
              key: NEO4J_USER
        - name: NEO4J_PASSWORD
          valueFrom:
            secretKeyRef:
              name: insight-secrets
              key: NEO4J_PASSWORD
        - name: NEO4J_dbms_memory_heap_initial__size
          value: "1G"
        - name: NEO4J_dbms_memory_heap_max__size
          value: "4G"
        resources:
          limits:
            cpu: "1"
            memory: "4Gi"
          requests:
            cpu: "500m"
            memory: "2Gi"
  volumeClaimTemplates:
  - metadata:
      name: neo4j-data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 10Gi
  - metadata:
      name: neo4j-logs
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 5Gi
---
apiVersion: v1
kind: Service
metadata:
  name: neo4j-service
  namespace: insight-tracker
spec:
  selector:
    app: neo4j
  ports:
  - port: 7474
    targetPort: 7474
    name: http
  - port: 7687
    targetPort: 7687
    name: bolt
  type: ClusterIP
```

### Redis Deployment

```yaml
# kubernetes/redis-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: insight-tracker
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:alpine
        command: ["redis-server", "--appendonly", "yes"]
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: redis-data
          mountPath: /data
        resources:
          limits:
            cpu: "500m"
            memory: "1Gi"
          requests:
            cpu: "200m"
            memory: "512Mi"
      volumes:
      - name: redis-data
        persistentVolumeClaim:
          claimName: redis-pvc
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-pvc
  namespace: insight-tracker
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: insight-tracker
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
  type: ClusterIP
```

### Celery Worker Deployment

```yaml
# kubernetes/celery-worker-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-worker
  namespace: insight-tracker
spec:
  replicas: 2
  selector:
    matchLabels:
      app: celery-worker
  template:
    metadata:
      labels:
        app: celery-worker
    spec:
      containers:
      - name: celery-worker
        image: insight-celery-worker:latest
        command: ["celery", "-A", "app.tasks.worker", "worker", "--loglevel=info", "--concurrency=4"]
        envFrom:
        - configMapRef:
            name: insight-config
        - secretRef:
            name: insight-secrets
        resources:
          limits:
            cpu: "500m"
            memory: "1Gi"
          requests:
            cpu: "200m"
            memory: "512Mi"
```

### Celery Beat Deployment

```yaml
# kubernetes/celery-beat-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-beat
  namespace: insight-tracker
spec:
  replicas: 1
  selector:
    matchLabels:
      app: celery-beat
  template:
    metadata:
      labels:
        app: celery-beat
    spec:
      containers:
      - name: celery-beat
        image: insight-celery-beat:latest
        command: ["celery", "-A", "app.tasks.worker", "beat", "--loglevel=info"]
        envFrom:
        - configMapRef:
            name: insight-config
        - secretRef:
            name: insight-secrets
        resources:
          limits:
            cpu: "200m"
            memory: "256Mi"
          requests:
            cpu: "100m"
            memory: "128Mi"
```

### Ingress

```yaml
# kubernetes/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: insight-ingress
  namespace: insight-tracker
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - insight.example.com
    secretName: insight-tls
  rules:
  - host: insight.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 8000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
```

## Estratégias de Escalonamento

### Escalonamento Horizontal

O Insight Tracker é projetado para escalar horizontalmente em momentos de alta carga. As diferentes estratégias incluem:

1. **Replicas Backend**: Aumentar o número de réplicas do serviço FastAPI
   ```bash
   # Com Docker Swarm
   docker service scale insight_backend=5
   
   # Com Kubernetes
   kubectl scale deployment backend -n insight-tracker --replicas=5
   ```

2. **Replicas Celery Workers**: Ajustar dinamicamente o número de workers para processamento assíncrono
   ```bash
   # Com Docker Swarm
   docker service scale insight_celery-worker=3
   
   # Com Kubernetes
   kubectl scale deployment celery-worker -n insight-tracker --replicas=3
   ```

3. **Auto-Scaling em Kubernetes**: Implementação de HPA (Horizontal Pod Autoscaler)
   ```yaml
   # kubernetes/hpa.yaml
   apiVersion: autoscaling/v2
   kind: HorizontalPodAutoscaler
   metadata:
     name: backend-hpa
     namespace: insight-tracker
   spec:
     scaleTargetRef:
       apiVersion: apps/v1
       kind: Deployment
       name: backend
     minReplicas: 2
     maxReplicas: 10
     metrics:
     - type: Resource
       resource:
         name: cpu
         target:
           type: Utilization
           averageUtilization: 70
   ```

### Escalonamento Vertical

Para componentes de banco de dados que geralmente não escalam horizontalmente com facilidade:

1. **Upgrade de Recursos**: Aumentar CPU e memória
   ```yaml
   # Exemplo para MongoDB no Kubernetes
   resources:
     limits:
       cpu: "4"
       memory: "8Gi"
     requests:
       cpu: "2"
       memory: "4Gi"
   ```

2. **Sharding MongoDB**: Para volumes de dados muito grandes
   - Configurar conjuntos de shards
   - Definir chaves de sharding (por exemplo, user_id para coleção insights)

3. **Neo4j Enterprise Clustering**: Para relacionamentos de grafos em grande escala
   - Configuração de múltiplos leitores
   - Um único escritor

## Monitoramento e Observabilidade

### Stack de Monitoramento

1. **Prometheus**: Coleta de métricas
   - Exposição de endpoint `/metrics` em todos os serviços
   - Configuração de scraping de métricas

2. **Grafana**: Visualização de métricas
   - Dashboards pré-configurados para:
     - Performance de API
     - Uso de recursos por container
     - Latência de banco de dados
     - Performance de Celery

3. **ELK Stack**: Agregação de logs
   - Filebeat nos containers
   - Logstash para processamento
   - Elasticsearch para armazenamento
   - Kibana para visualização

### Exemplo de Configuração Prometheus

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
  
  - job_name: 'mongodb'
    static_configs:
      - targets: ['mongodb-exporter:9216']
  
  - job_name: 'neo4j'
    static_configs:
      - targets: ['neo4j:2004']
  
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
  
  - job_name: 'celery'
    static_configs:
      - targets: ['celery-exporter:9808']
```

## Estratégias de Backup e Recuperação

### MongoDB

1. **Backup Periódico**:
   ```bash
   # Script de backup
   mongodump --uri="mongodb://admin:password@mongodb:27017/insight" \
     --gzip --archive=/backups/mongodb/insight-$(date +%Y%m%d%H%M).gz
   ```

2. **Configuração de Replicação**:
   - Replica Set com 3 nós para alta disponibilidade
   - Pelo menos um nó secundário em zona diferente

### Neo4j

1. **Backup Online**:
   ```bash
   # Para Neo4j Enterprise
   neo4j-admin backup --backup-dir=/backups/neo4j \
     --name=insight-$(date +%Y%m%d%H%M)
   ```

2. **Estratégia de Retenção**:
   - Backups diários por 7 dias
   - Backups semanais por 1 mês
   - Backups mensais por 1 ano

### Sistemas de Arquivos

1. **Volumes Persistentes**:
   - Snapshots regulares de volumes
   - Replicação geográfica para DR (Disaster Recovery)

2. **Restauração Simulada**:
   - Testes regulares de restauração em ambiente de staging
   - Documentação detalhada de procedimentos de recuperação

## Segurança de Containers

### Princípios

1. **Menor Privilégio**:
   - Execução de containers como usuário não-root
   - Capabilities Linux limitadas

2. **Imagens Slim**:
   - Uso de imagens base mínimas (alpine, slim)
   - Remoção de ferramentas desnecessárias

3. **Scan de Vulnerabilidades**:
   - Trivy para scan de imagens
   - Pipeline CI/CD com bloqueio automático para vulnerabilidades críticas

### Exemplo de Configuração de Segurança

```yaml
# Trecho para adicionar ao Dockerfile
# Criar usuário não-privilegiado
RUN adduser --disabled-password --gecos "" appuser

# Definir diretórios acessíveis
RUN mkdir -p /app/data && chown -R appuser:appuser /app

# Trocar para usuário não-root
USER appuser

# Diretório de trabalho
WORKDIR /app
```

## Migração e Upgrades

### Estratégia de Migração Zero-Downtime

1. **Deployment Azul/Verde**:
   - Deploy da nova versão em paralelo (verde)
   - Testes de smoke na nova versão
   - Transição gradual de tráfego
   - Rollback rápido se necessário

2. **Migrações de Banco de Dados**:
   - Migrações backward-compatible
   - Schema versioning explícito
   - Scripts de migração idempotentes

### Automação de Deployment

1. **CI/CD Pipeline**:
   ```yaml
   # Trecho de GitHub Actions
   deploy:
     name: Deploy to Production
     runs-on: ubuntu-latest
     needs: [build, test]
     if: github.ref == 'refs/heads/main'
     steps:
       - uses: actions/checkout@v3
       
       # Autenticação no registry
       - name: Log in to Docker Hub
         uses: docker/login-action@v2
         with:
           username: ${{ secrets.DOCKER_HUB_USERNAME }}
           password: ${{ secrets.DOCKER_HUB_ACCESS_TOKEN }}
       
       # Construção e push de imagens
       - name: Build and push
         uses: docker/build-push-action@v4
         with:
           context: .
           push: true
           tags: odeciojunior/insight-backend:${{ github.sha }}
       
       # Deploy para Kubernetes
       - name: Deploy to Kubernetes
         uses: azure/k8s-deploy@v1
         with:
           manifests: |
             kubernetes/backend-deployment.yaml
           images: |
             odeciojunior/insight-backend:${{ github.sha }}
           namespace: insight-tracker
   ```

## Gerenciamento de Configuração

### Estratégia de Configuração

1. **Hierarquia de Configuração**:
   - Valores padrão embutidos na aplicação
   - Sobrescrita por arquivos de configuração
   - Sobrescrita por variáveis de ambiente
   - Sobrescrita por flags de linha de comando

2. **Gerenciamento de Secrets**:
   - Integração com soluções de gerenciamento de secrets:
     - HashiCorp Vault
     - AWS Secrets Manager
     - Kubernetes Secrets (com Sealed Secrets para versionamento seguro)

3. **Injeção de Configuração**:
   - ConfigMaps para configurações não-sensíveis
   - Secrets para configurações sensíveis
   - Volume mounts para arquivos de configuração

### Exemplo de Vault Integration

```yaml
# Trecho de sidecar para integração com Vault
containers:
- name: vault-agent
  image: hashicorp/vault:latest
  args:
  - agent
  - -config=/etc/vault/config.hcl
  volumeMounts:
  - name: vault-config
    mountPath: /etc/vault
  - name: secrets
    mountPath: /secrets
```

## Boas Práticas e Recomendações

### Design de Containers

1. **Imagens Leves e Específicas**:
   - Otimização de camadas do Docker
   - Multi-stage builds para reduzir tamanho final
   - Alpine ou distroless quando possível

2. **Imutabilidade**:
   - Tratar containers como imutáveis
   - Não modificar estado interno após inicialização
   - Reconstruir imagem para atualizações

3. **Uma Preocupação por Container**:
   - Cada container com uma responsabilidade principal
   - Facilita escalonamento, atualização e monitoramento independentes

### Operação e Manutenção

1. **Logging Estruturado**:
   - Formato JSON para logs de aplicação
   - Incluir metadados úteis (request ID, user ID, etc.)
   - Nível de log configurável por componente

2. **Health Checks**:
   - Implementação de endpoints `/health` e `/readiness`
   - Verificações internas de dependências (bancos de dados, etc.)
   - Auto-healing para pods não saudáveis

3. **Gestão de Recursos**:
   - Definir requests e limits para todos os containers
   - Monitorar uso real e ajustar periodicamente
   - Implementar políticas de Quality of Service (QoS)

## Ferramentas e Recursos Necessários

### Ferramentas de Development

1. **Docker Desktop**: Desenvolvimento local com Docker
2. **K9s**: Interface de terminal para Kubernetes
3. **Lens**: Interface gráfica para gerenciamento de Kubernetes
4. **Tilt ou Skaffold**: Para desenvolvimento contínuo em Kubernetes

### Ferramentas de Operação

1. **Prometheus + Grafana**: Monitoramento e visualização
2. **ELK Stack**: Gestão centralizada de logs
3. **Jaeger ou Zipkin**: Tracing distribuído
4. **Kustomize ou Helm**: Gerenciamento de configurações Kubernetes

### Infraestrutura Cloud

#### AWS

* **EKS**: Kubernetes gerenciado
* **ECR**: Registry de containers
* **RDS/DocumentDB**: Alternativa para MongoDB gerenciado
* **ElastiCache**: Alternativa para Redis gerenciado

#### GCP

* **GKE**: Kubernetes gerenciado
* **Container Registry**: Registry de containers
* **Cloud SQL**: Bancos de dados gerenciados
* **Memorystore**: Redis gerenciado

#### Azure

* **AKS**: Kubernetes gerenciado
* **Container Registry**: Registry de containers
* **CosmosDB**: Alternativa para MongoDB gerenciado
* **Cache for Redis**: Redis gerenciado

## Considerações sobre Custos

### Estimativa de Recursos

| Componente     | Desenvolvimento | Produção Inicial | Produção Escalada |
|----------------|----------------|------------------|-------------------|
| Backend        | 1 instância    | 3 instâncias     | 5-10 instâncias   |
| Frontend       | 1 instância    | 2 instâncias     | 3-5 instâncias    |
| MongoDB        | 1 instância    | 3 instâncias (ReplicaSet) | Sharded Cluster |
| Neo4j          | 1 instância    | 1 instância + 2 réplicas | Cluster Enterprise |
| Redis          | 1 instância    | 2 instâncias (master-slave) | Cluster |
| Celery Workers | 1 instância    | 2 instâncias     | 5-10 instâncias   |
| Celery Beat    | 1 instância    | 1 instância      | 1 instância redundante |
| Storage        | 25GB total     | 100GB total      | 500GB+ total      |

### Otimização de Custos

1. **Rightsizing**:
   - Ajustar resources (CPU/Memória) com base em métricas reais
   - Iniciar pequeno e escalar conforme necessário

2. **Spot Instances/Preemptive VMs**:
   - Usar instâncias de menor custo para workloads tolerantes a falhas (workers)
   - Implementar recuperação automática

3. **Autoscaling**:
   - Escalar para baixo durante períodos de baixa utilização
   - Programar escalonamento baseado em padrões de uso

## Plano de Implementação Gradual

### Fase 1: Ambiente de Desenvolvimento

1. Configurar Docker Compose para desenvolvimento local
2. Implementar Dockerfiles otimizados para cada componente
3. Configurar volumes persistentes para desenvolvimento

### Fase 2: Ambiente de Teste

1. Implementar CI/CD básico com GitHub Actions
2. Configurar cluster Kubernetes de teste
3. Deployar aplicação em ambiente de teste com dados sintéticos

### Fase 3: Ambiente de Produção Inicial

1. Configurar infraestrutura de produção (cluster Kubernetes)
2. Implementar monitoramento básico (Prometheus + Grafana)
3. Configurar backup automatizado
4. Realizar testes de carga e ajustar recursos

### Fase 4: Produção Escalável

1. Implementar autoscaling baseado em métricas
2. Configurar múltiplas zonas de disponibilidade
3. Implementar disaster recovery
4. Otimizar para performance e custo

## Conclusão

A arquitetura de containers proposta para o Insight Tracker fornece uma base robusta para desenvolvimento, teste e operação do sistema. Utilizando Docker para desenvolvimento e Kubernetes para produção, a infraestrutura permite escalar os componentes independentemente conforme a necessidade, mantendo alta disponibilidade, resiliência e performance.

A abordagem com microserviços containerizados simplifica a manutenção e evolução do sistema, permitindo atualizações graduais e reduzindo o risco de falhas catastróficas. As estratégias de monitoramento, backup e segurança garantem que o sistema possa operar de forma confiável em ambiente de produção, mesmo sob carga elevada.

Esta documentação deve ser revisada e atualizada regularmente conforme o sistema evolui e novas tecnologias e práticas emergem no ecossistema de containers.
                           ┌─────────────┐
                           │   Usuário   │
                           └──────┬──────┘
                                  │
                           ┌──────▼──────┐
                           │    HTTPS    │
                           │  (Ingress)  │
                           └──────┬──────┘
                                  │
         ┌────────────────────────┴─────────────────────┐
         │                                              │
┌────────▼───────┐                           ┌──────────▼────────┐
│                │                           │                    │
│    Frontend    │◄────── API REST ─────────►│      Backend      │
│   (Flutter)    │                           │     (FastAPI)     │
│                │                           │                    │
└────────────────┘                           └──────────┬─────────┘
                                                        │
                     ┌─────────────────────────────────┬┴────────────────────────────────┐
                     │                                 │                                  │
              ┌──────▼──────┐                  ┌───────▼────────┐                ┌───────▼────────┐
              │             │                  │                │                │                │
              │   MongoDB   │◄────Read/Write───┤     Redis      │◄──Messages────►│ Celery Workers │
              │             │                  │                │                │                │
              └─────────────┘                  └───────┬────────┘                └───────┬────────┘
                                                       │                                 │
                                               ┌───────▼───────┐                 ┌───────▼───────┐
                                               │               │                 │               │
                                               │     Neo4j     │◄───Read/Write───┤  Celery Beat  │
                                               │               │                 │               │
                                               └───────────────┘                 └───────────────┘
```

## Estratégia de Containerização

### Imagens de Container

#### Backend (Python/FastAPI)

```dockerfile
FROM python:3.10-slim AS base

# Configurar ambiente e variáveis
ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python em uma camada separada
FROM base AS python-deps

# Instalar pip e virtualenv
RUN pip install --upgrade pip setuptools wheel virtualenv

# Criar e ativar ambiente virtual
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiar requisitos e instalar dependências
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Imagem final
FROM base AS runtime

# Copiar ambiente virtual do estágio anterior
COPY --from=python-deps /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiar código da aplicação
COPY backend/ .

# Usuário não-privilegiado para segurança
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -s /bin/bash -m appuser && \
    chown -R appuser:appuser /app
USER appuser

# Porta da aplicação
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando de inicialização
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Frontend (Flutter Web)

```dockerfile
FROM ubuntu:20.04 AS builder

# Configurar ambiente não interativo
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependências
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    unzip \
    xz-utils \
    libglu1-mesa \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Instalar Flutter
RUN git clone https://github.com/flutter/flutter.git /flutter
ENV PATH="/flutter/bin:$PATH"

# Configurar Flutter
RUN flutter channel stable && \
    flutter upgrade && \
    flutter config --enable-web

# Copiar fonte e construir aplicação
WORKDIR /app
COPY frontend/ .
RUN flutter pub get && \
    flutter build web --release

# Imagem final com Nginx para servir o conteúdo
FROM nginx:alpine AS deploy

# Copiar build da aplicação
COPY --from=builder /app/build/web /usr/share/nginx/html

# Copiar configuração personalizada do Nginx (opcional)
COPY infrastructure/docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Porta da aplicação
EXPOSE 80

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD wget -q -O - http://localhost/ || exit 1
```

#### Celery Worker

```dockerfile
FROM python:3.10-slim

# Configurar ambiente
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar requisitos e instalar dependências
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY backend/ .

# Usuário não-privilegiado para segurança
RUN groupadd -g 1000 celeryuser && \
    useradd -u 1000 -g celeryuser -s /bin/bash -m celeryuser && \
    chown -R celeryuser:celeryuser /app
USER celeryuser

# Comando de inicialização
CMD ["celery", "-A", "app.tasks.worker", "worker", "--loglevel=info"]
```

### Docker Compose para Desenvolvimento

```yaml
# docker-compose.yml para ambiente de desenvolvimento
version: '3.8'

services:
  # Backend (FastAPI)
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    container_name: insight-backend
    volumes:
      - ./backend:/app
      - backend_venv:/opt/venv
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
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
  
  # Frontend (Flutter Web)
  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
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
      context: .
      dockerfile: backend/Dockerfile
    container_name: insight-celery-worker
    volumes:
      - ./backend:/app
      - backend_venv:/opt/venv
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
    command: celery -A app.tasks.worker worker --loglevel=info

  # Celery Beat (Scheduler)
  celery-beat:
    build:
      context: .
      dockerfile: backend/Dockerfile
    container_name: insight-celery-beat
    volumes:
      - ./backend:/app
      - backend_venv:/opt/venv
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
      - celery-worker
    networks:
      - insight-network
    command: celery -A app.tasks.worker beat --loglevel=info

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

### Docker Compose para Produção

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  # Backend (FastAPI)
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    image: insight-backend:${TAG:-latest}
    restart: always
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
    environment:
      - MONGODB_URI=mongodb://mongodb:27017/insight
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=${NEO4J_USER}
      - NEO4J_PASSWORD=${NEO4J_PASSWORD}
      - REDIS_URI=redis://redis:6379/0
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - mongodb
      - neo4j
      - redis
    networks:
      - insight-network
    command: gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000
  
  # Frontend (Flutter Web)
  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
    image: insight-frontend:${TAG:-latest}
    restart: always
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '0.2'
          memory: 256M
    depends_on:
      - backend
    networks:
      - insight-network
  
  # Nginx (Load Balancer)
  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./infrastructure/docker/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./infrastructure/docker/nginx/conf.d:/etc/nginx/conf.d:ro
      - ./infrastructure/docker/nginx/ssl:/etc/nginx/ssl:ro
      - static_volume:/var/www/static
    depends_on:
      - backend
      - frontend
    networks:
      - insight-network

  # MongoDB (com Replica Set para produção)
  mongodb:
    image: mongo:latest
    restart: always
    command: ["--replSet", "rs0", "--bind_ip_all", "--wiredTigerCacheSizeGB", "1"]
    volumes:
      - mongodb_data:/data/db
      - ./infrastructure/docker/mongodb/init-mongo.js:/docker-entrypoint-initdb.d/init-mongo.js:ro
    environment:
      - MONGO_INITDB_ROOT_USERNAME=${MONGO_ROOT_USER}
      - MONGO_INITDB_ROOT_PASSWORD=${MONGO_ROOT_PASSWORD}
      - MONGO_INITDB_DATABASE=insight
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 2G
    networks:
      - insight-network

  # Neo4j
  neo4j:
    image: neo4j:enterprise
    restart: always
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
      - ./infrastructure/docker/neo4j/conf:/conf
    environment:
      - NEO4J_AUTH=${NEO4J_USER}/${NEO4J_PASSWORD}
      - NEO4J_ACCEPT_LICENSE_AGREEMENT=yes
      - NEO4J_dbms_memory_heap_initial__size=1G
      - NEO4J_dbms_memory_heap_max__size=4G
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 4G
    networks:
      - insight-network

  # Redis (com persistência)
  redis:
    image: redis:alpine
    restart: always
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 1G
    networks:
      - insight-network

  # Celery Worker
  celery-worker:
    build:
      context: .
      dockerfile: backend/Dockerfile
    image: insight-celery-worker:${TAG:-latest}
    restart: always
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '0.5'
          memory: 1G
    environment:
      - MONGODB_URI=mongodb://mongodb:27017/insight
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=${NEO4J_USER}
      - NEO4J_PASSWORD=${NEO4J_PASSWORD}
      - REDIS_URI=redis://redis:6379/0
      - ENVIRONMENT=production
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - redis
      - mongodb
      - neo4j
    networks:
      - insight-network
    command: celery -A app.tasks.worker worker --loglevel=info --concurrency=4

  # Celery Beat (Scheduler)
  celery-beat:
    build:
      context: .
      dockerfile: backend/Dockerfile
    image: insight-celery-beat:${TAG:-latest}
    restart: always
    deploy:
      resources:
        limits:
          cpus: '0.2'
          memory: 256M
    environment:
      - MONGODB_URI=mongodb://mongodb:27017/insight
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=${NEO4J_USER}
      - NEO4J_PASSWORD=${NEO4J_PASSWORD}
      - REDIS_URI=redis://redis:6379/0
      - ENVIRONMENT=production
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - redis
      - celery-worker
    networks:
      - insight-network
    command: celery -A app.tasks.worker beat --loglevel=info

networks:
  insight-network:
    driver: bridge

volumes:
  mongodb_data:
  neo4j_data:
  neo4j_logs:
  redis_data:
  static_volume:
```