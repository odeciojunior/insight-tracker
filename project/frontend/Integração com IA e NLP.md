# Integração com IA e NLP

## Problemas Identificados

### 1. Funcionalidades de IA não Implementadas

Embora o projeto seja descrito como tendo capacidades de IA, as implementações estão ausentes:

- **Classificação Automática**: A documentação menciona "classificação automática de insights", mas não há código que implemente essa funcionalidade.
- **Relacionamento Semântico**: O sistema deveria estabelecer "conexões semânticas entre ideias relacionadas", mas essa funcionalidade não está implementada.
- **Assistente IA Personalizado**: A documentação destaca um "pipeline de IA para aprendizado contínuo e assistência personalizada", mas não há implementação.

### 2. Estrutura para NLP Incompleta

A estrutura para processamento de linguagem natural está apenas definida nos diretórios, sem implementação:

```
backend/
└── app/
    └── services/
        ├── nlp/
        │   ├── __init__.py
        │   ├── classification.py   # Vazio
        │   ├── embeddings.py       # Vazio
        │   └── relationship.py     # Vazio
        └── ai/
            ├── __init__.py
            ├── training.py         # Vazio
            └── recommendation.py   # Vazio
```

### 3. Ausência de Integração com Modelos de IA

Não há integração com ferramentas ou bibliotecas de IA:

- Sem integração com bibliotecas como TensorFlow, PyTorch, ou scikit-learn
- Sem utilização de modelos pré-treinados como BERT, GPT, ou sistemas de embeddings
- Ausência de APIs de serviços de IA de terceiros

### 4. Função de Transcrição de Áudio Limitada

O aplicativo inclui um gravador de áudio, mas as capacidades de transcrição são limitadas:

- Utiliza apenas APIs básicas de reconhecimento de voz local
- Não há processamento pós-transcrição (normalização, sumarização, extração de entidades)
- Não integra com serviços de transcrição mais robustos

## Soluções Propostas

### 1. Implementar Classificação Automática de Insights

#### Criar Serviço de Classificação no Frontend

```dart
// lib/services/nlp_service.dart
import 'package:get/get.dart';
import 'package:dio/dio.dart';
import '../app/data/models/insight.dart';
import '../app/data/models/category.dart';

class NLPService extends GetxService {
  final Dio _dio;
  final RxBool isProcessing = false.obs;
  
  NLPService({Dio? dio}) : _dio = dio ?? Dio();
  
  // Classificação automática de categoria
  Future<String?> suggestCategory(String title, String content) async {
    try {
      isProcessing.value = true;
      
      // Opção 1: Usar API externa
      final response = await _dio.post(
        'https://api.example.com/classify',
        data: {
          'title': title,
          'content': content,
        },
      );
      
      final categoryId = response.data['categoryId'];
      return categoryId;
      
      // Opção 2: Implementação local com regras básicas
      /*
      final text = (title + ' ' + content).toLowerCase();
      final categories = Get.find<CategoryController>().categories;
      
      // Regras simples de correspondência de palavras-chave
      for (final category in categories) {
        if (category.name.toLowerCase() == 'work' && 
            (text.contains('work') || text.contains('job') || text.contains('office'))) {
          return category.id;
        } else if (category.name.toLowerCase() == 'personal' && 
            (text.contains('personal') || text.contains('family') || text.contains('friend'))) {
          return category.id;
        } else if (category.name.toLowerCase() == 'ideas' && 
            (text.contains('idea') || text.contains('concept') || text.contains('innovation'))) {
          return category.id;
        }
      }
      
      return null;
      */
    } catch (e) {
      print('Error suggesting category: $e');
      return null;
    } finally {
      isProcessing.value = false;
    }
  }
  
  // Extração de tags
  Future<List<String>> extractTags(String title, String content) async {
    try {
      isProcessing.value = true;
      
      // Opção 1: Usar API externa
      final response = await _dio.post(
        'https://api.example.com/extract-tags',
        data: {
          'title': title,
          'content': content,
        },
      );
      
      final tags = List<String>.from(response.data['tags']);
      return tags;
      
      // Opção 2: Implementação local com TF-IDF simples
      /*
      final text = (title + ' ' + content).toLowerCase();
      final words = text.split(RegExp(r'\W+'))
          .where((word) => word.length > 3)
          .toList();
          
      // Lista de stop words
      final stopWords = ['this', 'that', 'there', 'here', 'where', 'when',
                        'how', 'what', 'why', 'who', 'which', 'whom'];
                        
      // Remover stop words e contar frequência
      final wordCount = <String, int>{};
      for (final word in words) {
        if (!stopWords.contains(word)) {
          wordCount[word] = (wordCount[word] ?? 0) + 1;
        }
      }
      
      // Ordenar por frequência e selecionar os top N
      final sortedWords = wordCount.entries.toList()
        ..sort((a, b) => b.value.compareTo(a.value));
        
      final topTags = sortedWords
          .take(5)
          .map((e) => e.key)
          .toList();
          
      return topTags;
      */
    } catch (e) {
      print('Error extracting tags: $e');
      return [];
    } finally {
      isProcessing.value = false;
    }
  }
}
```

#### Integrar Classificação na Tela de Captura

```dart
// lib/app/modules/capture/capture_page.dart
// Adicionar ao método initState

@override
void initState() {
  super.initState();
  
  // Escutar mudanças no conteúdo para sugerir categorias e tags
  _contentController.addListener(_processContent);
  
  // Resto do código existente...
}

void _processContent() {
  // Somente processar quando houver conteúdo suficiente
  final content = _contentController.text;
  final title = _titleController.text;
  
  if (content.length > 50 && !_isProcessingContent) {
    _isProcessingContent = true;
    
    final nlpService = Get.find<NLPService>();
    
    // Sugerir categoria
    if (_selectedCategoryId == null) {
      nlpService.suggestCategory(title, content).then((categoryId) {
        if (categoryId != null && mounted) {
          setState(() {
            _selectedCategoryId = categoryId;
          });
          
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Category automatically suggested'),
              duration: Duration(seconds: 2),
            ),
          );
        }
      });
    }
    
    // Extrair tags
    if (_tags.isEmpty) {
      nlpService.extractTags(title, content).then((suggestedTags) {
        if (suggestedTags.isNotEmpty && mounted) {
          _showTagSuggestions(suggestedTags);
        }
      });
    }
    
    Future.delayed(const Duration(seconds: 2), () {
      _isProcessingContent = false;
    });
  }
}

void _showTagSuggestions(List<String> suggestedTags) {
  showModalBottomSheet(
    context: context,
    builder: (context) => Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        ListTile(
          title: const Text('Suggested Tags'),
          subtitle: const Text('Select tags to add to your insight'),
        ),
        const Divider(),
        Wrap(
          spacing: 8,
          children: suggestedTags.map((tag) => ActionChip(
            label: Text(tag),
            onPressed: () {
              setState(() {
                if (!_tags.contains(tag)) {
                  _tags.add(tag);
                }
              });
            },
          )).toList(),
        ),
        const SizedBox(height: 16),
      ],
    ),
  );
}
```

### 2. Implementar Relacionamento Semântico entre Insights

#### Criar Serviço de Relacionamento

```dart
// lib/services/relationship_service.dart
import 'package:get/get.dart';
import 'package:dio/dio.dart';
import '../app/data/models/insight.dart';
import '../app/data/models/relationship.dart';

class RelationshipService extends GetxService {
  final Dio _dio;
  final RxBool isProcessing = false.obs;
  
  RelationshipService({Dio? dio}) : _dio = dio ?? Dio();
  
  // Encontrar insights relacionados
  Future<List<String>> findRelatedInsights(String insightId, String content) async {
    try {
      isProcessing.value = true;
      
      // Opção 1: Usar API externa
      final response = await _dio.post(
        'https://api.example.com/find-related',
        data: {
          'insightId': insightId,
          'content': content,
        },
      );
      
      final relatedIds = List<String>.from(response.data['relatedIds']);
      return relatedIds;
      
      // Opção 2: Implementação local com similaridade de cosseno
      /*
      final insightController = Get.find<InsightController>();
      final allInsights = await insightController.loadInsights();
      
      // Ignorar o próprio insight
      final otherInsights = allInsights
          .where((insight) => insight.id != insightId)
          .toList();
          
      // Implementação simplificada de similaridade
      final List<Map<String, dynamic>> similarities = [];
      
      for (final other in otherInsights) {
        final similarity = _calculateSimilarity(content, other.content);
        
        if (similarity > 0.3) { // Limite de similaridade
          similarities.add({
            'id': other.id,
            'similarity': similarity,
          });
        }
      }
      
      // Ordenar por similaridade
      similarities.sort((a, b) => b['similarity'].compareTo(a['similarity']));
      
      // Retornar os top N mais similares
      return similarities
          .take(5)
          .map((e) => e['id'] as String)
          .toList();
      */
    } catch (e) {
      print('Error finding related insights: $e');
      return [];
    } finally {
      isProcessing.value = false;
    }
  }
  
  // Detectar tipo de relacionamento
  Future<RelationshipType> detectRelationshipType(
    String sourceContent, 
    String targetContent
  ) async {
    try {
      isProcessing.value = true;
      
      // Opção 1: Usar API externa
      final response = await _dio.post(
        'https://api.example.com/relationship-type',
        data: {
          'sourceContent': sourceContent,
          'targetContent': targetContent,
        },
      );
      
      final typeString = response.data['type'];
      return _stringToRelationshipType(typeString);
      
      // Opção 2: Implementação local simples
      /*
      // Detectar se há palavras que indicam causalidade
      final sourceText = sourceContent.toLowerCase();
      final targetText = targetContent.toLowerCase();
      
      final causalWords = ['because', 'cause', 'effect', 'result', 'therefore'];
      final supportWords = ['support', 'agree', 'confirm', 'reinforce'];
      final contradictWords = ['but', 'however', 'contrary', 'disagree', 'oppose'];
      
      for (final word in causalWords) {
        if (sourceText.contains(word) || targetText.contains(word)) {
          return RelationshipType.causes;
        }
      }
      
      for (final word in supportWords) {
        if (sourceText.contains(word) || targetText.contains(word)) {
          return RelationshipType.supports;
        }
      }
      
      for (final word in contradictWords) {
        if (sourceText.contains(word) || targetText.contains(word)) {
          return RelationshipType.contradicts;
        }
      }
      
      return RelationshipType.related;
      */
    } catch (e) {
      print('Error detecting relationship type: $e');
      return RelationshipType.related; // Tipo padrão
    } finally {
      isProcessing.value = false;
    }
  }
  
  // Converter string para enum RelationshipType
  RelationshipType _stringToRelationshipType(String type) {
    switch (type.toLowerCase()) {
      case 'causes': 
        return RelationshipType.causes;
      case 'supports': 
        return RelationshipType.supports;
      case 'contradicts': 
        return RelationshipType.contradicts;
      case 'extends': 
        return RelationshipType.extend;
      case 'related':
      default: 
        return RelationshipType.related;
    }
  }
  
  // Implementação simplificada de similaridade de cosseno
  double _calculateSimilarity(String text1, String text2) {
    final words1 = _tokenize(text1);
    final words2 = _tokenize(text2);
    
    final allWords = {...words1, ...words2};
    
    // Vetorizar
    final vector1 = <double>[];
    final vector2 = <double>[];
    
    for (final word in allWords) {
      vector1.add(words1.contains(word) ? 1.0 : 0.0);
      vector2.add(words2.contains(word) ? 1.0 : 0.0);
    }
    
    // Calcular similaridade de cosseno
    double dotProduct = 0;
    double magnitude1 = 0;
    double magnitude2 = 0;
    
    for (int i = 0; i < vector1.length; i++) {
      dotProduct += vector1[i] * vector2[i];
      magnitude1 += vector1[i] * vector1[i];
      magnitude2 += vector2[i] * vector2[i];
    }
    
    magnitude1 = magnitude1 > 0 ? sqrt(magnitude1) : 0;
    magnitude2 = magnitude2 > 0 ? sqrt(magnitude2) : 0;
    
    if (magnitude1 > 0 && magnitude2 > 0) {
      return dotProduct / (magnitude1 * magnitude2);
    }
    
    return 0;
  }
  
  // Tokenizar texto em palavras
  Set<String> _tokenize(String text) {
    final stopWords = ['the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'with'];
    
    return text
        .toLowerCase()
        .replaceAll(RegExp(r'[^\w\s]'), '')
        .split(RegExp(r'\s+'))
        .where((word) => word.length > 2 && !stopWords.contains(word))
        .toSet();
  }
}
```

#### Integrar no MindmapController

```dart
// lib/app/controllers/mindmap_controller.dart
// Adicionar método para sugerir conexões

Future<void> suggestConnections(String insightId) async {
  try {
    final insightController = Get.find<InsightController>();
    final relationshipService = Get.find<RelationshipService>();
    
    // Obter o insight atual
    final insight = await insightController.getInsight(insightId);
    if (insight == null) return;
    
    // Encontrar insights relacionados
    final relatedIds = await relationshipService.findRelatedInsights(
      insightId, insight.content);
    
    if (relatedIds.isEmpty) return;
    
    // Para cada insight relacionado, carregar e criar nós
    for (final relatedId in relatedIds) {
      final relatedInsight = await insightController.getInsight(relatedId);
      if (relatedInsight == null) continue;
      
      // Criar nó se não existir
      if (!nodes.any((node) => node.id == relatedId)) {
        // Calcular posição para o novo nó
        final sourceNode = getNodeById(insightId);
        if (sourceNode == null) continue;
        
        final angle = 2 * pi * (nodes.length % 6) / 6;
        final x = sourceNode.position.dx + 200 * cos(angle);
        final y = sourceNode.position.dy + 200 * sin(angle);
        
        addNode(
          title: relatedInsight.title,
          description: relatedInsight.content.substring(
            0, min(100, relatedInsight.content.length)),
          position: Offset(x, y),
          color: _getCategoryColor(relatedInsight.categoryId),
        );
      }
      
      // Detectar tipo de relacionamento
      final relationshipType = await relationshipService.detectRelationshipType(
        insight.content, relatedInsight.content);
      
      // Criar conexão se não existir
      if (!connections.any((conn) => 
          conn.sourceId == insightId && conn.targetId == relatedId)) {
        connectNodes(
          sourceId: insightId,
          targetId: relatedId,
          label: _getRelationshipLabel(relationshipType),
        );
      }
    }
    
    update();
  } catch (e) {
    print('Error suggesting connections: $e');
  }
}

String _getRelationshipLabel(RelationshipType type) {
  switch (type) {
    case RelationshipType.causes:
      return 'Causes';
    case RelationshipType.supports:
      return 'Supports';
    case RelationshipType.contradicts:
      return 'Contradicts';
    case RelationshipType.extend:
      return 'Extends';
    case RelationshipType.related:
    default:
      return 'Related';
  }
}

Color _getCategoryColor(String? categoryId) {
  if (categoryId == null) return Colors.grey;
  
  final categoryController = Get.find<CategoryController>();
  final category = categoryController.getCategoryById(categoryId);
  
  return category?.color ?? Colors.grey;
}
```

### 3. Implementar Transcrição de Áudio Avançada

#### Melhorar o RecorderController

```dart
// lib/app/controllers/recorder_controller.dart
// Adicionar métodos para transcrição avançada

Future<String> transcribeAudio(String? filePath) async {
  if (filePath == null) return '';
  
  try {
    isLoading.value = true;
    
    // Opção 1: Usar API externa
    final dio = Get.find<Dio>();
    
    // Criar formulário multipart
    final formData = FormData.fromMap({
      'audio': await MultipartFile.fromFile(filePath),
      'model': 'whisper-1',
      'language': 'en',
    });
    
    final response = await dio.post(
      'https://api.example.com/transcribe',
      data: formData,
    );
    
    final transcription = response.data['text'];
    transcribedText.value = transcription;
    return transcription;
    
    // Opção 2: Continuar usando o reconhecimento local
    /*
    // Código atual da transcrição
    return transcribedText.value;
    */
  } catch (e) {
    debugPrint('Error transcribing audio: $e');
    return '';
  } finally {
    isLoading.value = false;
  }
}

Future<Map<String, dynamic>> analyzeTranscription(String text) async {
  if (text.isEmpty) return {};
  
  try {
    isLoading.value = true;
    
    final dio = Get.find<Dio>();
    final response = await dio.post(
      'https://api.example.com/analyze-text',
      data: {
        'text': text,
      },
    );
    
    return Map<String, dynamic>.from(response.data);
  } catch (e) {
    debugPrint('Error analyzing transcription: $e');
    return {};
  } finally {
    isLoading.value = false;
  }
}

Future<void> enhanceTranscription() async {
  if (transcribedText.value.isEmpty) return;
  
  try {
    isLoading.value = true;
    
    final dio = Get.find<Dio>();
    final response = await dio.post(
      'https://api.example.com/enhance-text',
      data: {
        'text': transcribedText.value,
      },
    );
    
    final enhancedText = response.data['enhanced_text'];
    transcribedText.value = enhancedText;
  } catch (e) {
    debugPrint('Error enhancing transcription: $e');
  } finally {
    isLoading.value = false;
  }
}
```

#### Integrar na Interface de Captura

```dart
// lib/app/modules/capture/capture_page.dart
// Adicionar opções para a transcrição avançada

Widget _buildTranscriptionTools() {
  return Obx(() {
    if (_recorderController.transcribedText.value.isEmpty) {
      return const SizedBox.shrink();
    }
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const Divider(),
        Text(
          'Transcription',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 8),
        Text(_recorderController.transcribedText.value),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: AppButton(
                text: 'Use as Content',
                icon: Icons.check,
                onPressed: () {
                  _contentController.text = 
                      _recorderController.transcribedText.value;
                },
                type: AppButtonType.secondary,
                size: AppButtonSize.small,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: AppButton(
                text: 'Enhance Text',
                icon: Icons.auto_fix_high,
                onPressed: () {
                  _recorderController.enhanceTranscription();
                },
                type: AppButtonType.secondary,
                size: AppButtonSize.small,
                isLoading: _recorderController.isLoading.value,
              ),
            ),
          ],
        ),
      ],
    );
  });
}
```

### 4. Implementar um Assistente IA Personalizado

#### Criar Serviço de Assistente IA

```dart
// lib/services/ai_assistant_service.dart
import 'package:get/get.dart';
import 'package:dio/dio.dart';
import '../app/data/models/insight.dart';

class AIAssistantService extends GetxService {
  final Dio _dio;
  final RxBool isProcessing = false.obs;
  final RxString assistantMessage = ''.obs;
  
  AIAssistantService({Dio? dio}) : _dio = dio ?? Dio();
  
  // Gerar sugestões de insights
  Future<List<String>> suggestInsightTopics() async {
    try {
      isProcessing.value = true;
      
      final insightController = Get.find<InsightController>();
      final insights = await insightController.loadInsights();
      
      // Extrair tópicos dos insights existentes
      final topics = <String>[];
      for (final insight in insights) {
        topics.add(insight.title);
        topics.addAll(insight.tags);
      }
      
      // Enviar tópicos para API de IA
      final response = await _dio.post(
        'https://api.example.com/suggest-topics',
        data: {
          'existing_topics': topics,
        },
      );
      
      final suggestions = List<String>.from(response.data['suggestions']);
      return suggestions;
    } catch (e) {
      print('Error suggesting topics: $e');
      return [];
    } finally {
      isProcessing.value = false;
    }
  }
  
  // Expandir um insight
  Future<String> expandInsight(String content) async {
    try {
      isProcessing.value = true;
      
      final response = await _dio.post(
        'https://api.example.com/expand-insight',
        data: {
          'content': content,
        },
      );
      
      final expandedContent = response.data['expanded_content'];
      return expandedContent;
    } catch (e) {
      print('Error expanding insight: $e');
      return content;
    } finally {
      isProcessing.value = false;
    }
  }
  
  // Analisar insights para encontrar padrões
  Future<Map<String, dynamic>> analyzeInsights() async {
    try {
      isProcessing.value = true;
      
      final insightController = Get.find<InsightController>();
      final insights = await insightController.loadInsights();
      
      // Preparar dados para enviar à API
      final insightData = insights.map((insight) => {
        'id': insight.id,
        'title': insight.title,
        'content': insight.content,
        'category': insight.categoryId,
        'tags': insight.tags,
        'created_at': insight.createdAt.toIso8601String(),
      }).toList();
      
      final response = await _dio.post(
        'https://api.example.com/analyze-insights',
        data: {
          'insights': insightData,
        },
      );
      
      return Map<String, dynamic>.from(response.data);
    } catch (e) {
      print('Error analyzing insights: $e');
      return {};
    } finally {
      isProcessing.value = false;
    }
  }
  
  // Obter mensagem personalizada do assistente
  Future<String> getAssistantMessage() async {
    try {
      isProcessing.value = true;
      
      final insightController = Get.find<InsightController>();
      final insights = await insightController.loadInsights();
      
      // Sem insights, retornar mensagem padrão
      if (insights.isEmpty) {
        return "Welcome! Start by capturing your first insight by tapping the + button.";
      }
      
      // Analisar padrões de uso
      final latestInsight = insights.reduce(
        (a, b) => a.createdAt.isAfter(b.createdAt) ? a : b);
      
      final insightsByCategory = <String?, List<Insight>>{};
      for (final insight in insights) {
        if (!insightsByCategory.containsKey(insight.categoryId)) {
          insightsByCategory[insight.categoryId] = [];
        }
        insightsByCategory[insight.categoryId]!.add(insight);
      }
      
      final topCategory = insightsByCategory.entries
          .reduce((a, b) => a.value.length > b.value.length ? a : b)
          .key;
      
      // Enviar dados para API de IA
      final response = await _dio.post(
        'https://api.example.com/assistant-message',
        data: {
          'latest_insight': {
            'title': latestInsight.title,
            'content': latestInsight.content,
          },
          'top_category': topCategory,
          'total_insights': insights.length,
        },
      );
      
      final message = response.data['message'];
      assistantMessage.value = message;
      return message;
    } catch (e) {
      print('Error getting assistant message: $e');
      
      // Mensagem de fallback
      final fallback = "I notice you've been capturing insights regularly. "
          "Keep up the good work!";
          
      assistantMessage.value = fallback;
      return fallback;
    } finally {
      isProcessing.value = false;
    }
  }
}
```

#### Criar Widget de Assistente IA

```dart
// lib/core/widgets/ai_assistant_widget.dart
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../services/ai_assistant_service.dart';

class AIAssistantWidget extends StatelessWidget {
  const AIAssistantWidget({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final aiAssistantService = Get.find<AIAssistantService>();
    
    return Obx(() {
      final message = aiAssistantService.assistantMessage.value;
      
      if (message.isEmpty) {
        return const SizedBox.shrink();
      }
      
      return Card(
        margin: const EdgeInsets.all(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const CircleAvatar(
                    backgroundColor: Colors.purple,
                    child: Icon(Icons.assistant, color: Colors.white),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    'AI Assistant',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Text(message),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                children: [
                  ActionChip(
                    avatar: const Icon(Icons.lightbulb_outline, size: 16),
                    label: const Text('Suggest Topics'),
                    onPressed: () => _showSuggestedTopics(context),
                  ),
                  ActionChip(
                    avatar: const Icon(Icons.analytics_outlined, size: 16),
                    label: const Text('Analyze Insights'),
                    onPressed: () => _showInsightAnalysis(context),
                  ),
                ],
              ),
            ],
          ),
        ),
      );
    });
  }
  
  void _showSuggestedTopics(BuildContext context) async {
    final aiAssistantService = Get.find<AIAssistantService>();
    
    final topics = await aiAssistantService.suggestInsightTopics();
    
    if (topics.isEmpty) return;
    
    Get.bottomSheet(
      Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color:# Integração com IA e NLP (continuação)

```dart
    Get.bottomSheet(
      Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surface,
          borderRadius: const BorderRadius.vertical(
            top: Radius.circular(16),
          ),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Suggested Topics',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            const Text(
              'Here are some topics based on your insights pattern:',
            ),
            const SizedBox(height: 16),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: topics.map((topic) => ActionChip(
                label: Text(topic),
                onPressed: () {
                  // Navegar para a página de captura com o tópico pré-preenchido
                  Get.back();
                  Get.toNamed('/capture', arguments: {'topic': topic});
                },
              )).toList(),
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: TextButton(
                onPressed: () => Get.back(),
                child: const Text('Close'),
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  void _showInsightAnalysis(BuildContext context) async {
    final aiAssistantService = Get.find<AIAssistantService>();
    
    final analysis = await aiAssistantService.analyzeInsights();
    
    if (analysis.isEmpty) return;
    
    Get.dialog(
      AlertDialog(
        title: const Text('Insight Analysis'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Principais temas
              if (analysis.containsKey('themes')) ...[
                Text(
                  'Main Themes',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  children: (analysis['themes'] as List)
                      .map((theme) => Chip(label: Text(theme.toString())))
                      .toList(),
                ),
                const SizedBox(height: 16),
              ],
              
              // Padrões temporais
              if (analysis.containsKey('temporal_patterns')) ...[
                Text(
                  'Temporal Patterns',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 8),
                Text(analysis['temporal_patterns'].toString()),
                const SizedBox(height: 16),
              ],
              
              // Recomendações
              if (analysis.containsKey('recommendations')) ...[
                Text(
                  'Recommendations',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 8),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: (analysis['recommendations'] as List)
                      .map((rec) => Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: Text('• $rec'),
                      ))
                      .toList(),
                ),
              ],
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Get.back(),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }
}
```

#### Integrar o Assistente na Página Principal

```dart
// lib/app/modules/home/home_page.dart
// Adicionar o widget de assistente antes da lista de insights

@override
Widget build(BuildContext context) {
  final insightController = Get.find<InsightController>();
  final aiAssistantService = Get.find<AIAssistantService>();

  // Carregar mensagem do assistente ao abrir a página
  useEffect(() {
    aiAssistantService.getAssistantMessage();
    return null;
  }, []);

  return Scaffold(
    appBar: AppBar(
      title: const Text('Insight Tracker'),
      actions: [
        // Ações existentes...
      ],
    ),
    body: Obx(() {
      if (insightController.isLoading.value) {
        return const LoadingIndicator(message: 'Loading insights...');
      }

      return Column(
        children: [
          // Assistente IA
          const AIAssistantWidget(),
          
          // Lista de insights
          Expanded(
            child: insightController.insights.isEmpty
                ? _buildEmptyState()
                : ListView.builder(
                    itemCount: insightController.insights.length,
                    itemBuilder: (context, index) {
                      // Código existente...
                    },
                  ),
          ),
        ],
      );
    }),
    floatingActionButton: FloatingActionButton(
      onPressed: () {
        Get.toNamed(AppRoutes.CAPTURE);
      },
      child: const Icon(Icons.add),
    ),
  );
}
```

## Priorização de Ações

1. **Alta prioridade**: Implementar classificação automática de insights
   - Criar serviço NLP básico
   - Integrar sugestão de categorias na tela de captura
   - Adicionar extração de tags

2. **Alta prioridade**: Melhorar transcrição de áudio
   - Aprimorar a funcionalidade de transcrição existente
   - Adicionar opções para pós-processamento do texto
   - Melhorar a interface de captura de áudio

3. **Média prioridade**: Implementar o relacionamento semântico
   - Criar serviço de relacionamento
   - Integrar na visualização de mindmap
   - Implementar detecção de tipos de relacionamento

4. **Média prioridade**: Implementar assistente IA
   - Criar serviço de assistente
   - Desenvolver widget de interface do assistente
   - Integrar na página principal
   - Adicionar recursos de sugestão e análise

## Impacto da Implementação

- **Experiência do Usuário**: Simplificação do processo de captura com sugestões automáticas
- **Valor da Aplicação**: Descoberta de insights não óbvios através de relacionamentos semânticos
- **Produtividade**: Melhoria na eficiência do usuário com assistência personalizada
- **Diferenciação**: Funcionalidades de IA como diferencial competitivo

## Integrações Externas Recomendadas

Em vez de implementar toda a lógica de IA/NLP localmente, considere integrar com serviços de terceiros:

1. **OpenAI API**: Para classificação, relacionamento semântico e assistente
2. **Google Cloud Speech-to-Text API**: Para transcrição avançada
3. **Hugging Face**: Para modelos de NLP pré-treinados
4. **Google TensorFlow.js**: Para execução local de modelos leves de IA

## Documentação Recomendada

Adicionar documentação para:
- Arquitetura de IA e NLP
- Fluxo de processamento de texto e áudio
- Guia de integração com serviços externos
- Exemplos de uso das funcionalidades de IA
- Limitações e considerações para dispositivos móveis

# Testes e Qualidade de Código

## Problemas Identificados

### 1. Falta de Testes Automatizados

O projeto não contém testes automatizados, apesar de ter as dependências configuradas:

```yaml
dev_dependencies:
  flutter_test:
    sdk: flutter
  integration_test:
    sdk: flutter
  mockito: ^5.4.2
  build_runner: ^2.4.15
  alchemist: ^0.11.0
```

### 2. Ausência de CI/CD

Não há configuração de integração contínua ou entrega contínua, embora exista a estrutura de diretórios:

```
.github/
├── workflows/                # GitHub Actions para CI/CD
└── ISSUE_TEMPLATE/          # Templates para issues
```

### 3. Problemas de Qualidade de Código

- Muitos métodos são muito longos (mais de 20 linhas)
- Comentários insuficientes ou desatualizados
- Falta de documentação para classes e métodos
- Não há análise estática de código configurada além do básico

## Soluções Propostas

### 1. Implementar Testes Unitários

Criar testes para os elementos principais do sistema:

```dart
// test/controllers/insight_controller_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:get/get.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:insight_tracker/app/controllers/insight_controller.dart';
import 'package:insight_tracker/services/storage_service.dart';
import 'package:insight_tracker/app/data/models/insight.dart';

import 'insight_controller_test.mocks.dart';

@GenerateMocks([StorageService])
void main() {
  late MockStorageService mockStorageService;
  late InsightController insightController;

  setUp(() {
    mockStorageService = MockStorageService();
    Get.put<StorageService>(mockStorageService);
    insightController = InsightController();
  });

  tearDown(() {
    Get.reset();
  });

  group('InsightController Tests', () {
    test('loadInsights should load insights from storage', () async {
      // Arrange
      final mockInsights = [
        Insight.create(
          title: 'Test Insight 1',
          content: 'Test Content 1',
        ),
        Insight.create(
          title: 'Test Insight 2',
          content: 'Test Content 2',
        ),
      ];
      
      when(mockStorageService.getAllInsights())
          .thenAnswer((_) async => mockInsights);

      // Act
      await insightController.loadInsights();

      // Assert
      expect(insightController.insights.length, equals(2));
      expect(insightController.insights[0].title, equals('Test Insight 1'));
      expect(insightController.insights[1].title, equals('Test Insight 2'));
      expect(insightController.isLoading.value, equals(false));
      verify(mockStorageService.getAllInsights()).called(1);
    });

    test('addInsight should save insight to storage', () async {
      // Arrange
      when(mockStorageService.saveInsight(any))
          .thenAnswer((_) async => null);

      // Act
      await insightController.addInsight(
        title: 'New Insight',
        content: 'New Content',
      );

      // Assert
      verify(mockStorageService.saveInsight(any)).called(1);
      expect(insightController.isLoading.value, equals(false));
    });

    test('deleteInsight should remove insight from storage', () async {
      // Arrange
      const insightId = 'test-id';
      when(mockStorageService.deleteInsight(insightId))
          .thenAnswer((_) async => null);

      // Act
      await insightController.deleteInsight(insightId);

      // Assert
      verify(mockStorageService.deleteInsight(insightId)).called(1);
      expect(insightController.isLoading.value, equals(false));
    });

    test('getInsight should retrieve insight from storage', () async {
      // Arrange
      const insightId = 'test-id';
      final mockInsight = Insight.create(
        title: 'Test Insight',
        content: 'Test Content',
      );
      
      when(mockStorageService.getInsight(insightId))
          .thenAnswer((_) async => mockInsight);

      // Act
      final result = await insightController.getInsight(insightId);

      // Assert
      expect(result?.title, equals('Test Insight'));
      expect(result?.content, equals('Test Content'));
      verify(mockStorageService.getInsight(insightId)).called(1);
    });

    test('handle errors during insight loading', () async {
      // Arrange
      when(mockStorageService.getAllInsights())
          .thenThrow(Exception('Test error'));

      // Act
      await insightController.loadInsights();

      // Assert
      expect(insightController.isLoading.value, equals(false));
      expect(insightController.errorMessage.value, isNotNull);
      verify(mockStorageService.getAllInsights()).called(1);
    });
  });
}
```

### 2. Implementar Testes de Widget

```dart
// test/widgets/insight_card_test.dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:insight_tracker/core/widgets/insight_card.dart';

void main() {
  group('InsightCard Widget Tests', () {
    testWidgets('should display title and content', (WidgetTester tester) async {
      // Arrange
      const title = 'Test Title';
      const content = 'Test Content';
      final createdAt = DateTime.now();

      // Act
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: InsightCard(
              title: title,
              content: content,
              tags: const ['test'],
              createdAt: createdAt,
            ),
          ),
        ),
      );

      // Assert
      expect(find.text(title), findsOneWidget);
      expect(find.text(content), findsOneWidget);
      expect(find.text('test'), findsOneWidget); // tag
    });

    testWidgets('should call onTap when tapped', (WidgetTester tester) async {
      // Arrange
      const title = 'Test Title';
      const content = 'Test Content';
      final createdAt = DateTime.now();
      var tapped = false;

      // Act
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: InsightCard(
              title: title,
              content: content,
              tags: const [],
              createdAt: createdAt,
              onTap: () {
                tapped = true;
              },
            ),
          ),
        ),
      );

      await tester.tap(find.byType(InsightCard));
      await tester.pump();

      // Assert
      expect(tapped, isTrue);
    });

    testWidgets('should limit content to 3 lines', (WidgetTester tester) async {
      // Arrange
      const title = 'Test Title';
      final longContent = 'Line 1\nLine 2\nLine 3\nLine 4\nLine 5';
      final createdAt = DateTime.now();

      // Act
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: InsightCard(
              title: title,
              content: longContent,
              tags: const [],
              createdAt: createdAt,
            ),
          ),
        ),
      );

      // Assert
      final textWidget = tester.widget<Text>(
        find.descendant(
          of: find.byType(InsightCard),
          matching: find.text(longContent),
        ),
      );
      
      expect(textWidget.maxLines, equals(3));
      expect(textWidget.overflow, equals(TextOverflow.ellipsis));
    });
  });
}
```

### 3. Implementar Testes de Integração

```dart
// integration_test/app_test.dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:insight_tracker/main.dart' as app;
import 'package:insight_tracker/core/config/routes.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('End-to-End Tests', () {
    testWidgets('Create and view an insight', (WidgetTester tester) async {
      // Iniciar o aplicativo
      app.main();
      await tester.pumpAndSettle();

      // Verificar se estamos na página inicial
      expect(find.text('Insight Tracker'), findsOneWidget);

      // Verificar se não há insights
      expect(find.text('No insights yet'), findsOneWidget);

      // Clicar no botão de adicionar insight
      await tester.tap(find.byIcon(Icons.add));
      await tester.pumpAndSettle();

      // Verificar se estamos na página de captura
      expect(find.text('Capture Insight'), findsOneWidget);

      // Preencher o formulário
      await tester.enterText(
        find.widgetWithText(TextField, 'Title'),
        'Test Integration Title',
      );
      await tester.enterText(
        find.widgetWithText(TextField, 'Content'),
        'Test Integration Content',
      );

      // Salvar o insight
      await tester.tap(find.text('Save Insight'));
      await tester.pumpAndSettle();

      // Verificar se voltamos para a página inicial
      expect(find.text('Insight Tracker'), findsOneWidget);

      // Verificar se o insight aparece na lista
      expect(find.text('Test Integration Title'), findsOneWidget);
      expect(find.text('Test Integration Content'), findsOneWidget);

      // Clicar no insight para ver detalhes
      await tester.tap(find.text('Test Integration Title'));
      await tester.pumpAndSettle();

      // Verificar se estamos na página de detalhes
      expect(find.text('Test Integration Title'), findsOneWidget);
      expect(find.text('Test Integration Content'), findsOneWidget);

      // Voltar para a página inicial
      await tester.tap(find.byIcon(Icons.arrow_back));
      await tester.pumpAndSettle();
    });
  });
}
```

### 4. Configurar Análise Estática

Melhorar o arquivo `analysis_options.yaml`:

```yaml
include: package:flutter_lints/flutter.yaml

linter:
  rules:
    # Erros
    - always_use_package_imports
    - avoid_empty_else
    - avoid_relative_lib_imports
    - avoid_return_types_on_setters
    - avoid_types_as_parameter_names
    - avoid_web_libraries_in_flutter
    - empty_statements
    - hash_and_equals
    - no_duplicate_case_values
    - unrelated_type_equality_checks
    - valid_regexps
    
    # Estilo
    - always_declare_return_types
    - always_put_required_named_parameters_first
    - annotate_overrides
    - avoid_function_literals_in_foreach_calls
    - avoid_init_to_null
    - avoid_null_checks_in_equality_operators
    - avoid_renaming_method_parameters
    - avoid_return_types_on_setters
    - avoid_unused_constructor_parameters
    - await_only_futures
    - camel_case_types
    - cancel_subscriptions
    - comment_references
    - constant_identifier_names
    - control_flow_in_finally
    - directives_ordering
    - empty_catches
    - empty_constructor_bodies
    - implementation_imports
    - library_names
    - library_prefixes
    - non_constant_identifier_names
    - overridden_fields
    - package_api_docs
    - package_names
    - package_prefixed_library_names
    - prefer_adjacent_string_concatenation
    - prefer_collection_literals
    - prefer_conditional_assignment
    - prefer_const_constructors
    - prefer_contains
    - prefer_equal_for_default_values
    - prefer_final_fields
    - prefer_final_locals
    - prefer_initializing_formals
    - prefer_interpolation_to_compose_strings
    - prefer_is_empty
    - prefer_is_not_empty
    - prefer_single_quotes
    - prefer_typing_uninitialized_variables
    - recursive_getters
    - slash_for_doc_comments
    - sort_constructors_first
    - test_types_in_equals
    - throw_in_finally
    - type_init_formals
    - unawaited_futures
    - unnecessary_brace_in_string_interps
    - unnecessary_const
    - unnecessary_getters_setters
    - unnecessary_lambdas
    - unnecessary_new
    - unnecessary_this
    - use_rethrow_when_possible

analyzer:
  errors:
    # Configurações de severidade
    missing_required_param: error
    missing_return: error
    must_be_immutable: error
    sort_unnamed_constructors_first: ignore
    
  exclude:
    - "**/*.g.dart"
    - "**/*.freezed.dart"
    - "lib/generated/**"

  language:
    strict-casts: true
    strict-raw-types: true
```

### 5. Configurar CI/CD com GitHub Actions

Criar arquivo de workflow para CI/CD:

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.16.0'
          channel: 'stable'
      - name: Install dependencies
        run: flutter pub get
      - name: Analyze project
        run: flutter analyze

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.16.0'
          channel: 'stable'
      - name: Install dependencies
        run: flutter pub get
      - name: Run tests
        run: flutter test --coverage
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          file: ./coverage/lcov.info

  build-android:
    runs-on: ubuntu-latest
    needs: [analyze, test]
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop'
    steps:
      - uses: actions/checkout@v3
      - uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.16.0'
          channel: 'stable'
      - name: Install dependencies
        run: flutter pub get
      - name: Build APK
        run: flutter build apk --split-per-abi
      - name: Upload APK
        uses: actions/upload-artifact@v3
        with:
          name: app-release
          path: build/app/outputs/flutter-apk/*.apk

  build-ios:
    runs-on: macos-latest
    needs: [analyze, test]
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop'
    steps:
      - uses: actions/checkout@v3
      - uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.16.0'
          channel: 'stable'
      - name: Install dependencies
        run: flutter pub get
      - name: Build iOS
        run: flutter build ios --release --no-codesign
```

### 6. Adicionar Documentação com Dartdoc

Adicionar documentação adequada às classes e métodos:

```dart
/// A controller responsible for managing insights.
///
/// This controller provides methods for loading, creating, updating
/// and deleting insights, as well as managing the loading state and
/// error handling.
class InsightController extends GetxController {
  final StorageService _storageService = Get.find<StorageService>();
  
  /// Observable list of insights
  final insights = <Insight>[].obs;
  
  /// Loading state
  final isLoading = false.obs;
  
  /// Error message
  final errorMessage = Rx<String?>(null);
  
  @override
  void onInit() {
    super.onInit();
    loadInsights();
  }
  
  /// Loads all insights from storage.
  ///
  /// This method queries the storage service to retrieve all insights
  /// and updates the [insights] observable list.
  /// 
  /// Throws an exception if the storage service fails.
  Future<void> loadInsights() async {
    try {
      isLoading.value = true;
      final allInsights = await _storageService.getAllInsights();
      insights.assignAll(allInsights);
    } catch (e) {
      errorMessage.value = 'Failed to load insights: $e';
    } finally {
      isLoading.value = false;
    }
  }

  // Other methods...
}
```

## Priorização de Ações

1. **Alta prioridade**: Implementar testes unitários
   - Criar testes para controllers
   - Criar testes para models
   - Criar testes para services

2. **Alta prioridade**: Configurar análise estática
   - Melhorar configuração de lint
   - Resolver problemas de estilo e qualidade
   - Documentar classes e métodos principais

3. **Média prioridade**: Configurar CI/CD
   - Criar workflow para GitHub Actions
   - Configurar análise, testes e build automatizados
   - Adicionar validação de pull requests

4. **Média prioridade**: Implementar testes de widget
   - Testar componentes de UI principais
   - Verificar interações de usuário
   - Validar comportamento responsivo

5. **Baixa prioridade**: Implementar testes de integração
   - Criar testes end-to-end para fluxos principais
   - Verificar navegação e persistência de dados
   - Testar integração entre componentes

## Impacto da Implementação

- **Qualidade**: Redução de bugs e problemas com testes automatizados
- **Manutenção**: Código mais legível e documentado
- **Colaboração**: Fluxo de trabalho melhorado com CI/CD
- **Evolução**: Base sólida para adição de novas funcionalidades
- **Confiabilidade**: Aplicativo mais estável e robusto

## Documentação Recomendada

Adicionar documentação para:
- Guia de testes
- Padrões de código
- Processo de desenvolvimento
- Configuração de ambiente
- Fluxo de CI/CD