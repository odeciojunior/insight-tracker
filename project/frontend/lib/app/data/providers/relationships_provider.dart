import '../../../models/relationship_model.dart';
import 'api_provider.dart';

/// Provedor específico para operações relacionadas a Relacionamentos
class RelationshipsProvider extends BaseApiProvider {
  /// Busca todos os relacionamentos com opções de filtro
  Future<List<RelationshipModel>> getAll({
    int? page,
    int? limit,
    String? type,
    double? minStrength,
    String? sortBy,
    bool? ascending,
  }) async {
    final options = <String, dynamic>{};
    
    if (page != null) options['page'] = page;
    if (limit != null) options['limit'] = limit;
    if (type != null) options['type'] = type;
    if (minStrength != null) options['minStrength'] = minStrength;
    if (sortBy != null) options['sortBy'] = sortBy;
    if (ascending != null) options['order'] = ascending ? 'asc' : 'desc';
    
    return await apiService.getRelationships(options: options);
  }
  
  /// Busca um relacionamento específico por ID
  Future<RelationshipModel> getById(String id) async {
    return await apiService.getRelationshipById(id);
  }
  
  /// Busca todos os relacionamentos para um insight específico
  Future<List<RelationshipModel>> getByInsightId(String insightId, {
    String? type,
    bool? asSource,
    bool? asTarget,
  }) async {
    final options = <String, dynamic>{};
    
    if (type != null) options['type'] = type;
    if (asSource != null) options['asSource'] = asSource;
    if (asTarget != null) options['asTarget'] = asTarget;
    
    return await apiService.getRelationshipsByInsightId(insightId);
  }
  
  /// Cria um novo relacionamento
  Future<RelationshipModel> create(RelationshipModel relationship) async {
    return await apiService.createRelationship(relationship);
  }
  
  /// Deleta um relacionamento pelo ID
  Future<bool> delete(String id) async {
    return await apiService.deleteRelationship(id);
  }
  
  /// Cria um relacionamento bidirecional entre dois insights
  Future<List<RelationshipModel>> createBidirectional({
    required String firstInsightId,
    required String secondInsightId,
    required String type,
    String? description,
    double? strength,
  }) async {
    // Criar o primeiro relacionamento
    final firstRelationship = RelationshipModel(
      sourceId: firstInsightId,
      targetId: secondInsightId,
      type: type,
      description: description,
      strength: strength,
    );
    
    // Criar o segundo relacionamento (direção oposta)
    final secondRelationship = RelationshipModel(
      sourceId: secondInsightId,
      targetId: firstInsightId,
      type: type,
      description: description,
      strength: strength,
    );
    
    // Executar as duas criações
    final results = await Future.wait([
      apiService.createRelationship(firstRelationship),
      apiService.createRelationship(secondRelationship),
    ]);
    
    return results;
  }
}
