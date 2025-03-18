import 'package:get/get.dart';

import '../../services/storage_service.dart';
import '../data/models/insight.dart';

class InsightController extends GetxController {
  final StorageService _storageService = Get.find<StorageService>();
  
  // Observable list of insights
  final insights = <Insight>[].obs;
  final insight = Insight;
  
  // Loading state
  final isLoading = false.obs;
  
  // Error message
  final errorMessage = Rx<String?>(null);
  
  @override
  void onInit() {
    super.onInit();
    loadInsights();
  }
  
  // Load all insights from storage
  Future<void> loadInsights() async {
    try {
      isLoading.value = true;
      final allInsights = _storageService.getAllInsights();
      insights.assignAll(allInsights);
    } catch (e) {
      errorMessage.value = 'Failed to load insights: $e';
    } finally {
      isLoading.value = false;
    }
  }

  // Add a new insight
  Future<void> addInsight({
    required String title,
    required String content,
    List<String>? tags,
    String? categoryId,
  }) async {
    try {
      isLoading.value = true;
      
      // Create a new insight
      final insight = Insight.create(
        title: title,
        content: content,
        tags: tags,
        categoryId: categoryId,
      );
      
      // Save to storage
      await _storageService.saveInsight(insight);
      
      // Add to list
      insights.add(insight);
      
      // Success message
      Get.snackbar(
        'Success',
        'Insight captured successfully',
        snackPosition: SnackPosition.BOTTOM,
      );
    } catch (e) {
      errorMessage.value = 'Failed to add insight: $e';
      Get.snackbar(
        'Error',
        'Failed to add insight',
        snackPosition: SnackPosition.BOTTOM,
      );
    } finally {
      isLoading.value = false;
    }
  }
  
  // Get a single insight by ID
  Future<Insight?> getInsight(String id) async {
    try {
      isLoading.value = true;
      final insight = _storageService.getInsight(id);
      return insight;
    } catch (e) {
      errorMessage.value = 'Failed to get insight: $e';
      return null;
    } finally {
      isLoading.value = false;
    }
  }

  // Update an existing insight
  Future<void> updateInsight(Insight updatedInsight, String id) async {
    try {
      isLoading.value = true;
      
      // Save to storage
      await _storageService.saveInsight(updatedInsight);
      
      // Update in list
      final index = insights.indexWhere((i) => i.id == id);
      if (index >= 0) {
        insights[index] = updatedInsight.copyWith(categoryId: id);
      }
      
      Get.snackbar(
        'Success',
        'Insight updated successfully',
        snackPosition: SnackPosition.BOTTOM,
      );
    } catch (e) {
      errorMessage.value = 'Failed to update insight: $e';
      Get.snackbar(
        'Error',
        'Failed to update insight',
        snackPosition: SnackPosition.BOTTOM,
      );
    } finally {
      isLoading.value = false;
    }
  }
  
  // Delete an insight
  Future<void> deleteInsight(String insightId) async {
    try {
      isLoading.value = true;
      
      // Delete from storage
      await _storageService.deleteInsight(insightId);
      
      // Remove from list
      insights.removeWhere((i) => i.id == insightId);
      
      Get.snackbar(
        'Success',
        'Insight deleted successfully',
        snackPosition: SnackPosition.BOTTOM,
      );
    } catch (e) {
      errorMessage.value = 'Failed to delete insight: $e';
      Get.snackbar(
        'Error',
        'Failed to delete insight',
        snackPosition: SnackPosition.BOTTOM,
      );
    } finally {
      isLoading.value = false;
    }
  }
}