class RelationshipModel {
  final String? id;
  final String sourceId;
  final String targetId;
  final String type;
  final String? description;
  final DateTime? createdAt;
  final DateTime? updatedAt;
  final double? strength;

  RelationshipModel({
    this.id,
    required this.sourceId,
    required this.targetId,
    required this.type,
    this.description,
    this.createdAt,
    this.updatedAt,
    this.strength,
  });

  // Cria uma cópia do relacionamento com algumas propriedades alteradas
  RelationshipModel copyWith({
    String? id,
    String? sourceId,
    String? targetId,
    String? type,
    String? description,
    DateTime? createdAt,
    DateTime? updatedAt,
    double? strength,
  }) {
    return RelationshipModel(
      id: id ?? this.id,
      sourceId: sourceId ?? this.sourceId,
      targetId: targetId ?? this.targetId,
      type: type ?? this.type,
      description: description ?? this.description,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      strength: strength ?? this.strength,
    );
  }

  // Cria um relacionamento a partir de um Map/JSON
  factory RelationshipModel.fromJson(Map<String, dynamic> json) {
    return RelationshipModel(
      id: json['id'],
      sourceId: json['sourceId'],
      targetId: json['targetId'],
      type: json['type'],
      description: json['description'],
      createdAt: json['createdAt'] != null ? DateTime.parse(json['createdAt']) : null,
      updatedAt: json['updatedAt'] != null ? DateTime.parse(json['updatedAt']) : null,
      strength: json['strength'] != null ? json['strength'].toDouble() : null,
    );
  }

  // Converte o relacionamento para Map/JSON
  Map<String, dynamic> toJson() {
    final Map<String, dynamic> data = <String, dynamic>{};
    if (id != null) data['id'] = id;
    data['sourceId'] = sourceId;
    data['targetId'] = targetId;
    data['type'] = type;
    if (description != null) data['description'] = description;
    if (createdAt != null) data['createdAt'] = createdAt!.toIso8601String();
    if (updatedAt != null) data['updatedAt'] = updatedAt!.toIso8601String();
    if (strength != null) data['strength'] = strength;
    return data;
  }

  @override
  String toString() {
    return 'RelationshipModel(id: $id, sourceId: $sourceId, targetId: $targetId, type: $type, description: $description, createdAt: $createdAt, updatedAt: $updatedAt, strength: $strength)';
  }
}
