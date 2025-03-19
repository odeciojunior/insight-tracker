# Serviços Não Implementados ou Parcialmente Implementados

## Problemas Identificados

### 1. Serviços Referenciados Mas Não Implementados

Vários serviços são referenciados ao longo do código, mas seus arquivos estão vazios ou possuem implementações incompletas:

- **`lib/services/api_service.dart`**: Arquivo vazio, mas é importado em diversos controllers
- **`lib/services/auth_service.dart`**: Vazio, mas referenciado pelo AuthController
- **`lib/services/speech_service.dart`**: Vazio, mas importado no app

Exemplo típico de importação de serviço inexistente:
```dart
import '../../services/api_service.dart';
```

### 2. StorageService com Implementação Parcial

O serviço de armazenamento (`lib/services/storage_service.dart`) tem uma implementação parcial, mas apresenta problemas:

- Alguns métodos retornam diretamente valores síncronos, enquanto outros são assíncronos:
  ```dart
  // Método síncrono
  List<Insight> getAllInsights() {
    return _insightsBox.values.toList();
  }
  
  // Método assíncrono
  Future<void> saveInsight(Insight insight) async {
    await _insightsBox.put(insight.id, insight);
  }
  ```

- Falta de tratamento de erros consistente:
  ```dart
  Future<void> init() async {
    try {
      // Registro de adapters...
    } catch (e) {
      print('Error initializing storage: $e');
      rethrow; // Exceção propagada sem tratamento
    }
  }
  ```

- Inconsistência entre a expectativa dos controllers e a implementação real:
  ```dart
  // No StorageService
  List<Category> getAllCategories() {
    return _categoriesBox.values.toList();
  }
  
  // No CategoryController
  Future<void> loadCategories() async {
    try {
      isLoading.value = true;
      final allCategories = _storageService.getAllCategories();
      categories.assignAll(allCategories);
    } catch (e) {
      // ...
    }
  }
  ```

### 3. Falta de Mock Services para Testes

Não há implementações de serviços de mock para facilitar os testes. Isso dificulta:
- Testes unitários de controllers
- Testes de widgets que dependem de serviços
- Execução de testes sem dependências externas

### 4. Ausência de Gerenciamento de Estado dos Serviços

Os serviços não fornecem mecanismos para notificar sobre seu estado atual:
- Não há indicadores de carregamento
- Não há gerenciamento de erros centralizado
- Não há mecanismo para refresh ou invalidação de cache

## Soluções Propostas

### 1. Implementar ApiService

Este serviço deve encapsular todas as chamadas à API REST:

```dart
// lib/services/api_service.dart
import 'package:dio/dio.dart';
import 'package:dio_cache_interceptor/dio_cache_interceptor.dart';
import 'package:get/get.dart';
import '../app/data/models/insight.dart';
import '../app/data/models/relationship.dart';
import '../app/data/models/category.dart';
import '../app/data/models/user.dart';

class ApiService extends GetxService {
  late final Dio _dio;
  final RxBool isLoading = false.obs;
  final Rx<String?> errorMessage = Rx<String?>(null);
  
  // Base URL da API
  final String baseUrl = 'https://api.insighttracker.example/v1';
  
  @override
  void onInit() {
    super.onInit();
    _initDio();
  }
  
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
    
    // Configuração do cache
    final cacheOptions = CacheOptions(
      store: MemCacheStore(),
      policy: CachePolicy.request,
      maxStale: Duration(days: 1),
      hitCacheOnErrorExcept: [401, 403],
    );
    
    _dio = Dio(options);
    
    // Adicionar interceptors
    _dio.interceptors.add(DioCacheInterceptor(options: cacheOptions));
    _dio.interceptors.add(LogInterceptor(
      request: true,
      requestBody: true,
      responseBody: true,
      error: true,
    ));
    
    // Interceptor para gerenciamento de estado
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
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
        errorMessage.value = _handleError(e);
        return handler.next(e);
      },
    ));
  }
  
  String _handleError(DioException error) {
    String message = 'Something went wrong';
    
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        message = 'Connection timeout';
        break;
      case DioExceptionType.badResponse:
        final statusCode = error.response?.statusCode;
        if (statusCode == 401) {
          message = 'Unauthorized';
          // Logout user ou redirecionar para login
          Get.offAllNamed('/login');
        } else if (statusCode == 404) {
          message = 'Resource not found';
        } else {
          message = 'Server error: ${statusCode}';
        }
        break;
      case DioExceptionType.cancel:
        message = 'Request cancelled';
        break;
      default:
        message = 'Network error';
        break;
    }
    
    return message;
  }
  
  // INSIGHT ENDPOINTS
  
  Future<List<Insight>> getInsights() async {
    try {
      final response = await _dio.get('/insights');
      final data = response.data as List;
      return data.map((json) => Insight.fromJson(json)).toList();
    } catch (e) {
      rethrow;
    }
  }
  
  Future<Insight> getInsight(String id) async {
    try {
      final response = await _dio.get('/insights/$id');
      return Insight.fromJson(response.data);
    } catch (e) {
      rethrow;
    }
  }
  
  Future<Insight> createInsight(Insight insight) async {
    try {
      final response = await _dio.post('/insights', data: insight.toJson());
      return Insight.fromJson(response.data);
    } catch (e) {
      rethrow;
    }
  }
  
  Future<Insight> updateInsight(String id, Insight insight) async {
    try {
      final response = await _dio.put('/insights/$id', data: insight.toJson());
      return Insight.fromJson(response.data);
    } catch (e) {
      rethrow;
    }
  }
  
  Future<void> deleteInsight(String id) async {
    try {
      await _dio.delete('/insights/$id');
    } catch (e) {
      rethrow;
    }
  }
  
  // CATEGORY ENDPOINTS
  
  Future<List<Category>> getCategories() async {
    try {
      final response = await _dio.get('/categories');
      final data = response.data as List;
      return data.map((json) => Category.fromJson(json)).toList();
    } catch (e) {
      rethrow;
    }
  }
  
  // Implementar demais métodos para categorias...
  
  // RELATIONSHIP ENDPOINTS
  
  Future<List<Relationship>> getRelationships() async {
    try {
      final response = await _dio.get('/relationships');
      final data = response.data as List;
      return data.map((json) => Relationship.fromJson(json)).toList();
    } catch (e) {
      rethrow;
    }
  }
  
  // Implementar demais métodos para relacionamentos...
}
```

### 2. Implementar AuthService

Este serviço deve gerenciar a autenticação, integrando-se com Firebase ou outros provedores:

```dart
// lib/services/auth_service.dart
import 'package:firebase_auth/firebase_auth.dart' as firebase;
import 'package:get/get.dart';
import '../app/data/models/user.dart';
import '../core/config/routes.dart';

class AuthService extends GetxService {
  final firebase.FirebaseAuth _auth = firebase.FirebaseAuth.instance;
  final Rx<User?> currentUser = Rx<User?>(null);
  final RxBool isLoading = false.obs;
  final Rx<String?> errorMessage = Rx<String?>(null);
  
  @override
  void onInit() {
    super.onInit();
    _setupAuthStateListener();
  }
  
  void _setupAuthStateListener() {
    _auth.authStateChanges().listen((firebase.User? firebaseUser) {
      if (firebaseUser != null) {
        // Converter FirebaseUser para o modelo User do app
        currentUser.value = User(
          id: firebaseUser.uid,
          email: firebaseUser.email!,
          displayName: firebaseUser.displayName,
          photoUrl: firebaseUser.photoURL,
          createdAt: firebaseUser.metadata.creationTime!,
          lastLoginAt: firebaseUser.metadata.lastSignInTime,
        );
      } else {
        currentUser.value = null;
      }
    });
  }
  
  bool isLoggedIn() {
    return currentUser.value != null;
  }
  
  Future<void> login(String email, String password) async {
    try {
      isLoading.value = true;
      errorMessage.value = null;
      
      await _auth.signInWithEmailAndPassword(
        email: email.trim(),
        password: password.trim(),
      );
      
      // Navegação feita através do listener de authStateChanges
    } catch (e) {
      errorMessage.value = _handleAuthError(e);
      rethrow;
    } finally {
      isLoading.value = false;
    }
  }
  
  Future<void> register(String email, String password) async {
    try {
      isLoading.value = true;
      errorMessage.value = null;
      
      await _auth.createUserWithEmailAndPassword(
        email: email.trim(),
        password: password.trim(),
      );
      
      // Navegação feita através do listener de authStateChanges
    } catch (e) {
      errorMessage.value = _handleAuthError(e);
      rethrow;
    } finally {
      isLoading.value = false;
    }
  }
  
  Future<void> logout() async {
    try {
      isLoading.value = true;
      errorMessage.value = null;
      
      await _auth.signOut();
      
      // Navegação feita através do listener de authStateChanges
    } catch (e) {
      errorMessage.value = _handleAuthError(e);
      rethrow;
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
      rethrow;
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
        default:
          return 'Authentication error: ${e.message}';
      }
    }
    return 'An unexpected error occurred';
  }
}
```

### 3. Padronizar o StorageService

Refatorar o serviço de armazenamento para torná-lo consistente:

```dart
// lib/services/storage_service.dart
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:hive/hive.dart';
import 'package:hive_flutter/hive_flutter.dart';

import '../app/data/models/category.dart';
import '../app/data/models/insight.dart';
import '../app/data/models/relationship.dart';

class StorageService extends GetxService {
  static const String INSIGHTS_BOX = 'insights';
  static const String RELATIONSHIPS_BOX = 'relationships';
  static const String CATEGORIES_BOX = 'categories';
  static const String SETTINGS_BOX = 'settings';

  late Box<Insight> _insightsBox;
  late Box<Relationship> _relationshipsBox;
  late Box<Category> _categoriesBox;
  late Box<dynamic> _settingsBox;
  
  final RxBool isLoading = false.obs;
  final Rx<String?> errorMessage = Rx<String?>(null);

  Future<StorageService> init() async {
    try {
      isLoading.value = true;
      errorMessage.value = null;
      
      // Registrar adapters
      if (!Hive.isAdapterRegistered(0)) {
        Hive.registerAdapter(InsightAdapter());
      }
      if (!Hive.isAdapterRegistered(1)) {
        Hive.registerAdapter(RelationshipTypeAdapter());
      }
      if (!Hive.isAdapterRegistered(2)) {
        Hive.registerAdapter(RelationshipAdapter());
      }
      if (!Hive.isAdapterRegistered(3)) {
        Hive.registerAdapter(CategoryAdapter());
      }
      if (!Hive.isAdapterRegistered(4)) {
        Hive.registerAdapter(ColorAdapter());
      }
      if (!Hive.isAdapterRegistered(5)) {
        Hive.registerAdapter(IconDataAdapter());
      }

      // Abrir boxes
      _insightsBox = await Hive.openBox<Insight>(INSIGHTS_BOX);
      _relationshipsBox = await Hive.openBox<Relationship>(RELATIONSHIPS_BOX);
      _categoriesBox = await Hive.openBox<Category>(CATEGORIES_BOX);
      _settingsBox = await Hive.openBox(SETTINGS_BOX);

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

  // INSIGHTS METHODS - Todos assíncronos para consistência

  Future<List<Insight>> getAllInsights() async {
    try {
      return _insightsBox.values.toList();
    } catch (e) {
      errorMessage.value = 'Error getting insights: $e';
      throw Exception('Failed to get insights: $e');
    }
  }

  Future<Insight?> getInsight(String id) async {
    try {
      return _insightsBox.get(id);
    } catch (e) {
      errorMessage.value = 'Error getting insight: $e';
      throw Exception('Failed to get insight: $e');
    }
  }

  Future<void> saveInsight(Insight insight) async {
    try {
      await _insightsBox.put(insight.id, insight);
    } catch (e) {
      errorMessage.value = 'Error saving insight: $e';
      throw Exception('Failed to save insight: $e');
    }
  }

  Future<void> deleteInsight(String id) async {
    try {
      await _insightsBox.delete(id);
      
      // Deletar relacionamentos
      final toDelete = _relationshipsBox.values
          .where((rel) => rel.sourceId == id || rel.targetId == id)
          .map((rel) => rel.id)
          .toList();
      
      for (final relId in toDelete) {
        await _relationshipsBox.delete(relId);
      }
    } catch (e) {
      errorMessage.value = 'Error deleting insight: $e';
      throw Exception('Failed to delete insight: $e');
    }
  }

  // CATEGORIES METHODS

  Future<List<Category>> getAllCategories() async {
    try {
      return _categoriesBox.values.toList();
    } catch (e) {
      errorMessage.value = 'Error getting categories: $e';
      throw Exception('Failed to get categories: $e');
    }
  }

  Future<Category?> getCategory(String id) async {
    try {
      return _categoriesBox.get(id);
    } catch (e) {
      errorMessage.value = 'Error getting category: $e';
      throw Exception('Failed to get category: $e');
    }
  }

  Future<void> saveCategory(Category category) async {
    try {
      await _categoriesBox.put(category.id, category);
    } catch (e) {
      errorMessage.value = 'Error saving category: $e';
      throw Exception('Failed to save category: $e');
    }
  }

  Future<void> deleteCategory(String id) async {
    try {
      // Atualizar insights com esta categoria
      final insightsToUpdate = _insightsBox.values
          .where((insight) => insight.categoryId == id)
          .toList();
      
      for (final insight in insightsToUpdate) {
        final updated = insight.copyWith(categoryId: null);
        await _insightsBox.put(insight.id, updated);
      }
      
      await _categoriesBox.delete(id);
    } catch (e) {
      errorMessage.value = 'Error deleting category: $e';
      throw Exception('Failed to delete category: $e');
    }
  }

  // RELATIONSHIPS METHODS

  Future<List<Relationship>> getAllRelationships() async {
    try {
      return _relationshipsBox.values.toList();
    } catch (e) {
      errorMessage.value = 'Error getting relationships: $e';
      throw Exception('Failed to get relationships: $e');
    }
  }

  Future<List<Relationship>> getInsightRelationships(String insightId) async {
    try {
      return _relationshipsBox.values
          .where((rel) => rel.sourceId == insightId || rel.targetId == insightId)
          .toList();
    } catch (e) {
      errorMessage.value = 'Error getting insight relationships: $e';
      throw Exception('Failed to get insight relationships: $e');
    }
  }

  Future<void> saveRelationship(Relationship relationship) async {
    try {
      await _relationshipsBox.put(relationship.id, relationship);
    } catch (e) {
      errorMessage.value = 'Error saving relationship: $e';
      throw Exception('Failed to save relationship: $e');
    }
  }

  Future<void> deleteRelationship(String id) async {
    try {
      await _relationshipsBox.delete(id);
    } catch (e) {
      errorMessage.value = 'Error deleting relationship: $e';
      throw Exception('Failed to delete relationship: $e');
    }
  }

  // SETTINGS METHODS

  Future<dynamic> getSetting(String key, {dynamic defaultValue}) async {
    try {
      return _settingsBox.get(key, defaultValue: defaultValue);
    } catch (e) {
      errorMessage.value = 'Error getting setting: $e';
      throw Exception('Failed to get setting: $e');
    }
  }

  Future<void> saveSetting(String key, dynamic value) async {
    try {
      await _settingsBox.put(key, value);
    } catch (e) {
      errorMessage.value = 'Error saving setting: $e';
      throw Exception('Failed to save setting: $e');
    }
  }

  // PRIVATE METHODS

  Future<void> _addDefaultCategories() async {
    final defaultCategories = [
      Category.create(
        name: 'Work',
        color: const Color(0xFF2196F3),
        icon: Icons.work,
      ),
      Category.create(
        name: 'Personal',
        color: const Color(0xFF4CAF50),
        icon: Icons.person,
      ),
      Category.create(
        name: 'Ideas',
        color: const Color(0xFFFFC107),
        icon: Icons.lightbulb,
      ),
      Category.create(
        name: 'Tasks',
        color: const Color(0xFFF44336),
        icon: Icons.task_alt,
      ),
    ];

    for (final category in defaultCategories) {
      await _categoriesBox.put(category.id, category);
    }
  }

  // UTILITY METHODS

  Future<void> clearAllData() async {
    try {
      await _insightsBox.clear();
      await _relationshipsBox.clear();
      await _categoriesBox.clear();
      await _settingsBox.clear();
      await _addDefaultCategories();
    } catch (e) {
      errorMessage.value = 'Error clearing data: $e';
      throw Exception('Failed to clear data: $e');
    }
  }
}
```

### 4. Implementar SpeechService

```dart
// lib/services/speech_service.dart
import 'package:flutter/foundation.dart';
import 'package:get/get.dart';
import 'package:speech_to_text/speech_recognition_error.dart';
import 'package:speech_to_text/speech_recognition_result.dart';
import 'package:speech_to_text/speech_to_text.dart';

class SpeechService extends GetxService {
  final SpeechToText _speechToText = SpeechToText();
  
  final RxBool isAvailable = false.obs;
  final RxBool isListening = false.obs;
  final RxString recognizedText = ''.obs;
  final RxDouble confidenceLevel = 0.0.obs;
  final Rx<String?> errorMessage = Rx<String?>(null);
  
  @override
  Future<void> onInit() async {
    super.onInit();
    await initialize();
  }
  
  Future<bool> initialize() async {
    try {
      errorMessage.value = null;
      
      final available = await _speechToText.initialize(
        onError: _onError,
        options: [SpeechToText.androidYesIsConfirmation],
      );
      
      isAvailable.value = available;
      return available;
    } catch (e) {
      errorMessage.value = 'Failed to initialize speech recognition: $e';
      isAvailable.value = false;
      return false;
    }
  }
  
  Future<void> startListening() async {
    if (!isAvailable.value) {
      await initialize();
      if (!isAvailable.value) {
        errorMessage.value = 'Speech recognition not available';
        return;
      }
    }
    
    try {
      errorMessage.value = null;
      recognizedText.value = '';
      
      await _speechToText.listen(
        onResult: _onResult,
        listenFor: const Duration(seconds: 30),
        pauseFor: const Duration(seconds: 3),
        partialResults: true,
        localeId: null,
        cancelOnError: true,
      );
      
      isListening.value = true;
    } catch (e) {
      errorMessage.value = 'Failed to start listening: $e';
    }
  }
  
  Future<void> stopListening() async {
    try {
      await _speechToText.stop();
      isListening.value = false;
    } catch (e) {
      errorMessage.value = 'Failed to stop listening: $e';
    }
  }
  
  void _onResult(SpeechRecognitionResult result) {
    recognizedText.value = result.recognizedWords;
    confidenceLevel.value = result.confidence;
    
    if (result.finalResult) {
      isListening.value = false;
    }
  }
  
  void _onError(SpeechRecognitionError error) {
    debugPrint('Speech recognition error: ${error.errorMsg}');
    errorMessage.value = 'Speech recognition error: ${error.errorMsg}';
    isListening.value = false;
  }
  
  void clearRecognizedText() {
    recognizedText.value = '';
  }
  
  List<String> get availableLocales {
    return _speechToText.locales().map((locale) => locale.localeId).toList();
  }
}
```

### 5. Criar Mock Services para Testes

```dart
// lib/services/mocks/mock_storage_service.dart
import 'package:get/get.dart';
import '../../app/data/models/category.dart';
import '../../app/data/models/insight.dart';
import '../../app/data/models/relationship.dart';
import '../storage_service.dart';

class MockStorageService extends GetxService {
  final Map<String, Insight> _insights = {};
  final Map<String, Category> _categories = {};
  final Map<String, Relationship> _relationships = {};
  final Map<String, dynamic> _settings = {};
  
  final RxBool isLoading = false.obs;
  final Rx<String?> errorMessage = Rx<String?>(null);
  
  MockStorageService() {
    _addDefaultCategories();
  }
  
  Future<MockStorageService> init() async {
    return this;
  }
  
  // INSIGHTS METHODS
  
  Future<List<Insight>> getAllInsights() async {
    return _insights.values.toList();
  }
  
  Future<Insight?> getInsight(String id) async {
    return _insights[id];
  }
  
  Future<void> saveInsight(Insight insight) async {
    _insights[insight.id] = insight;
  }
  
  Future<void> deleteInsight(String id) async {
    _insights.remove(id);
    
    // Remover relacionamentos
    _relationships.removeWhere(
      (k, rel) => rel.sourceId == id || rel.targetId == id
    );
  }
  
  // CATEGORIES METHODS
  
  Future<List<Category>> getAllCategories() async {
    return _categories.values.toList();
  }
  
  Future<Category?> getCategory(String id) async {
    return _categories[id];
  }
  
  Future<void> saveCategory(Category category) async {
    _categories[category.id] = category;
  }
  
  Future<void> deleteCategory(String id) async {
    _categories.remove(id);
    
    // Atualizar insights
    for (final insight in _insights.values) {
      if (insight.categoryId == id) {
        _insights[insight.id] = insight.copyWith(categoryId: null);
      }
    }
  }
  
  // Implementar outros métodos...
  
  void _addDefaultCategories() {
    // Adicionar categorias padrão para testes
    final defaultCategories = [
      Category.create(
        name: 'Test Category 1',
        color: const Color(0xFF2196F3),
        icon: Icons.work,
      ),
      Category.create(
        name: 'Test Category 2',
        color: const Color(0xFF4CAF50),
        icon: Icons.person,
      ),
    ];
    
    for (final category in defaultCategories) {
      _categories[category.id] = category;
    }
  }
}
```

## Priorização de Ações

1. **Alta prioridade**: Padronizar o StorageService existente
   - Tornar todos os métodos assíncronos
   - Adicionar tratamento de erros consistente
   - Implementar indicadores de estado (loading, error)

2. **Alta prioridade**: Implementar AuthService
   - Integrar com Firebase Auth
   - Adicionar gerenciamento de estado de autenticação
   - Fornecer métodos para login, registro, logout

3. **Média prioridade**: Implementar ApiService
   - Configurar Dio com interceptors
   - Implementar endpoints principais
   - Adicionar cache e tratamento de erros

4. **Média prioridade**: Implementar SpeechService
   - Adicionar funcionalidades de reconhecimento de voz
   - Integrar com o RecorderController existente

5. **Baixa prioridade**: Criar mock services para testes
   - Implementar versões de teste de todos os serviços
   - Configurar injeção de dependências para testes

## Impacto da Implementação

- **Arquitetura**: Melhor separação de responsabilidades
- **Manutenção**: Código mais organizado e previsível
- **Testabilidade**: Facilidade para testar componentes isoladamente
- **Experiência do usuário**: Melhor feedback sobre estados de carregamento e erros
- **Desempenho**: Melhoria no cache e otimização de chamadas de rede

## Documentação Recomendada

Adicionar documentação para:
- Estrutura de serviços e responsabilidades
- Padrões de tratamento de erros
- Integração com APIs externas
- Estratégia de persistência de dados
- Guia para testes com mock services