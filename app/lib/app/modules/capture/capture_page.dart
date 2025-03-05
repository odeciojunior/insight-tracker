import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../controllers/insight_controller.dart';
import '../../controllers/recorder_controller.dart';
import '../../controllers/category_controller.dart';
import '../../data/models/category.dart';
import '../../../core/widgets/custom_button.dart';
import '../../../core/widgets/audio_waveform.dart';

class CapturePage extends StatefulWidget {
  const CapturePage({Key? key}) : super(key: key);

  @override
  State<CapturePage> createState() => _CapturePageState();
}

class _CapturePageState extends State<CapturePage> {
  final InsightController _insightController = Get.find();
  final RecorderController _recorderController = Get.find();
  final CategoryController _categoryController = Get.find();
  
  final _titleController = TextEditingController();
  final _contentController = TextEditingController();
  final _tagController = TextEditingController();
  final List<String> _tags = [];
  
  String? _selectedCategoryId;
  
  @override
  void initState() {
    super.initState();
    
    // Listen for transcribed text and update content field
    _recorderController.transcribedText.listen((text) {
      if (text.isNotEmpty) {
        _contentController.text = text;
      }
    });
  }
  
  @override
  void dispose() {
    _titleController.dispose();
    _contentController.dispose();
    _tagController.dispose();
    super.dispose();
  }

  void _addTag() {
    final tag = _tagController.text.trim();
    if (tag.isNotEmpty && !_tags.contains(tag)) {
      setState(() {
        _tags.add(tag);
        _tagController.clear();
      });
    }
  }
  
  void _removeTag(String tag) {
    setState(() {
      _tags.remove(tag);
    });
  }
  
  void _saveInsight() {
    final title = _titleController.text.trim();
    final content = _contentController.text.trim();
    
    if (title.isEmpty) {
      Get.snackbar(
        'Error',
        'Title cannot be empty',
        snackPosition: SnackPosition.BOTTOM,
      );
      return;
    }
    
    if (content.isEmpty) {
      Get.snackbar(
        'Error',
        'Content cannot be empty',
        snackPosition: SnackPosition.BOTTOM,
      );
      return;
    }
    
    _insightController.addInsight(
      title: title,
      content: content,
      tags: _tags,
      categoryId: _selectedCategoryId,
    ).then((_) {
      _titleController.clear();
      _contentController.clear();
      setState(() {
        _tags.clear();
        _selectedCategoryId = null;
      });
      
      // Navigate back if this was opened as a modal
      if (Get.isDialogOpen ?? false) {
        Get.back();
      } else {
        Get.back();
      }
    });
  }

  Widget _buildCategorySelector() {
    return Obx(() {
      final categories = _categoryController.categories;
      
      if (categories.isEmpty) {
        return const SizedBox.shrink();
      }
      
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Category',
            style: TextStyle(
              fontWeight: FontWeight.bold,
              fontSize: 16,
            ),
          ),
          const SizedBox(height: 8),
          Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: Theme.of(context).colorScheme.outline,
                width: 1,
              ),
            ),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
            child: DropdownButtonHideUnderline(
              child: DropdownButton<String>(
                value: _selectedCategoryId,
                isExpanded: true,
                hint: const Text('Select a category'),
                items: [
                  const DropdownMenuItem<String>(
                    value: null,
                    child: Text('No category'),
                  ),
                  ...categories.map((category) {
                    return DropdownMenuItem<String>(
                      value: category.id,
                      child: Row(
                        children: [
                          Icon(
                            category.icon,
                            color: category.color,
                            size: 20,
                          ),
                          const SizedBox(width: 8),
                          Text(category.name),
                        ],
                      ),
                    );
                  }).toList(),
                ],
                onChanged: (value) {
                  setState(() {
                    _selectedCategoryId = value;
                  });
                },
              ),
            ),
          ),
          const SizedBox(height: 16),
        ],
      );
    });
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Capture Insight'),
        actions: [
          IconButton(
            icon: const Icon(Icons.save),
            onPressed: _saveInsight,
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Title Field
            TextField(
              controller: _titleController,
              decoration: const InputDecoration(
                labelText: 'Title',
                border: OutlineInputBorder(),
              ),
              maxLines: 1,
            ),
            
            const SizedBox(height: 16),
            
            // Category Selector
            _buildCategorySelector(),
            
            // Content Field
            Expanded(
              child: TextField(
                controller: _contentController,
                decoration: const InputDecoration(
                  labelText: 'Content',
                  border: OutlineInputBorder(),
                  alignLabelWithHint: true,
                ),
                maxLines: null,
                expands: true,
                textAlignVertical: TextAlignVertical.top,
              ),
            ),
            
            const SizedBox(height: 16),
            
            // Tags Input
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _tagController,
                    decoration: const InputDecoration(
                      labelText: 'Add Tag',
                      border: OutlineInputBorder(),
                      suffixIcon: Icon(Icons.tag),
                    ),
                    onSubmitted: (_) => _addTag(),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.add),
                  onPressed: _addTag,
                ),
              ],
            ),
            
            const SizedBox(height: 8),
            
            // Tags Display
            Wrap(
              spacing: 8,
              children: _tags.map((tag) => Chip(
                label: Text(tag),
                onDeleted: () => _removeTag(tag),
              )).toList(),
            ),
            
            const SizedBox(height: 16),
            
            // Voice Recording Button
            Obx(() => CustomButton(
              text: _recorderController.isRecording.value
                  ? 'Stop Recording'
                  : 'Record Voice',
              icon: _recorderController.isRecording.value
                  ? Icons.stop
                  : Icons.mic,
              onPressed: () async {
                if (_recorderController.isRecording.value) {
                  await _recorderController.stopRecording();
                } else {
                  await _recorderController.startRecording();
                }
              },
              backgroundColor: _recorderController.isRecording.value
                  ? Colors.red
                  : Theme.of(context).colorScheme.primary,
              fullWidth: true,
            )),
            
            const SizedBox(height: 16),

            // Audio Waveform
            Obx(() => _recorderController.isRecording.value
                ? AudioWaveform(
                    waveData: _recorderController.waveData,
                    height: 100,
                    width: double.infinity,
                    color: Theme.of(context).colorScheme.primary,
                  )
                : const SizedBox.shrink(),
            ),
            
            const SizedBox(height: 16),
            
            // Save Button
            CustomButton(
              text: 'Save Insight',
              icon: Icons.save,
              onPressed: _saveInsight,
              fullWidth: true,
            ),
          ],
        ),
      ),
    );
  }
}