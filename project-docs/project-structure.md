# Estrutura de Arquivos do Projeto Insight Tracker

Este documento detalha a estrutura de arquivos recomendada para o projeto Insight Tracker, concebida para promover modularidade, clareza e facilidade de manutenção. A estrutura segue as melhores práticas para uma aplicação containerizada com frontend em Flutter, backend em Python/FastAPI, e bancos de dados MongoDB e Neo4j.

## Estrutura de Diretórios Raiz

```
insight/
├── .github/                      # Configurações e workflows do GitHub
│   ├── workflows/                # GitHub Actions para CI/CD
│   └── ISSUE_TEMPLATE/           # Templates para issues
├── docs/                         # Documentação do projeto
│   ├── architecture/             # Diagramas e especificações de arquitetura
│   ├── api/                      # Documentação da API
│   ├── guides/                   # Guias e tutoriais
│   └── assets/                   # Imagens e outros recursos para documentação
├── backend/                      # Código do backend Python/FastAPI
├── frontend/                     # Código do frontend Flutter
├── infrastructure/               # Configurações de infraestrutura
│   ├── docker/                   # Arquivos Dockerfile e docker-compose
│   ├── kubernetes/               # Configurações para deploy em Kubernetes
│   └── scripts/                  # Scripts de automação e utilidades
├── tools/                        # Ferramentas de desenvolvimento e utilidades
├── .editorconfig                 # Configurações de editor consistentes
├── .gitignore                    # Arquivos e diretórios ignorados pelo Git
├── README.md                     # Documentação principal do projeto
└── LICENSE                       # Licença do projeto
```

## Backend (Python/FastAPI)

```
backend/
├── app/                          # Código principal da aplicação
│   ├── api/                      # Definições de API e endpoints
│   │   ├── dependencies.py       # Dependências compartilhadas para API
│   │   ├── router.py             # Router principal da API
│   │   └── endpoints/            # Módulos de endpoints por funcionalidade
│   │       ├── __init__.py
│   │       ├── auth.py           # Endpoints de autenticação
│   │       ├── insights.py       # Endpoints de insights
│   │       ├── relationships.py  # Endpoints de relacionamentos
│   │       └── ai_assistant.py   # Endpoints do assistente IA
│   ├── core/                     # Configurações e funcionalidades centrais
│   │   ├── __init__.py
│   │   ├── config.py             # Configurações da aplicação
│   │   ├── security.py           # Segurança e autenticação
│   │   └── logging.py            # Configuração de logs
│   ├── db/                       # Configurações e conexões com bancos de dados
│   │   ├── __init__.py
│   │   ├── mongodb.py            # Cliente e funções para MongoDB
│   │   ├── neo4j.py              # Cliente e funções para Neo4j
│   │   └── redis.py              # Cliente e funções para Redis
│   ├── models/                   # Modelos de dados internos
│   │   ├── __init__.py
│   │   ├── user.py               # Modelo de usuário
│   │   ├── insight.py            # Modelo de insight
│   │   └── relationship.py       # Modelo de relacionamento
│   ├── schemas/                  # Esquemas Pydantic para validação
│   │   ├── __init__.py
│   │   ├── user.py               # Esquemas de usuário
│   │   ├── insight.py            # Esquemas de insight
│   │   └── relationship.py       # Esquemas de relacionamento
│   ├── services/                 # Serviços de negócio
│   │   ├── __init__.py
│   │   ├── nlp/                  # Serviços de processamento de linguagem natural
│   │   │   ├── __init__.py
│   │   │   ├── classification.py # Classificação de insights
│   │   │   ├── embeddings.py     # Geração de embeddings
│   │   │   └── relationship.py   # Detecção de relacionamentos
│   │   ├── audio/                # Serviços de processamento de áudio
│   │   │   ├── __init__.py
│   │   │   ├── transcription.py  # Transcrição de áudio para texto
│   │   │   └── processing.py     # Processamento de áudio
│   │   └── ai/                   # Serviços de IA
│   │       ├── __init__.py
│   │       ├── training.py       # Treinamento de modelos
│   │       └── recommendation.py # Recomendações e sugestões
│   ├── tasks/                    # Tarefas assíncronas (Celery)
│   │   ├── __init__.py
│   │   ├── nlp_tasks.py          # Tarefas de NLP
│   │   ├── insight_processing.py # Processamento de insights
│   │   └── model_training.py     # Treinamento de modelos
│   └── utils/                    # Utilidades compartilhadas
│       ├── __init__.py
│       ├── validators.py         # Funções de validação
│       └── helpers.py            # Funções auxiliares
├── tests/                        # Testes
│   ├── __init__.py
│   ├── conftest.py               # Configurações para testes
│   ├── api/                      # Testes de API
│   └── services/                 # Testes de serviços
├── alembic/                      # Migrações de banco de dados
│   ├── env.py
│   ├── README
│   ├── script.py.mako
│   └── versions/                 # Scripts de migração versionados
├── .env.example                  # Exemplo de variáveis de ambiente
├── Dockerfile                    # Configuração para containerização
├── requirements.txt              # Dependências Python
├── pyproject.toml                # Configuração do projeto Python
├── setup.py                      # Script de instalação
├── tox.ini                       # Configuração para testes automatizados
└── main.py                       # Ponto de entrada da aplicação
```

## Frontend (Flutter)

```
frontend/
├── android/                      # Configurações específicas para Android
├── ios/                          # Configurações específicas para iOS
├── web/                          # Configurações específicas para Web
├── windows/                      # Configurações específicas para Windows
├── macos/                        # Configurações específicas para macOS
├── linux/                        # Configurações específicas para Linux
├── lib/                          # Código fonte principal Flutter/Dart
│   ├── app/                      # Código da aplicação
│   │   ├── bindings/             # Bindings GetX (ou similar)
│   │   │   ├── home_binding.dart
│   │   │   ├── insight_binding.dart
│   │   │   └── settings_binding.dart
│   │   ├── controllers/          # Controllers (GetX/Bloc)
│   │   │   ├── insight_controller.dart
│   │   │   ├── mindmap_controller.dart
│   │   │   ├── recorder_controller.dart
│   │   │   └── settings_controller.dart
│   │   ├── data/                 # Camada de dados
│   │   │   ├── models/           # Modelos de dados
│   │   │   │   ├── insight.dart
│   │   │   │   ├── relationship.dart
│   │   │   │   └── user.dart
│   │   │   ├── providers/        # Provedores de dados
│   │   │   │   ├── api_provider.dart
│   │   │   │   └── local_storage_provider.dart
│   │   │   └── repositories/     # Repositórios
│   │   │       ├── insight_repository.dart
│   │   │       └── user_repository.dart
│   │   └── modules/              # Módulos da aplicação
│   │       ├── auth/             # Autenticação
│   │       │   ├── views/
│   │       │   └── widgets/
│   │       ├── capture/          # Captura de insights
│   │       │   ├── views/
│   │       │   └── widgets/
│   │       ├── home/             # Tela inicial
│   │       │   ├── views/
│   │       │   └── widgets/
│   │       ├── mindmap/          # Visualização de mindmap
│   │       │   ├── views/
│   │       │   └── widgets/
│   │       ├── settings/         # Configurações
│   │       │   ├── views/
│   │       │   └── widgets/
│   │       └── shared/           # Componentes compartilhados
│   │           ├── views/
│   │           └── widgets/
│   ├── core/                     # Núcleo da aplicação
│   │   ├── config/               # Configurações
│   │   │   ├── app_config.dart
│   │   │   ├── routes.dart
│   │   │   └── themes.dart
│   │   ├── utils/                # Utilidades
│   │   │   ├── analytics.dart
│   │   │   ├── error_handler.dart
│   │   │   └── validators.dart
│   │   └── widgets/              # Widgets do núcleo
│   │       ├── custom_button.dart
│   │       ├── insight_card.dart
│   │       └── loading_indicator.dart
│   ├── services/                 # Serviços
│   │   ├── api_service.dart
│   │   ├── auth_service.dart
│   │   ├── speech_service.dart
│   │   └── storage_service.dart
│   └── main.dart                 # Ponto de entrada da aplicação
├── assets/                       # Recursos estáticos
│   ├── fonts/                    # Fontes
│   ├── images/                   # Imagens
│   ├── animations/               # Animações Lottie
│   └── i18n/                     # Arquivos de internacionalização
├── test/                         # Testes
│   ├── widget_tests/             # Testes de widgets
│   ├── unit_tests/               # Testes unitários
│   └── golden_tests/             # Testes de screenshot
├── integration_test/             # Testes de integração
├── coverage/                     # Relatórios de cobertura de testes
├── .metadata                     # Metadados do Flutter
├── analysis_options.yaml         # Configurações de análise estática
├── l10n.yaml                     # Configuração de localização
├── pubspec.yaml                  # Dependências e configuração do projeto
├── pubspec.lock                  # Lock file de dependências
└── README.md                     # Documentação específica do frontend
```

## Infraestrutura (Docker, Kubernetes)

```
infrastructure/
├── docker/                       # Configurações Docker
│   ├── docker-compose.yml        # Composição principal
│   ├── docker-compose.dev.yml    # Configuração para desenvolvimento
│   ├── docker-compose.prod.yml   # Configuração para produção
│   ├── backend/                  # Configurações Docker para backend
│   │   ├── Dockerfile            # Dockerfile para backend
│   │   └── entrypoint.sh         # Script de entrada
│   ├── frontend/                 # Configurações Docker para frontend
│   │   ├── Dockerfile            # Dockerfile para frontend
│   │   └── nginx.conf            # Configuração Nginx para web
│   ├── mongodb/                  # Configurações para MongoDB
│   │   ├── init-mongo.js         # Script de inicialização
│   │   └── mongod.conf           # Configuração MongoDB
│   └── neo4j/                    # Configurações para Neo4j
│       └── neo4j.conf            # Configuração Neo4j
├── kubernetes/                   # Configurações Kubernetes
│   ├── backend/                  # Manifests para backend
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   ├── frontend/                 # Manifests para frontend
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   ├── databases/                # Manifests para bancos de dados
│   │   ├── mongodb/
│   │   │   ├── statefulset.yaml
│   │   │   └── service.yaml
│   │   └── neo4j/
│   │       ├── statefulset.yaml
│   │       └── service.yaml
│   ├── ingress/                  # Configurações de ingress
│   │   └── ingress.yaml
│   └── config/                   # ConfigMaps e Secrets
│       ├── configmap.yaml
│       └── secrets.yaml
└── scripts/                      # Scripts de automação
    ├── setup-dev.sh              # Configuração de ambiente de desenvolvimento
    ├── backup-db.sh              # Backup de bancos de dados
    ├── deploy.sh                 # Script de deploy
    └── monitoring/               # Scripts para monitoramento
        ├── setup-prometheus.sh
        └── setup-grafana.sh
```

## Documentação

```
docs/
├── architecture/                 # Documentação de arquitetura
│   ├── overview.md               # Visão geral da arquitetura
│   ├── backend-specs.md          # Especificações do backend
│   ├── frontend-specs.md         # Especificações do frontend
│   ├── database-architecture.md  # Arquitetura de banco de dados
│   └── diagrams/                 # Diagramas de arquitetura
│       ├── system-overview.png
│       ├── data-flow.png
│       └── component-diagram.png
├── api/                          # Documentação da API
│   ├── openapi.yaml              # Especificação OpenAPI
│   ├── auth.md                   # Documentação de endpoints de autenticação
│   ├── insights.md               # Documentação de endpoints de insights
│   └── relationships.md          # Documentação de endpoints de relacionamentos
├── guides/                       # Guias e tutoriais
│   ├── getting-started.md        # Guia inicial
│   ├── development-workflow.md   # Fluxo de desenvolvimento
│   ├── deployment.md             # Guia de deploy
│   └── contribution.md           # Guia de contribuição
├── assets/                       # Recursos para documentação
│   └── images/                   # Imagens para documentação
└── README.md                     # Índice da documentação
```

## Ferramentas de Desenvolvimento

```
tools/
├── codegen/                      # Ferramentas de geração de código
│   ├── generate-models.py        # Script para gerar modelos
│   └── api-generator.py          # Gerador de código da API
├── database/                     # Ferramentas para banco de dados
│   ├── seed-data.py              # Dados de exemplo
│   └── create-indexes.js         # Criação de índices
├── performance/                  # Ferramentas de análise de performance
│   └── benchmark.py              # Script de benchmark
└── ci/                           # Ferramentas para CI/CD
    ├── lint.sh                   # Script de linting
    └── test-coverage.sh          # Análise de cobertura de testes
```

## Arquivos de Configuração da Raiz

```
.editorconfig                     # Configurações consistentes para editores
.gitignore                        # Arquivos e pastas ignorados pelo Git
README.md                         # Documentação principal do projeto
LICENSE                           # Licença do projeto (por exemplo, MIT)
```

## Notas Adicionais para Implementação

1. **Versionamento**: A estrutura suporta o desenvolvimento baseado em recursos, com branches organizados por funcionalidade/módulo.

2. **Containerização**: Cada componente principal está isolado em seu próprio container, facilitando desenvolvimento, teste e implantação independentes.

3. **Desenvolvimento Local**: O ambiente de desenvolvimento local é configurado via Docker Compose, garantindo consistência entre todos os desenvolvedores.

4. **CI/CD**: A estrutura de .github/workflows permite configurar pipelines de CI/CD para testes automáticos, build e deploy.

5. **Escalabilidade**: A estrutura modular facilita a adição de novos componentes ou a substituição de tecnologias específicas sem afetar todo o sistema.

6. **Documentação**: Cada componente deve manter sua própria documentação, além da documentação central que fornece uma visão de todo o sistema.

7. **Monitoramento**: Arquivos de configuração para monitoramento e logging estão incluídos na infraestrutura, preparando o projeto para observabilidade desde o início.

Esta estrutura de arquivos fornece um equilíbrio entre modularidade, clareza e escalabilidade, adequada para o desenvolvimento contínuo do Insight Tracker em uma equipe de qualquer tamanho, desde um desenvolvedor individual até uma equipe distribuída.
