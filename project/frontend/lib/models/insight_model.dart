class InsightModel {
  final String? id;
  final String title;
  final String? description;
  final DateTime? createdAt;
  final DateTime? updatedAt;
  final List<String>? tags;
  final String? category;
  final String? source;
  final double? importance;

  InsightModel({
    this.id,
    required this.title,
    this.description,
    this.createdAt,
    this.updatedAt,
    this.tags,
    this.category,
    this.source,
    this.importance,
  });

  // Cria uma cópia do insight com algumas propriedades alteradas
  InsightModel copyWith({
    String? id,
    String? title,
    String? description,
    DateTime? createdAt,
    DateTime? updatedAt,
    List<String>? tags,
    String? category,
    String? source,
    double? importance,
  }) {
    return InsightModel(
      id: id ?? this.id,
      title: title ?? this.title,
      description: description ?? this.description,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      tags: tags ?? this.tags,
      category: category ?? this.category,
      source: source ?? this.source,
      importance: importance ?? this.importance,
    );
  }

  // Cria um insight a partir de um Map/JSON
  factory InsightModel.fromJson(Map<String, dynamic> json) {
    return InsightModel(
      id: json['id'],
      title: json['title'],
      description: json['description'],
      createdAt: json['createdAt'] != null ? DateTime.parse(json['createdAt']) : null,
      updatedAt: json['updatedAt'] != null ? DateTime.parse(json['updatedAt']) : null,
      tags: json['tags'] != null ? List<String>.from(json['tags']) : null,
      category: json['category'],
      source: json['source'],
      importance: json['importance'] != null ? json['importance'].toDouble() : null,
    );
  }

  // Converte o insight para Map/JSON
  Map<String, dynamic> toJson() {
    final Map<String, dynamic> data = <String, dynamic>{};
    if (id != null) data['id'] = id;
    data['title'] = title;
    if (description != null) data['description'] = description;
    if (createdAt != null) data['createdAt'] = createdAt!.toIso8601String();
    if (updatedAt != null) data['updatedAt'] = updatedAt!.toIso8601String();
    if (tags != null) data['tags'] = tags;
    if (category != null) data['category'] = category;
    if (source != null) data['source'] = source;
    if (importance != null) data['importance'] = importance;
    return data;
  }

  @override
  String toString() {
    return 'InsightModel(id: $id, title: $title, description: $description, createdAt: $createdAt, updatedAt: $updatedAt, tags: $tags, category: $category, source: $source, importance: $importance)';
  }
}
