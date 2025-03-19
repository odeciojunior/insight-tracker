import 'dart:async';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:get/get.dart';

class ConnectivityService extends GetxService {
  final _connectivity = Connectivity();
  final isOnline = false.obs;
  StreamSubscription? _subscription;

  @override
  void onInit() {
    super.onInit();
    _initConnectivity();
    _subscription = _connectivity.onConnectivityChanged.listen(_updateConnectionStatus);
  }

  @override
  void onClose() {
    _subscription?.cancel();
    super.onClose();
  }

  // Initialize connectivity and set initial status
  Future<void> _initConnectivity() async {
    try {
      final status = await _connectivity.checkConnectivity();
      _updateConnectionStatus(status);
    } catch (e) {
      print('ConnectivityService: Error checking initial connectivity status: $e');
      isOnline.value = false;
    }
  }

  // Update connection status based on connectivity changes
  void _updateConnectionStatus(ConnectivityResult result) {
    isOnline.value = result != ConnectivityResult.none;
    print('ConnectivityService: Connection status updated - Online: ${isOnline.value}');
  }

  // Method to check if device is currently connected
  Future<bool> isConnected() async {
    try {
      final result = await _connectivity.checkConnectivity();
      return result != ConnectivityResult.none;
    } catch (e) {
      print('ConnectivityService: Error checking connectivity: $e');
      return false;
    }
  }
}
