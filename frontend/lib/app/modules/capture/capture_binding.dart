import 'package:get/get.dart';
import '../../controllers/insight_controller.dart';
import '../../controllers/recorder_controller.dart';
import '../../controllers/category_controller.dart';  // Add this import

class CaptureBinding extends Bindings {
  @override
  void dependencies() {
    Get.lazyPut(() => InsightController());
    Get.lazyPut(() => RecorderController());
    Get.lazyPut(() => CategoryController());  // Add this line
  }
}