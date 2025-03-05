import 'package:equatable/equatable.dart';
import 'package:flutter/material.dart';
import 'package:hive/hive.dart';
import 'package:uuid/uuid.dart';

part 'category.g.dart'; // This will be generated by build_runner

@HiveType(typeId: 4)
class Category with EquatableMixin {
  @HiveField(0)
  final String id;
  
  @HiveField(1)
  final String name;
  
  @HiveField(2)
  final Color color;
  
  @HiveField(3)
  final IconData icon;

  Category({
    required this.id,
    required this.name,
    required this.color,
    required this.icon,
  });

  // Factory constructor to create a new category
  factory Category.create({
    required String name,
    required Color color,
    required IconData icon,
  }) {
    return Category(
      id: const Uuid().v4(),
      name: name,
      color: color,
      icon: icon,
    );
  }

  // Create a copy with updated fields
  Category copyWith({
    String? name,
    Color? color,
    IconData? icon,
  }) {
    return Category(
      id: id,
      name: name ?? this.name,
      color: color ?? this.color,
      icon: icon ?? this.icon,
    );
  }

  @override
  List<Object?> get props => [id, name, color, icon];
}

// Custom adapter for IconData since it's not directly serializable
class IconDataAdapter extends TypeAdapter<IconData> {
  @override
  final typeId = 5;

  @override
  IconData read(BinaryReader reader) {
    return IconData(reader.readInt(), fontFamily: 'MaterialIcons');
  }

  @override
  void write(BinaryWriter writer, IconData obj) {
    writer.writeInt(obj.codePoint);
  }
}

// Custom adapter for Color since it's not directly serializable
class ColorAdapter extends TypeAdapter<Color> {
  @override
  final typeId = 6;

  @override
  Color read(BinaryReader reader) {
    return Color(reader.readInt());
  }

  @override
  void write(BinaryWriter writer, Color obj) {
    writer.writeInt(obj.value);
  }
}