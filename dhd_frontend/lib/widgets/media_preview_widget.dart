import 'package:flutter/material.dart';
import 'package:file_selector/file_selector.dart';
import 'dart:convert';
import 'video_player_widget.dart';

class MediaPreviewWidget extends StatelessWidget {
  final XFile? selectedFile;
  final String? fileType;
  final bool isLoading;
  final bool isLiveDetection;
  final String? processedImagePath;
  final String? processedVideoPath;
  final String? liveFrameBase64;
  final VoidCallback onClearFile;
  final VoidCallback onPickFile;

  const MediaPreviewWidget({
    super.key,
    required this.selectedFile,
    required this.fileType,
    required this.isLoading,
    required this.isLiveDetection,
    required this.processedImagePath,
    required this.processedVideoPath,
    required this.liveFrameBase64,
    required this.onClearFile,
    required this.onPickFile,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: theme.colorScheme.outline.withOpacity(0.2), width: 2),
        color: theme.colorScheme.surfaceVariant.withOpacity(0.3),
      ),
      child: AspectRatio(
        aspectRatio: 16 / 9,
        child: Stack(
          fit: StackFit.expand,
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(14),
              child: _buildPreviewContent(theme),
            ),
            if (selectedFile != null && !isLoading)
              Positioned(
                top: 12,
                right: 12,
                child: Material(
                  color: Colors.black.withOpacity(0.6),
                  shape: const CircleBorder(),
                  clipBehavior: Clip.antiAlias,
                  child: IconButton(
                    icon: const Icon(Icons.close, color: Colors.white, size: 20),
                    onPressed: onClearFile,
                    tooltip: 'Remove current file',
                    constraints: const BoxConstraints(minWidth: 36, minHeight: 36),
                    padding: EdgeInsets.zero,
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildPreviewContent(ThemeData theme) {
    if (processedVideoPath != null) {
      return VideoPlayerWidget(key: ValueKey(processedVideoPath), videoPath: processedVideoPath!);
    }
    if (isLiveDetection && liveFrameBase64 != null) {
      return Image.memory(base64Decode(liveFrameBase64!.split(',')[1]), fit: BoxFit.contain, gaplessPlayback: true);
    }
    if (fileType == 'image' && processedImagePath != null) {
      return Image.memory(base64Decode(processedImagePath!.split(',')[1]), fit: BoxFit.contain, gaplessPlayback: true);
    }

    return Container(
      color: theme.colorScheme.surfaceVariant.withOpacity(0.3),
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(color: theme.colorScheme.primaryContainer.withOpacity(0.5), shape: BoxShape.circle),
              child: Icon(
                selectedFile == null ? Icons.add_photo_alternate_outlined : Icons.hourglass_empty,
                size: 48,
                color: theme.colorScheme.primary,
              ),
            ),
            const SizedBox(height: 24),
            FilledButton.tonalIcon(
              onPressed: onPickFile,
              icon: const Icon(Icons.upload_file),
              label: Text(selectedFile == null ? 'Select File' : 'Change File'),
              style: FilledButton.styleFrom(
                padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
            if (selectedFile != null) ...[
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(color: theme.colorScheme.surface.withOpacity(0.8), borderRadius: BorderRadius.circular(8)),
                child: Column(
                  children: [
                    Text(
                      selectedFile!.path.split('/').last,
                      style: theme.textTheme.bodySmall?.copyWith(fontWeight: FontWeight.w500),
                      overflow: TextOverflow.ellipsis,
                      maxLines: 1,
                    ),
                    const SizedBox(height: 4),
                    Text(fileType!.toUpperCase(), style: theme.textTheme.labelSmall?.copyWith(color: theme.colorScheme.primary, fontWeight: FontWeight.bold)),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}