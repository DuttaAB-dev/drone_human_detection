import 'package:flutter/material.dart';
import 'package:media_kit/media_kit.dart';
import 'package:media_kit_video/media_kit_video.dart';
import 'dart:io';

class VideoPlayerWidget extends StatefulWidget {
  final String videoPath;

  const VideoPlayerWidget({super.key, required this.videoPath});

  @override
  State<VideoPlayerWidget> createState() => _VideoPlayerWidgetState();
}

class _VideoPlayerWidgetState extends State<VideoPlayerWidget> {
  late final Player _player;
  VideoController? _videoController;
  bool _isInitialized = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _initializePlayer();
  }

  Future<void> _initializePlayer() async {
    try {
      debugPrint("--- VideoPlayerWidget: Initializing with path: ${widget.videoPath} ---");
      
      // Give the OS file locks from the download thread time to fully release
      await Future.delayed(const Duration(milliseconds: 200));

      final file = File(widget.videoPath);
      if (!await file.exists() || await file.length() == 0) {
        setState(() {
          _errorMessage = "Video file does not exist or is empty at target path.";
        });
        return;
      }

      // Initialize the core media engine
      _player = Player(
        configuration: const PlayerConfiguration(
          bufferSize: 32 * 1024 * 1024, // 32MB buffer safety
        ),
      );
      
      // Force a clean software texture rendering pipeline.
      // This completely circumvents the native container method channel bugs.
      _videoController = VideoController(
        _player,
        configuration: const VideoControllerConfiguration(
          enableHardwareAcceleration: false,
        ),
      );

      // Open the target video file path directly
      await _player.open(Media(file.path), play: true);

      if (mounted) {
        setState(() {
          _isInitialized = true;
        });
        debugPrint("--- VideoPlayerWidget: Initialization Successful ---");
      }
    } catch (e) {
      debugPrint("--- DESKTOP MEDIA PLAYER ERROR ---: $e");
      if (mounted) {
        setState(() {
          _errorMessage = "Failed to open video engine pipeline: $e";
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_errorMessage != null) {
      return Container(
        color: Colors.black,
        padding: const EdgeInsets.all(16),
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, color: Colors.red, size: 42),
              const SizedBox(height: 12),
              Text(
                _errorMessage!,
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.white, fontSize: 14),
              ),
            ],
          ),
        ),
      );
    }

    if (!_isInitialized || _videoController == null) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 12),
            Text('Initializing software video pipeline...', style: TextStyle(color: Colors.white70)),
          ],
        ),
      );
    }

    return MaterialVideoControlsTheme(
      normal: const MaterialVideoControlsThemeData(
        buttonBarButtonSize: 24.0,
        buttonBarButtonColor: Colors.white,
      ),
      fullscreen: const MaterialVideoControlsThemeData(),
      child: Video(
        controller: _videoController!,
        controls: MaterialVideoControls,
      ),
    );
  }

  @override
  void dispose() {
    debugPrint("--- VideoPlayerWidget: Disposing Player Resources ---");
    _player.dispose();
    super.dispose();
  }
}