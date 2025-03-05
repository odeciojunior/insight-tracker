import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../controllers/recorder_controller.dart';

class RecorderPage extends GetView<RecorderController> {
  const RecorderPage({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // The controller should be initialized via the binding
    // No need to create a new instance here
    
    return Scaffold(
      appBar: AppBar(
        title: const Text('Voice Recorder'),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // UI components here
            Obx(() => Text('Recording: ${controller.isRecording.value}')),
            ElevatedButton(
              onPressed: () async {
                if (controller.isRecording.value) {
                  await controller.stopRecording();
                } else {
                  await controller.startRecording();
                }
              },
              child: Obx(() => Text(
                controller.isRecording.value ? 'Stop Recording' : 'Start Recording'
              )),
            ),
          ],
        ),
      ),
    );
  }
}
