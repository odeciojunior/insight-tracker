# Inconsistências nas Dependências e Importações

## Problemas Identificados

### 1. Importações com referência a arquivos inexistentes

Vários arquivos no projeto fazem referência a serviços e utilitários que ainda não foram implementados:

- Em `lib/app/controllers/insight_controller.dart`:
  ```dart
  import '../../services/storage_service.dart';
  ```
  Este serviço é usado, mas há incompatibilidade entre sua implementação e uso.

- Em `lib/app/modules/login/login_page.dart` e outros:
  ```dart
  import '../../controllers/auth_controller.dart';
  ```
  O AuthController importa `firebase_auth`, mas o serviço correspondente não está implementado.

- Em múltiplos arquivos:
  ```dart
  import '../../../services/api_service.dart';
  ```
  Este arquivo está vazio, mas é referenciado em várias partes do código.

### 2. Dependências declaradas não utilizadas corretamente

No arquivo `pubspec.yaml`, várias dependências são declaradas, mas nem todas são usadas adequadamente:

- **graphview**: Declarada mas não usada efetivamente no visualizador de mindmap.
- **dio** e **dio_cache_interceptor**: Declaradas para networking, mas sem implementação do serviço de API.
- **sqflite**: Declarado mas não integrado ao sistema de armazenamento principal.

### 3. Importações relativas vulneráveis a refatoração

Muitos arquivos usam caminhos relativos profundos:

```dart
import '../../../core/widgets/loading_indicator.dart';
```

Isso dificulta a refatoração e manutenção do código, pois mover um arquivo exige atualizar todos os caminhos relativos.

## Soluções Propostas

### 1. Corrigir importações e implementar serviços faltantes

Para cada serviço referenciado mas não implementado:

#### StorageService
- Revisar a implementação atual em `lib/services/storage_service.dart`
- Garantir que seja compatível com os contratos esperados por todos os controllers
- Adicionar métodos para todos os tipos de dados usados (insights, relacionamentos, categorias)

#### ApiService
- Implementar o serviço em `lib/services/api_service.dart` usando Dio como cliente HTTP
- Adicionar métodos para cada endpoint da API
- Implementar cache com dio_cache_interceptor
- Adicionar gerenciamento de erros e timeouts

#### AuthService
- Implementar o serviço em `lib/services/auth_service.dart`
- Integrar com firebase_auth para autenticação
- Adicionar métodos para login, registro, recuperação de senha
- Adicionar armazenamento seguro de tokens

### 2. Padronizar e otimizar uso de dependências

- **Revisão de dependências**: Avaliar todas as dependências declaradas no pubspec.yaml e remover as não utilizadas
- **Atualização de versões**: Verificar se todas as dependências estão usando versões compatíveis entre si
- **Documentação de uso**: Adicionar comentários sobre o propósito de cada dependência

### 3. Padronizar estilo de importação

Migrar para um estilo de importação baseado em pacote, usando aliases para facilitar a importação:

1. Configurar aliases no `analysis_options.yaml`:
   ```yaml
   analyzer:
     strong-mode: true
     errors:
       unused_import: warning
       unused_local_variable: warning
       unused_field: warning
     exclude:
       - "**/*.g.dart"
       - "**/*.freezed.dart"
   ```

2. Usar imports de pacote em vez de relativos:
   ```dart
   // Em vez de
   import '../../../core/widgets/loading_indicator.dart';
   
   // Usar
   import 'package:insight_tracker/core/widgets/loading_indicator.dart';
   ```

3. Organizar imports em grupos lógicos:
   ```dart
   // Dart e Flutter
   import 'dart:async';
   import 'package:flutter/material.dart';
   
   // Pacotes externos
   import 'package:get/get.dart';
   import 'package:hive/hive.dart';
   
   // Pacote do projeto
   import 'package:insight_tracker/core/widgets/loading_indicator.dart';
   import 'package:insight_tracker/services/storage_service.dart';
   ```

### 4. Implementar scripts de verificação e análise

- Adicionar scripts de linting para verificar importações não utilizadas
- Implementar CI/CD para validar a estrutura de importações
- Adicionar documentação para padronizar o estilo de código

## Priorização de Ações

1. **Alta prioridade**: Implementar os serviços básicos faltantes
2. **Média prioridade**: Padronizar estilo de importação
3. **Baixa prioridade**: Otimizar dependências

## Impacto da Implementação

- **Manutenção**: Código mais fácil de manter com importações padronizadas
- **Produtividade**: Menos tempo gasto corrigindo problemas de importação
- **Estabilidade**: Menos erros relacionados a dependências incorretas
- **Desempenho**: Código mais enxuto sem importações desnecessárias