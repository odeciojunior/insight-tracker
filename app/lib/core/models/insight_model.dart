import 'package:cloud_firestore/cloud_firestore.dart';

class InsightModel {
  final String id;
  final String title;
  final String content;
  final List<String> tags;
  final DateTime createdAt;
  final DateTime? updatedAt;
  final String userId;
  
  InsightModel({
    required this.id,
    required this.title,
    required this.content,
    required this.tags,
    required this.createdAt,
    this.updatedAt,
    required this.userId,
  });

  Map<String, dynamic> toMap() {
    return {
      'title': title,
      'content': content,
      'tags': tags,
      'createdAt': Timestamp.fromDate(createdAt),
      'updatedAt': updatedAt != null ? Timestamp.fromDate(updatedAt!) : null,
      'userId': userId,
    };
  }

  factory InsightModel.fromMap(Map<String, dynamic> map, String documentId) {
    return InsightModel(
      id: documentId,
      title: map['title'] ?? '',
      content: map['content'] ?? '',
      tags: List<String>.from(map['tags'] ?? []),
      createdAt: (map['createdAt'] as Timestamp?)?.toDate() ?? DateTime.now(),
      updatedAt: (map['updatedAt'] as Timestamp?)?.toDate(),
      userId: map['userId'] ?? '',
    );
  }

  InsightModel copyWith({
    String? id,
    String? title,
    String? content,
    List<String>? tags,
    DateTime? createdAt,
    DateTime? updatedAt,
    String? userId,
  }) {
    return InsightModel(
      id: id ?? this.id,
      title: title ?? this.title,
      content: content ?? this.content,
      tags: tags ?? this.tags,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      userId: userId ?? this.userId,
    );
  }
}
