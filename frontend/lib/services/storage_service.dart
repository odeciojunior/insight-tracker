import 'package:flutter/material.dart'; // Add import for Color and Icons
import 'package:hive/hive.dart';
import 'package:hive_flutter/hive_flutter.dart';

import '../app/data/models/category.dart';
import '../app/data/models/insight.dart';
import '../app/data/models/relationship.dart';

class StorageService {
  static const String INSIGHTS_BOX = 'insights';
  static const String RELATIONSHIPS_BOX = 'relationships';
  static const String CATEGORIES_BOX = 'categories';
  static const String SETTINGS_BOX = 'settings';

  late Box<Insight> _insightsBox;
  late Box<Relationship> _relationshipsBox;
  late Box<Category> _categoriesBox;
  late Box<dynamic> _settingsBox;

  Future<void> init() async {
    try {
      // Register adapters with unique type IDs
      if (!Hive.isAdapterRegistered(0)) {
        Hive.registerAdapter(InsightAdapter());
      }
      if (!Hive.isAdapterRegistered(1)) {
        Hive.registerAdapter(RelationshipTypeAdapter());
      }
      if (!Hive.isAdapterRegistered(2)) {
        Hive.registerAdapter(RelationshipAdapter());
      }
      if (!Hive.isAdapterRegistered(3)) {
        Hive.registerAdapter(CategoryAdapter());
      }
      if (!Hive.isAdapterRegistered(4)) {
        Hive.registerAdapter(ColorAdapter());
      }
      if (!Hive.isAdapterRegistered(5)) {
        Hive.registerAdapter(IconDataAdapter());
      }

      // Open boxes
      _insightsBox = await Hive.openBox<Insight>(INSIGHTS_BOX);
      _relationshipsBox = await Hive.openBox<Relationship>(RELATIONSHIPS_BOX);
      _categoriesBox = await Hive.openBox<Category>(CATEGORIES_BOX);
      _settingsBox = await Hive.openBox(SETTINGS_BOX);

      // Add default categories if empty
      if (_categoriesBox.isEmpty) {
        _addDefaultCategories();
      }
    } catch (e) {
      print('Error initializing storage: $e');
      rethrow; // Rethrow to allow caller to handle the error
    }
  }

  // Insight Methods
  Future<void> saveInsight(Insight insight) async {
    await _insightsBox.put(insight.id, insight);
  }

  Future<void> deleteInsight(String id) async {
    await _insightsBox.delete(id);
    // Also delete relationships involving this insight
    final toDelete = _relationshipsBox.values
        .where((rel) => rel.sourceId == id || rel.targetId == id)
        .map((rel) => rel.id)
        .toList();
    
    for (final relId in toDelete) {
      await _relationshipsBox.delete(relId);
    }
  }

  List<Insight> getAllInsights() {
    return _insightsBox.values.toList();
  }

  Insight? getInsight(String id) {
    return _insightsBox.get(id);
  }

  // Relationship Methods
  Future<void> saveRelationship(Relationship relationship) async {
    await _relationshipsBox.put(relationship.id, relationship);
  }

  Future<void> deleteRelationship(String id) async {
    await _relationshipsBox.delete(id);
  }

  List<Relationship> getAllRelationships() {
    return _relationshipsBox.values.toList();
  }

  List<Relationship> getInsightRelationships(String insightId) {
    return _relationshipsBox.values
        .where((rel) => rel.sourceId == insightId || rel.targetId == insightId)
        .toList();
  }

  // Category Methods
  Future<void> saveCategory(Category category) async {
    await _categoriesBox.put(category.id, category);
  }

  Future<void> deleteCategory(String id) async {
    // Update insights with this category to have no category
    final insightsToUpdate = _insightsBox.values
        .where((insight) => insight.categoryId == id)
        .toList();
    
    for (final insight in insightsToUpdate) {
      final updated = insight.copyWith(categoryId: null);
      await _insightsBox.put(insight.id, updated);
    }
    
    await _categoriesBox.delete(id);
  }

  List<Category> getAllCategories() {
    return _categoriesBox.values.toList();
  }

  // Settings Methods
  Future<void> saveSetting(String key, dynamic value) async {
    await _settingsBox.put(key, value);
  }

  dynamic getSetting(String key, {dynamic defaultValue}) {
    return _settingsBox.get(key, defaultValue: defaultValue);
  }

  // Private Methods
  void _addDefaultCategories() {
    final defaultCategories = [
      Category.create(
        name: 'Work',
        color: const Color(0xFF2196F3), // Blue
        icon: Icons.work,
      ),
      Category.create(
        name: 'Personal',
        color: const Color(0xFF4CAF50), // Green
        icon: Icons.person,
      ),
      Category.create(
        name: 'Ideas',
        color: const Color(0xFFFFC107), // Amber
        icon: Icons.lightbulb,
      ),
      Category.create(
        name: 'Tasks',
        color: const Color(0xFFF44336), // Red
        icon: Icons.task_alt,
      ),
    ];

    for (final category in defaultCategories) {
      _categoriesBox.put(category.id, category);
    }
  }

  // Clear all data (for testing/logout)
  Future<void> clearAllData() async {
    await _insightsBox.clear();
    await _relationshipsBox.clear();
    await _categoriesBox.clear();
    await _settingsBox.clear();
    _addDefaultCategories();
  }
}