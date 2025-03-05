import 'package:equatable/equatable.dart';
import 'package:hive/hive.dart';
import 'package:uuid/uuid.dart';

part 'relationship.g.dart'; // This will be generated by build_runner

// Enum for relationship types
@HiveType(typeId: 1)
enum RelationshipType {
  @HiveField(0)
  related,
  
  @HiveField(1)
  causes,
  
  @HiveField(2)
  supports,
  
  @HiveField(3)
  contradicts,
  
  @HiveField(4)
  extends,
}

// Adapter for RelationshipType enum
class RelationshipTypeAdapter extends TypeAdapter<RelationshipType> {
  @override
  final int typeId = 1;

  @override
  RelationshipType read(BinaryReader reader) {
    return RelationshipType.values[reader.readByte()];
  }

  @override
  void write(BinaryWriter writer, RelationshipType obj) {
    writer.writeByte(obj.index);
  }
}

// Main Relationship model
@HiveType(typeId: 2)
class Relationship extends HiveObject with EquatableMixin {
  @HiveField(0)
  final String id;
  
  @HiveField(1)
  final String sourceId;
  
  @HiveField(2)
  final String targetId;
  
  @HiveField(3)
  final RelationshipType type;
  
  @HiveField(4)
  final String? description;
  
  @HiveField(5)
  final DateTime createdAt;

  Relationship({
    required this.id,
    required this.sourceId,
    required this.targetId,
    required this.type,
    this.description,
    required this.createdAt,
  });

  // Factory constructor to create a new relationship
  factory Relationship.create({
    required String sourceId,
    required String targetId,
    required RelationshipType type,
    String? description,
  }) {
    return Relationship(
      id: const Uuid().v4(),
      sourceId: sourceId,
      targetId: targetId,
      type: type,
      description: description,
      createdAt: DateTime.now(),
    );
  }

  // Create a copy with updated fields
  Relationship copyWith({
    String? sourceId,
    String? targetId,
    RelationshipType? type,
    String? description,
  }) {
    return Relationship(
      id: id,
      sourceId: sourceId ?? this.sourceId,
      targetId: targetId ?? this.targetId,
      type: type ?? this.type,
      description: description ?? this.description,
      createdAt: createdAt,
    );
  }

  @override
  List<Object?> get props => [
        id,
        sourceId,
        targetId,
        type,
        description,
        createdAt,
      ];
}

// Adapter for Relationship model
class RelationshipAdapter extends TypeAdapter<Relationship> {
  @override
  final int typeId = 2;

  @override
  Relationship read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{
      for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read(),
    };
    
    return Relationship(
      id: fields[0] as String,
      sourceId: fields[1] as String,
      targetId: fields[2] as String,
      type: fields[3] as RelationshipType,
      description: fields[4] as String?,
      createdAt: fields[5] as DateTime,
    );
  }

  @override
  void write(BinaryWriter writer, Relationship obj) {
    writer.writeByte(6);
    writer.writeByte(0);
    writer.write(obj.id);
    writer.writeByte(1);
    writer.write(obj.sourceId);
    writer.writeByte(2);
    writer.write(obj.targetId);
    writer.writeByte(3);
    writer.write(obj.type);
    writer.writeByte(4);
    writer.write(obj.description);
    writer.writeByte(5);
    writer.write(obj.createdAt);
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is RelationshipAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}