import 'package:flutter/material.dart';

class AudioWaveform extends StatelessWidget {
  final List<double> levels;
  final List<double> waveData;
  final Color color;
  final double height;
  final double width;
  final bool isRecording;
  
  const AudioWaveform({
    super.key,
    required this.levels,
    this.color = Colors.blue,
    this.height = 60,
    this.width = double.infinity,
    this.isRecording = false,
    required this.waveData,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: height,
      width: width,
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(12),
        child: CustomPaint(
          painter: _WaveformPainter(
            levels: levels,
            color: color,
            isRecording: isRecording,
          ),
          size: Size(width, height),
        ),
      ),
    );
  }
}

class _WaveformPainter extends CustomPainter {
  final List<double> levels;
  final Color color;
  final bool isRecording;

  _WaveformPainter({
    required this.levels,
    required this.color,
    required this.isRecording,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..style = PaintingStyle.fill;

    // Draw some default bars if no levels
    if (levels.isEmpty) {
      final barWidth = size.width / 30;
      final spacing = barWidth / 2;
      for (int i = 0; i < 30; i++) {
        final x = i * (barWidth + spacing);
        final barHeight = size.height * 0.1;
        
        final rect = Rect.fromLTWH(
          x,
          (size.height - barHeight) / 2,
          barWidth,
          barHeight,
        );
        
        canvas.drawRRect(
          RRect.fromRectAndRadius(rect, const Radius.circular(4)),
          paint,
        );
      }
      return;
    }

    // Draw bars based on levels
    final barWidth = size.width / levels.length;
    final spacing = barWidth * 0.2;
    final effectiveBarWidth = barWidth - spacing;

    for (int i = 0; i < levels.length; i++) {
      final level = levels[i];
      final x = i * barWidth;
      
      // Make the bars pulsate when recording
      final pulseFactor = isRecording ? (1.0 + 0.2 * (i % 3)) : 1.0;
      final barHeight = size.height * 0.1 + (size.height * 0.8 * level * pulseFactor);
      
      final rect = Rect.fromLTWH(
        x + spacing / 2,
        (size.height - barHeight) / 2,
        effectiveBarWidth,
        barHeight,
      );
      
      canvas.drawRRect(
        RRect.fromRectAndRadius(rect, const Radius.circular(4)),
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _WaveformPainter oldDelegate) {
    return oldDelegate.levels != levels || 
           oldDelegate.color != color ||
           oldDelegate.isRecording != isRecording;
  }
}