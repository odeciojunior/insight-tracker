import 'dart:async';  // Added to fix Timer errors
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:get/get.dart';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';
import 'package:speech_to_text/speech_to_text.dart';

class RecorderController extends GetxController {
  // Audio recorder
  final _audioRecorder = Record();
  
  // Speech to text
  final SpeechToText _speechToText = SpeechToText();
  
  // Recording status
  final isRecording = false.obs;
  
  // Transcribed text
  final transcribedText = ''.obs;
  
  // Recording path
  String? _recordingPath;
  
  // Audio levels for visualization
  final RxList<double> audioLevels = <double>[].obs;
  final int maxLevels = 30; // Number of levels to show in the visualization
  
  // Timer for updating audio levels
  Timer? _levelTimer;

  // Is voice recognition available
  final isVoiceRecognitionAvailable = false.obs;

  @override
  void onInit() async {
    super.onInit();
    // Initialize speech to text
    isVoiceRecognitionAvailable.value = 
        await _speechToText.initialize(onError: _onSpeechError);
  }
  
  @override
  void onClose() {
    _stopLevelTimer();
    _audioRecorder.dispose();
    super.onClose();
  }
  
  // Start recording
  Future<void> startRecording() async {
    try {
      if (await _audioRecorder.hasPermission()) {
        // Define the recording path
        final directory = await getTemporaryDirectory();
        _recordingPath = '${directory.path}/audio_${DateTime.now().millisecondsSinceEpoch}.m4a';
        
        // Clear audio levels
        audioLevels.clear();
        
        // Start recording
        await _audioRecorder.start(
          path: _recordingPath,
          encoder: AudioEncoder.aacLc,
          bitRate: 128000,
          samplingRate: 44100,
        );
        
        isRecording.value = true;
        
        // Start level monitoring
        _startLevelTimer();
        
        // Start voice recognition if available
        if (isVoiceRecognitionAvailable.value) {
          _startVoiceRecognition();
        }
      } else {
        Get.snackbar(
          'Permission Denied',
          'Microphone permission is required',
          snackPosition: SnackPosition.BOTTOM,
        );
      }
    } catch (e) {
      Get.snackbar(
        'Error',
        'Failed to start recording: $e',
        snackPosition: SnackPosition.BOTTOM,
      );
    }
  }
  
  // Stop recording
  Future<String?> stopRecording() async {
    try {
      if (isRecording.value) {
        _stopLevelTimer();
        
        // Stop recording
        final path = await _audioRecorder.stop();
        isRecording.value = false;
        
        // Stop voice recognition
        if (_speechToText.isListening) {
          _speechToText.stop();
        }
        
        return path;
      }
    } catch (e) {
      Get.snackbar(
        'Error',
        'Failed to stop recording: $e',
        snackPosition: SnackPosition.BOTTOM,
      );
    }
    return null;
  }
  
  // Start voice recognition
  void _startVoiceRecognition() {
    try {
      _speechToText.listen(
        onResult: _onSpeechResult,
        listenFor: const Duration(seconds: 30),
        pauseFor: const Duration(seconds: 3),
        partialResults: true,
      );
    } catch (e) {
      debugPrint('Voice recognition error: $e');
    }
  }
  
  // Handle speech result
  void _onSpeechResult(SpeechRecognitionResult result) {
    transcribedText.value = result.recognizedWords;
  }
  
  // Handle speech error
  void _onSpeechError(SpeechRecognitionError error) {
    debugPrint('Speech recognition error: ${error.errorMsg}');
  }
  
  // Clear transcribed text
  void clearTranscription() {
    transcribedText.value = '';
  }
  
  // Delete recording file
  Future<void> deleteRecording() async {
    if (_recordingPath != null) {
      final file = File(_recordingPath!);
      if (await file.exists()) {
        await file.delete();
      }
      _recordingPath = null;
    }
  }
  
  // Start timer to update audio levels
  void _startLevelTimer() {
    _levelTimer = Timer.periodic(const Duration(milliseconds: 100), (timer) async {
      if (isRecording.value) {
        final amplitude = await _audioRecorder.getAmplitude();
        final level = amplitude.current.clamp(0.0, 100.0) / 100.0;
        
        // Add to levels list
        if (audioLevels.length >= maxLevels) {
          audioLevels.removeAt(0);
        }
        audioLevels.add(level);
      }
    });
  }
  
  // Stop level timer
  void _stopLevelTimer() {
    _levelTimer?.cancel();
    _levelTimer = null;
  }
}