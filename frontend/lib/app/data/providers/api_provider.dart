import 'package:dio/dio.dart';
import 'package:get/get.dart';
import '../../../services/api_service.dart';
import '../models/insight.dart';
import '../models/relationship.dart';

/// Classe base para provedores da API
/// 
/// Fornece funcionalidades comuns para todos os provedores específicos
abstract class BaseApiProvider {
  final ApiService _apiService = Get.find<ApiService>();
  
  // Acesso protegido ao ApiService para uso nas subclasses
  ApiService get apiService => _apiService;
}

/// Provedor de acesso à API que organiza as requisições por domínio
class ApiProvider {
  final ApiService _apiService;
  
  ApiProvider({ApiService? apiService}) : _apiService = apiService ?? ApiService();
  
  // INSIGHTS API
  
  /// Busca todos os insights
  Future<List<dynamic>> getInsights({
    Map<String, dynamic>? filters,
    CancelToken? cancelToken,
  }) async {
    try {
      final response = await _apiService.getInsights(
        filters: filters,
        cancelToken: cancelToken,
      );
      return response.data['data'] as List<dynamic>;
    } on ApiException catch (e) {
      _handleApiException(e);
      return [];
    }
  }
  
  /// Busca um insight específico pelo ID
  Future<Map<String, dynamic>?> getInsightById(String id) async {
    try {
      final response = await _apiService.getInsightById(id);
      return response.data['data'] as Map<String, dynamic>;
    } on ApiException catch (e) {
      _handleApiException(e);
      return null;
    }
  }
  
  /// Cria um novo insight
  Future<Map<String, dynamic>?> createInsight(Map<String, dynamic> data) async {
    try {
      final response = await _apiService.createInsight(data);
      return response.data['data'] as Map<String, dynamic>;
    } on ApiException catch (e) {
      _handleApiException(e);
      return null;
    }
  }
  
  /// Atualiza um insight existente
  Future<Map<String, dynamic>?> updateInsight(String id, Map<String, dynamic> data) async {
    try {
      final response = await _apiService.updateInsight(id, data);
      return response.data['data'] as Map<String, dynamic>;
    } on ApiException catch (e) {
      _handleApiException(e);
      return null;
    }
  }
  
  /// Exclui um insight
  Future<bool> deleteInsight(String id) async {
    try {
      await _apiService.deleteInsight(id);
      return true;
    } on ApiException catch (e) {
      _handleApiException(e);
      return false;
    }
  }
  
  /// Busca insights relacionados a um insight específico
  Future<List<dynamic>> getRelatedInsights(
    String insightId, {
    int limit = 10,
  }) async {
    try {
      final response = await _apiService.getRelatedInsights(insightId, limit: limit);
      return response.data['data'] as List<dynamic>;
    } on ApiException catch (e) {
      _handleApiException(e);
      return [];
    }
  }
  
  // RELACIONAMENTOS API
  
  /// Busca todos os relacionamentos
  Future<List<dynamic>> getRelationships({
    Map<String, dynamic>? filters,
  }) async {
    try {
      final response = await _apiService.getRelationships(filters: filters);
      return response.data['data'] as List<dynamic>;
    } on ApiException catch (e) {
      _handleApiException(e);
      return [];
    }
  }
  
  /// Busca relacionamentos por ID de insight
  Future<List<dynamic>> getRelationshipsByInsightId(String insightId) async {
    try {
      final response = await _apiService.getRelationshipsByInsightId(insightId);
      return response.data['data'] as List<dynamic>;
    } on ApiException catch (e) {
      _handleApiException(e);
      return [];
    }
  }
  
  /// Cria um novo relacionamento entre insights
  Future<Map<String, dynamic>?> createRelationship(Map<String, dynamic> data) async {
    try {
      final response = await _apiService.createRelationship(data);
      return response.data['data'] as Map<String, dynamic>;
    } on ApiException catch (e) {
      _handleApiException(e);
      return null;
    }
  }
  
  /// Atualiza um relacionamento existente
  Future<Map<String, dynamic>?> updateRelationship(
    String id,
    Map<String, dynamic> data,
  ) async {
    try {
      final response = await _apiService.updateRelationship(id, data);
      return response.data['data'] as Map<String, dynamic>;
    } on ApiException catch (e) {
      _handleApiException(e);
      return null;
    }
  }
  
  /// Exclui um relacionamento
  Future<bool> deleteRelationship(String id) async {
    try {
      await _apiService.deleteRelationship(id);
      return true;
    } on ApiException catch (e) {
      _handleApiException(e);
      return false;
    }
  }
  
  /// Busca força de relacionamento entre dois insights
  Future<double> getRelationshipStrength(String sourceId, String targetId) async {
    try {
      final response = await _apiService.getRelationshipStrength(sourceId, targetId);
      return (response.data['data']['strength'] as num).toDouble();
    } on ApiException catch (e) {
      _handleApiException(e);
      return 0.0;
    }
  }
  
  /// Obtém sugestões de relacionamentos para um insight
  Future<List<dynamic>> getRelationshipSuggestions(
    String insightId, {
    int limit = 5,
  }) async {
    try {
      final response = await _apiService.getRelationshipSuggestions(insightId, limit: limit);
      return response.data['data'] as List<dynamic>;
    } on ApiException catch (e) {
      _handleApiException(e);
      return [];
    }
  }
  
  // MANIPULAÇÃO DE ERROS
  
  /// Trata exceções da API de forma consistente
  void _handleApiException(ApiException exception) {
    // Log do erro
    print('API Error: ${exception.message} (${exception.statusCode})');
    
    // Aqui você pode adicionar lógica para:
    // 1. Mostrar mensagens de erro para o usuário
    // 2. Registrar erros em um serviço de analytics
    // 3. Realizar ações específicas com base no tipo de erro
    
    // Por exemplo:
    if (exception.statusCode == 401) {
      // TODO: Redirecionar para tela de login ou atualizar token
    } else if (exception.statusCode == 403) {
      // TODO: Mostrar mensagem de permissão negada
    }
    
    // Rethrow para permitir que o chamador também possa tratar se necessário
    //throw exception;
  }
}
