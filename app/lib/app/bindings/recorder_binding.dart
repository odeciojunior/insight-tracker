import 'package:get/get.dart';
import '../controllers/recorder_controller.dart';

class RecorderBinding extends Bindings {
  @override
  void dependencies() {
    // Ensure we're using the proper concrete implementation
    Get.lazyPut<RecorderController>(() => RecorderController());
  }
}
