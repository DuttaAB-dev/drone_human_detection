import 'package:flutter/material.dart';
import 'dart:convert';
import 'detection_group_widget.dart';

class ResultsCardWidget extends StatelessWidget {
  final Map<String, dynamic> detectionResults;

  const ResultsCardWidget({super.key, required this.detectionResults});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final detections = detectionResults['detections'] as List?;
    final count = detectionResults['count'];

    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        color: theme.colorScheme.surface,
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, 4))],
      ),
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.analytics_outlined, color: theme.colorScheme.primary, size: 20),
              const SizedBox(width: 8),
              Text('Detection Results', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
              const Spacer(),
              if (count != null)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(color: theme.colorScheme.primaryContainer, borderRadius: BorderRadius.circular(20)),
                  child: Text('$count objects', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: theme.colorScheme.onPrimaryContainer)),
                ),
            ],
          ),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(color: theme.colorScheme.surfaceVariant.withOpacity(0.5), borderRadius: BorderRadius.circular(12)),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (detections != null)
                  ..._buildGroupedDetections(theme, detections)
                else
                  SelectableText(jsonEncode(detectionResults), style: TextStyle(fontFamily: 'monospace', fontSize: 12, color: theme.colorScheme.onSurfaceVariant)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  List<Widget> _buildGroupedDetections(ThemeData theme, List detections) {
    final Map<String, List<Map<String, dynamic>>> grouped = {};
    for (var detection in detections) {
      final className = detection['class'] as String;
      if (!grouped.containsKey(className)) grouped[className] = [];
      grouped[className]!.add(detection);
    }
    final sortedEntries = grouped.entries.toList()..sort((a, b) => b.value.length.compareTo(a.value.length));

    return sortedEntries.map((entry) => DetectionGroupWidget(
      className: entry.key,
      count: entry.value.length,
      items: entry.value,
      theme: theme,
    )).toList();
  }
}