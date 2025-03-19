import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../utils/connectivity_service.dart';
import '../services/api_service.dart';
import 'data/providers/api_provider_module.dart';

class App extends StatelessWidget {
  const App({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    _initServices();
    
    return GetMaterialApp(
      title: 'Insight Tracker',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      // TODO: Add routes and initial page
      initialRoute: '/',
      getPages: [
        // Define your routes here
      ],
    );
  }
  
  void _initServices() {
    // Initialize services
    Get.put(ConnectivityService(), permanent: true);
    
    // ApiService is a singleton, just ensure it's initialized
    Get.put(ApiService(), permanent: true);
    
    // Initialize API providers
    ApiProviderModule.init();
    
    // Other services initialization
  }
}
