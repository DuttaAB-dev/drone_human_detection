import 'package:flutter/material.dart';
import 'package:file_selector/file_selector.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'dart:convert';
import 'dart:io';

import '../main.dart'; 
import '../services/api_service.dart';

import '../widgets/media_preview_widget.dart';
import '../widgets/category_selection_widget.dart';
import '../widgets/filter_selection_widget.dart';
import '../widgets/action_buttons_widget.dart';
import '../widgets/results_card_widget.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ApiService _apiService = ApiService();

  XFile? selectedFile;
  String? fileType;
  bool isLoading = false;
  bool isLiveDetection = false;
  bool isPlayingVideo = false;

  Map<String, dynamic>? detectionResults;
  String? processedImagePath;
  String? processedVideoPath;
  String? liveFrameBase64;
  List<String>? videoFrames;

  int currentVideoFrame = 0;
  int currentFrame = 0;
  int totalFrames = 0;
  double processingProgress = 0.0;

  WebSocketChannel? wsChannel;
  List<String> selectedClasses = [];
  List<String> selectedFilters = [];

  @override
  void dispose() {
    _cleanupState();
    super.dispose();
  }

  void _cleanupState() {
    wsChannel?.sink.close();
    wsChannel = null;
    isPlayingVideo = false;
  }

  void clearFile() {
    _cleanupState();
    setState(() {
      selectedFile = null;
      fileType = null;
      detectionResults = null;
      processedImagePath = null;
      processedVideoPath = null;
      liveFrameBase64 = null;
      videoFrames = null;
      currentVideoFrame = 0;
      currentFrame = 0;
      totalFrames = 0;
      processingProgress = 0.0;
      isLiveDetection = false;
      isLoading = false;
    });
  }

  Future<void> pickFile() async {
    try {
      final XFile? file = await openFile(
        acceptedTypeGroups: const [
          XTypeGroup(label: 'Images', extensions: ['jpg', 'jpeg', 'png']),
          XTypeGroup(label: 'Videos', extensions: ['mp4', 'avi', 'mov']),
        ],
      );

      if (file != null) {
        if (!mounted) return;
        _cleanupState();
        String extension = file.path.split('.').last.toLowerCase();

        setState(() {
          selectedFile = file;
          fileType = ['mp4', 'avi', 'mov'].contains(extension)
              ? 'video'
              : 'image';
          detectionResults = null;
          processedImagePath = null;
          liveFrameBase64 = null;
          processedVideoPath = null;
          videoFrames = null;
          currentVideoFrame = 0;
          isLiveDetection = false;
          processingProgress = 0.0;
        });
      }
    } catch (e) {
      _showSnackBar('Error selecting file: $e');
    }
  }

  Future<void> detectImage() async {
    if (selectedFile == null || selectedClasses.isEmpty) {
      _showSnackBar('Please select a file and at least one category');
      return;
    }
    setState(() => isLoading = true);
    try {
      final results = await _apiService.detectImage(
        File(selectedFile!.path),
        selectedClasses,
        selectedFilters,
      );
      if (!mounted) return;
      setState(() {
        detectionResults = results;
        if (results['image'] != null) processedImagePath = results['image'];
      });
    } catch (e) {
      if (mounted) _showSnackBar('Error: $e');
    } finally {
      if (mounted) setState(() => isLoading = false);
    }
  }

  Future<void> detectVideoLive() async {
    if (selectedFile == null || selectedClasses.isEmpty) return;
    _cleanupState();
    setState(() {
      isLoading = true;
      isLiveDetection = true;
      liveFrameBase64 = null;
      processedVideoPath = null;
      processingProgress = 0.0;
      videoFrames = [];
    });

    try {
      wsChannel = await _apiService.startLiveDetection(
        File(selectedFile!.path),
        selectedClasses,
        selectedFilters,
      );
      if (!mounted) return;
      setState(() => isLoading = false);

      wsChannel!.stream.listen(
        (message) {
          if (!mounted) return;
          var data = jsonDecode(message);
          if (data['completed'] == true) {
            setState(() => isLiveDetection = false);
            _showSnackBar('Detection completed! Click play to review');
            wsChannel?.sink.close();
            _playVideoFrames();
          } else if (data['error'] != null) {
            _showSnackBar('Error: ${data['error']}');
            setState(() => isLiveDetection = false);
          } else {
            setState(() {
              liveFrameBase64 = data['frame'];
              videoFrames!.add(data['frame']);
              detectionResults = {
                'detections': data['detections'],
                'count': data['detections'].length,
              };
              currentFrame = data['frame_number'] ?? 0;
              totalFrames = data['total_frames'] ?? 0;
              processingProgress = data['progress'] ?? 0.0;
            });
          }
        },
        onError: (error) {
          if (!mounted) return;
          _showSnackBar('WebSocket error: $error');
          setState(() => isLiveDetection = false);
        },
        onDone: () {
          if (mounted) setState(() => isLiveDetection = false);
        },
      );
    } catch (e) {
      if (mounted) {
        _showSnackBar('Error: $e');
        setState(() {
          isLoading = false;
          isLiveDetection = false;
        });
      }
    }
  }

  void _playVideoFrames() async {
    if (videoFrames == null || videoFrames!.isEmpty) return;
    setState(() {
      isPlayingVideo = true;
      currentVideoFrame = 0;
      isLiveDetection = true;
    });

    while (isPlayingVideo && currentVideoFrame < videoFrames!.length) {
      if (!mounted) return;
      setState(() => liveFrameBase64 = videoFrames![currentVideoFrame]);
      currentVideoFrame++;
      await Future.delayed(const Duration(milliseconds: 33));
    }

    if (mounted && currentVideoFrame >= videoFrames!.length) {
      setState(() {
        isPlayingVideo = false;
        currentVideoFrame = 0;
        isLiveDetection = false;
      });
    }
  }

  Future<void> detectVideoComplete() async {
    if (selectedFile == null || selectedClasses.isEmpty) return;
    setState(() {
      isLoading = true;
      liveFrameBase64 = null;
      processedImagePath = null;
      processedVideoPath = null;
      videoFrames = null;
    });

    try {
      final responseData = await _apiService.processCompleteVideo(
        File(selectedFile!.path),
        selectedClasses,
        selectedFilters,
      );
      if (!mounted) return;
      setState(() {
        processedVideoPath = responseData['videoPath'];
        if (responseData['results'] != null)
          detectionResults = responseData['results'];
      });
      _showSnackBar('Video ready! Loading internal canvas player...');
    } catch (e) {
      if (mounted) _showSnackBar('Error: $e');
    } finally {
      if (mounted) setState(() => isLoading = false);
    }
  }

  void _showSnackBar(String message) {
      ScaffoldMessenger.of(context).hideCurrentSnackBar();
  
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          behavior: SnackBarBehavior.floating,
          margin: const EdgeInsets.only(bottom: 24, left: 50, right: 50),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          // Adjust padding so the icon fits nicely without making the bar too tall
          padding: const EdgeInsets.only(left: 16, right: 8, top: 4, bottom: 4), 
          content: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Expanded(
              //   child: Text(message, textAlign: TextAlign.center),
              // )
              Text(message, textAlign: TextAlign.center),
              IconButton(
                icon: const Icon(Icons.close, size: 20),
                color: Theme.of(context).colorScheme.inversePrimary, 
                onPressed: () => ScaffoldMessenger.of(context).hideCurrentSnackBar(),
                // These constraints strip out the default bulky padding around standard IconButtons
                constraints: const BoxConstraints(minWidth: 36, minHeight: 36), 
                padding: EdgeInsets.zero,
              ),
            ],
          ),
        ),
      );
    }

  // --- UI Build Method ---

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      backgroundColor: theme.colorScheme.background,
      appBar: AppBar(
        title: const Text(
          'Drone Object Detection',
          style: TextStyle(fontWeight: FontWeight.w600),
        ),
        centerTitle: true,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            MediaPreviewWidget(
              selectedFile: selectedFile,
              fileType: fileType,
              isLoading: isLoading,
              isLiveDetection: isLiveDetection,
              processedImagePath: processedImagePath,
              processedVideoPath: processedVideoPath,
              liveFrameBase64: liveFrameBase64,
              onClearFile: clearFile,
              onPickFile: pickFile,
            ),
            if (isLiveDetection && totalFrames > 0)
              Padding(
                padding: const EdgeInsets.only(top: 16),
                child: Column(
                  children: [
                    LinearProgressIndicator(
                      value: processingProgress / 100,
                      minHeight: 8,
                      borderRadius: BorderRadius.circular(4),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Processing: $currentFrame / $totalFrames frames (${processingProgress.toStringAsFixed(1)}%)',
                      style: theme.textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
            const SizedBox(height: 24),
            CategorySelectionWidget(
              allClasses: kYoloClasses,
              selectedClasses: selectedClasses,
              onCategoryToggled: (category, isSelected) {
                setState(() {
                  isSelected
                      ? selectedClasses.add(category)
                      : selectedClasses.remove(category);
                });
              },
              onSelectAll: () =>
                  setState(() => selectedClasses = List.from(kYoloClasses)),
              onClearAll: () => setState(() => selectedClasses.clear()),
            ),
            FilterSelectionWidget(
              allFilters: kYoloFilters,
              selectedFilters: selectedFilters,
              onFilterToggled: (filter, isSelected) {
                setState(() {
                  isSelected
                      ? selectedFilters.add(filter)
                      : selectedFilters.remove(filter);
                });
              },
              onSelectAll: () =>
                  setState(() => selectedFilters = List.from(kYoloFilters)),
              onClearAll: () => setState(() => selectedFilters.clear()),
            ),
            const SizedBox(height: 24),
            ActionButtonsWidget(
              fileType: fileType,
              isLoading: isLoading,
              isLiveDetection: isLiveDetection,
              onDetectImage: detectImage,
              onDetectVideoLive: detectVideoLive,
              onDetectVideoComplete: detectVideoComplete,
            ),
            if (detectionResults != null) ...[
              const SizedBox(height: 24),
              ResultsCardWidget(detectionResults: detectionResults!),
            ],
          ],
        ),
      ),
    );
  }
}
