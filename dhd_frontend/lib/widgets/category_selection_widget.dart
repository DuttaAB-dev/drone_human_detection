import 'package:flutter/material.dart';
import '../main.dart';

class CategorySelectionWidget extends StatefulWidget {
  final List<String> allClasses;
  final List<String> selectedClasses;
  final Function(String category, bool isSelected) onCategoryToggled;
  final VoidCallback onSelectAll;
  final VoidCallback onClearAll;

  const CategorySelectionWidget({
    super.key,
    required this.allClasses,
    required this.selectedClasses,
    required this.onCategoryToggled,
    required this.onSelectAll,
    required this.onClearAll,
  });

  @override
  State<CategorySelectionWidget> createState() =>
      _CategorySelectionWidgetState();
}

class _CategorySelectionWidgetState extends State<CategorySelectionWidget> {
  bool isCategoriesExpanded = false;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final displayClasses = isCategoriesExpanded
        ? widget.allClasses
        : widget.allClasses.take(12).toList();

    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        color: theme.colorScheme.surface,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Object Classes',
                style: theme.textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
              ),
              if (widget.selectedClasses.isNotEmpty)
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    color: theme.colorScheme.primaryContainer,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    '${widget.selectedClasses.length} selected',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: theme.colorScheme.onPrimaryContainer,
                    ),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: displayClasses.map((category) {
              bool isSelected = widget.selectedClasses.contains(category);
              Color chipColor =
                  kYoloClassColors[category] ??
                  theme.colorScheme.primaryContainer;
              Color contrastColor = chipColor.computeLuminance() > 0.5
                  ? Colors.black87
                  : Colors.white;

              return FilterChip(
                label: Text(category),
                selected: isSelected,
                onSelected: (selected) =>
                    widget.onCategoryToggled(category, selected),
                showCheckmark: true,
                selectedColor: chipColor,
                checkmarkColor: contrastColor,
                labelStyle: TextStyle(
                  fontSize: 13,
                  fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
                  color: isSelected
                      ? contrastColor
                      : theme.colorScheme.onSurface,
                ),
              );
            }).toList(),
          ),
          if (!isCategoriesExpanded && widget.allClasses.length > 12) ...[
            const SizedBox(height: 12),
            Center(
              child: TextButton.icon(
                onPressed: () => setState(() => isCategoriesExpanded = true),
                icon: const Icon(Icons.expand_more, size: 20),
                label: Text('Show ${widget.allClasses.length - 12} more'),
              ),
            ),
          ],
          if (isCategoriesExpanded) ...[
            const SizedBox(height: 12),
            Center(
              child: TextButton.icon(
                onPressed: () => setState(() => isCategoriesExpanded = false),
                icon: const Icon(Icons.expand_less, size: 20),
                label: const Text('Show less'),
              ),
            ),
          ],
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: widget.onSelectAll,
                  icon: const Icon(Icons.select_all, size: 18),
                  label: const Text('Select All'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: widget.onClearAll,
                  icon: const Icon(Icons.clear, size: 18),
                  label: const Text('Clear All'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
