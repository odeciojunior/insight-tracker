import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:insight_tracker/app/services/storage/get_storage.dart'; // Add this line to import StorageService

class ThemeService extends GetxController {
  final _box = GetStorage(); 
  final _key = 'isDarkMode';
  
  // Observable to track theme changes
  final Rx<ThemeMode> _themeMode = ThemeMode.system.obs;
  
  @override
  void onInit() {
    super.onInit();
    _loadThemeFromStorage();
  }
  
  // Load the saved theme mode from storage
  void _loadThemeFromStorage() {
    final isDarkMode = _box.read(_key);
    if (isDarkMode == null) {
      // If no preference is stored, use system default
      _themeMode.value = ThemeMode.system;
    } else {
      _themeMode.value = isDarkMode ? ThemeMode.dark : ThemeMode.light;
    }
  }
  
  // Get the current theme mode
  ThemeMode get themeMode => _themeMode.value;
  
  // Check if dark mode is enabled
  bool get isDarkMode => _themeMode.value == ThemeMode.dark;
  
  // Save the theme mode to storage
  Future<void> _saveThemeToStorage(bool isDarkMode) async {
    await _box.write(_key, isDarkMode);
  }
  
  // Toggle between light and dark mode
  Future<void> toggleTheme() async {
    Get.changeThemeMode(_themeMode.value == ThemeMode.light 
        ? ThemeMode.dark 
        : ThemeMode.light);
        
    _themeMode.value = _themeMode.value == ThemeMode.light 
        ? ThemeMode.dark 
        : ThemeMode.light;
        
    await _saveThemeToStorage(_themeMode.value == ThemeMode.dark);
  }
  
  // Set a specific theme mode
  Future<void> setTheme(ThemeMode mode) async {
    Get.changeThemeMode(mode);
    _themeMode.value = mode;
    await _saveThemeToStorage(mode == ThemeMode.dark);
  }
}
