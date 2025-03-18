import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

class LoadingIndicator extends StatelessWidget {
  final String? message;
  final Color? color;
  final double size;

  const LoadingIndicator({
    Key? key,
    this.message,
    this.color,
    this.size = 40.0,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
            width: size,
            height: size,
            child: CircularProgressIndicator(
              valueColor: AlwaysStoppedAnimation<Color>(
                color ?? Theme.of(context).colorScheme.primary,
              ),
            ),
          )
              .animate()
              .fade(duration: 300.ms)
              .scale(begin: const Offset(0.8, 0.8), duration: 300.ms),
          if (message != null) ...[
            const SizedBox(height: 16),
            Text(
              message!,
              style: TextStyle(
                color: Theme.of(context).textTheme.bodyMedium?.color,
                fontSize: 16,
              ),
            ).animate().fade(duration: 300.ms, delay: 100.ms),
          ],
        ],
      ),
    );
  }
}