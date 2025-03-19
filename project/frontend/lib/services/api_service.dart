import 'package:dio/dio.dart';
import 'package:dio_cache_interceptor/dio_cache_interceptor.dart';
import 'package:get/get.dart';
import 'dart:convert';
import 'dart:async';

// Adicionando modelos para tipagem adequada
import '../models/insight_model.dart';
import '../models/relationship_model.dart';
import '../utils/connectivity_service.dart';

enum Environment {
  development,
  staging,
  production,
}

class ApiService {
  late final Dio _dio;
  late final String baseUrl;
  late final Environment currentEnvironment;

  // Cache options
  late final CacheOptions _cacheOptions;

  // Singleton pattern
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;

  ApiService._internal() {
    // Default to development environment
    _configureEnvironment(Environment.development);
    _configureCacheOptions();
    _configureDio();
  }

  void _configureEnvironment(Environment env) {
    currentEnvironment = env;
    
    switch (env) {
      case Environment.development:
        baseUrl = 'http://localhost:3000/api';
        break;
      case Environment.staging:
        baseUrl = 'https://staging-api.insighttracker.com/api';
        break;
      case Environment.production:
        baseUrl = 'https://api.insighttracker.com/api';
        break;
    }
  }

  void _configureCacheOptions() {
    _cacheOptions = CacheOptions(
      // A default store is required
      store: MemCacheStore(),
      // Default policy
      policy: CachePolicy.request,
      // Maximum age of a cached response
      maxStale: const Duration(minutes: 5),
      // Priority for cache options
      priority: CachePriority.normal,
      // Key builder to retrieve requests
      keyBuilder: CacheOptions.defaultCacheKeyBuilder,
      // Allow cache sharing between instances
      allowPostMethod: false,
    );
  }

  // Retry configuration
  static const int _maxRetries = 3;
  static const Duration _retryDelay = Duration(seconds: 2);

  void _configureDio() {
    _dio = Dio(
      BaseOptions(
        baseUrl: baseUrl,
        connectTimeout: const Duration(seconds: 5),
        receiveTimeout: const Duration(seconds: 3),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );
    
    // Add cache interceptor
    _dio.interceptors.add(DioCacheInterceptor(options: _cacheOptions));
    
    // Add logging interceptor
    _dio.interceptors.add(LogInterceptor(
      requestBody: true,
      responseBody: true,
      logPrint: (object) {
        if (currentEnvironment != Environment.production) {
          print(object);
        }
      },
    ));
    
    // Add enhanced error handling interceptor with retry
    _dio.interceptors.add(
      InterceptorsWrapper(
        onError: (DioException error, ErrorInterceptorHandler handler) async {
          // Try to get more information about the error
          final statusCode = error.response?.statusCode;
          final responseData = error.response?.data;
          final requestOptions = error.requestOptions;
          
          // Log the error details for debugging
          _logError('API Error', error);

          // Only retry idempotent requests (GET, HEAD, OPTIONS)
          final canRetry = _isRequestRetryable(requestOptions);
          final shouldRetry = canRetry && 
                              (error.type == DioExceptionType.connectionTimeout || 
                               error.type == DioExceptionType.sendTimeout ||
                               error.type == DioExceptionType.receiveTimeout ||
                               error.type == DioExceptionType.connectionError ||
                               (statusCode != null && statusCode >= 500));

          // Handle specific error scenarios
          if (statusCode == 401) {
            // Authentication error
            await _handleAuthError();
            handler.next(error);
          } else if (shouldRetry && !_hasReachedMaxRetries(requestOptions)) {
            // Network issues or server errors that can be retried
            await _retryRequest(error, handler);
          } else if (statusCode == 403) {
            // Permission issues
            _handleForbiddenError(error);
            handler.next(error);
          } else if (statusCode == 404) {
            // Resource not found
            _handleNotFoundError(error);
            handler.next(error);
          } else if (statusCode != null && statusCode >= 500) {
            // Server errors that can't be retried anymore
            _handleServerError(error);
            handler.next(error);
          } else if (error.type == DioExceptionType.connectionTimeout ||
                     error.type == DioExceptionType.receiveTimeout ||
                     error.type == DioExceptionType.connectionError) {
            // Connectivity issues
            await _handleConnectivityError(error);
            handler.next(error);
          } else {
            // Handle other errors
            _handleGenericError(error);
            handler.next(error);
          }
        },
        
        onRequest: (options, handler) {
          // Initialize retry count for new requests
          options.extra['retryCount'] = options.extra['retryCount'] ?? 0;
          
          // Add authorization token if available
          final authToken = _getAuthToken();
          if (authToken != null && authToken.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $authToken';
          }
          
          handler.next(options);
        },
        
        onResponse: (response, handler) {
          // Process successful responses if needed
          handler.next(response);
        },
      ),
    );
  }
  
  // Retry request helper method
  Future<void> _retryRequest(DioException err, ErrorInterceptorHandler handler) async {
    final options = err.requestOptions;
    final retryCount = options.extra['retryCount'] as int;
    
    if (retryCount < _maxRetries) {
      _logInfo('Retrying request (${retryCount + 1}/$_maxRetries): ${options.path}');
      
      // Exponential backoff for retry
      final delay = _retryDelay * (retryCount + 1);
      await Future.delayed(delay);
      
      // Check connectivity before retry
      final connectivityService = Get.find<ConnectivityService>();
      if (!await connectivityService.isConnected()) {
        _logWarning('No network connection available for retry');
        handler.next(err);
        return;
      }
      
      // Update retry count and attempt the request again
      options.extra['retryCount'] = retryCount + 1;
      
      try {
        final newRequest = await _dio.fetch(options);
        handler.resolve(newRequest);
      } catch (e) {
        handler.next(err);
      }
    } else {
      _logError('Max retry attempts reached for request', err);
      Get.snackbar(
        'Connection Error',
        'Failed to connect to server after several attempts',
        snackPosition: SnackPosition.BOTTOM,
      );
      handler.next(err);
    }
  }
  
  // Check if request has reached max retries
  bool _hasReachedMaxRetries(RequestOptions options) {
    final retryCount = options.extra['retryCount'] as int? ?? 0;
    return retryCount >= _maxRetries;
  }
  
  // Check if request can be retried
  bool _isRequestRetryable(RequestOptions options) {
    // Only GET, HEAD, OPTIONS requests are considered idempotent
    final method = options.method.toUpperCase();
    return method == 'GET' || method == 'HEAD' || method == 'OPTIONS';
  }
  
  // Handle authentication errors
  Future<void> _handleAuthError() async {
    _logWarning('Authentication error - redirecting to login');
    
    // TODO: Implement token refresh before redirecting
    // Example:
    // try {
    //   final refreshed = await refreshToken();
    //   if (refreshed) return;
    // } catch (e) {
    //   _logError('Failed to refresh token', e);
    // }
    
    // Redirect to login screen
    Get.offAllNamed('/login');
  }
  
  // Handle forbidden errors (403)
  void _handleForbiddenError(DioException error) {
    _logWarning('Permission denied: ${error.requestOptions.path}');
    Get.snackbar(
      'Permission Denied',
      'You don\'t have permission to access this resource',
      snackPosition: SnackPosition.BOTTOM,
    );
  }
  
  // Handle not found errors (404)
  void _handleNotFoundError(DioException error) {
    _logWarning('Resource not found: ${error.requestOptions.path}');
    Get.snackbar(
      'Not Found',
      'The requested resource was not found',
      snackPosition: SnackPosition.BOTTOM,
    );
  }
  
  // Handle server errors (500+)
  void _handleServerError(DioException error) {
    _logError('Server error', error);
    Get.snackbar(
      'Server Error',
      'An unexpected server error occurred',
      snackPosition: SnackPosition.BOTTOM,
    );
  }
  
  // Handle connectivity issues
  Future<void> _handleConnectivityError(DioException error) async {
    _logWarning('Network connectivity issue: ${error.type}');
    
    // Check if the device is connected to the internet
    final connectivityService = Get.find<ConnectivityService>();
    final isConnected = await connectivityService.isConnected();
    
    Get.snackbar(
      'Connection Error',
      isConnected 
          ? 'Could not reach the server. Please try again later.'
          : 'No internet connection. Please check your network settings.',
      snackPosition: SnackPosition.BOTTOM,
      duration: const Duration(seconds: 5),
    );
  }
  
  // Handle other generic errors
  void _handleGenericError(DioException error) {
    _logError('API request failed', error);
    Get.snackbar(
      'Error',
      'Something went wrong. Please try again later.',
      snackPosition: SnackPosition.BOTTOM,
    );
  }
  
  // Structured logging methods
  void _logError(String message, dynamic error) {
    if (currentEnvironment != Environment.production) {
      print('❌ ERROR: $message');
      if (error is DioException) {
        print('  URL: ${error.requestOptions.path}');
        print('  Method: ${error.requestOptions.method}');
        print('  Status: ${error.response?.statusCode}');
        print('  Response: ${error.response?.data}');
      } else {
        print('  Details: $error');
      }
    }
  }
  
  void _logWarning(String message) {
    if (currentEnvironment != Environment.production) {
      print('⚠️ WARNING: $message');
    }
  }
  
  void _logInfo(String message) {
    if (currentEnvironment != Environment.production) {
      print('ℹ️ INFO: $message');
    }
  }

  // Helper method to get auth token from secure storage
  String? _getAuthToken() {
    // TODO: Implement secure storage retrieval
    // This will be replaced with actual secure storage implementation
    return null;
  }
  
  // Configure cache policy for specific requests
  CacheOptions cacheForTime(Duration duration) {
    return _cacheOptions.copyWith(
      maxStale: duration,
    );
  }
  
  // Method to clear all cache
  Future<void> clearCache() async {
    await _cacheOptions.store.clean();
    print('API cache cleared');
  }
  
  // Method to clear cache for a specific key
  Future<void> clearCacheForKey(String key) async {
    await _cacheOptions.store.delete(key);
    print('Cache cleared for key: $key');
  }

  // Getter para acessar a instância do Dio
  Dio get dio => _dio;

  // ==== INSIGHTS API METHODS ====
  
  /// Obtém todos os insights
  /// 
  /// Retorna uma lista de todos os insights
  /// [options] permite configurar parâmetros como paginação, ordenação e filtros
  Future<List<InsightModel>> getInsights({Map<String, dynamic>? options}) async {
    try {
      final queryParams = options ?? {};
      
      final response = await _dio.get(
        '/insights',
        queryParameters: queryParams,
        options: Options(
          extra: {
            'dio_cache_interceptor': cacheForTime(const Duration(minutes: 10)),
          },
        ),
      );
      
      if (response.statusCode == 200) {
        final List<dynamic> data = response.data;
        return data.map((json) => InsightModel.fromJson(json)).toList();
      } else {
        throw DioException(
          requestOptions: RequestOptions(path: '/insights'),
          error: 'Failed to load insights: ${response.statusCode}',
        );
      }
    } catch (e) {
      print('Error getting insights: $e');
      rethrow;
    }
  }
  
  /// Obtém um insight específico pelo ID
  /// 
  /// [id] ID do insight a ser recuperado
  Future<InsightModel> getInsightById(String id) async {
    try {
      final response = await _dio.get(
        '/insights/$id',
        options: Options(
          extra: {
            'dio_cache_interceptor': cacheForTime(const Duration(minutes: 10)),
          },
        ),
      );
      
      if (response.statusCode == 200) {
        return InsightModel.fromJson(response.data);
      } else {
        throw DioException(
          requestOptions: RequestOptions(path: '/insights/$id'),
          error: 'Failed to load insight: ${response.statusCode}',
        );
      }
    } catch (e) {
      print('Error getting insight by id: $e');
      rethrow;
    }
  }
  
  /// Cria um novo insight
  /// 
  /// [insight] O modelo de insight a ser criado
  Future<InsightModel> createInsight(InsightModel insight) async {
    try {
      final response = await _dio.post(
        '/insights',
        data: insight.toJson(),
      );
      
      if (response.statusCode == 201) {
        // Limpa o cache após criar um novo insight
        await clearCacheForKey('${baseUrl}/insights');
        return InsightModel.fromJson(response.data);
      } else {
        throw DioException(
          requestOptions: RequestOptions(path: '/insights'),
          error: 'Failed to create insight: ${response.statusCode}',
        );
      }
    } catch (e) {
      print('Error creating insight: $e');
      rethrow;
    }
  }
  
  /// Atualiza um insight existente
  /// 
  /// [id] ID do insight a ser atualizado
  /// [insight] Novos dados do insight
  Future<InsightModel> updateInsight(String id, InsightModel insight) async {
    try {
      final response = await _dio.put(
        '/insights/$id',
        data: insight.toJson(),
      );
      
      if (response.statusCode == 200) {
        // Limpa o cache após atualizar o insight
        await clearCacheForKey('${baseUrl}/insights');
        await clearCacheForKey('${baseUrl}/insights/$id');
        return InsightModel.fromJson(response.data);
      } else {
        throw DioException(
          requestOptions: RequestOptions(path: '/insights/$id'),
          error: 'Failed to update insight: ${response.statusCode}',
        );
      }
    } catch (e) {
      print('Error updating insight: $e');
      rethrow;
    }
  }
  
  /// Deleta um insight pelo ID
  /// 
  /// [id] ID do insight a ser deletado
  Future<bool> deleteInsight(String id) async {
    try {
      final response = await _dio.delete('/insights/$id');
      
      if (response.statusCode == 200 || response.statusCode == 204) {
        // Limpa o cache após deletar o insight
        await clearCacheForKey('${baseUrl}/insights');
        await clearCacheForKey('${baseUrl}/insights/$id');
        return true;
      } else {
        throw DioException(
          requestOptions: RequestOptions(path: '/insights/$id'),
          error: 'Failed to delete insight: ${response.statusCode}',
        );
      }
    } catch (e) {
      print('Error deleting insight: $e');
      rethrow;
    }
  }
  
  // ==== RELATIONSHIPS API METHODS ====
  
  /// Obtém todos os relacionamentos
  /// 
  /// Retorna uma lista de todos os relacionamentos entre insights
  /// [options] permite configurar parâmetros como paginação, ordenação e filtros
  Future<List<RelationshipModel>> getRelationships({Map<String, dynamic>? options}) async {
    try {
      final queryParams = options ?? {};
      
      final response = await _dio.get(
        '/relationships',
        queryParameters: queryParams,
        options: Options(
          extra: {
            'dio_cache_interceptor': cacheForTime(const Duration(minutes: 10)),
          },
        ),
      );
      
      if (response.statusCode == 200) {
        final List<dynamic> data = response.data;
        return data.map((json) => RelationshipModel.fromJson(json)).toList();
      } else {
        throw DioException(
          requestOptions: RequestOptions(path: '/relationships'),
          error: 'Failed to load relationships: ${response.statusCode}',
        );
      }
    } catch (e) {
      print('Error getting relationships: $e');
      rethrow;
    }
  }
  
  /// Obtém todos os relacionamentos para um insight específico
  /// 
  /// [insightId] ID do insight para buscar os relacionamentos
  Future<List<RelationshipModel>> getRelationshipsByInsightId(String insightId) async {
    try {
      final response = await _dio.get(
        '/insights/$insightId/relationships',
        options: Options(
          extra: {
            'dio_cache_interceptor': cacheForTime(const Duration(minutes: 10)),
          },
        ),
      );
      
      if (response.statusCode == 200) {
        final List<dynamic> data = response.data;
        return data.map((json) => RelationshipModel.fromJson(json)).toList();
      } else {
        throw DioException(
          requestOptions: RequestOptions(path: '/insights/$insightId/relationships'),
          error: 'Failed to load relationships for insight: ${response.statusCode}',
        );
      }
    } catch (e) {
      print('Error getting relationships by insight id: $e');
      rethrow;
    }
  }
  
  /// Cria um novo relacionamento entre insights
  /// 
  /// [relationship] O modelo de relacionamento a ser criado
  Future<RelationshipModel> createRelationship(RelationshipModel relationship) async {
    try {
      final response = await _dio.post(
        '/relationships',
        data: relationship.toJson(),
      );
      
      if (response.statusCode == 201) {
        // Limpa o cache relacionado a relacionamentos
        await clearCacheForKey('${baseUrl}/relationships');
        await clearCacheForKey('${baseUrl}/insights/${relationship.sourceId}/relationships');
        await clearCacheForKey('${baseUrl}/insights/${relationship.targetId}/relationships');
        
        return RelationshipModel.fromJson(response.data);
      } else {
        throw DioException(
          requestOptions: RequestOptions(path: '/relationships'),
          error: 'Failed to create relationship: ${response.statusCode}',
        );
      }
    } catch (e) {
      print('Error creating relationship: $e');
      rethrow;
    }
  }
  
  /// Deleta um relacionamento pelo ID
  /// 
  /// [id] ID do relacionamento a ser deletado
  Future<bool> deleteRelationship(String id) async {
    try {
      // Primeiro, obtém o relacionamento para saber os IDs de origem e destino
      // para invalidação de cache adequada
      RelationshipModel? relationship;
      try {
        relationship = await getRelationshipById(id);
      } catch (e) {
        print('Não foi possível obter o relacionamento antes da exclusão: $e');
        // Continua com a exclusão mesmo sem os dados para o cache
      }
      
      final response = await _dio.delete('/relationships/$id');
      
      if (response.statusCode == 200 || response.statusCode == 204) {
        // Limpa o cache relacionado a relacionamentos
        await clearCacheForKey('${baseUrl}/relationships');
        
        // Se conseguimos obter o relacionamento, limpa os caches específicos
        if (relationship != null) {
          await clearCacheForKey('${baseUrl}/insights/${relationship.sourceId}/relationships');
          await clearCacheForKey('${baseUrl}/insights/${relationship.targetId}/relationships');
        }
        
        return true;
      } else {
        throw DioException(
          requestOptions: RequestOptions(path: '/relationships/$id'),
          error: 'Failed to delete relationship: ${response.statusCode}',
        );
      }
    } catch (e) {
      print('Error deleting relationship: $e');
      rethrow;
    }
  }
  
  /// Obtém um relacionamento específico pelo ID
  /// 
  /// [id] ID do relacionamento a ser recuperado
  Future<RelationshipModel> getRelationshipById(String id) async {
    try {
      final response = await _dio.get(
        '/relationships/$id',
        options: Options(
          extra: {
            'dio_cache_interceptor': cacheForTime(const Duration(minutes: 10)),
          },
        ),
      );
      
      if (response.statusCode == 200) {
        return RelationshipModel.fromJson(response.data);
      } else {
        throw DioException(
          requestOptions: RequestOptions(path: '/relationships/$id'),
          error: 'Failed to load relationship: ${response.statusCode}',
        );
      }
    } catch (e) {
      print('Error getting relationship by id: $e');
      rethrow;
    }
  }
}
