import 'dart:math';

import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:uuid/uuid.dart';

/// Model for a mind map node
class MindMapNode {
  final String id;
  String title;
  String? description;
  Color? color;
  Offset position;
  double width;
  double height;

  MindMapNode({
    String? id,
    required this.title,
    this.description,
    this.color,
    required this.position,
    this.width = 150,
    this.height = 80,
  }) : id = id ?? const Uuid().v4();
}

/// Model for a connection between nodes
class NodeConnection {
  final String id;
  final String sourceId;
  final String targetId;
  String? label;

  NodeConnection({
    String? id,
    required this.sourceId, 
    required this.targetId,
    this.label,
  }) : id = id ?? const Uuid().v4();
}

/// Controller for managing mind maps
class MindMapController extends GetxController {
  final nodes = <MindMapNode>[].obs;
  final connections = <NodeConnection>[].obs;
  final selectedNodeId = RxnString();
  final selectedConnectionId = RxnString();
  final Rx<Offset> viewOffset = Offset.zero.obs;
  final Rx<double> viewScale = 1.0.obs;
  
  /// Add a new node to the mind map
  void addNode({
    required String title,
    String? description,
    Color? color,
    required Offset position,
    double? width,
    double? height,
  }) {
    final node = MindMapNode(
      title: title,
      description: description,
      color: color,
      position: position,
      width: width ?? 150,
      height: height ?? 80,
    );
    nodes.add(node);
    update();
  }
  
  /// Update an existing node
  void updateNode({
    required String id,
    String? title,
    String? description,
    Color? color,
    Offset? position,
    double? width,
    double? height,
  }) {
    final index = nodes.indexWhere((node) => node.id == id);
    if (index == -1) return;
    
    final node = nodes[index];
    nodes[index] = MindMapNode(
      id: id,
      title: title ?? node.title,
      description: description ?? node.description,
      color: color ?? node.color,
      position: position ?? node.position,
      width: width ?? node.width,
      height: height ?? node.height,
    );
    update();
  }
  
  /// Remove a node and its connections
  void removeNode(String id) {
    nodes.removeWhere((node) => node.id == id);
    connections.removeWhere(
      (connection) => connection.sourceId == id || connection.targetId == id
    );
    
    if (selectedNodeId.value == id) {
      selectedNodeId.value = null;
    }
    update();
  }
  
  /// Select a node
  void selectNode(String? id) {
    selectedNodeId.value = id;
    selectedConnectionId.value = null;
  }
  
  /// Get a node by its ID
  MindMapNode? getNodeById(String id) {
    try {
      return nodes.firstWhere((node) => node.id == id);
    } catch (e) {
      return null;
    }
  }
  
  /// Connect two nodes
  void connectNodes({
    required String sourceId,
    required String targetId,
    String? label,
  }) {
    // Check if both nodes exist
    final sourceExists = nodes.any((node) => node.id == sourceId);
    final targetExists = nodes.any((node) => node.id == targetId);
    
    if (!sourceExists || !targetExists) return;
    
    // Check if connection already exists
    final connectionExists = connections.any(
      (connection) => 
        connection.sourceId == sourceId && connection.targetId == targetId
    );
    
    if (!connectionExists) {
      connections.add(NodeConnection(
        sourceId: sourceId,
        targetId: targetId,
        label: label,
      ));
      update();
    }
  }
  
  /// Remove a connection
  void removeConnection(String id) {
    connections.removeWhere((connection) => connection.id == id);
    
    if (selectedConnectionId.value == id) {
      selectedConnectionId.value = null;
    }
    update();
  }
  
  /// Select a connection
  void selectConnection(String? id) {
    selectedConnectionId.value = id;
    selectedNodeId.value = null;
  }
  
  /// Move a node to a new position
  void moveNode(String id, Offset position) {
    final index = nodes.indexWhere((node) => node.id == id);
    if (index == -1) return;
    
    final node = nodes[index];
    nodes[index] = MindMapNode(
      id: id,
      title: node.title,
      description: node.description,
      color: node.color,
      position: position,
      width: node.width,
      height: node.height,
    );
    update();
  }
  
  /// Apply auto-layout to organize the mind map
  void applyAutoLayout() {
    // Simple radial layout implementation
    if (nodes.isEmpty) return;
    
    final centerX = 0.0;
    final centerY = 0.0;
    final radius = 300.0;
    
    if (nodes.length == 1) {
      moveNode(nodes[0].id, Offset(centerX, centerY));
      return;
    }
    
    for (int i = 0; i < nodes.length; i++) {
      final angle = (2 * 3.14159 * i) / nodes.length;
      final x = centerX + radius * cos(angle);
      final y = centerY + radius * sin(angle);
      moveNode(nodes[i].id, Offset(x, y));
    }
    
    update();
  }
  
  /// Update view transformation (pan and zoom)
  void updateViewTransform({Offset? offset, double? scale}) {
    if (offset != null) viewOffset.value = offset;
    if (scale != null) viewScale.value = scale;
  }
  
  /// Clear the mind map
  void clear() {
    nodes.clear();
    connections.clear();
    selectedNodeId.value = null;
    selectedConnectionId.value = null;
    viewOffset.value = Offset.zero;
    viewScale.value = 1.0;
    update();
  }
  
  /// Get the data representation of the mind map for saving
  Map<String, dynamic> toJson() {
    return {
      'nodes': nodes.map((node) => {
        'id': node.id,
        'title': node.title,
        'description': node.description,
        'color': node.color?.value,
        'position': {
          'x': node.position.dx,
          'y': node.position.dy,
        },
        'width': node.width,
        'height': node.height,
      }).toList(),
      'connections': connections.map((connection) => {
        'id': connection.id,
        'sourceId': connection.sourceId,
        'targetId': connection.targetId,
        'label': connection.label,
      }).toList(),
    };
  }
  
  /// Load mind map from saved data
  void fromJson(Map<String, dynamic> data) {
    clear();
    
    final nodeList = (data['nodes'] as List?)?.cast<Map<String, dynamic>>();
    final connectionList = (data['connections'] as List?)?.cast<Map<String, dynamic>>();
    
    if (nodeList != null) {
      for (final nodeData in nodeList) {
        final posData = nodeData['position'] as Map<String, dynamic>;
        nodes.add(MindMapNode(
          id: nodeData['id'],
          title: nodeData['title'],
          description: nodeData['description'],
          color: nodeData['color'] != null ? Color(nodeData['color']) : null,
          position: Offset(posData['x'], posData['y']),
          width: nodeData['width'] ?? 150,
          height: nodeData['height'] ?? 80,
        ));
      }
    }
    
    if (connectionList != null) {
      for (final connectionData in connectionList) {
        connections.add(NodeConnection(
          id: connectionData['id'],
          sourceId: connectionData['sourceId'],
          targetId: connectionData['targetId'],
          label: connectionData['label'],
        ));
      }
    }
    
    update();
  }
}
