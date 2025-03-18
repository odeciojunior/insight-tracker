import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

export 'get_storage.dart';

/// A simple implementation of GetStorage that uses SharedPreferences under the hood.
/// This mocks the functionality of the actual get_storage package.
class GetStorage {
  static final Map<String, GetStorage> _cache = {};
  final String _container;
  Map<String, dynamic> _data = {};
  bool _initialized = false;

  /// Creates a GetStorage instance with an optional container name.
  factory GetStorage([String container = 'GetStorage']) {
    if (_cache.containsKey(container)) {
      return _cache[container]!;
    } else {
      final instance = GetStorage._internal(container);
      _cache[container] = instance;
      return instance;
    }
  }

  GetStorage._internal(this._container);

  /// Initializes the storage by loading data from SharedPreferences.
  Future<GetStorage> init() async {
    if (!_initialized) {
      final prefs = await SharedPreferences.getInstance();
      final storedData = prefs.getString(_container);
      
      if (storedData != null) {
        try {
          _data = Map<String, dynamic>.from(json.decode(storedData));
        } catch (e) {
          _data = {};
        }
      }
      _initialized = true;
    }
    return this;
  }

  /// Reads a value from storage with the given key.
  T? read<T>(String key) {
    return _data[key] as T?;
  }

  /// Writes a value to storage with the given key.
  Future<void> write(String key, dynamic value) async {
    _data[key] = value;
    await _saveToPrefs();
  }

  /// Removes a value from storage with the given key.
  Future<void> remove(String key) async {
    _data.remove(key);
    await _saveToPrefs();
  }

  /// Checks if the storage contains a value with the given key.
  bool hasData(String key) {
    return _data.containsKey(key);
  }

  /// Erases all data from the storage.
  Future<void> erase() async {
    _data.clear();
    await _saveToPrefs();
  }

  /// Saves the current state to SharedPreferences.
  Future<void> _saveToPrefs() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_container, json.encode(_data));
  }
}
