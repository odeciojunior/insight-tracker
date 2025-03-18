import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../../core/config/routes.dart';
import '../../../core/widgets/insight_card.dart';
import '../../../core/widgets/loading_indicator.dart';
import '../../controllers/insight_controller.dart';

class HomePage extends StatelessWidget {
  const HomePage({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final insightController = Get.find<InsightController>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Insight Tracker'),
        actions: [
          IconButton(
            icon: const Icon(Icons.search),
            onPressed: () {
              // TODO: Implement search functionality
            },
          ),
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () {
              Get.toNamed(AppRoutes.SETTINGS);
            },
          ),
        ],
      ),
      body: Obx(() {
        if (insightController.isLoading.value) {
          return const LoadingIndicator(message: 'Loading insights...');
        }

        if (insightController.insights.isEmpty) {
          return _buildEmptyState();
        }

        return ListView.builder(
          itemCount: insightController.insights.length,
          itemBuilder: (context, index) {
            final insight = insightController.insights[index];
            return InsightCard(
              title: insight.title,
              content: insight.content,
              tags: insight.tags,
              createdAt: insight.createdAt,
              onTap: () {
                Get.toNamed(AppRoutes.DETAIL, arguments: insight.id);
              },
              onLongPress: () {
                _showOptionsMenu(context, insightController, insight);
              },
            );
          },
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

  // Extracted empty state to a separate method
  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(
            Icons.lightbulb_outline,
            size: 80,
            color: Colors.grey,
          ),
          const SizedBox(height: 16),
          const Text(
            'No insights yet',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Tap the + button to capture your first insight',
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            icon: const Icon(Icons.add),
            label: const Text('Capture Insight'),
            onPressed: () {
              Get.toNamed(AppRoutes.CAPTURE);
            },
          ),
        ],
      ),
    );
  }

  // Extracted options menu to a separate method
  void _showOptionsMenu(BuildContext context, InsightController controller, dynamic insight) {
    // Check if insight is null or missing id
    if (insight == null || insight.id == null) {
      Get.snackbar('Error', 'Cannot perform operations on this insight');
      return;
    }

    Get.bottomSheet(
      Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surface,
          borderRadius: const BorderRadius.only(
            topLeft: Radius.circular(16),
            topRight: Radius.circular(16),
          ),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.edit),
              title: const Text('Edit'),
              onTap: () {
                Get.back();
                Get.toNamed(AppRoutes.EDIT, arguments: insight.id);
              },
            ),
            ListTile(
              leading: const Icon(Icons.delete),
              title: const Text('Delete'),
              onTap: () {
                Get.back();
                _showDeleteConfirmation(context, controller, insight.id);
              },
            ),
            ListTile(
              leading: const Icon(Icons.share),
              title: const Text('Share'),
              onTap: () {
                Get.back();
                // TODO: Implement share functionality
                Get.snackbar('Coming Soon', 'Share functionality will be available in the next update');
              },
            ),
          ],
        ),
      ),
    );
  }

  // Extracted delete confirmation to a separate method
  void _showDeleteConfirmation(BuildContext context, InsightController controller, String insightId) {
    Get.dialog(
      AlertDialog(
        title: const Text('Delete Insight'),
        content: const Text(
          'Are you sure you want to delete this insight?',
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