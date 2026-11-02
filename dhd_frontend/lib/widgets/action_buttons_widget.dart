import 'package:flutter/material.dart';

class ActionButtonsWidget extends StatelessWidget {
  final String? fileType;
  final bool isLoading;
  final bool isLiveDetection;
  final VoidCallback onDetectImage;
  final VoidCallback onDetectVideoLive;
  final VoidCallback onDetectVideoComplete;

  const ActionButtonsWidget({
    super.key,
    required this.fileType,
    required this.isLoading,
    required this.isLiveDetection,
    required this.onDetectImage,
    required this.onDetectVideoLive,
    required this.onDetectVideoComplete,
  });

  @override
  Widget build(BuildContext context) {
    final bool isImage = fileType == 'image';
    final bool isVideo = fileType == 'video';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        FilledButton.icon(
          onPressed: (isImage && !isLoading) ? onDetectImage : null,
          icon: (isLoading && isImage)
              ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
              : const Icon(Icons.image_search),
          label: Text((isLoading && isImage) ? 'Processing...' : 'Detect Objects in Image'),
          style: FilledButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 18), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
        ),
        // const SizedBox(height: 12),
        // FilledButton.icon(
        //   onPressed: (isVideo && !isLoading && !isLiveDetection) ? onDetectVideoLive : null,
        //   icon: isLiveDetection
        //       ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
        //       : const Icon(Icons.play_circle),
        //   label: Text(isLiveDetection ? 'Live Detection Running...' : 'Live Detection'),
        //   style: FilledButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 18), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
        // ),
        const SizedBox(height: 12),
        OutlinedButton.icon(
          onPressed: (isVideo && !isLoading && !isLiveDetection) ? onDetectVideoComplete : null,
          icon: (isLoading && !isLiveDetection && isVideo)
              ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
              : const Icon(Icons.videocam),
          label: Text((isLoading && !isLiveDetection && isVideo) ? 'Processing...' : 'Process Complete Video'),
          style: OutlinedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 18), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
        ),
      ],
    );
  }
}