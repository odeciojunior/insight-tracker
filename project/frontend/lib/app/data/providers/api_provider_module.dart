import 'package:get/get.dart';
import '../../../services/api_service.dart';
import 'insights_provider.dart';
import 'relationships_provider.dart';

/// Módulo para registro de todos os provedores de API
class ApiProviderModule {
  static void init() {
    // Registrar ApiService se ainda não estiver registrado
    if (!Get.isRegistered<ApiService>()) {
      Get.put(ApiService(), permanent: true);
    }
    
    // Registrar provedores específicos
    Get.lazyPut<InsightsProvider>(() => InsightsProvider(), fenix: true);
    Get.lazyPut<RelationshipsProvider>(() => RelationshipsProvider(), fenix: true);
  }
}
