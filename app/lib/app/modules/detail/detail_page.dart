import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../controllers/insight_controller.dart';
import '../../../core/models/insight_model.dart';
import '../../../core/widgets/loading_indicator.dart';
import '../../../core/config/routes.dart';

class DetailPage extends StatelessWidget {
  const DetailPage({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final insightId = Get.arguments as String;
    final insightController = Get.find<InsightController>();
    
    return FutureBuilder<InsightModel?>(
      future: insightController.getInsight(insightId),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return Scaffold(
            appBar: AppBar(title: const Text('Loading...')),
            body: const LoadingIndicator(message: 'Loading insight...'),
          );
        }
        
        if (snapshot.hasError) {
          return Scaffold(
            appBar: AppBar(title: const Text('Error')),
            body: Center(child: Text('Error: ${snapshot.error}')),
          );
        }
        
        final insight = snapshot.data;
        if (insight == null) {
          return Scaffold(
            appBar: AppBar(title: const Text('Not Found')),
            body: const Center(child: Text('Insight not found')),
          );
        }
        
        return Scaffold(
          appBar: AppBar(
            title: Text(insight.title, overflow: TextOverflow.ellipsis),
            actions: [
              IconButton(
                icon: const Icon(Icons.edit),
                onPressed: () {
                  Get.toNamed(AppRoutes.EDIT, arguments: insightId);
                },
              ),
              IconButton(
                icon: const Icon(Icons.delete),
                onPressed: () => _showDeleteConfirmation(context, insightController, insightId),
              ),
            ],
          ),
          body: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  insight.title,
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 16),
                _buildDateInfo(context, insight),
                const SizedBox(height: 24),
                Text(
                  insight.content,
                  style: Theme.of(context).textTheme.bodyLarge,
                ),
                const SizedBox(height: 24),
                _buildTagsList(context, insight.tags),
              ],
            ),
          ),
        );
      },
    );
  }
  
  Widget _buildDateInfo(BuildContext context, InsightModel insight) {
    final theme = Theme.of(context);
    final createdAt = '${insight.createdAt.day}/${insight.createdAt.month}/${insight.createdAt.year}';
    
    if (insight.updatedAt != null) {
      final updatedAt = '${insight.updatedAt!.day}/${insight.updatedAt!.month}/${insight.updatedAt!.year}';
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Created: $createdAt',
            style: theme.textTheme.bodySmall?.copyWith(fontStyle: FontStyle.italic),
          ),
          const SizedBox(height: 4),
          Text(
            'Last updated: $updatedAt',
            style: theme.textTheme.bodySmall?.copyWith(fontStyle: FontStyle.italic),
          ),
        ],
      );
    }
    
    return Text(
      'Created: $createdAt',
      style: theme.textTheme.bodySmall?.copyWith(fontStyle: FontStyle.italic),
    );
  }
  
  Widget _buildTagsList(BuildContext context, List<String> tags) {
    if (tags.isEmpty) return const SizedBox.shrink();
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Tags',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8.0,
          runSpacing: 8.0,
          children: tags.map((tag) => _buildTagChip(context, tag)).toList(),
        ),
      ],
    );
  }
  
  Widget _buildTagChip(BuildContext context, String tag) {
    return Chip(
      label: Text(tag),
      backgroundColor: Theme.of(context).colorScheme.surfaceVariant,
    );
  }
  
  void _showDeleteConfirmation(BuildContext context, InsightController controller, String insightId) {
    Get.dialog(
      AlertDialog(
        title: const Text('Delete Insight'),
        content: const Text(
          'Are you sure you want to delete this insight? This action cannot be undone.',
        ),
        actions: [
          TextButton(
            child: const Text('Cancel'),
            onPressed: () {
              Get.back();
            },
          ),
          TextButton(
            child: const Text('Delete'),
            onPressed: () async {
              try {
                await controller.deleteInsight(insightId);
                Get.back();
                Get.offNamed(AppRoutes.HOME);
                Get.snackbar('Success', 'Insight deleted successfully');
              } catch (e) {
                Get.back();
                Get.snackbar('Error', 'Failed to delete insight: ${e.toString()}');
              }
            },
          ),
        ],
      ),
    );
  }
}
