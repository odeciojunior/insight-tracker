import 'package:get/get.dart';
import '../../controllers/insight_controller.dart';
import '../../controllers/recorder_controller.dart';

class CaptureBinding extends Bindings {
  @override
  void dependencies() {
    Get.lazyPut(() => InsightController());
    Get.lazyPut(() => RecorderController());
  }
}