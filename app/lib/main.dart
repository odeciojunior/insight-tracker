import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:get/get.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:path_provider/path_provider.dart' as path_provider;
import 'core/config/routes.dart';
import 'core/config/themes.dart';
import 'app/modules/home/home_binding.dart';
import 'app/modules/home/home_page.dart';
import 'services/storage_service.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize Hive for local storage
  final appDocumentDirectory = 
      await path_provider.getApplicationDocumentsDirectory();
  await Hive.initFlutter(appDocumentDirectory.path);
  
  // Initialize and register the storage service
  final storageService = StorageService();
  await storageService.init();
  Get.put(storageService);
  
  // Set preferred orientations
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);
  
  runApp(const InsightTrackerApp());
}

class InsightTrackerApp extends StatelessWidget {
  const InsightTrackerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return GetMaterialApp(
      title: 'Insight Tracker',
      debugShowCheckedModeBanner: false,
      theme: AppThemes.lightTheme,
      darkTheme: AppThemes.darkTheme,
      themeMode: ThemeMode.system,
      initialRoute: AppRoutes.HOME,
      getPages: AppRoutes.routes,
      initialBinding: HomeBinding(),
      home: const HomePage(),
    );
  }
}