import 'package:flutter/material.dart';

class FilterSelectionWidget extends StatefulWidget {
  final List<String> allFilters;
  final List<String> selectedFilters;
  final Function(String filter, bool isSelected) onFilterToggled;
  final VoidCallback onSelectAll;
  final VoidCallback onClearAll;

  const FilterSelectionWidget({
    super.key,
    required this.allFilters,
    required this.selectedFilters,
    required this.onFilterToggled,
    required this.onSelectAll,
    required this.onClearAll,
  });

  @override
  State<FilterSelectionWidget> createState() => _FilterSelectionWidgetState();
}

class _FilterSelectionWidgetState extends State<FilterSelectionWidget> {
  bool isFiltersExpanded = false;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final displayClasses = isFiltersExpanded ? widget.allFilters : widget.allFilters.take(12).toList();

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
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Image Filters', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
              if (widget.selectedFilters.isNotEmpty)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(color: theme.colorScheme.primaryContainer, borderRadius: BorderRadius.circular(20)),
                  child: Text('${widget.selectedFilters.length} selected', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: theme.colorScheme.onPrimaryContainer)),
                ),
            ],
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: displayClasses.map((filter) {
              bool isSelected = widget.selectedFilters.contains(filter);
              return FilterChip(
                label: Text(filter),
                selected: isSelected,
                onSelected: (selected) => widget.onFilterToggled(filter, selected),
                showCheckmark: true,
                selectedColor: theme.colorScheme.primaryContainer,
                checkmarkColor: theme.colorScheme.onPrimaryContainer,
                labelStyle: TextStyle(fontSize: 13, fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500),
              );
            }).toList(),
          ),
          if (!isFiltersExpanded && widget.allFilters.length > 12) ...[
            const SizedBox(height: 12),
            Center(
              child: TextButton.icon(
                onPressed: () => setState(() => isFiltersExpanded = true),
                icon: const Icon(Icons.expand_more, size: 20),
                label: Text('Show ${widget.allFilters.length - 12} more'),
              ),
            ),
          ],
          if (isFiltersExpanded) ...[
            const SizedBox(height: 12),
            Center(
              child: TextButton.icon(
                onPressed: () => setState(() => isFiltersExpanded = false),
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