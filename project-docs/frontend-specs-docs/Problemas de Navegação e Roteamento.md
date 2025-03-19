# Problemas de Navegação e Roteamento

## Problemas Identificados

### 1. Rotas Incompletas em `routes.dart`

O arquivo `lib/core/config/routes.dart` contém apenas algumas das rotas definidas no aplicativo:

```dart
// Definição de nomes de rotas
static const String HOME = '/home';
static const String AUTH = '/auth';
static const String CAPTURE = '/capture';
static const String MINDMAP = '/mindmap';
static const String SETTINGS = '/settings';
static const String LOGIN = '/login';
static const String EDIT = '/edit';
static const String DETAIL = '/detail';
static const String REGISTER = '/register';

// Implementação de rotas
static final List<GetPage> routes = [
  // Home route
  GetPage(
    name: HOME,
    page: () => const HomePage(),
    binding: HomeBinding(),
  ),
  
  // Auth route (placeholder for now)
  GetPage(
    name: AUTH,
    page: () => const Scaffold(
      body: Center(
        child: Text('Auth Page - Coming Soon'),
      ),
    ),
  ),
  
  // Capture route
  GetPage(
    name: CAPTURE,
    page: () => const CapturePage(),
    binding: CaptureBinding(),
    transition: Transition.rightToLeft,
  ),
  
  // Mindmap route (placeholder for now)
  GetPage(
    name: MINDMAP,
    page: () => const Scaffold(
      body: Center(
        child: Text('Mindmap Page - Coming Soon'),
      ),
    ),
  ),
  
  // Settings route (placeholder for now)
  GetPage(
    name: SETTINGS,
    page: () => const Scaffold(
      body: Center(
        child: Text('Settings Page - Coming Soon'),
      ),
    ),
  ),
```

Faltam definições para LOGIN, REGISTER, DETAIL e EDIT, embora esses nomes sejam referenciados no código.

### 2. Inconsistências entre Nomes de Rotas e Implementações

Algumas rotas são definidas, mas suas implementações estão incompletas ou inconsistentes:

- `SETTINGS` está definido como um placeholder, mas existe uma implementação real em `lib/app/modules/settings/settings_page.dart`
- `AUTH` é uma rota genérica, mas o código utiliza `LOGIN` e `REGISTER` diretamente

### 3. Problemas de Navegação

Diversos padrões de navegação são usados no aplicativo:

```dart
// Navegação direta
Get.toNamed(AppRoutes.DETAIL, arguments: insight.id);

// Navegação substituindo a tela atual
Get.offNamed(AppRoutes.EDIT, arguments: insight.id);

// Navegação com limpeza de pilha
Get.offAllNamed(AppRoutes.HOME);

// Navegação de retorno
Get.back();
```

Além disso, o uso de argumentos é inconsistente:
- Alguns controladores esperam argumentos específicos
- Não há validação de argumentos
- Algumas páginas tentam acessar argumentos que podem não existir

### 4. Falta de Middleware e Autenticação nas Rotas

O sistema de rotas não implementa:
- Middleware para verificar autenticação
- Redirecionamentos automáticos para login quando necessário
- Proteção de rotas que requerem autenticação

## Soluções Propostas

### 1. Completar a Definição de Rotas

Atualizar o arquivo `routes.dart` para incluir todas as rotas com suas respectivas páginas e bindings:

```dart
static final List<GetPage> routes = [
  GetPage(
    name: HOME,
    page: () => const HomePage(),
    binding: HomeBinding(),
  ),
  GetPage(
    name: LOGIN,
    page: () => const LoginPage(),
    binding: LoginBinding(),
  ),
  GetPage(
    name: REGISTER,
    page: () => const RegisterPage(),
    binding: RegisterBinding(),
  ),
  GetPage(
    name: DETAIL,
    page: () => const DetailPage(),
    binding: DetailBinding(),
  ),
  GetPage(
    name: EDIT,
    page: () => const EditPage(),
    binding: EditBinding(),
  ),
  GetPage(
    name: SETTINGS,
    page: () => const SettingsPage(),
    binding: SettingsBinding(),
  ),
  GetPage(
    name: CAPTURE,
    page: () => const CapturePage(),
    binding: CaptureBinding(),
    transition: Transition.rightToLeft,
  ),
  GetPage(
    name: MINDMAP,
    page: () => const MindmapPage(),
    binding: MindmapBinding(),
  ),
  // Outras rotas...
];
```

### 2. Implementar Bindings Faltantes

Para cada rota, criar o binding correspondente:

```dart
// lib/app/modules/detail/detail_binding.dart
import 'package:get/get.dart';
import '../../controllers/insight_controller.dart';

class DetailBinding extends Bindings {
  @override
  void dependencies() {
    Get.lazyPut<InsightController>(() => InsightController());
  }
}

// lib/app/modules/edit/edit_binding.dart
import 'package:get/get.dart';
import '../../controllers/insight_controller.dart';

class EditBinding extends Bindings {
  @override
  void dependencies() {
    Get.lazyPut<InsightController>(() => InsightController());
  }
}

// Outros bindings...
```

### 3. Padronizar a Navegação

#### Criar uma Classe Helper de Navegação

```dart
// lib/core/utils/navigation_helper.dart
import 'package:get/get.dart';
import '../config/routes.dart';

class NavigationHelper {
  // Navegação para uma nova tela
  static void toDetail(String insightId) {
    Get.toNamed(AppRoutes.DETAIL, arguments: insightId);
  }
  
  static void toEdit(String insightId) {
    Get.toNamed(AppRoutes.EDIT, arguments: insightId);
  }
  
  static void toCapture() {
    Get.toNamed(AppRoutes.CAPTURE);
  }
  
  // Navegação com substituição
  static void toHome() {
    Get.offAllNamed(AppRoutes.HOME);
  }
  
  static void toLogin() {
    Get.offAllNamed(AppRoutes.LOGIN);
  }
  
  // Funções para diálogos comuns
  static Future<bool?> showConfirmDialog(String title, String message) {
    return Get.dialog<bool>(
      AlertDialog(
        title: Text(title),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Get.back(result: false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Get.back(result: true),
            child: const Text('Confirm'),
          ),
        ],
      ),
    );
  }
}
```

#### Utilizar o Helper em Todo o Código

```dart
// Em vez de
Get.toNamed(AppRoutes.DETAIL, arguments: insight.id);

// Usar
NavigationHelper.toDetail(insight.id);

// Em vez de
final confirm = await Get.dialog<bool>(AlertDialog(...));

// Usar
final confirm = await NavigationHelper.showConfirmDialog('Delete Insight', 'Are you sure?');
```

### 4. Implementar Middleware para Autenticação

#### Criar um Middleware de Autenticação

```dart
// lib/core/middleware/auth_middleware.dart
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../app/controllers/auth_controller.dart';
import '../config/routes.dart';

class AuthMiddleware extends GetMiddleware {
  final authController = Get.find<AuthController>();
  
  @override
  RouteSettings? redirect(String? route) {
    if (!authController.isLoggedIn() && 
        route != AppRoutes.LOGIN && 
        route != AppRoutes.REGISTER) {
      return RouteSettings(name: AppRoutes.LOGIN);
    }
    return null;
  }
  
  @override
  GetPage? onPageCalled(GetPage? page) {
    return page;
  }
}
```

#### Aplicar o Middleware às Rotas Protegidas

```dart
// No arquivo routes.dart
GetPage(
  name: HOME,
  page: () => const HomePage(),
  binding: HomeBinding(),
  middlewares: [AuthMiddleware()],
),
GetPage(
  name: DETAIL,
  page: () => const DetailPage(),
  binding: DetailBinding(),
  middlewares: [AuthMiddleware()],
),
// Aplicar às outras rotas protegidas...
```

### 5. Implementar Validação de Argumentos

Em cada página que recebe argumentos, adicionar validação:

```dart
// lib/app/modules/detail/detail_page.dart
@override
Widget build(BuildContext context) {
  // Verificar se há argumentos
  final args = Get.arguments;
  if (args == null || args is! String) {
    return Scaffold(
      appBar: AppBar(title: const Text('Error')),
      body: const Center(
        child: Text('Invalid arguments. Please go back and try again.'),
      ),
    );
  }

  final insightId = args;
  // Resto do código...
}
```

## Priorização de Ações

1. **Alta prioridade**: Completar definições de rotas e bindings faltantes
2. **Alta prioridade**: Padronizar navegação com NavigationHelper
3. **Média prioridade**: Implementar validação de argumentos
4. **Média prioridade**: Adicionar middleware de autenticação
5. **Baixa prioridade**: Refatorar código existente para usar os novos padrões

## Impacto da Implementação

- **Consistência**: Todas as rotas seguirão o mesmo padrão
- **Segurança**: Rotas protegidas exigirão autenticação
- **Manutenção**: Código mais organizado e previsível
- **Experiência do usuário**: Fluxos de navegação mais coerentes
- **Desenvolvimento**: Facilidade para adicionar novas rotas seguindo o padrão

## Documentação Recomendada

Adicionar documentação para:
- Estrutura de navegação do aplicativo
- Padrões de passagem de argumentos
- Sistema de autenticação e proteção de rotas
- Fluxos de navegação principais