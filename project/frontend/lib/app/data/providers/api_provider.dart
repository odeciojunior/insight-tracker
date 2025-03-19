import 'package:get/get.dart';
import '../../../services/api_service.dart';

/// Classe base para provedores da API
/// 
/// Fornece funcionalidades comuns para todos os provedores específicos
abstract class BaseApiProvider {
  final ApiService _apiService = Get.find<ApiService>();
  
  // Acesso protegido ao ApiService para uso nas subclasses
  ApiService get apiService => _apiService;
}
