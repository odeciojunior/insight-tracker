# Interface de Usuário e Experiência do Usuário

## Problemas Identificados

### 1. Inconsistências na Interface do Usuário

A interface do usuário apresenta inconsistências em diferentes componentes:

- **Estilo de Botões**: Diferentes abordagens são usadas para botões em todo o aplicativo:
  ```dart
  // Em algumas telas
  ElevatedButton(
    onPressed: _submit,
    child: const Text('Update Insight'),
  );
  
  // Em outras telas
  CustomButton(
    text: 'Save Insight',
    icon: Icons.save,
    onPressed: _saveInsight,
    fullWidth: true,
  );
  ```

- **Exibição de Mensagens**: Diferentes abordagens para exibir mensagens ao usuário:
  ```dart
  // Em alguns controladores
  Get.snackbar(
    'Success',
    'Category added successfully',
    snackPosition: SnackPosition.BOTTOM,
  );
  
  // Em algumas páginas
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(content: Text('Insight deleted')),
  );
  ```

- **Indicadores de Carregamento**: Abordagens variadas para mostrar estados de carregamento:
  ```dart
  // Em algumas telas
  if (_isLoading) {
    return const CircularProgressIndicator();
  }
  
  // Em outras telas
  return const LoadingIndicator(message: 'Loading insights...');
  ```

### 2. Problemas de Acessibilidade

- **Contraste Insuficiente**: Possíveis problemas de contraste em chips e tags.
- **Ausência de Semânticas**: Falta de labels de acessibilidade para elementos interativos.
- **Tamanhos de Fonte Fixos**: Fontes com tamanhos fixos que não se adaptam às configurações de acessibilidade.
- **Foco de Teclado**: Não há gestão adequada de foco de teclado para usuários que não utilizam toque.

### 3. Responsividade Limitada

- **Layouts Fixos**: Diversos widgets têm tamanhos fixos sem adaptação para diferentes tamanhos de tela.
- **Orientação Fixa**: Configuração para forçar apenas o modo retrato:
  ```dart
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);
  ```
- **Uso Inadequado de MediaQuery**: Falta de uso consistente de MediaQuery para adaptar layouts.

### 4. Feedback Visual Insuficiente

- **Estados de Interação**: Alguns elementos interativos não fornecem feedback visual adequado.
- **Validação de Entrada**: Feedback inconsistente para erros de validação.
- **Transições**: Animações e transições limitadas entre estados da interface.

## Soluções Propostas

### 1. Criar um Design System Consistente

#### Implementar um Theme Centralizado

Expandir o arquivo `lib/core/config/themes.dart` para incluir todos os componentes comuns:

```dart
// lib/core/config/themes.dart
import 'package:flutter/material.dart';

class AppThemes {
  // Cores principais
  static const Color primaryColor = Color(0xFF6750A4);
  static const Color secondaryColor = Color(0xFF9C4146);
  static const Color backgroundColor = Color(0xFFF9F9F9);
  static const Color errorColor = Color(0xFFB3261E);
  
  // Espaçamento
  static const double spacing1 = 4.0;
  static const double spacing2 = 8.0;
  static const double spacing3 = 16.0;
  static const double spacing4 = 24.0;
  static const double spacing5 = 32.0;
  
  // Raio de borda
  static const double borderRadius1 = 4.0;
  static const double borderRadius2 = 8.0;
  static const double borderRadius3 = 12.0;
  static const double borderRadius4 = 16.0;
  
  // Elevação
  static const double elevation1 = 1.0;
  static const double elevation2 = 2.0;
  static const double elevation3 = 4.0;
  static const double elevation4 = 8.0;
  
  // Light theme
  static final ThemeData lightTheme = ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: primaryColor,
      brightness: Brightness.light,
      background: backgroundColor,
      error: errorColor,
    ),
    fontFamily: 'Poppins',
    
    // AppBar
    appBarTheme: const AppBarTheme(
      elevation: 0,
      centerTitle: true,
      backgroundColor: Colors.transparent,
      foregroundColor: primaryColor,
      iconTheme: IconThemeData(color: primaryColor),
    ),
    
    // Card
    cardTheme: CardTheme(
      elevation: elevation2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(borderRadius3),
      ),
      clipBehavior: Clip.antiAlias,
      margin: EdgeInsets.all(spacing2),
    ),
    
    // Input
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Colors.white,
      contentPadding: EdgeInsets.all(spacing3),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(borderRadius2),
        borderSide: BorderSide(color: Colors.grey.shade300),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(borderRadius2),
        borderSide: BorderSide(color: Colors.grey.shade300),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(borderRadius2),
        borderSide: const BorderSide(color: primaryColor, width: 2),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(borderRadius2),
        borderSide: const BorderSide(color: errorColor, width: 1),
      ),
      floatingLabelBehavior: FloatingLabelBehavior.auto,
    ),
    
    // Buttons
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        padding: EdgeInsets.symmetric(horizontal: spacing3, vertical: spacing2),
        elevation: elevation2,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(borderRadius2),
        ),
      ),
    ),
    
    // Text button
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        padding: EdgeInsets.symmetric(horizontal: spacing2, vertical: spacing1),
      ),
    ),
    
    // Chip
    chipTheme: ChipThemeData(
      backgroundColor: Colors.grey.shade100,
      selectedColor: primaryColor.withOpacity(0.1),
      labelStyle: const TextStyle(fontSize: 12),
      padding: const EdgeInsets.symmetric(horizontal: spacing2, vertical: spacing1),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(borderRadius1),
      ),
    ),
    
    // SnackBar
    snackBarTheme: SnackBarThemeData(
      behavior: SnackBarBehavior.floating,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(borderRadius2),
      ),
    ),
    
    // Dialog
    dialogTheme: DialogTheme(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(borderRadius3),
      ),
      elevation: elevation4,
    ),
    
    // BottomSheet
    bottomSheetTheme: BottomSheetThemeData(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(
          top: Radius.circular(borderRadius3),
        ),
      ),
      modalElevation: elevation3,
    ),
  );

  // Dark theme com adaptações similares
  static final ThemeData darkTheme = ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: primaryColor,
      brightness: Brightness.dark,
      error: errorColor,
    ),
    // Configurações similares ao tema claro...
  );
}
```

#### Criar Widgets de UI Reutilizáveis

Implementar widgets padronizados para uso em todo o aplicativo:

```dart
// lib/core/widgets/app_button.dart
import 'package:flutter/material.dart';

enum AppButtonType { primary, secondary, text, error }
enum AppButtonSize { small, medium, large }

class AppButton extends StatelessWidget {
  final String text;
  final VoidCallback? onPressed;
  final IconData? icon;
  final AppButtonType type;
  final AppButtonSize size;
  final bool isLoading;
  final bool fullWidth;

  const AppButton({
    Key? key,
    required this.text,
    required this.onPressed,
    this.icon,
    this.type = AppButtonType.primary,
    this.size = AppButtonSize.medium,
    this.isLoading = false,
    this.fullWidth = false,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    // Configurações baseadas no tamanho
    double verticalPadding;
    double horizontalPadding;
    double fontSize;
    double iconSize;
    
    switch (size) {
      case AppButtonSize.small:
        verticalPadding = 6.0;
        horizontalPadding = 12.0;
        fontSize = 12.0;
        iconSize = 16.0;
        break;
      case AppButtonSize.large:
        verticalPadding = 16.0;
        horizontalPadding = 24.0;
        fontSize = 16.0;
        iconSize = 24.0;
        break;
      case AppButtonSize.medium:
      default:
        verticalPadding = 12.0;
        horizontalPadding = 16.0;
        fontSize = 14.0;
        iconSize = 20.0;
        break;
    }
    
    // Configurações baseadas no tipo
    Widget buttonWidget;
    
    switch (type) {
      case AppButtonType.text:
        buttonWidget = TextButton(
          onPressed: isLoading ? null : onPressed,
          style: TextButton.styleFrom(
            padding: EdgeInsets.symmetric(
              vertical: verticalPadding,
              horizontal: horizontalPadding,
            ),
            textStyle: TextStyle(fontSize: fontSize),
          ),
          child: _buildButtonContent(iconSize),
        );
        break;
      case AppButtonType.secondary:
        buttonWidget = OutlinedButton(
          onPressed: isLoading ? null : onPressed,
          style: OutlinedButton.styleFrom(
            padding: EdgeInsets.symmetric(
              vertical: verticalPadding,
              horizontal: horizontalPadding,
            ),
            textStyle: TextStyle(fontSize: fontSize),
          ),
          child: _buildButtonContent(iconSize),
        );
        break;
      case AppButtonType.error:
        buttonWidget = ElevatedButton(
          onPressed: isLoading ? null : onPressed,
          style: ElevatedButton.styleFrom(
            backgroundColor: theme.colorScheme.error,
            foregroundColor: theme.colorScheme.onError,
            padding: EdgeInsets.symmetric(
              vertical: verticalPadding,
              horizontal: horizontalPadding,
            ),
            textStyle: TextStyle(fontSize: fontSize),
          ),
          child: _buildButtonContent(iconSize),
        );
        break;
      case AppButtonType.primary:
      default:
        buttonWidget = ElevatedButton(
          onPressed: isLoading ? null : onPressed,
          style: ElevatedButton.styleFrom(
            padding: EdgeInsets.symmetric(
              vertical: verticalPadding,
              horizontal: horizontalPadding,
            ),
            textStyle: TextStyle(fontSize: fontSize),
          ),
          child: _buildButtonContent(iconSize),
        );
    }
    
    // Aplicar largura total se necessário
    if (fullWidth) {
      return SizedBox(
        width: double.infinity,
        child: buttonWidget,
      );
    }
    
    return buttonWidget;
  }
  
  Widget _buildButtonContent(double iconSize) {
    if (isLoading) {
      return const SizedBox(
        width: 20,
        height: 20,
        child: CircularProgressIndicator(strokeWidth: 2),
      );
    }
    
    if (icon != null) {
      return Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: iconSize),
          const SizedBox(width: 8),
          Text(text),
        ],
      );
    }
    
    return Text(text);
  }
}
```

#### Criar Utilitário para Mensagens

```dart
// lib/core/utils/message_utils.dart
import 'package:flutter/material.dart';
import 'package:get/get.dart';

enum MessageType { info, success, error, warning }

class MessageUtils {
  static void showSnackbar({
    required String title,
    required String message,
    MessageType type = MessageType.info,
    Duration duration = const Duration(seconds: 3),
  }) {
    Color backgroundColor;
    Color textColor;
    IconData icon;
    
    switch (type) {
      case MessageType.success:
        backgroundColor = Colors.green.shade700;
        textColor = Colors.white;
        icon = Icons.check_circle;
        break;
      case MessageType.error:
        backgroundColor = Colors.red.shade700;
        textColor = Colors.white;
        icon = Icons.error;
        break;
      case MessageType.warning:
        backgroundColor = Colors.orange.shade700;
        textColor = Colors.white;
        icon = Icons.warning;
        break;
      case MessageType.info:
      default:
        backgroundColor = Colors.blue.shade700;
        textColor = Colors.white;
        icon = Icons.info;
        break;
    }
    
    Get.snackbar(
      title,
      message,
      snackPosition: SnackPosition.BOTTOM,
      backgroundColor: backgroundColor,
      colorText: textColor,
      margin: const EdgeInsets.all(16),
      borderRadius: 8,
      duration: duration,
      isDismissible: true,
      dismissDirection: DismissDirection.horizontal,
      icon: Icon(icon, color: textColor),
    );
  }
  
  static Future<bool?> showConfirmDialog({
    required String title,
    required String message,
    String confirmText = 'Confirm',
    String cancelText = 'Cancel',
    bool isDanger = false,
  }) {
    return Get.dialog<bool>(
      AlertDialog(
        title: Text(title),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Get.back(result: false),
            child: Text(cancelText),
          ),
          ElevatedButton(
            onPressed: () => Get.back(result: true),
            style: isDanger 
                ? ElevatedButton.styleFrom(
                    backgroundColor: Colors.red,
                    foregroundColor: Colors.white,
                  )
                : null,
            child: Text(confirmText),
          ),
        ],
      ),
    );
  }
}
```

### 2. Melhorar a Acessibilidade

#### Implementar Semântica Clara

```dart
// Exemplo de uso em InsightCard
@override
Widget build(BuildContext context) {
  return Semantics(
    label: 'Insight: $title',
    hint: 'Double tap to view details',
    child: Card(
      // Conteúdo existente...
    ),
  );
}
```

#### Adicionar Suporte para Tamanho de Fonte Dinâmico

```dart
// Em widgets que exibem texto
Text(
  title,
  style: Theme.of(context).textTheme.titleMedium,
  // Use MediaQuery para escalar o tamanho da fonte
  textScaleFactor: MediaQuery.of(context).textScaleFactor,
)
```

#### Melhorar o Contraste

```dart
// Em widgets como chips e tags
final backgroundColor = Theme.of(context).brightness == Brightness.light
  ? tag.color.withOpacity(0.2)
  : tag.color.withOpacity(0.4);
final textColor = tag.color.computeLuminance() > 0.5
  ? Colors.black
  : Colors.white;
```

#### Adicionar Ordem de Foco

```dart
// Nas telas com múltiplos campos
FocusScope(
  child: FocusTraversalGroup(
    child: Form(
      child: Column(
        children: [
          TextFormField(
            autofocus: true, // Primeiro campo recebe foco
            // ...
          ),
          TextFormField(
            // ...
          ),
          // ...
        ],
      ),
    ),
  ),
)
```

### 3. Melhorar a Responsividade

#### Criar Utilitário Responsivo

```dart
// lib/core/utils/responsive_utils.dart
import 'package:flutter/material.dart';

enum DeviceType { mobile, tablet, desktop }

class ResponsiveUtils {
  static DeviceType getDeviceType(BuildContext context) {
    final width = MediaQuery.of(context).size.width;
    
    if (width < 600) {
      return DeviceType.mobile;
    } else if (width < 1200) {
      return DeviceType.tablet;
    } else {
      return DeviceType.desktop;
    }
  }
  
  static double getResponsiveWidth(BuildContext context, {
    required double mobile,
    double? tablet,
    double? desktop,
  }) {
    final deviceType = getDeviceType(context);
    
    switch (deviceType) {
      case DeviceType.tablet:
        return tablet ?? mobile * 1.5;
      case DeviceType.desktop:
        return desktop ?? mobile * 2;
      case DeviceType.mobile:
      default:
        return mobile;
    }
  }
  
  static double getResponsiveFontSize(BuildContext context, {
    required double base,
    double? tablet,
    double? desktop,
  }) {
    final deviceType = getDeviceType(context);
    
    switch (deviceType) {
      case DeviceType.tablet:
        return tablet ?? base * 1.2;
      case DeviceType.desktop:
        return desktop ?? base * 1.4;
      case DeviceType.mobile:
      default:
        return base;
    }
  }
  
  static EdgeInsets getResponsivePadding(BuildContext context, {
    required EdgeInsets mobile,
    EdgeInsets? tablet,
    EdgeInsets? desktop,
  }) {
    final deviceType = getDeviceType(context);
    
    switch (deviceType) {
      case DeviceType.tablet:
        return tablet ?? mobile * 1.5;
      case DeviceType.desktop:
        return desktop ?? mobile * 2;
      case DeviceType.mobile:
      default:
        return mobile;
    }
  }
  
  static Widget responsiveBuilder({
    required BuildContext context,
    required Widget mobile,
    Widget? tablet,
    Widget? desktop,
  }) {
    final deviceType = getDeviceType(context);
    
    switch (deviceType) {
      case DeviceType.tablet:
        return tablet ?? mobile;
      case DeviceType.desktop:
        return desktop ?? tablet ?? mobile;
      case DeviceType.mobile:
      default:
        return mobile;
    }
  }
}
```

#### Implementar Layouts Responsivos

```dart
// Exemplo de uso em uma página
@override
Widget build(BuildContext context) {
  return Scaffold(
    appBar: AppBar(title: const Text('Insight Tracker')),
    body: ResponsiveUtils.responsiveBuilder(
      context: context,
      mobile: _buildMobileLayout(),
      tablet: _buildTabletLayout(),
      desktop: _buildDesktopLayout(),
    ),
  );
}

Widget _buildMobileLayout() {
  return ListView(...);
}

Widget _buildTabletLayout() {
  return Row(
    children: [
      Flexible(
        flex: 1,
        child: _buildSidebar(),
      ),
      Flexible(
        flex: 2,
        child: _buildMainContent(),
      ),
    ],
  );
}

Widget _buildDesktopLayout() {
  return Row(
    children: [
      Flexible(
        flex: 1,
        child: _buildSidebar(),
      ),
      Flexible(
        flex: 3,
        child: _buildMainContent(),
      ),
    ],
  );
}
```

#### Suportar Orientação Landscape

Remover a restrição de orientação retrato-apenas:

```dart
// main.dart - remover estas linhas
await SystemChrome.setPreferredOrientations([
  DeviceOrientation.portraitUp,
  DeviceOrientation.portraitDown,
]);
```

E adaptar layouts para orientação landscape:

```dart
@override
Widget build(BuildContext context) {
  final isLandscape = MediaQuery.of(context).orientation == Orientation.landscape;
  
  if (isLandscape) {
    return Row(
      children: [
        Expanded(child: _buildFormSection()),
        Expanded(child: _buildPreviewSection()),
      ],
    );
  } else {
    return Column(
      children: [
        _buildFormSection(),
        _buildPreviewSection(),
      ],
    );
  }
}
```

### 4. Melhorar o Feedback Visual

#### Implementar Transições e Animações

```dart
// lib/core/utils/transition_utils.dart
import 'package:flutter/material.dart';
import 'package:get/get.dart';

class TransitionUtils {
  static Widget fadeTransition(BuildContext context, Animation<double> animation, Animation<double> secondaryAnimation, Widget child) {
    return FadeTransition(
      opacity: animation,
      child: child,
    );
  }
  
  static Widget slideTransition(BuildContext context, Animation<double> animation, Animation<double> secondaryAnimation, Widget child) {
    return SlideTransition(
      position: Tween<Offset>(
        begin: const Offset(1, 0),
        end: Offset.zero,
      ).animate(animation),
      child: child,
    );
  }
  
  static Widget bottomSheetTransition(Widget child) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
      child: child,
    );
  }
  
  static void configurePageTransitions() {
    // Configurar transições padrão para GetX
    Get.config(
      defaultTransition: Transition.cupertino,
      transitionDuration: const Duration(milliseconds: 300),
    );
  }
}
```

#### Adicionar Animações para Estados de Widget

```dart
// Para estados de carregamento
AnimatedSwitcher(
  duration: const Duration(milliseconds: 300),
  child: isLoading
      ? const LoadingIndicator()
      : const InsightContent(),
)

// Para alternar entre visualizações
AnimatedCrossFade(
  firstChild: ListView(...),
  secondChild: GridView(...),
  crossFadeState: isListView
      ? CrossFadeState.showFirst
      : CrossFadeState.showSecond,
  duration: const Duration(milliseconds: 300),
)
```

#### Adicionar Efeitos de Ripple para Feedback Tátil

```dart
// Em widgets interativos sem esse efeito naturalmente
InkWell(
  onTap: onTap,
  borderRadius: BorderRadius.circular(8),
  splashColor: Theme.of(context).colorScheme.primary.withOpacity(0.2),
  highlightColor: Theme.of(context).colorScheme.primary.withOpacity(0.1),
  child: Container(
    // Conteúdo do widget
  ),
)
```

## Priorização de Ações

1. **Alta prioridade**: Criar um design system consistente
   - Implementar tema centralizado
   - Criar widgets de UI reutilizáveis
   - Padronizar mensagens e diálogos

2. **Alta prioridade**: Melhorar a acessibilidade
   - Adicionar semântica para leitores de tela
   - Melhorar contraste
   - Suportar tamanhos de fonte dinâmicos

3. **Média prioridade**: Implementar layouts responsivos
   - Criar utilitário responsivo
   - Adaptar layouts para diferentes tamanhos de tela
   - Suportar orientação landscape

4. **Média prioridade**: Melhorar feedback visual
   - Adicionar transições e animações
   - Padronizar estados de carregamento
   - Implementar feedback tátil

## Impacto da Implementação

- **Consistência Visual**: Interface unificada e coerente
- **Acessibilidade**: Aplicativo mais inclusivo para todos os usuários
- **Experiência Multiplataforma**: Melhor adaptação a diferentes dispositivos
- **Engajamento**: Melhoria na experiência do usuário com feedback visual adequado
- **Desenvolvimento**: Facilidade para criar novas telas que seguem os padrões estabelecidos

## Documentação Recomendada

Adicionar documentação para:
- Guia de estilo (cores, tipografia, espaçamento)
- Biblioteca de componentes de UI
- Padrões de layout responsivo
- Práticas de acessibilidade
- Exemplos de animações e transições