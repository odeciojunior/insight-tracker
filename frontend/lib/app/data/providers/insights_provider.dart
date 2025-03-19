import '../../../models/insight_model.dart';
import 'api_provider.dart';

/// Provedor específico para operações relacionadas a Insights
class InsightsProvider extends BaseApiProvider {
  /// Busca todos os insights com opções de filtro
  /// 
  /// [page] - Página atual para paginação
  /// [limit] - Número de itens por página
  /// [search] - Termo de busca para título ou descrição
  /// [category] - Filtro por categoria
  /// [tags] - Lista de tags para filtrar
  Future<List<InsightModel>> getAll({
    int? page,
    int? limit,
    String? search,
    String? category,
    List<String>? tags,
    String? sortBy,
    bool? ascending,
  }) async {
    final options = <String, dynamic>{};
    
    if (page != null) options['page'] = page;
    if (limit != null) options['limit'] = limit;
    if (search != null && search.isNotEmpty) options['search'] = search;
    if (category != null) options['category'] = category;
    if (tags != null && tags.isNotEmpty) options['tags'] = tags.join(',');
    if (sortBy != null) options['sortBy'] = sortBy;
    if (ascending != null) options['order'] = ascending ? 'asc' : 'desc';
    
    return await apiService.getInsights(options: options);
  }
  
  /// Busca um insight específico por ID
  Future<InsightModel> getById(String id) async {
    return await apiService.getInsightById(id);
  }
  
  /// Cria um novo insight
  Future<InsightModel> create(InsightModel insight) async {
    return await apiService.createInsight(insight);
  }
  
  /// Atualiza um insight existente
  Future<InsightModel> update(String id, InsightModel insight) async {
    return await apiService.updateInsight(id, insight);
  }
  
  /// Deleta um insight pelo ID
  Future<bool> delete(String id) async {
    return await apiService.deleteInsight(id);
  }
  
  /// Busca insights recentes
  Future<List<InsightModel>> getRecent({int limit = 5}) async {
    return await getAll(
      limit: limit,
      sortBy: 'createdAt',
      ascending: false,
    );
  }
  
  /// Busca insights por categoria
  Future<List<InsightModel>> getByCategory(String category, {int? limit}) async {
    return await getAll(
      category: category,
      limit: limit,
    );
  }
  
  /// Busca insights por tags
  Future<List<InsightModel>> getByTags(List<String> tags, {int? limit}) async {
    return await getAll(
      tags: tags,
      limit: limit,
    );
  }
}
