import 'package:dio/dio.dart';
import 'package:dio_cache_interceptor/dio_cache_interceptor.dart';
import 'package:get/get.dart';
import '../models/insight.dart';
import '../models/relationship.dart';

class ApiService extends GetxService {
  final Dio _dio = Dio();
  final CacheOptions _cacheOptions = CacheOptions(
    store: MemCacheStore(),
    policy: CachePolicy.refreshForceCache,
    hitCacheOnErrorExcept: [401, 403],
    maxStale: const Duration(days: 1),
  );
  
  // URLs base para diferentes ambientes
  final String _devBaseUrl = 'http://localhost:8000/api';
  final String _stagingBaseUrl = 'https://staging-api.insight-tracker.com/api';
  final String _prodBaseUrl = 'https://api.insight-tracker.com/api';
  
  late String _baseUrl;
  
  // Getter para a URL base atual
  String get baseUrl => _baseUrl;

  @override
  void onInit() {
    super.onInit();
    _configureBaseUrl();
    _configureDio();
  }

  void _configureBaseUrl() {
    // Configurar URL base de acordo com o ambiente
    const String environment = String.fromEnvironment('ENV', defaultValue: 'dev');
    switch (environment) {
      case 'prod':
        _baseUrl = _prodBaseUrl;
        break;
      case 'staging':
        _baseUrl = _stagingBaseUrl;
        break;
      default:
        _baseUrl = _devBaseUrl;
    }
  }

  void _configureDio() {
    // Configurar Dio com interceptors
    _dio.options.baseUrl = _baseUrl;
    _dio.options.connectTimeout = const Duration(seconds: 5);
    _dio.options.receiveTimeout = const Duration(seconds: 3);
    
    // Adicionar interceptor de cache
    _dio.interceptors.add(DioCacheInterceptor(options: _cacheOptions));
    
    // Interceptor para adicionar token de autenticação
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
        // Adicionar lógica para pegar o token de autenticação
        // final String? token = Get.find<AuthService>().token;
        // if (token != null) {
        //   options.headers['Authorization'] = 'Bearer $token';
        // }
        return handler.next(options);
      },
      onError: (DioException e, handler) {
        // Lógica para tratamento de erros
        _handleError(e);
        return handler.next(e);
      }
    ));
    
    // Adicionar interceptor de logging para depuração
    _dio.interceptors.add(LogInterceptor(
      requestBody: true,
      responseBody: true,
    ));
  }
  
  void _handleError(DioException error) {
    // Implementar lógica de tratamento de erros
    print('API Error: ${error.message}');
    
    // Retry lógica para falhas de conexão
    if (error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.receiveTimeout) {
      // Implementar retry
    }
    
    // Tratamento específico para diferentes códigos HTTP
    if (error.response != null) {
      switch (error.response!.statusCode) {
        case 401:
          // Unauthorized - redirecionar para login
          print('Unauthorized access');
          break;
        case 404:
          // Not found
          print('Resource not found');
          break;
        default:
          print('Server error: ${error.response!.statusCode}');
      }
    }
  }
  
  // Métodos básicos da API serão implementados nas próximas tarefas
}
