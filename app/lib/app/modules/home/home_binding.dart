import 'package:get/get.dart';
import '../../controllers/insight_controller.dart';
import '../../controllers/category_controller.dart';

class HomeBinding extends Bindings {
  @override
  void dependencies() {
    Get.lazyPut(() => InsightController());
    Get.lazyPut(() => CategoryController());
  }
}