import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../../core/widgets/loading_indicator.dart';
import '../../controllers/insight_controller.dart';
import '../../data/models/insight.dart';

class EditPage extends StatefulWidget {
  const EditPage({Key? key}) : super(key: key);

  @override
  State<EditPage> createState() => _EditPageState();
}

class _EditPageState extends State<EditPage> {
  final _formKey = GlobalKey<FormState>();
  final _titleController = TextEditingController();
  final _contentController = TextEditingController();
  final _tagController = TextEditingController();
  List<String> _tags = [];
  bool _isLoading = true;
  bool _isSubmitting = false;
  String? _insightId;
  
  @override
  void initState() {
    super.initState();
    _loadInsight();
  }
  
  Future<void> _loadInsight() async {
    final insightId = Get.arguments as String;
    _insightId = insightId;
    
    try {
      final insightController = Get.find<InsightController>();
      final insight = await insightController.getInsight(insightId);
      
      if (insight != null) {
        setState(() {
          _titleController.text = insight.title;
          _contentController.text = insight.content;
          _tags = List<String>.from(insight.tags);
          _isLoading = false;
        });
      } else {
        Get.snackbar('Error', 'Insight not found');
        Get.back();
      }
    } catch (e) {
      Get.snackbar('Error', 'Failed to load insight: ${e.toString()}');
      Get.back();
    }
  }

  @override
  void dispose() {
    _titleController.dispose();
    _contentController.dispose();
    _tagController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(title: const Text('Edit Insight')),
        body: const LoadingIndicator(message: 'Loading insight...'),
      );
    }
    
    return Scaffold(
      appBar: AppBar(
        title: const Text('Edit Insight'),
        actions: [
          IconButton(
            icon: const Icon(Icons.check),
            onPressed: _submit,
          ),
        ],
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16.0),
          children: [
            TextFormField(
              controller: _titleController,
              decoration: const InputDecoration(
                labelText: 'Title',
                border: OutlineInputBorder(),
              ),
              validator: (value) {
                if (value == null || value.isEmpty) {
                  return 'Please enter a title';
                }
                return null;
              },
              maxLength: 100,
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _contentController,
              decoration: const InputDecoration(
                labelText: 'Content',
                border: OutlineInputBorder(),
                alignLabelWithHint: true,
              ),
              validator: (value) {
                if (value == null || value.isEmpty) {
                  return 'Please enter content';
                }
                return null;
              },
              maxLines: 10,
              minLines: 5,
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: TextFormField(
                    controller: _tagController,
                    decoration: const InputDecoration(
                      labelText: 'Add Tags',
                      border: OutlineInputBorder(),
                      hintText: 'Enter a tag name',
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                ElevatedButton(
                  onPressed: _addTag,
                  child: const Text('Add'),
                ),
              ],
            ),
            const SizedBox(height: 16),
            _buildTagsList(),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: _isSubmitting ? null : _submit,
              child: _isSubmitting
                  ? const CircularProgressIndicator()
                  : const Text('Update Insight'),
            ),
          ],
        ),
      ),
    );
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

  Widget _buildTagsList() {
    if (_tags.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(16.0),
          child: Text('No tags added yet'),
        ),
      );
    }

    return Wrap(
      spacing: 8.0,
      runSpacing: 8.0,
      children: _tags
          .map((tag) => Chip(
                label: Text(tag),
                deleteIcon: const Icon(Icons.close, size: 18),
                onDeleted: () {
                  setState(() {
                    _tags.remove(tag);
                  });
                },
              ))
          .toList(),
    );
  }

  Future<void> _submit() async {
    if (_formKey.currentState!.validate() && _insightId != null) {
      setState(() {
        _isSubmitting = true;
      });

      try {
        var insight = Insight.create(
          title: _titleController.text.trim(),
          content: _contentController.text.trim(),
        );

        final insightController = Get.find<InsightController>();
        
        await insightController.updateInsight(
          insight, 
          _insightId!
        );

        Get.back();
        Get.snackbar('Success', 'Insight updated successfully');
      } catch (e) {
        Get.snackbar('Error', 'Failed to update insight: ${e.toString()}');
      } finally {
        if (mounted) {
          setState(() {
            _isSubmitting = false;
          });
        }
      }
    }
  }
}
