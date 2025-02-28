# Arquitetura de Banco de Dados

## Visão Geral

O Insight Tracker utilizará uma abordagem híbrida de bancos de dados, combinando MongoDB para armazenamento primário de documentos (insights) e Neo4j para gerenciamento de relacionamentos e visualização de grafos. Esta arquitetura permite aproveitar as vantagens específicas de cada sistema: a flexibilidade de schema do MongoDB para dados semi-estruturados e a otimização do Neo4j para consultas de relacionamento e travessia de grafos.

## Requisitos Funcionais do Banco de Dados

1. Armazenamento eficiente de insights em formato texto ou transcritos de áudio
2. Suporte a metadados variáveis e esquema flexível para diferentes tipos de insights
3. Indexação e busca de texto completo
4. Armazenamento e consulta eficiente de relacionamentos entre insights
5. Suporte a consultas de travessia de grafo para visualização de mindmaps
6. Persistência de dados para treinamento de modelos de IA
7. Alta disponibilidade e resiliência
8. Capacidade de escala horizontal

## Arquitetura MongoDB

### Estrutura de Coleções

```
insight_tracker_db
├── users
├── insights
├── categories
├── tags
├── embeddings
├── feedback
└── system_metadata
```

### Schema de Documentos Principais

#### Coleção: users

```json
{
  "_id": "ObjectId",
  "email": "string",
  "password_hash": "string",
  "name": "string",
  "created_at": "datetime",
  "last_login": "datetime",
  "preferences": {
    "theme": "string",
    "notification_settings": "object",
    "ui_preferences": "object"
  },
  "usage_stats": {
    "insights_count": "integer",
    "last_activity": "datetime",
    "feature_usage": "object"
  },
  "subscription": {
    "plan": "string",
    "status": "string",
    "expires_at": "datetime"
  }
}
```

#### Coleção: insights

```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "title": "string",
  "content": "string",
  "source_type": "string",  // "text", "audio", "imported"
  "created_at": "datetime",
  "updated_at": "datetime",
  "categories": ["string"],
  "tags": ["string"],
  "metadata": {
    "language": "string",
    "sentiment_score": "float",
    "complexity_score": "float",
    "custom_fields": "object"
  },
  "embedding_id": "ObjectId",  // Referência ao vetor de embedding
  "processing_status": "string",  // "pending", "processed", "failed"
  "ai_suggestions": ["string"],
  "visibility": "string"  // "private", "shared", "public"
}
```

#### Coleção: embeddings

```json
{
  "_id": "ObjectId",
  "insight_id": "ObjectId",
  "vector": [0.1, 0.2, ...],  // Array de floats representando o vetor de embedding
  "model_version": "string",
  "created_at": "datetime"
}
```

### Índices

#### Coleção: insights
- Índice composto: `{ user_id: 1, created_at: -1 }`
- Índice de texto: `{ content: "text", title: "text" }`
- Índice de categorias: `{ user_id: 1, categories: 1 }`
- Índice de tags: `{ user_id: 1, tags: 1 }`

#### Coleção: embeddings
- Índice único: `{ insight_id: 1 }`

### Sharding Strategy

- Chave de Shard para insights: `{ user_id: 1 }`
- Chave de Shard para users: `{ _id: 1 }`
- Chave de Shard para embeddings: `{ insight_id: 1 }`

## Arquitetura Neo4j

### Modelo de Grafo

#### Nós
- Label: `User`
  - Properties: `userId`, `name`, `email`

- Label: `Insight`
  - Properties: `insightId`, `title`, `created_at`, `categories`

- Label: `Category`
  - Properties: `name`, `description`

- Label: `Tag`
  - Properties: `name`

#### Relacionamentos
- Type: `CREATED` (User → Insight)
  - Properties: `created_at`

- Type: `RELATED_TO` (Insight → Insight)
  - Properties: `strength` (float 0-1), `relation_type`, `created_at`

- Type: `CATEGORIZED_AS` (Insight → Category)
  - Properties: `confidence` (float 0-1)

- Type: `TAGGED_WITH` (Insight → Tag)

### Cypher Queries Principais

#### Obter Mindmap para um Insight Específico
```cypher
MATCH (i:Insight {insightId: $insightId})-[r:RELATED_TO*1..3]-(related:Insight)
WHERE related.userId = $userId
RETURN i, r, related
```

#### Encontrar Caminhos entre Insights
```cypher
MATCH path = shortestPath((i1:Insight {insightId: $insightId1})-[r:RELATED_TO*]-(i2:Insight {insightId: $insightId2}))
RETURN path
```

#### Insights Mais Conectados
```cypher
MATCH (i:Insight {userId: $userId})
WITH i, size((i)-[:RELATED_TO]-()) as connections
RETURN i.insightId, i.title, connections
ORDER BY connections DESC
LIMIT 10
```

## Integração entre MongoDB e Neo4j

### Estratégia de Sincronização
1. **Unidirecional**: Dados primários em MongoDB, relacionamentos derivados em Neo4j
2. **Identificadores Consistentes**: Usar o mesmo ID para entidades em ambos os sistemas
3. **Batch Processing**: Sincronização periódica em lote para otimizar performance
4. **Change Data Capture**: Monitorar operações de escrita no MongoDB para atualizar Neo4j

### Fluxo de Dados
```
[Frontend] → [API] → [MongoDB] → [Processor Service] → [Neo4j]
                                       ↓
                              [Embedding Generation]
```

### Consistência Eventual
- Priorizar disponibilidade e particionamento sobre consistência imediata
- Implementar mecanismos de recuperação para falhas de sincronização
- Monitorar e registrar discrepâncias entre os sistemas

## Armazenamento de Cache

### Redis

#### Estruturas de Dados
- **Insights Recentes**: Sorted Sets com timestamps
- **Resultados de Pesquisa**: Hashes com TTL
- **Sessões de Usuário**: Hashes com TTL
- **Contadores e Estatísticas**: Strings e Counters

#### Políticas de Cache
- **TTL para Pesquisas**: 15 minutos
- **TTL para Dados de Perfil**: 30 minutos
- **Invalidação Seletiva**: Ao atualizar insights

## Backup e Recuperação

### Estratégia de Backup
- **MongoDB**: Backups diários completos, oplog para point-in-time recovery
- **Neo4j**: Snapshots diários, transaction logs para recuperação incremental
- **Redis**: RDB persistance a cada 15 minutos + AOF

### Localização
- Armazenamento primário no mesmo datacenter
- Armazenamento secundário em região geográfica distinta
- Criptografia em trânsito e em repouso

### Políticas de Retenção
- Backups diários: 7 dias
- Backups semanais: 1 mês
- Backups mensais: 1 ano

## Requisitos de Infraestrutura

### MongoDB
- **Ambiente Desenvolvimento**:
  - MongoDB 6.0+ Single Instance
  - 4 vCPUs, 8GB RAM, 100GB SSD
  
- **Ambiente Produção**:
  - MongoDB 6.0+ Replica Set (3 nós)
  - Cada nó: 8 vCPUs, 32GB RAM, 500GB SSD
  - Monitoramento via MongoDB Atlas ou Ops Manager

### Neo4j
- **Ambiente Desenvolvimento**:
  - Neo4j 5.0+ Single Instance
  - 4 vCPUs, 16GB RAM, 100GB SSD
  
- **Ambiente Produção**:
  - Neo4j 5.0+ Causal Cluster (3+ nós)
  - Cada nó: 8 vCPUs, 32GB RAM, 500GB SSD
  - Monitoramento via Neo4j Fabric ou solução custom

### Redis
- **Ambiente Desenvolvimento**:
  - Redis 7.0+ Single Instance
  - 2 vCPUs, 4GB RAM
  
- **Ambiente Produção**:
  - Redis 7.0+ Sentinel ou Redis Cluster
  - Cada nó: 4 vCPUs, 16GB RAM
  - Persistência habilitada

## Migração e Evolução do Schema

### Estratégia de Migração
- Scripts de migração versionados no controle de código
- Utilização de padrão de design para backward compatibility
- Testes automáticos para validar integridade após migrações

### MongoDB Schema Evolution
- Estratégia de Schema Versioning via campo `schema_version`
- Migração gradual on-read/on-write para documentos legados
- Utilização de validação via JSON Schema quando apropriado

### Neo4j Evolution
- Scripts Cypher versionados para evolução do grafo
- Operações APOC para manipulação em massa quando necessário
- Backup pré-migração para rollback se necessário

## Ferramentas e Serviços Necessários

### MongoDB
- MongoDB Atlas ou instalação self-hosted
- MongoDB Compass para interface visual
- MongoDB BI Connector para analytics
- mongodump/mongorestore para backups

### Neo4j
- Neo4j Enterprise Edition ou Neo4j Aura
- Neo4j Browser para interface visual
- Neo4j Bloom para visualização avançada
- APOC para procedimentos estendidos
- Cypher Shell para scripts

### Redis
- Redis Stack ou Redis Enterprise
- RedisInsight para monitoramento e gerenciamento