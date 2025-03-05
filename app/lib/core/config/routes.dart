import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../app/modules/capture/capture_binding.dart';
import '../../app/modules/capture/capture_page.dart';
import '../../app/modules/home/home_binding.dart';
import '../../app/modules/home/home_page.dart';

class AppRoutes {
  // Route names
  static const String HOME = '/home';
  static const String AUTH = '/auth';
  static const String CAPTURE = '/capture';
  static const String MINDMAP = '/mindmap';
  static const String SETTINGS = '/settings';
  
  // GetX route definitions
  static final List<GetPage> routes = [
    // Home route
    GetPage(
      name: HOME,
      page: () => const HomePage(),
      binding: HomeBinding(),
    ),
    
    // Auth route (placeholder for now)
    GetPage(
      name: AUTH,
      page: () => const Scaffold(
        body: Center(
          child: Text('Auth Page - Coming Soon'),
        ),
      ),
    ),
    
    // Capture route
    GetPage(
      name: CAPTURE,
      page: () => const CapturePage(),
      binding: CaptureBinding(),
      transition: Transition.rightToLeft,
    ),
    
    // Mindmap route (placeholder for now)
    GetPage(
      name: MINDMAP,
      page: () => const Scaffold(
        body: Center(
          child: Text('Mindmap Page - Coming Soon'),
        ),
      ),
    ),
    
    // Settings route (placeholder for now)
    GetPage(
      name: SETTINGS,
      page: () => const Scaffold(
        body: Center(
          child: Text('Settings Page - Coming Soon'),
        ),
      ),
    ),
  ];
}