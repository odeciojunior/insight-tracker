import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../data/models/category.dart';
import '../../services/storage_service.dart';

class CategoryController extends GetxController {
  final StorageService _storageService = Get.find<StorageService>();
  
  // Observable list of categories
  final RxList<Category> categories = <Category>[].obs;
  
  // Loading state
  final isLoading = false.obs;
  
  // Error message
  final errorMessage = Rx<String?>(null);

  @override
  void onInit() {
    super.onInit();
    loadCategories();
  }
  
  // Load all categories from storage
  Future<void> loadCategories() async {
    try {
      isLoading.value = true;
      final allCategories = _storageService.getAllCategories();
      categories.assignAll(allCategories);
    } catch (e) {
      errorMessage.value = 'Failed to load categories: $e';
    } finally {
      isLoading.value = false;
    }
  }
  
  // Add a new category
  Future<void> addCategory({
    required String name,
    required Color color,
    required IconData icon,
  }) async {
    try {
      isLoading.value = true;
      
      // Check for duplicate name
      if (categories.any((c) => c.name.toLowerCase() == name.toLowerCase())) {
        throw Exception('A category with this name already exists');
      }
      
      // Create a new category
      final category = Category.create(
        name: name,
        color: color,
        icon: icon,
      );
      
      // Save to storage
      await _storageService.saveCategory(category);
      
      // Add to list
      categories.add(category);
      
      // Success message
      Get.snackbar(
        'Success',
        'Category added successfully',
        snackPosition: SnackPosition.BOTTOM,
      );
    } catch (e) {
      errorMessage.value = 'Failed to add category: $e';
      Get.snackbar(
        'Error',
        'Failed to add category: $e',
        snackPosition: SnackPosition.BOTTOM,
      );
    } finally {
      isLoading.value = false;
    }
  }
  
  // Update an existing category
  Future<void> updateCategory(Category updatedCategory) async {
    try {
      isLoading.value = true;
      
      // Check for duplicate name
      if (categories.any((c) => c.id != updatedCategory.id && 
                              c.name.toLowerCase() == updatedCategory.name.toLowerCase())) {
        throw Exception('A category with this name already exists');
      }
      
      // Save to storage
      await _storageService.saveCategory(updatedCategory);
      
      // Update in list
      final index = categories.indexWhere((c) => c.id == updatedCategory.id);
      if (index >= 0) {
        categories[index] = updatedCategory;
      }
      
      // Success message
      Get.snackbar(
        'Success',
        'Category updated successfully',
        snackPosition: SnackPosition.BOTTOM,
      );
    } catch (e) {
      errorMessage.value = 'Failed to update category: $e';
      Get.snackbar(
        'Error',
        'Failed to update category: $e',
        snackPosition: SnackPosition.BOTTOM,
      );
    } finally {
      isLoading.value = false;
    }
  }
  
  // Delete a category
  Future<void> deleteCategory(String categoryId) async {
    try {
      isLoading.value = true;
      
      // Delete from storage
      await _storageService.deleteCategory(categoryId);
      
      // Remove from list
      categories.removeWhere((c) => c.id == categoryId);
      
      // Success message
      Get.snackbar(
        'Success',
        'Category deleted successfully',
        snackPosition: SnackPosition.BOTTOM,
      );
    } catch (e) {
      errorMessage.value = 'Failed to delete category: $e';
      Get.snackbar(
        'Error',
        'Failed to delete category: $e',
        snackPosition: SnackPosition.BOTTOM,
      );
    } finally {
      isLoading.value = false;
    }
  }
  
  // Get category by ID
  Category? getCategoryById(String? id) {
    if (id == null) return null;
    try {
      return categories.firstWhere((c) => c.id == id);
    } catch (e) {
      return null;
    }
  }
}