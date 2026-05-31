import 'package:flutter/material.dart';

/// Health score badge widget for AppBar
class HealthBadge extends StatelessWidget {
  final Map<String, dynamic> health;

  const HealthBadge({super.key, required this.health});

  @override
  Widget build(BuildContext context) {
    final score = health['score'] ?? 100;
    final color = score >= 80
        ? Colors.green
        : score >= 50
            ? Colors.orange
            : Colors.red;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.4)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.favorite, color: color, size: 14),
          const SizedBox(width: 4),
          Text(
            '$score%',
            style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 12),
          ),
        ],
      ),
    );
  }
}
