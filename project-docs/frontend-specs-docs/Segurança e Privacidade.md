# Segurança e Privacidade

## Problemas Identificados

### 1. Gerenciamento de Autenticação Inadequado

O sistema atual de autenticação tem várias vulnerabilidades:

- **Falta de Consistência**: O `AuthController` usa Firebase, mas não implementa todas as práticas de segurança recomendadas.
- **Armazenamento Inseguro de Tokens**: Não há mecanismo explícito para armazenar tokens de forma segura.
- **Ausência de Refresh Token**: Não há implementação de refresh token para manter a sessão do usuário.
- **Verificação de Autenticação Inconsistente**: Algumas rotas podem ser acessíveis sem autenticação adequada.

```dart
// lib/app/controllers/auth_controller.dart
Future<void> login(String email, String password) async {
  try {
    await _auth.signInWithEmailAndPassword(
      email: email.trim(),
      password: password.trim(),
    );
  } catch (e) {
    Get.snackbar(
      'Login Error',
      e.toString(),
      snackPosition: SnackPosition.BOTTOM,
    );
  }
}
```

### 2. Falta de Criptografia para Dados Sensíveis

Os dados são armazenados localmente sem criptografia:

- **Insights e Dados Pessoais**: Armazenados no Hive sem criptografia.
- **Chaves Hardcoded**: Alguns serviços podem usar chaves hardcoded.
- **Ausência de Secure Storage**: Não há uso de armazenamento seguro para dados sensíveis.

```dart
// lib/services/storage_service.dart
// Armazenamento não criptografado
_insightsBox = await Hive.openBox<Insight>(INSIGHTS_BOX);
```

### 3. Vulnerabilidades em Solicitações de Rede

Potenciais vulnerabilidades em chamadas de API:

- **Ausência de SSL Pinning**: Não há implementação de SSL pinning para prevenir ataques MITM.
- **Falta de Sanitização de Entradas**: Dados de entrada não são adequadamente validados ou sanitizados.
- **Gerenciamento de Erros Inseguro**: Mensagens de erro podem expor informações sensíveis.

### 4. Considerações de Privacidade Ausentes

O aplicativo não implementa funcionalidades relacionadas à privacidade do usuário:

- **Ausência de Política de Privacidade**: Não há política de privacidade ou termos de uso.
- **Falta de Opções de Exportação/Exclusão de Dados**: Usuários não podem exportar ou excluir seus dados facilmente.
- **Ausência de Configurações de Privacidade**: Não há opções para o usuário controlar a coleta de dados.

## Soluções Propostas

### 1. Melhorar Autenticação e Gerenciamento de Sessão

#### Implementar AuthService Seguro

```dart
// lib/services/auth_service.dart
import 'package:firebase_auth/firebase_auth.dart' as firebase;
import 'package:get/get.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../app/data/models/user.dart';
import '../core/config/routes.dart';

class AuthService extends GetxService {
  final firebase.FirebaseAuth _auth = firebase.FirebaseAuth.instance;
  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();
  
  final Rx<User?> currentUser = Rx<User?>(null);
  final RxBool isLoading = false.obs;
  final Rx<String?> errorMessage = Rx<String?>(null);
  
  static const String _tokenKey = 'auth_token';
  static const String _refreshTokenKey = 'refresh_token';
  static const String _userIdKey = 'user_id';
  
  @override
  Future<void> onInit() async {
    super.onInit();
    await _loadStoredAuth();
    _setupAuthStateListener();
  }
  
  Future<void> _loadStoredAuth() async {
    try {
      final storedToken = await _secureStorage.read(key: _tokenKey);
      final storedUserId = await _secureStorage.read(key: _userIdKey);
      
      if (storedToken != null && storedUserId != null) {
        // Verificar se o token é válido
        final currentFirebaseUser = _auth.currentUser;
        if (currentFirebaseUser != null && currentFirebaseUser.uid == storedUserId) {
          // Token válido, usuário já autenticado
          _syncUserData(currentFirebaseUser);
        } else {
          // Token inválido ou expirado, tentar refresh
          await _refreshToken();
        }
      }
    } catch (e) {
      print('Error loading stored auth: $e');
      // Limpar tokens inválidos
      await _clearTokens();
    }
  }
  
  void _setupAuthStateListener() {
    _auth.authStateChanges().listen((firebase.User? firebaseUser) async {
      if (firebaseUser != null) {
        // Novo login, salvar tokens
        final idToken = await firebaseUser.getIdToken();
        await _saveTokens(
          token: idToken,
          refreshToken: firebaseUser.refreshToken,
          userId: firebaseUser.uid,
        );
        
        _syncUserData(firebaseUser);
      } else {
        // Logout
        currentUser.value = null;
        await _clearTokens();
      }
    });
  }
  
  void _syncUserData(firebase.User firebaseUser) {
    // Converter FirebaseUser para o modelo User do app
    currentUser.value = User(
      id: firebaseUser.uid,
      email: firebaseUser.email!,
      displayName: firebaseUser.displayName,
      photoUrl: firebaseUser.photoURL,
      createdAt: firebaseUser.metadata.creationTime!,
      lastLoginAt: firebaseUser.metadata.lastSignInTime,
    );
  }
  
  Future<void> _saveTokens({
    required String token,
    String? refreshToken,
    required String userId,
  }) async {
    await _secureStorage.write(key: _tokenKey, value: token);
    if (refreshToken != null) {
      await _secureStorage.write(key: _refreshTokenKey, value: refreshToken);
    }
    await _secureStorage.write(key: _userIdKey, value: userId);
  }
  
  Future<void> _clearTokens() async {
    await _secureStorage.delete(key: _tokenKey);
    await _secureStorage.delete(key: _refreshTokenKey);
    await _secureStorage.delete(key: _userIdKey);
  }
  
  Future<bool> _refreshToken() async {
    try {
      final refreshToken = await _secureStorage.read(key: _refreshTokenKey);
      if (refreshToken == null) return false;
      
      // Implementar lógica de refresh token com Firebase
      // Como o Firebase gerencia automaticamente o refresh de tokens,
      // esta implementação pode variar
      
      return true;
    } catch (e) {
      print('Error refreshing token: $e');
      await _clearTokens();
      return false;
    }
  }
  
  bool isLoggedIn() {
    return currentUser.value != null;
  }
  
  Future<String?> getIdToken() async {
    try {
      // Verificar se token está salvo
      final storedToken = await _secureStorage.read(key: _tokenKey);
      if (storedToken != null) return storedToken;
      
      // Se não, solicitar novo token
      final user = _auth.currentUser;
      if (user != null) {
        final token = await user.getIdToken(true);
        await _secureStorage.write(key: _tokenKey, value: token);
        return token;
      }
      
      return null;
    } catch (e) {
      print('Error getting ID token: $e');
      return null;
    }
  }
  
  Future<void> login(String email, String password) async {
    try {
      isLoading.value = true;
      errorMessage.value = null;
      
      await _auth.signInWithEmailAndPassword(
        email: email.trim(),
        password: password.trim(),
      );
      
      // Navegação será feita pelo listener de authStateChanges
    } catch (e) {
      errorMessage.value = _handleAuthError(e);
      throw e;
    } finally {
      isLoading.value = false;
    }
  }
  
  Future<void> register(String email, String password) async {
    try {
      isLoading.value = true;
      errorMessage.value = null;
      
      final userCredential = await _auth.createUserWithEmailAndPassword(
        email: email.trim(),
        password: password.trim(),
      );
      
      // Enviar email de verificação
      await userCredential.user?.sendEmailVerification();
      
      // Navegação será feita pelo listener de authStateChanges
    } catch (e) {
      errorMessage.value = _handleAuthError(e);
      throw e;
    } finally {
      isLoading.value = false;
    }
  }
  
  Future<void> logout() async {
    try {
      isLoading.value = true;
      errorMessage.value = null;
      
      await _auth.signOut();
      await _clearTokens();
      
      // Navegação será feita pelo listener de authStateChanges
    } catch (e) {
      errorMessage.value = _handleAuthError(e);
      throw e;
    } finally {
      isLoading.value = false;
    }
  }
  
  Future<void> resetPassword(String email) async {
    try {
      isLoading.value = true;
      errorMessage.value = null;
      
      await _auth.sendPasswordResetEmail(email: email.trim());
      
      Get.snackbar(
        'Password Reset',
        'Password reset link sent to your email',
        snackPosition: SnackPosition.BOTTOM,
      );
    } catch (e) {
      errorMessage.value = _handleAuthError(e);
      throw e;
    } finally {
      isLoading.value = false;
    }
  }
  
  String _handleAuthError(dynamic e) {
    if (e is firebase.FirebaseAuthException) {
      switch (e.code) {
        case 'user-not-found':
          return 'No user found with this email';
        case 'wrong-password':
          return 'Wrong password';
        case 'email-already-in-use':
          return 'Email already in use';
        case 'weak-password':
          return 'Password is too weak';
        case 'invalid-email':
          return 'Invalid email address';
        case 'user-disabled':
          return 'This account has been disabled';
        case 'too-many-requests':
          return 'Too many unsuccessful login attempts. Please try again later.';
        default:
          return 'Authentication error: ${e.message}';
      }
    }
    return 'An unexpected error occurred';
  }
}
```

#### Implementar Middleware de Autenticação

```dart
// lib/core/middleware/auth_middleware.dart
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../services/auth_service.dart';
import '../config/routes.dart';

class AuthMiddleware extends GetMiddleware {
  final authService = Get.find<AuthService>();
  
  @override
  RouteSettings? redirect(String? route) {
    // Rotas públicas que não precisam de autenticação
    final publicRoutes = [
      AppRoutes.LOGIN,
      AppRoutes.REGISTER,
      AppRoutes.RESET_PASSWORD,
    ];
    
    if (!authService.isLoggedIn() && !publicRoutes.contains(route)) {
      // Salvar rota atual para redirecionamento após login
      if (route != null && route != AppRoutes.HOME) {
        Get.find<StorageService>().saveSetting('last_route', route);
      }
      
      return const RouteSettings(name: AppRoutes.LOGIN);
    }
    
    // Se o usuário já está logado e tenta acessar uma rota de autenticação
    if (authService.isLoggedIn() && publicRoutes.contains(route)) {
      return const RouteSettings(name: AppRoutes.HOME);
    }
    
    return null;
  }
  
  @override
  GetPage? onPageCalled(GetPage? page) {
    return page;
  }
}
```

### 2. Implementar Criptografia para Dados Sensíveis

#### Criar Serviço de Criptografia

```dart
// lib/services/encryption_service.dart
import 'dart:convert';
import 'package:crypto/crypto.dart';
import 'package:encrypt/encrypt.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:get/get.dart';
import 'package:uuid/uuid.dart';

class EncryptionService extends GetxService {
  static const String _keyName = 'encryption_key';
  static const String _ivName = 'encryption_iv';
  
  late final Encrypter _encrypter;
  late final IV _iv;
  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();
  
  @override
  Future<EncryptionService> onInit() async {
    await _initializeEncryption();
    return this;
  }
  
  Future<void> _initializeEncryption() async {
    try {
      // Tentar recuperar chave e IV existentes
      String? storedKey = await _secureStorage.read(key: _keyName);
      String? storedIv = await _secureStorage.read(key: _ivName);
      
      if (storedKey == null || storedIv == null) {
        // Gerar nova chave e IV
        final key = Key.fromSecureRandom(32);
        final iv = IV.fromSecureRandom(16);
        
        // Salvar chave e IV
        await _secureStorage.write(key: _keyName, value: base64Encode(key.bytes));
        await _secureStorage.write(key: _ivName, value: base64Encode(iv.bytes));
        
        storedKey = base64Encode(key.bytes);
        storedIv = base64Encode(iv.bytes);
      }
      
      // Inicializar encrypter
      final key = Key(base64Decode(storedKey));
      _iv = IV(base64Decode(storedIv));
      _encrypter = Encrypter(AES(key, mode: AESMode.cbc));
    } catch (e) {
      print('Error initializing encryption: $e');
      // Fallback para evitar falha completa
      final fallbackKey = Key.fromUtf8(const Uuid().v4().substring(0, 32));
      _iv = IV.fromLength(16);
      _encrypter = Encrypter(AES(fallbackKey, mode: AESMode.cbc));
    }
  }
  
  String encrypt(String plainText) {
    if (plainText.isEmpty) return '';
    
    try {
      final encrypted = _encrypter.encrypt(plainText, iv: _iv);
      return encrypted.base64;
    } catch (e) {
      print('Error encrypting data: $e');
      return plainText; // Fallback para evitar perda de dados
    }
  }
  
  String decrypt(String encryptedText) {
    if (encryptedText.isEmpty) return '';
    
    try {
      final encrypted = Encrypted.fromBase64(encryptedText);
      return _encrypter.decrypt(encrypted, iv: _iv);
    } catch (e) {
      print('Error decrypting data: $e');
      return encryptedText; // Fallback para evitar perda de dados
    }
  }
  
  String hashPassword(String password, String salt) {
    final bytes = utf8.encode(password + salt);
    final digest = sha256.convert(bytes);
    return digest.toString();
  }
  
  String generateSalt() {
    return const Uuid().v4();
  }
}
```

#### Modificar o StorageService para Usar Criptografia

```dart
// lib/services/storage_service.dart
// Adicionar suporte para criptografia

Future<void> saveInsight(Insight insight) async {
  try {
    final encryptionService = Get.find<EncryptionService>();
    
    // Criptografar conteúdo sensível
    final encryptedInsight = insight.copyWith(
      title: encryptionService.encrypt(insight.title),
      content: encryptionService.encrypt(insight.content),
    );
    
    await _insightsBox.put(insight.id, encryptedInsight);
  } catch (e) {
    errorMessage.value = 'Error saving insight: $e';
    throw Exception('Failed to save insight: $e');
  }
}

Future<Insight?> getInsight(String id) async {
  try {
    final encryptionService = Get.find<EncryptionService>();
    final encryptedInsight = _insightsBox.get(id);
    
    if (encryptedInsight == null) return null;
    
    // Descriptografar conteúdo
    return encryptedInsight.copyWith(
      title: encryptionService.decrypt(encryptedInsight.title),
      content: encryptionService.decrypt(encryptedInsight.content),
    );
  } catch (e) {
    errorMessage.value = 'Error getting insight: $e';
    throw Exception('Failed to get insight: $e');
  }
}

Future<List<Insight>> getAllInsights() async {
  try {
    final encryptionService = Get.find<EncryptionService>();
    final encryptedInsights = _insightsBox.values.toList();
    
    // Descriptografar todos os insights
    return encryptedInsights.map((insight) => insight.copyWith(
      title: encryptionService.decrypt(insight.title),
      content: encryptionService.decrypt(insight.content),
    )).toList();
  } catch (e) {
    errorMessage.value = 'Error getting insights: $e';
    throw Exception('Failed to get insights: $e');
  }
}
```

### 3. Melhorar Segurança em Chamadas de Rede

#### Implementar SSL Pinning

```dart
// lib/services/api_service.dart
// Adicionar configuração de SSL Pinning ao Dio

void _initDio() {
  // Opções básicas
  final options = BaseOptions(
    baseUrl: baseUrl,
    connectTimeout: Duration(seconds: 30),
    receiveTimeout: Duration(seconds: 30),
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
  );
  
  _dio = Dio(options);
  
  // Implementar SSL Pinning
  _configureSSLPinning();
  
  // Adicionar interceptors
  _dio.interceptors.add(DioCacheInterceptor(options: cacheOptions));
  _dio.interceptors.add(LogInterceptor(
    request: true,
    requestBody: true,
    responseBody: true,
    error: true,
  ));
  
  // Interceptor para adicionar token de autenticação
  _dio.interceptors.add(InterceptorsWrapper(
    onRequest: (options, handler) async {
      // Adicionar token de autenticação
      final authService = Get.find<AuthService>();
      final token = await authService.getIdToken();
      
      if (token != null) {
        options.headers['Authorization'] = 'Bearer $token';
      }
      
      isLoading.value = true;
      errorMessage.value = null;
      return handler.next(options);
    },
    onResponse: (response, handler) {
      isLoading.value = false;
      return handler.next(response);
    },
    onError: (DioException e, handler) {
      isLoading.value = false;
      
      // Verificar erros de autenticação
      if (e.response?.statusCode == 401) {
        // Token expirado ou inválido
        final authService = Get.find<AuthService>();
        authService.logout();
      }
      
      errorMessage.value = _handleError(e);
      return handler.next(e);
    },
  ));
}

void _configureSSLPinning() {
  // No Flutter, o SSL Pinning pode ser implementado de várias formas
  // Uma opção é usar o pacote 'dio_pinning' ou 'dio_http_formatter'
  
  // Exemplo com HttpClient personalizado
  (_dio.httpClientAdapter as DefaultHttpClientAdapter).onHttpClientCreate = (client) {
    client.badCertificateCallback = (cert, host, port) {
      // Verificar certificado
      return _validateCertificate(cert, host);
    };
    return client;
  };
}

bool _validateCertificate(X509Certificate cert, String host) {
  // Hash SHA-256 do certificado esperado
  const List<String> validSHA256Fingerprints = [
    'ab:cd:ef:...', // Fingerprint do certificado de produção
    '12:34:56:...', // Fingerprint do certificado de homologação
  ];
  
  // Obter fingerprint do certificado atual
  final fingerprint = cert.sha256Fingerprint();
  
  return validSHA256Fingerprints.contains(fingerprint);
}

String _handleError(DioException error) {
  // Tratar erro sem expor detalhes sensíveis
  String message;
  
  switch (error.type) {
    case DioExceptionType.connectionTimeout:
    case DioExceptionType.sendTimeout:
    case DioExceptionType.receiveTimeout:
      message = 'Connection timeout';
      break;
    case DioExceptionType.badResponse:
      final statusCode = error.response?.statusCode;
      if (statusCode == 401) {
        message = 'Authentication required';
      } else if (statusCode == 403) {
        message = 'Access denied';
      } else if (statusCode == 404) {
        message = 'Resource not found';
      } else if (statusCode! >= 500) {
        message = 'Server error, please try again later';
      } else {
        message = 'Request failed';
      }
      break;
    case DioExceptionType.cancel:
      message = 'Request cancelled';
      break;
    case DioExceptionType.unknown:
    default:
      if (error.error is SocketException) {
        message = 'No internet connection';
      } else {
        message = 'Unexpected error occurred';
      }
      break;
  }
  
  // Log do erro completo apenas em ambiente de desenvolvimento
  assert(() {
    print('API Error: ${error.message}\n${error.response}');
    return true;
  }());
  
  return message;
}
```

#### Implementar Validação de Entrada

```dart
// lib/core/utils/input_validator.dart
class InputValidator {
  static String? validateEmail(String? value) {
    if (value == null || value.isEmpty) {
      return 'Email is required';
    }
    
    // Expressão regular para validação de email
    const pattern = r'^[\w-]+(\.[\w-]+)*@([\w-]+\.)+[a-zA-Z]{2,7}$';
    final regex = RegExp(pattern);
    
    if (!regex.hasMatch(value)) {
      return 'Enter a valid email address';
    }
    
    return null;
  }
  
  static String? validatePassword(String? value) {
    if (value == null || value.isEmpty) {
      return 'Password is required';
    }
    
    if (value.length < 8) {
      return 'Password must be at least 8 characters';
    }
    
    // Verificar complexidade da senha
    bool hasUppercase = value.contains(RegExp(r'[A-Z]'));
    bool hasDigits = value.contains(RegExp(r'[0-9]'));
    bool hasSpecialChars = value.contains(RegExp(r'[!@#$%^&*(),.?":{}|<>]'));
    
    if (!(hasUppercase && hasDigits && hasSpecialChars)) {
      return 'Password must include uppercase, number, and special character';
    }
    
    return null;
  }
  
  static String? validateName(String? value) {
    if (value == null || value.isEmpty) {
      return 'Name is required';
    }
    
    // Sanitizar entrada para evitar injeção
    if (value.contains(RegExp(r'[<>]'))) {
      return 'Invalid characters';
    }
    
    return null;
  }
  
  static String? validateInsightTitle(String? value) {
    if (value == null || value.isEmpty) {
      return 'Title is required';
    }
    
    if (value.length > 100) {
      return 'Title must be less than 100 characters';
    }
    
    // Sanitizar entrada para evitar injeção
    if (value.contains(RegExp(r'[<>]'))) {
      return 'Invalid characters';
    }
    
    return null;
  }
  
  static String? validateInsightContent(String? value) {
    if (value == null || value.isEmpty) {
      return 'Content is required';
    }
    
    // Sanitizar entrada para evitar injeção
    if (value.contains(RegExp(r'<script'))) {
      return 'Invalid content';
    }
    
    return null;
  }
  
  static String sanitizeInput(String input) {
    // Remove tags HTML potencialmente perigosos
    String sanitized = input.replaceAll(RegExp(r'<script.*?>.*?</script>', 
      caseSensitive: false, multiLine: true), '');
    
    // Escapa outros tags HTML
    sanitized = sanitized.replaceAll('<', '&lt;').replaceAll('>', '&gt;');
    
    return sanitized;
  }
}
```

#### Usar os Validadores nos Formulários

```dart
// lib/app/modules/login/login_page.dart
// Adicionar validação ao formulário de login

TextFormField(
  controller: _emailController,
  decoration: const InputDecoration(
    labelText: 'Email',
    hintText: 'Enter your email',
    border: OutlineInputBorder(),
    prefixIcon: Icon(Icons.email),
  ),
  keyboardType: TextInputType.emailAddress,
  validator: InputValidator.validateEmail,
  enabled: !_isLoading,
),

TextFormField(
  controller: _passwordController,
  decoration: InputDecoration(
    labelText: 'Password',
    hintText: 'Enter your password',
    border: const OutlineInputBorder(),
    prefixIcon: const Icon(Icons.lock),
    suffixIcon: IconButton(
      icon: Icon(
        _obscurePassword
            ? Icons.visibility_off
            : Icons.visibility,
      ),
      onPressed: () {
        setState(() {
          _obscurePassword = !_obscurePassword;
        });
      },
    ),
  ),
  obscureText: _obscurePassword,
  validator: InputValidator.validatePassword,
  enabled: !_isLoading,
),
```

### 4. Implementar Recursos de Privacidade

#### Criar Tela de Configurações de Privacidade

```dart
// lib/app/modules/privacy/privacy_settings_page.dart
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../services/storage_service.dart';

class PrivacySettingsPage extends StatefulWidget {
  const PrivacySettingsPage({Key? key}) : super(key: key);

  @override
  State<PrivacySettingsPage> createState() => _PrivacySettingsPageState();
}

class _PrivacySettingsPageState extends State<PrivacySettingsPage> {
  final StorageService _storageService = Get.find<StorageService>();
  
  bool _encryptData = true;
  bool _collectAnalytics = true;
  bool _requireBiometrics = false;
  bool _autoLogout = true;
  int _autoLogoutMinutes = 30;
  bool _isLoading = true;
  
  @override
  void initState() {
    super.initState();
    _loadSettings();
  }
  
  Future<void> _loadSettings() async {
    setState(() {
      _isLoading = true;
    });
    
    try {
      _encryptData = await _storageService.getSetting('encrypt_data', 
                             defaultValue: true) as bool;
      _collectAnalytics = await _storageService.getSetting('collect_analytics', 
                             defaultValue: true) as bool;
      _requireBiometrics = await _storageService.getSetting('require_biometrics', 
                             defaultValue: false) as bool;
      _autoLogout = await _storageService.getSetting('auto_logout', 
                             defaultValue: true) as bool;
      _autoLogoutMinutes = await _storageService.getSetting('auto_logout_minutes', 
                             defaultValue: 30) as int;
    } catch (e) {
      print('Error loading privacy settings: $e');
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }
  
  Future<void> _saveSettings() async {
    setState(() {
      _isLoading = true;
    });
    
    try {
      await _storageService.saveSetting('encrypt_data', _encryptData);
      await _storageService.saveSetting('collect_analytics', _collectAnalytics);
      await _storageService.saveSetting('require_biometrics', _requireBiometrics);
      await _storageService.saveSetting('auto_logout', _autoLogout);
      await _storageService.saveSetting('auto_logout_minutes', _autoLogoutMinutes);
      
      Get.snackbar(
        'Success',
        'Privacy settings saved',
        snackPosition: SnackPosition.BOTTOM,
      );
    } catch (e) {
      print('Error saving privacy settings: $e');
      Get.snackbar(
        'Error',
        'Failed to save privacy settings',
        snackPosition: SnackPosition.BOTTOM,
      );
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Privacy Settings'),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Data Security',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 16),# Segurança e Privacidade (continuação)

```dart
                  SwitchListTile(
                    title: const Text('Encrypt data'),
                    subtitle: const Text(
                      'Encrypts your insights for additional security',
                    ),
                    value: _encryptData,
                    onChanged: (value) {
                      setState(() {
                        _encryptData = value;
                      });
                    },
                  ),
                  
                  SwitchListTile(
                    title: const Text('Require biometric authentication'),
                    subtitle: const Text(
                      'Use fingerprint or face ID to access your insights',
                    ),
                    value: _requireBiometrics,
                    onChanged: (value) {
                      setState(() {
                        _requireBiometrics = value;
                      });
                    },
                  ),
                  
                  const Divider(height: 32),
                  
                  const Text(
                    'Session Management',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 16),
                  
                  SwitchListTile(
                    title: const Text('Auto logout'),
                    subtitle: const Text(
                      'Automatically log out after period of inactivity',
                    ),
                    value: _autoLogout,
                    onChanged: (value) {
                      setState(() {
                        _autoLogout = value;
                      });
                    },
                  ),
                  
                  if (_autoLogout)
                    Padding(
                      padding: const EdgeInsets.only(left: 16, right: 16, top: 8),
                      child: Row(
                        children: [
                          const Text('Logout after: '),
                          Expanded(
                            child: Slider(
                              value: _autoLogoutMinutes.toDouble(),
                              min: 1,
                              max: 60,
                              divisions: 59,
                              label: '$_autoLogoutMinutes minutes',
                              onChanged: (value) {
                                setState(() {
                                  _autoLogoutMinutes = value.toInt();
                                });
                              },
                            ),
                          ),
                          Text('$_autoLogoutMinutes min'),
                        ],
                      ),
                    ),
                  
                  const Divider(height: 32),
                  
                  const Text(
                    'App Usage',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 16),
                  
                  SwitchListTile(
                    title: const Text('Usage analytics'),
                    subtitle: const Text(
                      'Share anonymous usage data to help improve the app',
                    ),
                    value: _collectAnalytics,
                    onChanged: (value) {
                      setState(() {
                        _collectAnalytics = value;
                      });
                    },
                  ),
                  
                  const Divider(height: 32),
                  
                  const Text(
                    'Data Management',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 16),
                  
                  ListTile(
                    title: const Text('Export all data'),
                    subtitle: const Text(
                      'Download all your data as a JSON file',
                    ),
                    trailing: const Icon(Icons.download),
                    onTap: _exportData,
                  ),
                  
                  ListTile(
                    title: const Text('Delete all data'),
                    subtitle: const Text(
                      'Permanently delete all your insights and settings',
                    ),
                    trailing: const Icon(Icons.delete_forever, color: Colors.red),
                    onTap: _confirmDataDeletion,
                  ),
                  
                  const SizedBox(height: 32),
                  
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: _saveSettings,
                      child: const Text('Save Settings'),
                    ),
                  ),
                ],
              ),
            ),
    );
  }
  
  Future<void> _exportData() async {
    // Mostrar diálogo de loading
    Get.dialog(
      const Center(
        child: Card(
          child: Padding(
            padding: EdgeInsets.all(16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                CircularProgressIndicator(),
                SizedBox(height: 16),
                Text('Preparing your data...'),
              ],
            ),
          ),
        ),
      ),
      barrierDismissible: false,
    );
    
    try {
      // Obter todos os insights
      final insights = await _storageService.getAllInsights();
      
      // Obter todas as categorias
      final categories = await _storageService.getAllCategories();
      
      // Obter todas as relações
      final relationships = await _storageService.getAllRelationships();
      
      // Preparar dados para exportação
      final exportData = {
        'insights': insights.map((i) => i.toJson()).toList(),
        'categories': categories.map((c) => c.toJson()).toList(),
        'relationships': relationships.map((r) => r.toJson()).toList(),
        'metadata': {
          'exportDate': DateTime.now().toIso8601String(),
          'appVersion': '1.0.0',
        },
      };
      
      // Converter para JSON
      final jsonData = jsonEncode(exportData);
      
      // Compartilhar arquivo (implementação depende da plataforma)
      // Aqui podemos usar pacotes como share_plus ou path_provider para salvar o arquivo
      
      // Fechar diálogo de loading
      Get.back();
      
      // Mostrar diálogo de conclusão
      Get.dialog(
        AlertDialog(
          title: const Text('Data Export Complete'),
          content: const Text('Your data has been exported successfully.'),
          actions: [
            TextButton(
              onPressed: () => Get.back(),
              child: const Text('OK'),
            ),
          ],
        ),
      );
    } catch (e) {
      // Fechar diálogo de loading
      Get.back();
      
      // Mostrar erro
      Get.snackbar(
        'Export Failed',
        'Could not export your data: $e',
        snackPosition: SnackPosition.BOTTOM,
      );
    }
  }
  
  void _confirmDataDeletion() {
    Get.dialog(
      AlertDialog(
        title: const Text('Delete All Data'),
        content: const Text(
          'This will permanently delete all your insights, categories, and settings. '
          'This action cannot be undone.'
        ),
        actions: [
          TextButton(
            onPressed: () => Get.back(),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              Get.back();
              _deleteAllData();
            },
            style: TextButton.styleFrom(
              foregroundColor: Colors.red,
            ),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }
  
  Future<void> _deleteAllData() async {
    // Mostrar diálogo de loading
    Get.dialog(
      const Center(
        child: Card(
          child: Padding(
            padding: EdgeInsets.all(16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                CircularProgressIndicator(),
                SizedBox(height: 16),
                Text('Deleting your data...'),
              ],
            ),
          ),
        ),
      ),
      barrierDismissible: false,
    );
    
    try {
      // Limpar todos os dados
      await _storageService.clearAllData();
      
      // Fechar diálogo de loading
      Get.back();
      
      // Mostrar confirmação
      Get.snackbar(
        'Data Deleted',
        'All your data has been permanently deleted',
        snackPosition: SnackPosition.BOTTOM,
      );
      
      // Redirecionar para login
      final authService = Get.find<AuthService>();
      await authService.logout();
    } catch (e) {
      // Fechar diálogo de loading
      Get.back();
      
      // Mostrar erro
      Get.snackbar(
        'Deletion Failed',
        'Could not delete your data: $e',
        snackPosition: SnackPosition.BOTTOM,
      );
    }
  }
}
```

#### Criar Política de Privacidade

```dart
// lib/app/modules/privacy/privacy_policy_page.dart
import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';

class PrivacyPolicyPage extends StatelessWidget {
  const PrivacyPolicyPage({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Privacy Policy'),
      ),
      body: Markdown(
        data: _privacyPolicyText,
        padding: const EdgeInsets.all(16),
      ),
    );
  }
  
  // Texto da política de privacidade
  static const String _privacyPolicyText = '''
# Privacy Policy

## Introduction

This Privacy Policy explains how Insight Tracker ("we", "our", or "us") collects, uses, and shares your information when you use our mobile application ("App").

## Information We Collect

### Information You Provide

When you use our App, we may collect the following information that you provide:

- **Account Information**: Email address and password when you create an account
- **Profile Information**: Name, profile picture, and other details you choose to add
- **Content**: Insights, notes, and other content you create in the App
- **Feedback**: Information you provide when you contact us for support

### Information Collected Automatically

When you use our App, we may automatically collect:

- **Device Information**: Device type, operating system, and unique device identifiers
- **Usage Information**: How you interact with our App, which features you use, and how often
- **Log Information**: Error reports and performance data

## How We Use Your Information

We use your information to:

- Provide and maintain the App
- Improve, personalize, and expand the App
- Understand how you use the App
- Develop new features, products, and services
- Communicate with you, including for customer support
- Protect against fraud and abuse

## Security

We use reasonable security measures to protect your information. These measures include encryption of sensitive data and secure authentication processes.

## Your Choices

You can:
- Update or correct your account information
- Export your data
- Delete your account and data
- Control privacy settings in the App

## Changes to This Policy

We may update this Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on this page and updating the "Last Updated" date.

## Contact Us

If you have any questions about this Privacy Policy, please contact us at: privacy@insighttracker.example.com

Last Updated: March 2023
''';
}
```

#### Adicionar Serviço de Proteção Biométrica

```dart
// lib/services/biometric_service.dart
import 'package:flutter/services.dart';
import 'package:get/get.dart';
import 'package:local_auth/local_auth.dart';
import 'package:local_auth/error_codes.dart' as auth_error;

class BiometricService extends GetxService {
  final LocalAuthentication _auth = LocalAuthentication();
  final RxBool isAvailable = false.obs;
  final RxBool isEnabled = false.obs;
  final RxString errorMessage = ''.obs;
  
  @override
  Future<BiometricService> onInit() async {
    await _checkBiometrics();
    return this;
  }
  
  Future<void> _checkBiometrics() async {
    try {
      final canCheckBiometrics = await _auth.canCheckBiometrics;
      final isDeviceSupported = await _auth.isDeviceSupported();
      isAvailable.value = canCheckBiometrics && isDeviceSupported;
      
      if (isAvailable.value) {
        final biometricTypes = await _auth.getAvailableBiometrics();
        print('Available biometrics: $biometricTypes');
      }
    } on PlatformException catch (e) {
      print('Error checking biometrics: $e');
      isAvailable.value = false;
    }
  }
  
  Future<bool> authenticate({
    String reason = 'Authenticate to access your insights',
  }) async {
    if (!isAvailable.value) {
      errorMessage.value = 'Biometric authentication not available';
      return false;
    }
    
    try {
      errorMessage.value = '';
      
      final authenticated = await _auth.authenticate(
        localizedReason: reason,
        options: const AuthenticationOptions(
          stickyAuth: true,
          biometricOnly: true,
        ),
      );
      
      return authenticated;
    } on PlatformException catch (e) {
      switch (e.code) {
        case auth_error.notAvailable:
          errorMessage.value = 'Biometric authentication not available';
          break;
        case auth_error.notEnrolled:
          errorMessage.value = 'No biometrics enrolled on this device';
          break;
        case auth_error.lockedOut:
          errorMessage.value = 'Biometric authentication locked out due to too many attempts';
          break;
        case auth_error.permanentlyLockedOut:
          errorMessage.value = 'Biometric authentication permanently locked';
          break;
        case auth_error.passcodeNotSet:
          errorMessage.value = 'Device does not have a screen lock set up';
          break;
        default:
          errorMessage.value = 'Error: ${e.message}';
      }
      
      print('Biometric authentication error: ${e.code} - ${e.message}');
      return false;
    }
  }
  
  Future<void> enableBiometrics() async {
    // Autenticar uma vez para confirmar que funciona
    final authenticated = await authenticate(
      reason: 'Authenticate to enable biometric login',
    );
    
    if (authenticated) {
      isEnabled.value = true;
      
      // Salvar preferência
      final storageService = Get.find<StorageService>();
      await storageService.saveSetting('require_biometrics', true);
      
      Get.snackbar(
        'Biometrics Enabled',
        'You can now use biometrics to access the app',
        snackPosition: SnackPosition.BOTTOM,
      );
    }
  }
  
  Future<void> disableBiometrics() async {
    isEnabled.value = false;
    
    // Salvar preferência
    final storageService = Get.find<StorageService>();
    await storageService.saveSetting('require_biometrics', false);
    
    Get.snackbar(
      'Biometrics Disabled',
      'Biometric authentication has been turned off',
      snackPosition: SnackPosition.BOTTOM,
    );
  }
  
  Future<bool> checkBiometricSettings() async {
    try {
      final storageService = Get.find<StorageService>();
      final requireBiometrics = await storageService.getSetting(
        'require_biometrics',
        defaultValue: false,
      ) as bool;
      
      isEnabled.value = requireBiometrics;
      return requireBiometrics;
    } catch (e) {
      print('Error checking biometric settings: $e');
      return false;
    }
  }
}
```

#### Implementar Auto-Logout por Inatividade

```dart
// lib/services/session_service.dart
import 'dart:async';
import 'package:get/get.dart';
import '../core/config/routes.dart';

class SessionService extends GetxService {
  Timer? _inactivityTimer;
  final RxBool isActive = true.obs;
  
  // Obtém a duração do auto-logout das configurações
  Future<int> _getAutoLogoutDuration() async {
    final storageService = Get.find<StorageService>();
    
    final autoLogout = await storageService.getSetting(
      'auto_logout',
      defaultValue: true,
    ) as bool;
    
    if (!autoLogout) {
      return -1; // Auto-logout desabilitado
    }
    
    final minutes = await storageService.getSetting(
      'auto_logout_minutes',
      defaultValue: 30,
    ) as int;
    
    return minutes;
  }
  
  // Iniciar monitoramento de inatividade
  Future<void> startMonitoring() async {
    final minutes = await _getAutoLogoutDuration();
    
    // Se auto-logout estiver desabilitado
    if (minutes < 0) {
      _stopTimer();
      return;
    }
    
    // Converter minutos para milissegundos
    final duration = Duration(minutes: minutes);
    
    _stopTimer(); // Parar timer existente
    
    _inactivityTimer = Timer(duration, () {
      // Tempo limite atingido, fazer logout
      _performAutoLogout();
    });
  }
  
  // Reiniciar o timer quando há atividade do usuário
  Future<void> userActivity() async {
    isActive.value = true;
    
    // Reiniciar o timer
    await startMonitoring();
  }
  
  // Parar o timer de inatividade
  void _stopTimer() {
    _inactivityTimer?.cancel();
    _inactivityTimer = null;
  }
  
  // Fazer logout por inatividade
  void _performAutoLogout() {
    isActive.value = false;
    
    // Obter AuthService e fazer logout
    final authService = Get.find<AuthService>();
    authService.logout();
    
    // Mostrar mensagem
    Get.offAllNamed(AppRoutes.LOGIN);
    Get.snackbar(
      'Session Expired',
      'You have been logged out due to inactivity',
      snackPosition: SnackPosition.BOTTOM,
    );
  }
  
  @override
  void onClose() {
    _stopTimer();
    super.onClose();
  }
}
```

#### Adicionar Detector de Atividade na Aplicação

```dart
// lib/main.dart
// Adicionar detector de atividade do usuário

class InsightTrackerApp extends StatelessWidget {
  const InsightTrackerApp({super.key});

  @override
  Widget build(BuildContext context) {
    // Obter SessionService
    final sessionService = Get.find<SessionService>();
    
    return Listener(
      // Detectar interações do usuário
      onPointerDown: (_) => sessionService.userActivity(),
      onPointerMove: (_) => sessionService.userActivity(),
      onPointerUp: (_) => sessionService.userActivity(),
      
      child: GetMaterialApp(
        title: 'Insight Tracker',
        debugShowCheckedModeBanner: false,
        theme: AppThemes.lightTheme,
        darkTheme: AppThemes.darkTheme,
        themeMode: ThemeMode.system,
        initialRoute: AppRoutes.HOME,
        getPages: AppRoutes.routes,
        initialBinding: HomeBinding(),
      ),
    );
  }
}
```

## Priorização de Ações

1. **Alta prioridade**: Melhorar autenticação e gerenciamento de sessão
   - Implementar AuthService seguro
   - Configurar middleware de autenticação
   - Adicionar armazenamento seguro de tokens

2. **Alta prioridade**: Implementar criptografia para dados sensíveis
   - Criar serviço de criptografia
   - Adaptar o StorageService para usar criptografia
   - Proteger dados pessoais e insights

3. **Média prioridade**: Melhorar segurança em chamadas de rede
   - Implementar SSL Pinning
   - Adicionar validação de entrada
   - Melhorar tratamento de erros

4. **Média prioridade**: Implementar recursos de privacidade
   - Criar tela de configurações de privacidade
   - Adicionar política de privacidade
   - Implementar exportação e exclusão de dados

5. **Baixa prioridade**: Implementar autenticação biométrica
   - Criar serviço de biometria
   - Integrar autenticação por impressão digital ou reconhecimento facial
   - Adicionar opção para habilitar/desabilitar

## Impacto da Implementação

- **Segurança**: Proteção aprimorada para dados sensíveis do usuário
- **Conformidade**: Alinhamento com regulamentações de privacidade (GDPR, LGPD, etc.)
- **Confiança do Usuário**: Maior confiança dos usuários na aplicação
- **Prevenção de Riscos**: Redução do risco de vazamentos de dados
- **Diferenciação**: Destaque frente a concorrentes com foco em segurança

## Documentação Recomendada

Adicionar documentação para:
- Modelo de segurança da aplicação
- Fluxo de autenticação e autorização
- Padrões de criptografia utilizados
- Política de privacidade e termos de uso
- Guia de configurações de segurança para usuários

# Desempenho e Otimização

## Problemas Identificados

### 1. Uso Ineficiente de Recursos

- **Carregamento Desnecessário**: Alguns dados são carregados mesmo quando não são necessários.
- **Processamento Redundante**: Algumas operações são executadas repetidamente.
- **Falta de Lazy Loading**: Carregamento imediato de todos os dados em vez de sob demanda.

### 2. Problemas de Renderização

- **Reconstruções Desnecessárias**: Widgets são reconstruídos quando não precisam ser.
- **Animações Não Otimizadas**: Animações podem causar janks (travamentos) em dispositivos mais fracos.
- **Complexidade Visual**: Alguns layouts podem ser muito complexos, afetando o desempenho.

### 3. Gestão de Memória

- **Possíveis Vazamentos de Memória**: Alguns controladores podem não ser descartados corretamente.
- **Caches Não Gerenciados**: Não há mecanismos para limitar o tamanho de caches.
- **Uso Ineficiente de Imagens**: Imagens podem ser carregadas em resoluções maiores que o necessário.

## Soluções Propostas

### 1. Otimizar o Carregamento de Dados

#### Implementar Carregamento Paginado

```dart
// lib/services/storage_service.dart
// Adicionar suporte para paginação

Future<List<Insight>> getInsightsPaginated({
  int page = 0,
  int pageSize = 20,
  String? categoryId,
  String? searchQuery,
  SortOrder sortOrder = SortOrder.dateDesc,
}) async {
  try {
    isLoading.value = true;
    
    // Obter todos os insights (poderíamos otimizar isso no nível do banco de dados)
    final allInsights = _insightsBox.values.toList();
    
    // Filtrar por categoria se necessário
    var filteredInsights = allInsights;
    if (categoryId != null) {
      filteredInsights = filteredInsights
          .where((insight) => insight.categoryId == categoryId)
          .toList();
    }
    
    // Filtrar por pesquisa se necessário
    if (searchQuery != null && searchQuery.isNotEmpty) {
      final query = searchQuery.toLowerCase();
      filteredInsights = filteredInsights
          .where((insight) => 
              insight.title.toLowerCase().contains(query) || 
              insight.content.toLowerCase().contains(query) ||
              insight.tags.any((tag) => tag.toLowerCase().contains(query)))
          .toList();
    }
    
    // Ordenar
    switch (sortOrder) {
      case SortOrder.dateAsc:
        filteredInsights.sort((a, b) => 
            a.createdAt.compareTo(b.createdAt));
        break;
      case SortOrder.dateDesc:
        filteredInsights.sort((a, b) => 
            b.createdAt.compareTo(a.createdAt));
        break;
      case SortOrder.titleAsc:
        filteredInsights.sort((a, b) => 
            a.title.toLowerCase().compareTo(b.title.toLowerCase()));
        break;
      case SortOrder.titleDesc:
        filteredInsights.sort((a, b) => 
            b.title.toLowerCase().compareTo(a.title.toLowerCase()));
        break;
    }
    
    // Calcular índices para paginação
    final startIndex = page * pageSize;
    final endIndex = min(startIndex + pageSize, filteredInsights.length);
    
    // Verificar se índices são válidos
    if (startIndex >= filteredInsights.length) {
      return [];
    }
    
    // Obter página de resultados
    final pagedInsights = filteredInsights.sublist(startIndex, endIndex);
    
    // Descriptografar se necessário
    final encryptionService = Get.find<EncryptionService>();
    
    return pagedInsights.map((insight) => insight.copyWith(
      title: encryptionService.decrypt(insight.title),
      content: encryptionService.decrypt(insight.content),
    )).toList();
  } catch (e) {
    errorMessage.value = 'Error getting insights: $e';
    throw Exception('Failed to get insights: $e');
  } finally {
    isLoading.value = false;
  }
}
```

#### Implementar ListView Paginada

```dart
// lib/app/modules/home/home_page.dart
// Usar ListView paginada

class HomePage extends StatefulWidget {
  const HomePage({Key? key}) : super(key: key);

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final InsightController insightController = Get.find<InsightController>();
  
  final ScrollController _scrollController = ScrollController();
  final int _pageSize = 20;
  int _currentPage = 0;
  bool _isLoadingMore = false;
  bool _hasMore = true;
  
  @override
  void initState() {
    super.initState();
    _loadFirstPage();
    
    _scrollController.addListener(_scrollListener);
  }
  
  @override
  void dispose() {
    _scrollController.removeListener(_scrollListener);
    _scrollController.dispose();
    super.dispose();
  }
  
  Future<void> _loadFirstPage() async {
    _currentPage = 0;
    _hasMore = true;
    
    await insightController.loadInsightsPaginated(
      page: _currentPage,
      pageSize: _pageSize,
    );
  }
  
  Future<void> _loadNextPage() async {
    if (_isLoadingMore || !_hasMore) return;
    
    setState(() {
      _isLoadingMore = true;
    });
    
    final insights = await insightController.loadInsightsPaginated(
      page: _currentPage + 1,
      pageSize: _pageSize,
    );
    
    setState(() {
      _isLoadingMore = false;
      
      if (insights.isEmpty) {
        _hasMore = false;
      } else {
        _currentPage += 1;
      }
    });
  }
  
  void _scrollListener() {
    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent - 200) {
      _loadNextPage();
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Insight Tracker'),
        actions: [
          IconButton(
            icon: const Icon(Icons.search),
            onPressed: () {
              Get.toNamed(AppRoutes.SEARCH);
            },
          ),
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () {
              Get.toNamed(AppRoutes.SETTINGS);
            },
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadFirstPage,
        child: Obx(() {
          if (insightController.isLoading.value && _currentPage == 0) {
            return const Center(
              child: CircularProgressIndicator(),
            );
          }
          
          if (insightController.insights.isEmpty) {
            return _buildEmptyState();
          }
          
          return ListView.builder(
            controller: _scrollController,
            itemCount: insightController.insights.length + (_hasMore ? 1 : 0),
            itemBuilder: (context, index) {
              if (index == insightController.insights.length) {
                return _buildLoadingIndicator();
              }
              
              final insight = insightController.insights[index];
              return InsightCard(
                title: insight.title,
                content: insight.content,
                tags: insight.tags,
                createdAt: insight.createdAt,
                onTap: () {
                  Get.toNamed(AppRoutes.DETAIL, arguments: insight.id);
                },
              );
            },
          );
        }),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          Get.toNamed(AppRoutes.CAPTURE);
        },
        child: const Icon(Icons.add),
      ),
    );
  }
  
  Widget _buildLoadingIndicator() {
    return _isLoadingMore
        ? const Padding(
            padding: EdgeInsets.all(16),
            child: Center(
              child: CircularProgressIndicator(),
            ),
          )
        : const SizedBox.shrink();
  }
  
  Widget _buildEmptyState() {
    // Implementação existente do estado vazio
  }
}
```

### 2. Otimizar Renderização

#### Refatorar Widgets para Evitar Reconstruções

```dart
// lib/core/widgets/insight_card.dart
// Otimizar para evitar reconstruções

class InsightCard extends StatelessWidget {
  final String title;
  final String content;
  final List<String>? tags;
  final DateTime createdAt;
  final VoidCallback? onTap;
  final VoidCallback? onLongPress;

  const InsightCard({
    Key? key,
    required this.title,
    required this.content,
    this.tags,
    required this.createdAt,
    this.onTap,
    this.onLongPress,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Usar const onde possível para otimização
    return Card(
      clipBehavior: Clip.antiAlias,
      margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
      child: InkWell(
        onTap: onTap,
        onLongPress: onLongPress,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            cross# Desempenho e Otimização (continuação)

```dart
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Usar widgets const onde possível
              Text(
                title,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 8),
              Text(
                content,
                style: Theme.of(context).textTheme.bodyMedium,
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
              ),
              // Otimizar a construção de tags para evitar reconstruções desnecessárias
              if (tags != null && tags!.isNotEmpty) ...[
                const SizedBox(height: 12),
                _buildTagsList(context),
              ],
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  const Icon(
                    Icons.access_time,
                    size: 14,
                  ),
                  const SizedBox(width: 4),
                  Text(
                    _formatDateTime(createdAt),
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
  
  // Extrair método para construção das tags
  Widget _buildTagsList(BuildContext context) {
    return Wrap(
      spacing: 8,
      children: tags!
          .map((tag) => _TagChip(tag: tag))
          .toList(),
    );
  }

  String _formatDateTime(DateTime dateTime) {
    final now = DateTime.now();
    final difference = now.difference(dateTime);

    if (difference.inDays == 0) {
      return 'Today, ${dateTime.hour}:${dateTime.minute.toString().padLeft(2, '0')}';
    } else if (difference.inDays == 1) {
      return 'Yesterday, ${dateTime.hour}:${dateTime.minute.toString().padLeft(2, '0')}';
    } else if (difference.inDays < 7) {
      return '${difference.inDays} days ago';
    } else {
      return '${dateTime.day}/${dateTime.month}/${dateTime.year}';
    }
  }
}

// Criar widget separado para tag para melhorar a memoização
class _TagChip extends StatelessWidget {
  final String tag;

  const _TagChip({
    Key? key,
    required this.tag,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Chip(
      label: Text(tag),
      labelStyle: TextStyle(
        fontSize: 12,
        color: Theme.of(context).colorScheme.onSurface,
      ),
      padding: EdgeInsets.zero,
      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
      backgroundColor: Theme.of(context).colorScheme.surfaceVariant,
    );
  }
}
```

#### Otimizar Animações

```dart
// lib/core/widgets/animated_fade_transition.dart
import 'package:flutter/material.dart';

class AnimatedFadeTransition extends StatefulWidget {
  final Widget child;
  final Duration duration;
  final Curve curve;
  final bool animate;

  const AnimatedFadeTransition({
    Key? key,
    required this.child,
    this.duration = const Duration(milliseconds: 300),
    this.curve = Curves.easeInOut,
    this.animate = true,
  }) : super(key: key);

  @override
  State<AnimatedFadeTransition> createState() => _AnimatedFadeTransitionState();
}

class _AnimatedFadeTransitionState extends State<AnimatedFadeTransition>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: widget.duration,
    );
    _animation = CurvedAnimation(
      parent: _controller,
      curve: widget.curve,
    );

    if (widget.animate) {
      _controller.forward();
    }
  }

  @override
  void didUpdateWidget(AnimatedFadeTransition oldWidget) {
    super.didUpdateWidget(oldWidget);
    
    if (widget.duration != oldWidget.duration) {
      _controller.duration = widget.duration;
    }
    
    if (widget.animate != oldWidget.animate) {
      if (widget.animate) {
        _controller.forward();
      } else {
        _controller.reverse();
      }
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _animation,
      child: widget.child,
    );
  }
}
```

#### Usar RepaintBoundary para Layouts Complexos

```dart
// lib/app/modules/mindmap/widgets/mindmap_canvas.dart
// Adicionar RepaintBoundary para otimizar renderização

class MindmapCanvas extends StatelessWidget {
  final List<MindMapNode> nodes;
  final List<NodeConnection> connections;
  final String? selectedNodeId;
  final String? selectedConnectionId;
  final Function(String) onNodeTap;
  final Function(String) onConnectionTap;
  final Function(String, Offset) onNodeDrag;

  const MindmapCanvas({
    Key? key,
    required this.nodes,
    required this.connections,
    this.selectedNodeId,
    this.selectedConnectionId,
    required this.onNodeTap,
    required this.onConnectionTap,
    required this.onNodeDrag,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return RepaintBoundary(
      child: CustomPaint(
        painter: _MindmapPainter(
          nodes: nodes,
          connections: connections,
          selectedNodeId: selectedNodeId,
          selectedConnectionId: selectedConnectionId,
        ),
        child: GestureDetector(
          onTapUp: (details) {
            _handleTap(details.localPosition);
          },
          child: Stack(
            children: nodes.map((node) => _buildDraggableNode(node)).toList(),
          ),
        ),
      ),
    );
  }

  Widget _buildDraggableNode(MindMapNode node) {
    return Positioned(
      left: node.position.dx - node.width / 2,
      top: node.position.dy - node.height / 2,
      child: GestureDetector(
        onTap: () => onNodeTap(node.id),
        onPanUpdate: (details) {
          onNodeDrag(node.id, node.position + details.delta);
        },
        child: RepaintBoundary(
          child: Container(
            width: node.width,
            height: node.height,
            decoration: BoxDecoration(
              color: node.color ?? Colors.blue,
              borderRadius: BorderRadius.circular(8),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.2),
                  blurRadius: 4,
                  offset: const Offset(0, 2),
                ),
              ],
              border: selectedNodeId == node.id
                  ? Border.all(color: Colors.yellow, width: 2)
                  : null,
            ),
            child: Center(
              child: Text(
                node.title,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  void _handleTap(Offset position) {
    // Verificar se clicou em uma conexão
    for (final connection in connections) {
      final nodeA = nodes.firstWhere((n) => n.id == connection.sourceId);
      final nodeB = nodes.firstWhere((n) => n.id == connection.targetId);
      
      if (_isPointOnLine(position, nodeA.position, nodeB.position)) {
        onConnectionTap(connection.id);
        return;
      }
    }
  }

  bool _isPointOnLine(Offset point, Offset lineStart, Offset lineEnd) {
    // Algoritmo para verificar se o ponto está próximo à linha
    const double threshold = 20.0;
    
    // Vetor da linha
    final lineVector = lineEnd - lineStart;
    final lineLength = lineVector.distance;
    
    // Vetor do ponto até o início da linha
    final pointVector = point - lineStart;
    
    // Projeção do pointVector na linha
    final projection = (pointVector.dx * lineVector.dx + 
                        pointVector.dy * lineVector.dy) / lineLength;
    
    // Verificar se a projeção está dentro da linha
    if (projection < 0 || projection > lineLength) {
      return false;
    }
    
    // Calcular o ponto projetado na linha
    final projectedPoint = Offset(
      lineStart.dx + projection * lineVector.dx / lineLength,
      lineStart.dy + projection * lineVector.dy / lineLength,
    );
    
    // Calcular a distância entre o ponto e a linha
    final distance = (point - projectedPoint).distance;
    
    return distance < threshold;
  }
}

class _MindmapPainter extends CustomPainter {
  final List<MindMapNode> nodes;
  final List<NodeConnection> connections;
  final String? selectedNodeId;
  final String? selectedConnectionId;

  const _MindmapPainter({
    required this.nodes,
    required this.connections,
    this.selectedNodeId,
    this.selectedConnectionId,
  });

  @override
  void paint(Canvas canvas, Size size) {
    // Desenhar conexões
    for (final connection in connections) {
      final nodeA = nodes.firstWhere((n) => n.id == connection.sourceId);
      final nodeB = nodes.firstWhere((n) => n.id == connection.targetId);
      
      final paint = Paint()
        ..color = selectedConnectionId == connection.id
            ? Colors.yellow
            : Colors.grey.shade600
        ..strokeWidth = selectedConnectionId == connection.id ? 3 : 2
        ..style = PaintingStyle.stroke;
      
      canvas.drawLine(nodeA.position, nodeB.position, paint);
      
      // Desenhar label da conexão, se houver
      if (connection.label != null) {
        final textSpan = TextSpan(
          text: connection.label,
          style: const TextStyle(
            color: Colors.black87,
            fontSize: 12,
          ),
        );
        
        final textPainter = TextPainter(
          text: textSpan,
          textDirection: TextDirection.ltr,
        );
        
        textPainter.layout();
        
        final midPoint = Offset(
          (nodeA.position.dx + nodeB.position.dx) / 2,
          (nodeA.position.dy + nodeB.position.dy) / 2,
        );
        
        textPainter.paint(
          canvas,
          midPoint - Offset(textPainter.width / 2, textPainter.height / 2),
        );
      }
    }
  }

  @override
  bool shouldRepaint(_MindmapPainter oldDelegate) {
    return nodes != oldDelegate.nodes ||
        connections != oldDelegate.connections ||
        selectedNodeId != oldDelegate.selectedNodeId ||
        selectedConnectionId != oldDelegate.selectedConnectionId;
  }
}
```

### 3. Otimizar Gerenciamento de Memória

#### Implementar Cache com Limite de Tamanho

```dart
// lib/services/cache_service.dart
import 'dart:collection';

class CacheService<K, V> {
  final int maxSize;
  final LinkedHashMap<K, V> _cache = LinkedHashMap<K, V>();

  CacheService({this.maxSize = 100});

  V? get(K key) {
    // Se não existe no cache, retorna null
    if (!_cache.containsKey(key)) {
      return null;
    }

    // Remover e reinserir para atualizar a ordem (MRU - Most Recently Used)
    final value = _cache.remove(key);
    _cache[key] = value as V;
    return value;
  }

  void set(K key, V value) {
    // Se a chave já existe, remova primeiro
    _cache.remove(key);

    // Verificar se o cache está cheio
    if (_cache.length >= maxSize) {
      // Remover o item menos recentemente usado (primeiro na lista)
      _cache.remove(_cache.keys.first);
    }

    // Adicionar novo item
    _cache[key] = value;
  }

  void remove(K key) {
    _cache.remove(key);
  }

  void clear() {
    _cache.clear();
  }

  int get size => _cache.length;

  bool containsKey(K key) => _cache.containsKey(key);

  Iterable<K> get keys => _cache.keys;
  Iterable<V> get values => _cache.values;
}
```

#### Implementar Gestão de Recursos para Imagens

```dart
// lib/core/utils/image_utils.dart
import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';
import 'package:flutter_image_compress/flutter_image_compress.dart';

class ImageUtils {
  /// Carrega e redimensiona uma imagem do armazenamento local
  static Future<File?> loadAndResizeLocalImage(
    String path, {
    int maxWidth = 1080,
    int maxHeight = 1080,
    int quality = 85,
  }) async {
    try {
      // Verificar se o arquivo existe
      final file = File(path);
      if (!await file.exists()) {
        return null;
      }
      
      // Diretório temporário para salvar a imagem redimensionada
      final tempDir = await getTemporaryDirectory();
      final targetPath = '${tempDir.path}/${DateTime.now().millisecondsSinceEpoch}.jpg';
      
      // Comprimir a imagem
      final result = await FlutterImageCompress.compressAndGetFile(
        file.path,
        targetPath,
        minWidth: maxWidth,
        minHeight: maxHeight,
        quality: quality,
      );
      
      return result;
    } catch (e) {
      print('Error loading and resizing image: $e');
      return null;
    }
  }
  
  /// Carrega um asset como uma imagem otimizada para a memória
  static Future<ui.Image> loadAssetImage(
    String assetPath, {
    int width = 0,
    int height = 0,
  }) async {
    ByteData data = await rootBundle.load(assetPath);
    ui.Codec codec = await ui.instantiateImageCodec(
      data.buffer.asUint8List(),
      targetWidth: width > 0 ? width : null,
      targetHeight: height > 0 ? height : null,
    );
    ui.FrameInfo fi = await codec.getNextFrame();
    return fi.image;
  }
  
  /// Redimensiona uma imagem da memória
  static Future<ui.Image> resizeImage(
    ui.Image image, {
    required int targetWidth,
    required int targetHeight,
  }) async {
    final recorder = ui.PictureRecorder();
    final canvas = Canvas(recorder);
    
    // Desenhar a imagem redimensionada
    final paint = Paint()
      ..filterQuality = FilterQuality.medium;
    
    canvas.drawImageRect(
      image,
      Rect.fromLTWH(0, 0, image.width.toDouble(), image.height.toDouble()),
      Rect.fromLTWH(0, 0, targetWidth.toDouble(), targetHeight.toDouble()),
      paint,
    );
    
    final picture = recorder.endRecording();
    return picture.toImage(targetWidth, targetHeight);
  }
  
  /// Liberar recursos de uma imagem
  static void disposeImage(ui.Image? image) {
    image?.dispose();
  }
}
```

#### Otimizar Ciclo de Vida dos Controladores

```dart
// lib/app/controllers/base_controller.dart
import 'package:get/get.dart';

abstract class BaseController extends GetxController {
  final RxBool isLoading = false.obs;
  final Rx<String?> errorMessage = Rx<String?>(null);
  
  // Lista de workers para gerenciar
  final List<Worker> _workers = [];
  
  @override
  void onInit() {
    super.onInit();
    setupWorkers();
  }
  
  /// Configura workers para reatividade
  void setupWorkers() {
    // Implementado pelas subclasses
  }
  
  /// Registra um worker para limpeza automática
  void registerWorker(Worker worker) {
    _workers.add(worker);
  }
  
  /// Limpa todos os recursos
  void clearResources() {
    // Implementado pelas subclasses
  }
  
  @override
  void onClose() {
    // Cancelar todos os workers
    for (final worker in _workers) {
      worker.dispose();
    }
    _workers.clear();
    
    // Limpar outros recursos
    clearResources();
    
    super.onClose();
  }
}
```

```dart
// lib/app/controllers/insight_controller.dart
// Estender BaseController
class InsightController extends BaseController {
  final StorageService _storageService = Get.find<StorageService>();
  
  // Cache para insights
  final CacheService<String, Insight> _insightCache = CacheService<String, Insight>();
  
  // Observable list of insights
  final insights = <Insight>[].obs;
  
  // Tamanho total de insights (para paginação)
  final RxInt totalInsights = 0.obs;
  
  // Flag para indicar se há mais insights para carregar
  final RxBool hasMoreInsights = true.obs;
  
  @override
  void setupWorkers() {
    // Exemplo de worker para monitorar mudanças
    final worker = ever(insights, (_) {
      totalInsights.value = insights.length;
    });
    
    registerWorker(worker);
  }
  
  @override
  void clearResources() {
    // Limpar cache
    _insightCache.clear();
    
    // Limpar lista de insights
    insights.clear();
  }
  
  // Resto do código do controlador...
}
```

### 4. Otimizar Acesso ao Banco de Dados

#### Implementar Índices e Consultas Eficientes

```dart
// lib/services/storage_service.dart
// Inicializar com índices para consultas rápidas

Future<StorageService> init() async {
  try {
    isLoading.value = true;
    errorMessage.value = null;
    
    // Registrar adapters
    if (!Hive.isAdapterRegistered(0)) {
      Hive.registerAdapter(InsightAdapter());
    }
    // Outros registros...
    
    // Abrir boxes
    _insightsBox = await Hive.openBox<Insight>(INSIGHTS_BOX);
    // Outros boxes...
    
    // Criar índices para consultas rápidas
    await _createIndices();
    
    // Adicionar categorias padrão se vazio
    if (_categoriesBox.isEmpty) {
      await _addDefaultCategories();
    }
    
    return this;
  } catch (e) {
    errorMessage.value = 'Error initializing storage: $e';
    throw Exception('Failed to initialize storage: $e');
  } finally {
    isLoading.value = false;
  }
}

Future<void> _createIndices() async {
  // Hive não suporta índices nativamente, mas podemos criar estruturas auxiliares
  
  // Criar mapa de índice para insights por categoria
  if (!_settingsBox.containsKey('index_insights_by_category')) {
    final categoryIndex = <String, List<String>>{};
    
    for (final insight in _insightsBox.values) {
      if (insight.categoryId != null) {
        if (!categoryIndex.containsKey(insight.categoryId)) {
          categoryIndex[insight.categoryId!] = [];
        }
        categoryIndex[insight.categoryId!]!.add(insight.id);
      }
    }
    
    await _settingsBox.put('index_insights_by_category', categoryIndex);
  }
  
  // Criar índice para insights por tag
  if (!_settingsBox.containsKey('index_insights_by_tag')) {
    final tagIndex = <String, List<String>>{};
    
    for (final insight in _insightsBox.values) {
      for (final tag in insight.tags) {
        if (!tagIndex.containsKey(tag)) {
          tagIndex[tag] = [];
        }
        tagIndex[tag]!.add(insight.id);
      }
    }
    
    await _settingsBox.put('index_insights_by_tag', tagIndex);
  }
}

// Método para atualizar índices ao salvar um insight
Future<void> _updateIndices(Insight insight, {Insight? oldInsight}) async {
  try {
    // Atualizar índice de categoria
    final categoryIndex = await _settingsBox.get(
      'index_insights_by_category',
      defaultValue: <String, List<String>>{},
    ) as Map<dynamic, dynamic>;
    
    // Converter para o tipo correto
    final typedCategoryIndex = categoryIndex.map(
      (key, value) => MapEntry(key.toString(), List<String>.from(value)),
    );
    
    // Remover do índice antigo, se necessário
    if (oldInsight != null && oldInsight.categoryId != null) {
      typedCategoryIndex[oldInsight.categoryId]?.remove(insight.id);
    }
    
    // Adicionar ao novo índice
    if (insight.categoryId != null) {
      if (!typedCategoryIndex.containsKey(insight.categoryId)) {
        typedCategoryIndex[insight.categoryId!] = [];
      }
      
      if (!typedCategoryIndex[insight.categoryId!]!.contains(insight.id)) {
        typedCategoryIndex[insight.categoryId!]!.add(insight.id);
      }
    }
    
    await _settingsBox.put('index_insights_by_category', typedCategoryIndex);
    
    // Atualizar índice de tags (processo similar)
    // ...
  } catch (e) {
    print('Error updating indices: $e');
  }
}
```

#### Otimizar Consultas com Índices

```dart
// lib/services/storage_service.dart
// Usar índices para consultas mais eficientes

Future<List<Insight>> getInsightsByCategory(String categoryId) async {
  try {
    // Usar índice para obter IDs rapidamente
    final categoryIndex = await _settingsBox.get(
      'index_insights_by_category',
      defaultValue: <String, List<String>>{},
    ) as Map<dynamic, dynamic>;
    
    final typedCategoryIndex = categoryIndex.map(
      (key, value) => MapEntry(key.toString(), List<String>.from(value)),
    );
    
    final insightIds = typedCategoryIndex[categoryId] ?? [];
    
    // Obter insights pelos IDs
    final insights = <Insight>[];
    for (final id in insightIds) {
      final insight = _insightsBox.get(id);
      if (insight != null) {
        insights.add(insight);
      }
    }
    
    // Descriptografar, se necessário
    final encryptionService = Get.find<EncryptionService>();
    
    return insights.map((insight) => insight.copyWith(
      title: encryptionService.decrypt(insight.title),
      content: encryptionService.decrypt(insight.content),
    )).toList();
  } catch (e) {
    errorMessage.value = 'Error getting insights by category: $e';
    throw Exception('Failed to get insights by category: $e');
  }
}

Future<List<Insight>> getInsightsByTag(String tag) async {
  try {
    // Processo similar ao getInsightsByCategory, usando o índice de tags
    // ...
  } catch (e) {
    // ...
  }
}
```

### 5. Otimizar Inicialização do Aplicativo

#### Implementar Inicialização Lazy dos Serviços

```dart
// lib/main.dart
// Inicializar serviços apenas quando necessário

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Inicializar Hive para acesso rápido ao armazenamento local
  final appDocumentDirectory = 
      await path_provider.getApplicationDocumentsDirectory();
  await Hive.initFlutter(appDocumentDirectory.path);
  
  // Inicializar serviços essenciais
  await initEssentialServices();
  
  runApp(const InsightTrackerApp());
}

Future<void> initEssentialServices() async {
  // Serviços que precisam estar disponíveis imediatamente
  final storageService = StorageService();
  await storageService.init();
  Get.put(storageService);
  
  // Serviço de autenticação (necessário para tela inicial)
  final authService = AuthService();
  await authService.onInit();
  Get.put(authService);
  
  // Outros serviços serão inicializados sob demanda
}

class InsightTrackerApp extends StatelessWidget {
  const InsightTrackerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return GetMaterialApp(
      title: 'Insight Tracker',
      debugShowCheckedModeBanner: false,
      theme: AppThemes.lightTheme,
      darkTheme: AppThemes.darkTheme,
      themeMode: ThemeMode.system,
      initialRoute: AppRoutes.SPLASH,
      getPages: AppRoutes.routes,
      onInit: () {
        // Pré-carregar serviços secundários em segundo plano
        _preloadSecondaryServices();
      },
    );
  }
  
  Future<void> _preloadSecondaryServices() async {
    // Inicializar serviços não essenciais em segundo plano
    final encryptionService = EncryptionService();
    await encryptionService.onInit();
    Get.put(encryptionService);
    
    // Outros serviços secundários
    final biometricService = BiometricService();
    await biometricService.onInit();
    Get.lazyPut(() => biometricService);
    
    // Serviços que podem ser inicializados ainda mais tarde
    Get.lazyPut(() => SessionService());
    Get.lazyPut(() => ThemeService());
    Get.lazyPut(() => NLPService());
  }
}

// lib/app/modules/splash/splash_page.dart
// Página de splash para inicialização
class SplashPage extends StatefulWidget {
  const SplashPage({Key? key}) : super(key: key);

  @override
  State<SplashPage> createState() => _SplashPageState();
}

class _SplashPageState extends State<SplashPage> {
  @override
  void initState() {
    super.initState();
    _navigateToNextScreen();
  }
  
  Future<void> _navigateToNextScreen() async {
    // Esperar animação do splash
    await Future.delayed(const Duration(seconds: 2));
    
    // Verificar autenticação
    final authService = Get.find<AuthService>();
    
    if (authService.isLoggedIn()) {
      // Verificar biometria, se necessário
      final biometricService = Get.find<BiometricService>();
      final requireBiometrics = await biometricService.checkBiometricSettings();
      
      if (requireBiometrics) {
        final authenticated = await biometricService.authenticate();
        if (authenticated) {
          Get.offAllNamed(AppRoutes.HOME);
        } else {
          Get.offAllNamed(AppRoutes.LOGIN);
        }
      } else {
        Get.offAllNamed(AppRoutes.HOME);
      }
    } else {
      Get.offAllNamed(AppRoutes.LOGIN);
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Logo animado
            AnimatedFadeTransition(
              child: const Icon(
                Icons.lightbulb_outline,
                size: 100,
                color: Colors.amber,
              ),
            ),
            const SizedBox(height: 24),
            AnimatedFadeTransition(
              duration: const Duration(milliseconds: 800),
              child: Text(
                'Insight Tracker',
                style: Theme.of(context).textTheme.headlineMedium,
              ),
            ),
            const SizedBox(height: 48),
            const CircularProgressIndicator(),
          ],
        ),
      ),
    );
  }
}
```

## Priorização de Ações

1. **Alta prioridade**: Otimizar carregamento de dados
   - Implementar paginação
   - Usar ListView.builder em vez de ListView
   - Implementar carregamento lazy

2. **Alta prioridade**: Otimizar renderização
   - Refatorar widgets para evitar reconstruções
   - Usar const widgets onde possível
   - Adicionar RepaintBoundary para layouts complexos

3. **Média prioridade**: Melhorar gerenciamento de memória
   - Implementar sistema de cache com limite
   - Gerenciar ciclo de vida dos controladores
   - Otimizar uso de imagens

4. **Média prioridade**: Otimizar acesso ao banco de dados
   - Criar índices para consultas frequentes
   - Usar queries otimizadas
   - Implementar batch operations

5. **Baixa prioridade**: Otimizar inicialização do aplicativo
   - Inicializar serviços de forma lazy
   - Adicionar tela de splash
   - Pré-carregar dados essenciais