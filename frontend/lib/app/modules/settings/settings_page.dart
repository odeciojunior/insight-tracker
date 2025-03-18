import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../controllers/auth_controller.dart';
import '../../services/theme_service.dart';

class SettingsPage extends StatelessWidget {
  const SettingsPage({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final themeService = Get.find<ThemeService>();
    final authController = Get.find<AuthController>();
    
    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
      ),
      body: ListView(
        children: [
          const SizedBox(height: 8),
          Obx(() => _buildThemeToggle(themeService)),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.account_circle),
            title: const Text('Account'),
            subtitle: Text(authController.user.value?.email ?? 'Not signed in'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () {
              // Navigate to account settings
              Get.snackbar(
                'Coming Soon',
                'Account settings will be available in the next update',
              );
            },
          ),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.backup),
            title: const Text('Backup & Restore'),
            subtitle: const Text('Backup or restore your insights'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () {
              // Navigate to backup settings
              Get.snackbar(
                'Coming Soon',
                'Backup & Restore will be available in the next update',
              );
            },
          ),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.notifications),
            title: const Text('Notifications'),
            subtitle: const Text('Configure notifications'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () {
              // Navigate to notification settings
              Get.snackbar(
                'Coming Soon',
                'Notification settings will be available in the next update',
              );
            },
          ),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.info),
            title: const Text('About'),
            subtitle: const Text('App information and credits'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () {
              _showAboutDialog(context);
            },
          ),
          const Divider(),
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: ElevatedButton.icon(
              icon: const Icon(Icons.logout),
              label: const Text('Sign Out'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Theme.of(context).colorScheme.error,
                foregroundColor: Theme.of(context).colorScheme.onError,
              ),
              onPressed: () async {
                final confirm = await Get.dialog<bool>(
                  AlertDialog(
                    title: const Text('Sign Out'),
                    content: const Text('Are you sure you want to sign out?'),
                    actions: [
                      TextButton(
                        child: const Text('Cancel'),
                        onPressed: () => Get.back(result: false),
                      ),
                      TextButton(
                        child: const Text('Sign Out'),
                        onPressed: () => Get.back(result: true),
                      ),
                    ],
                  ),
                );
                
                if (confirm == true) {
                  await authController.logout();
                }
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildThemeToggle(ThemeService themeService) {
    return SwitchListTile(
      title: const Text('Dark Mode'),
      subtitle: const Text('Toggle between light and dark themes'),
      secondary: Icon(
        themeService.isDarkMode ? Icons.dark_mode : Icons.light_mode,
      ),
      value: themeService.isDarkMode,
      onChanged: (_) {
        themeService.toggleTheme();
      },
    );
  }

  void _showAboutDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AboutDialog(
        applicationName: 'Insight Tracker',
        applicationVersion: '1.0.0',
        applicationIcon: const FlutterLogo(size: 48),
        children: [
          const SizedBox(height: 24),
          const Text(
            'Insight Tracker helps you capture and organize your ideas, insights, and reflections in one convenient place.',
          ),
          const SizedBox(height: 16),
          const Text(
            '© 2023 Insight Tracker Team',
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }
}
