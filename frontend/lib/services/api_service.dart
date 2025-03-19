import 'package:dio/dio.dart';
import 'package:dio_cache_interceptor/dio_cache_interceptor.dart';
import 'package:dio_cache_interceptor_hive_store/dio_cache_interceptor_hive_store.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';

/// Classe para representar exceções da API
class ApiException implements Exception {
  final String message;
  final int? statusCode;
  final dynamic data;
  
  ApiException({
    required this.message,
    this.statusCode,
    this.data,
  });
  
  @override
  String toString() => 'ApiException: $message (status: $statusCode)';
}

/// Serviço responsável por realizar chamadas à API do backend
class ApiService {
  late final Dio _dio;
  final String _baseUrl;
  
  // Singleton pattern
  static final ApiService _instance = ApiService._internal();
  
  factory ApiService() => _instance;
  
  ApiService._internal() : _baseUrl = _getBaseUrl() {
    _initDio();
  }
  
  // Cache store
  static CacheStore? _cacheStore;
  
  // Configurações de cache padrão
  static late CacheOptions _defaultCacheOptions;

  // Inicializa o cache store
  static Future<void> initCache() async {
    if (_cacheStore != null) return;

    try {
      final cacheDir = await getTemporaryDirectory();
      _cacheStore = HiveCacheStore(
        '${cacheDir.path}/dio_cache',
        hiveBoxName: 'api_cache',
      );
      
      _defaultCacheOptions = CacheOptions(
        store: _cacheStore!,
        policy: CachePolicy.request,
        hitCacheOnErrorExcept: [401, 403, 422],
        maxStale: const Duration(days: 1),
        priority: CachePriority.normal,
        cipher: null,
        keyBuilder: CacheOptions.defaultCacheKeyBuilder,
        allowPostMethod: false,
      );
      
      debugPrint('API Cache inicializado: ${cacheDir.path}/dio_cache');
    } catch (e) {
      debugPrint('Erro ao inicializar cache: $e');
      // Fallback para MemCacheStore se o acesso ao sistema de arquivos falhar
      _cacheStore = MemCacheStore();
      _defaultCacheOptions = CacheOptions(
        store: _cacheStore!,
        policy: CachePolicy.request,
        hitCacheOnErrorExcept: [401, 403],
        maxStale: const Duration(hours: 1),
        priority: CachePriority.normal,
        keyBuilder: CacheOptions.defaultCacheKeyBuilder,
      );
    }
  }

  /// Limpa todo o cache armazenado
  static Future<void> clearCache() async {
    try {
      await _cacheStore?.clean();
      debugPrint('Cache limpo com sucesso');
    } catch (e) {
      debugPrint('Erro ao limpar cache: $e');
    }
  }

  /// Invalida cache para um endpoint específico
  static Future<void> invalidateCacheForEndpoint(String endpoint) async {
    try {
      await _cacheStore?.delete(
        CacheOptions.defaultCacheKeyBuilder(
          RequestOptions(path: endpoint),
        ),
      );
      debugPrint('Cache invalidado para: $endpoint');
    } catch (e) {
      debugPrint('Erro ao invalidar cache para $endpoint: $e');
    }
  }
  
  /// Inicializa o cliente Dio com os interceptors necessários
  void _initDio() {
    // Inicializar cache se ainda não foi feito
    if (_cacheStore == null) {
      // Fallback temporário para MemCacheStore enquanto o cache assíncrono inicializa
      _cacheStore = MemCacheStore();
      _defaultCacheOptions = CacheOptions(
        store: _cacheStore!,
        policy: CachePolicy.request,
        hitCacheOnErrorExcept: [401, 403],
        maxStale: const Duration(hours: 1),
      );
      
      // Iniciamos o cache persistente
      initCache();
    }
    
    _dio = Dio(BaseOptions(
      baseUrl: _baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 10),
      headers: {'Content-Type': 'application/json'},
    ));
    
    // Adiciona interceptors
    _addInterceptors();
  }
  
  /// Adiciona interceptors para cache, autenticação e tratamento de erros
  void _addInterceptors() {
    // Adiciona o interceptor de cache
    _dio.interceptors.add(DioCacheInterceptor(options: _defaultCacheOptions));
    
    // Configuração de cache
    final cacheOptions = CacheOptions(
      store: MemCacheStore(),
      policy: CachePolicy.request,
      hitCacheOnErrorExcept: [401, 403],
      maxStale: const Duration(days: 1),
      priority: CachePriority.normal,
      keyBuilder: CacheOptions.defaultCacheKeyBuilder,
    );
    
    _dio.interceptors.add(DioCacheInterceptor(options: cacheOptions));
    
    // Retry interceptor para falhas de conexão
    _dio.interceptors.add(
      QueuedInterceptorsWrapper(
        onRequest: (options, handler) {
          // Adicionamos o cabeçalho de autenticação aqui
          // TODO: Implementar lógica para pegar token do storage
          // final token = await _getAuthToken();
          // if (token != null && token.isNotEmpty) {
          //   options.headers['Authorization'] = 'Bearer $token';
          // }
          return handler.next(options);
        },
        onError: (error, handler) async {
          // Tratamento de erros personalizado
          if (_shouldRetry(error)) {
            try {
              debugPrint('Tentando reconexão: ${error.requestOptions.path}');
              // Retry lógica
              final options = error.requestOptions;
              
              // Pequeno delay antes de tentar novamente
              await Future.delayed(const Duration(milliseconds: 500));
              
              final response = await _dio.request<dynamic>(
                options.path,
                data: options.data,
                queryParameters: options.queryParameters,
                options: Options(
                  method: options.method,
                  headers: options.headers,
                  responseType: options.responseType,
                  contentType: options.contentType,
                  extra: options.extra,
                ),
              );
              
              return handler.resolve(response);
            } catch (e) {
              // Se falhar novamente, registramos e passamos o erro original
              debugPrint('Falha na reconexão: $e');
              return handler.reject(error);
            }
          }
          
          // Tratamento do erro antes de rejeitar
          _handleError(error);
          
          // Convertemos para ApiException
          final exception = _convertToApiException(error);
          
          // Tratamento especial para erros de autenticação
          if (error.response?.statusCode == 401) {
            // TODO: Implementar refreshToken ou logout
            debugPrint('Error de autenticação - implementar refresh token');
          }
          
          return handler.reject(error);
        },
      ),
    );
    
    // Interceptor para logging (apenas em modo debug)
    if (kDebugMode) {
      _dio.interceptors.add(LogInterceptor(
        requestBody: true,
        responseBody: true,
      ));
    }
  }
  
  /// Verifica se a requisição deve ser tentada novamente
  bool _shouldRetry(DioException error) {
    // Retentar em caso de erros de timeout ou sem conexão
    return error.type == DioExceptionType.connectionTimeout ||
           error.type == DioExceptionType.receiveTimeout ||
           error.type == DioExceptionType.sendTimeout ||
           error.type == DioExceptionType.connectionError;
  }
  
  /// Converte DioException para ApiException
  ApiException _convertToApiException(DioException error) {
    String message;
    int? statusCode = error.response?.statusCode;
    
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        message = 'Tempo limite de conexão excedido';
        break;
      case DioExceptionType.badResponse:
        message = _getMessageFromStatusCode(statusCode);
        break;
      case DioExceptionType.cancel:
        message = 'Requisição cancelada';
        break;
      case DioExceptionType.connectionError:
        message = 'Falha na conexão com o servidor';
        break;
      case DioExceptionType.unknown:
        if (error.error != null && error.error.toString().contains('SocketException')) {
          message = 'Sem conexão com a internet';
        } else {
          message = 'Ocorreu um erro desconhecido';
        }
        break;
      default:
        message = 'Ocorreu um erro na comunicação com o servidor';
    }
    
    return ApiException(
      message: message,
      statusCode: statusCode,
      data: error.response?.data,
    );
  }
  
  /// Retorna mensagem de erro com base no código de status
  String _getMessageFromStatusCode(int? statusCode) {
    switch (statusCode) {
      case 400:
        return 'Requisição inválida';
      case 401:
        return 'Não autorizado';
      case 403:
        return 'Acesso negado';
      case 404:
        return 'Recurso não encontrado';
      case 409:
        return 'Conflito de dados';
      case 422:
        return 'Dados inválidos';
      case 429:
        return 'Muitas requisições. Tente novamente mais tarde';
      case 500:
        return 'Erro interno do servidor';
      case 503:
        return 'Serviço indisponível';
      default:
        return 'Ocorreu um erro na comunicação com o servidor';
    }
  }
  
  /// Trata erros de requisição
  void _handleError(DioException error) {
    final exception = _convertToApiException(error);
    
    // Logging detalhado
    debugPrint('===== API ERROR =====');
    debugPrint('URL: ${error.requestOptions.path}');
    debugPrint('Method: ${error.requestOptions.method}');
    debugPrint('Status Code: ${error.response?.statusCode}');
    debugPrint('Error Type: ${error.type}');
    debugPrint('Message: ${exception.message}');
    
    if (error.response?.data != null) {
      debugPrint('Response Data: ${error.response?.data}');
    }
    
    // TODO: Integrar com sistema de analytics para rastreamento de erros
    // await FirebaseCrashlytics.instance.recordError(
    //   exception,
    //   StackTrace.current,
    //   reason: 'API Error',
    // );
  }
  
  /// Executa uma requisição GET
  Future<Response> get(String path, {
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) async {
    try {
      final response = await _dio.get(
        path,
        queryParameters: queryParameters,
        options: options,
        cancelToken: cancelToken,
      );
      return response;
    } on DioException catch (e) {
      final apiException = _convertToApiException(e);
      throw apiException;
    } catch (e) {
      throw ApiException(
        message: 'Erro não esperado: ${e.toString()}',
      );
    }
  }
  
  /// Executa uma requisição POST
  Future<Response> post(String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) async {
    try {
      final response = await _dio.post(
        path,
        data: data,
        queryParameters: queryParameters,
        options: options,
        cancelToken: cancelToken,
      );
      return response;
    } on DioException catch (e) {
      final apiException = _convertToApiException(e);
      throw apiException;
    } catch (e) {
      throw ApiException(
        message: 'Erro não esperado: ${e.toString()}',
      );
    }
  }
  
  /// Executa uma requisição PUT
  Future<Response> put(String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) async {
    try {
      final response = await _dio.put(
        path,
        data: data,
        queryParameters: queryParameters,
        options: options,
        cancelToken: cancelToken,
      );
      return response;
    } on DioException catch (e) {
      final apiException = _convertToApiException(e);
      throw apiException;
    } catch (e) {
      throw ApiException(
        message: 'Erro não esperado: ${e.toString()}',
      );
    }
  }
  
  /// Executa uma requisição DELETE
  Future<Response> delete(String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) async {
    try {
      final response = await _dio.delete(
        path,
        data: data,
        queryParameters: queryParameters,
        options: options,
        cancelToken: cancelToken,
      );
      return response;
    } on DioException catch (e) {
      final apiException = _convertToApiException(e);
      throw apiException;
    } catch (e) {
      throw ApiException(
        message: 'Erro não esperado: ${e.toString()}',
      );
    }
  }
  
  /// Retorna a instância do Dio para uso em casos específicos
  Dio get dioInstance => _dio;

  // ENDPOINTS
  static const String _insightsEndpoint = '/insights';
  static const String _relationshipsEndpoint = '/relationships';

  // Cache helpers
  
  /// Retorna opções de cache otimizadas para listagens
  Options getCacheOptionsForListing({Duration maxStale = const Duration(minutes: 5)}) {
    return Options(
      extra: {
        'dio_cache_interceptor': CacheOptions(
          policy: CachePolicy.forceCache,
          maxStale: maxStale,
          priority: CachePriority.high,
        ).toExtra(),
      },
    );
  }
  
  /// Retorna opções de cache otimizadas para detalhes de item
  Options getCacheOptionsForDetail({Duration maxStale = const Duration(minutes: 10)}) {
    return Options(
      extra: {
        'dio_cache_interceptor': CacheOptions(
          policy: CachePolicy.forceCache,
          maxStale: maxStale,
          priority: CachePriority.normal,
        ).toExtra(),
      },
    );
  }
  
  /// Retorna opções para ignorar cache
  Options getNoCacheOptions() {
    return Options(
      extra: {
        'dio_cache_interceptor': CacheOptions(
          policy: CachePolicy.noCache,
        ).toExtra(),
      },
    );
  }
  
  /// Retorna opções para atualizar cache
  Options getRefreshCacheOptions() {
    return Options(
      extra: {
        'dio_cache_interceptor': CacheOptions(
          policy: CachePolicy.refresh,
        ).toExtra(),
      },
    );
  }

  // MÉTODOS PARA INSIGHTS
  
  /// Busca todos os insights do usuário
  Future<Response> getInsights({
    Map<String, dynamic>? filters,
    CancelToken? cancelToken,
  }) async {
    return get(
      _insightsEndpoint,
      queryParameters: filters,
      cancelToken: cancelToken,
      options: getCacheOptionsForListing(),
    );
  }
  
  /// Busca um insight específico pelo ID
  Future<Response> getInsightById(
    String id, {
    CancelToken? cancelToken,
  }) async {
    return get(
      '$_insightsEndpoint/$id',
      cancelToken: cancelToken,
      options: getCacheOptionsForDetail(),
    );
  }
  
  /// Cria um novo insight
  Future<Response> createInsight(
    Map<String, dynamic> insightData, {
    CancelToken? cancelToken,
  }) async {
    final response = await post(
      _insightsEndpoint,
      data: insightData,
      cancelToken: cancelToken,
      options: getNoCacheOptions(),
    );
    
    // Invalidar o cache da listagem após criar um novo insight
    await invalidateCacheForEndpoint(_insightsEndpoint);
    
    return response;
  }
  
  /// Atualiza um insight existente
  Future<Response> updateInsight(
    String id,
    Map<String, dynamic> insightData, {
    CancelToken? cancelToken,
  }) async {
    final response = await put(
      '$_insightsEndpoint/$id',
      data: insightData,
      cancelToken: cancelToken,
      options: getRefreshCacheOptions(),
    );
    
    // Invalidar caches relacionados
    await invalidateCacheForEndpoint(_insightsEndpoint);
    await invalidateCacheForEndpoint('$_insightsEndpoint/$id');
    
    return response;
  }
  
  /// Exclui um insight
  Future<Response> deleteInsight(
    String id, {
    CancelToken? cancelToken,
  }) async {
    final response = await delete(
      '$_insightsEndpoint/$id',
      cancelToken: cancelToken,
      options: getNoCacheOptions(),
    );
    
    // Invalidar caches relacionados
    await invalidateCacheForEndpoint(_insightsEndpoint);
    await invalidateCacheForEndpoint('$_insightsEndpoint/$id');
    
    return response;
  }
  
  /// Busca insights relacionados a um insight específico
  Future<Response> getRelatedInsights(
    String insightId, {
    int limit = 10,
    CancelToken? cancelToken,
  }) async {
    return get(
      '$_insightsEndpoint/$insightId/related',
      queryParameters: {'limit': limit},
      cancelToken: cancelToken,
      options: Options(
        extra: {
          'dio_cache_interceptor': CacheOptions(
            policy: CachePolicy.forceCache,
            maxStale: const Duration(minutes: 5),
          ).toExtra(),
        },
      ),
    );
  }

  // MÉTODOS PARA RELACIONAMENTOS
  
  /// Busca todos os relacionamentos
  Future<Response> getRelationships({
    Map<String, dynamic>? filters,
    CancelToken? cancelToken,
  }) async {
    return get(
      _relationshipsEndpoint,
      queryParameters: filters,
      cancelToken: cancelToken,
      options: Options(
        extra: {
          'dio_cache_interceptor': CacheOptions(
            policy: CachePolicy.forceCache,
            maxStale: const Duration(minutes: 5),
          ).toExtra(),
        },
      ),
    );
  }
  
  /// Busca relacionamentos por ID de insight
  Future<Response> getRelationshipsByInsightId(
    String insightId, {
    CancelToken? cancelToken,
  }) async {
    return get(
      '$_insightsEndpoint/$insightId/relationships',
      cancelToken: cancelToken,
      options: Options(
        extra: {
          'dio_cache_interceptor': CacheOptions(
            policy: CachePolicy.forceCache,
            maxStale: const Duration(minutes: 5),
          ).toExtra(),
        },
      ),
    );
  }
  
  /// Cria um novo relacionamento entre insights
  Future<Response> createRelationship(
    Map<String, dynamic> relationshipData, {
    CancelToken? cancelToken,
  }) async {
    return post(
      _relationshipsEndpoint,
      data: relationshipData,
      cancelToken: cancelToken,
      options: Options(
        extra: {
          'dio_cache_interceptor': CacheOptions(
            policy: CachePolicy.noCache,
          ).toExtra(),
        },
      ),
    );
  }
  
  /// Atualiza um relacionamento existente
  Future<Response> updateRelationship(
    String id,
    Map<String, dynamic> relationshipData, {
    CancelToken? cancelToken,
  }) async {
    return put(
      '$_relationshipsEndpoint/$id',
      data: relationshipData,
      cancelToken: cancelToken,
      options: Options(
        extra: {
          'dio_cache_interceptor': CacheOptions(
            policy: CachePolicy.refresh,
          ).toExtra(),
        },
      ),
    );
  }
  
  /// Exclui um relacionamento
  Future<Response> deleteRelationship(
    String id, {
    CancelToken? cancelToken,
  }) async {
    return delete(
      '$_relationshipsEndpoint/$id',
      cancelToken: cancelToken,
      options: Options(
        extra: {
          'dio_cache_interceptor': CacheOptions(
            policy: CachePolicy.noCache,
          ).toExtra(),
        },
      ),
    );
  }
  
  /// Busca força de relacionamento entre dois insights
  Future<Response> getRelationshipStrength(
    String sourceId,
    String targetId, {
    CancelToken? cancelToken,
  }) async {
    return get(
      '$_relationshipsEndpoint/strength',
      queryParameters: {
        'source_id': sourceId,
        'target_id': targetId,
      },
      cancelToken: cancelToken,
      options: Options(
        extra: {
          'dio_cache_interceptor': CacheOptions(
            policy: CachePolicy.forceCache,
            maxStale: const Duration(minutes: 10),
          ).toExtra(),
        },
      ),
    );
  }
  
  /// Obtém sugestões de relacionamentos para um insight
  Future<Response> getRelationshipSuggestions(
    String insightId, {
    int limit = 5,
    CancelToken? cancelToken,
  }) async {
    return get(
      '$_insightsEndpoint/$insightId/relationship-suggestions',
      queryParameters: {'limit': limit},
      cancelToken: cancelToken,
      options: Options(
        extra: {
          'dio_cache_interceptor': CacheOptions(
            policy: CachePolicy.refresh,
            maxStale: const Duration(minutes: 10),
          ).toExtra(),
        },
      ),
    );
  }
}
