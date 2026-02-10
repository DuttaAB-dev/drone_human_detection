import 'package:flutter/material.dart';
import 'package:file_selector/file_selector.dart';
import 'package:http/http.dart' as http;
import 'package:web_socket_channel/web_socket_channel.dart';
import 'dart:convert';
import 'dart:io';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'DHD',
      theme: ThemeData(
        primarySwatch: Colors.deepPurple,
        useMaterial3: true,
        brightness: Brightness.light,
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.deepPurple,
          brightness: Brightness.light,
        ),
      ),
      darkTheme: ThemeData(
        primarySwatch: Colors.deepPurple,
        useMaterial3: true,
        brightness: Brightness.dark,
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.deepPurple,
          brightness: Brightness.dark,
        ),
      ),
      themeMode: ThemeMode.dark,
      home: const DetectionScreen(),
    );
  }
}

class DetectionScreen extends StatefulWidget {
  const DetectionScreen({Key? key}) : super(key: key);

  @override
  State<DetectionScreen> createState() => _DetectionScreenState();
}

class _DetectionScreenState extends State<DetectionScreen> {
  XFile? selectedFile;
  String? fileType;
  bool isLoading = false;
  bool isLiveDetection = false;
  bool isPlayingVideo = false;
  Map<String, dynamic>? detectionResults;
  String? processedImagePath;
  String? liveFrameBase64;
  String? processedVideoPath;
  List<String>? videoFrames; // Store all frames as base64
  int currentVideoFrame = 0;
  WebSocketChannel? wsChannel;
  double processingProgress = 0.0;
  int currentFrame = 0;
  int totalFrames = 0;
  bool isCategoriesExpanded = false;
  
  final String backendUrl = 'http://localhost:3000';
  
  final List<String> yoloClasses = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 
    'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign', 
    'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 
    'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 
    'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 
    'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 
    'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 
    'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 
    'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 
    'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 
    'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 
    'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 
    'scissors', 'teddy bear', 'hair drier', 'toothbrush'
  ];
  
  List<String> selectedClasses = [];

  Future<void> pickFile() async {
    try {
      const XTypeGroup imageTypeGroup = XTypeGroup(
        label: 'Images',
        extensions: ['jpg', 'jpeg', 'png'],
      );
      const XTypeGroup videoTypeGroup = XTypeGroup(
        label: 'Videos',
        extensions: ['mp4', 'avi', 'mov'],
      );
      
      final XFile? file = await openFile(
        acceptedTypeGroups: [imageTypeGroup, videoTypeGroup],
      );

      if (file != null) {
        String extension = file.path.split('.').last.toLowerCase();
        setState(() {
          selectedFile = file;
          fileType = ['mp4', 'avi', 'mov'].contains(extension) ? 'video' : 'image';
          detectionResults = null;
          processedImagePath = null;
          liveFrameBase64 = null;
          processedVideoPath = null;
          videoFrames = null;
          isPlayingVideo = false;
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

    setState(() {
      isLoading = true;
    });

    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$backendUrl/detect/image'),
      );

      request.files.add(
        await http.MultipartFile.fromPath('file', selectedFile!.path),
      );
      
      request.fields['classes'] = jsonEncode(selectedClasses);

      var response = await request.send();
      
      if (response.statusCode == 200) {
        var responseData = await response.stream.bytesToString();
        var jsonData = jsonDecode(responseData);
        
        setState(() {
          detectionResults = jsonData;
          if (jsonData['image'] != null) {
            processedImagePath = jsonData['image'];
          }
        });
      } else {
        throw Exception('Detection failed: ${response.statusCode}');
      }
    } catch (e) {
      _showSnackBar('Error: $e');
    } finally {
      setState(() {
        isLoading = false;
      });
    }
  }

  Future<void> detectVideoLive() async {
    if (selectedFile == null || selectedClasses.isEmpty) {
      _showSnackBar('Please select a file and at least one category');
      return;
    }

    setState(() {
      isLoading = true;
      isLiveDetection = true;
      liveFrameBase64 = null;
      processingProgress = 0.0;
      videoFrames = []; // Store frames for playback
    });

    try {
      // Upload video first
      var uploadRequest = http.MultipartRequest(
        'POST',
        Uri.parse('$backendUrl/detect/video/upload'),
      );

      uploadRequest.files.add(
        await http.MultipartFile.fromPath('file', selectedFile!.path),
      );
      uploadRequest.fields['classes'] = jsonEncode(selectedClasses);

      var uploadResponse = await uploadRequest.send();
      
      if (uploadResponse.statusCode == 200) {
        var responseData = await uploadResponse.stream.bytesToString();
        var jsonData = jsonDecode(responseData);
        
        String videoId = jsonData['video_id'];
        String videoPath = jsonData['video_path'];
        
        // Connect to WebSocket
        wsChannel = WebSocketChannel.connect(
          Uri.parse('ws://localhost:3000/ws/detect/video/$videoId'),
        );
        
        // Send video info
        wsChannel!.sink.add(jsonEncode({
          'video_path': videoPath,
          'classes': jsonEncode(selectedClasses),
        }));
        
        setState(() {
          isLoading = false;
        });
        
        // Listen to frames
        wsChannel!.stream.listen(
          (message) {
            var data = jsonDecode(message);
            
            if (data['completed'] == true) {
              setState(() {
                isLiveDetection = false;
              });
              _showSnackBar('Detection completed! Click play to review');
              wsChannel?.sink.close();
              
              // Start playback automatically
              _playVideoFrames();
            } else if (data['error'] != null) {
              _showSnackBar('Error: ${data['error']}');
              setState(() {
                isLiveDetection = false;
              });
            } else {
              setState(() {
                liveFrameBase64 = data['frame'];
                videoFrames!.add(data['frame']); // Store frame
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
            _showSnackBar('WebSocket error: $error');
            setState(() {
              isLiveDetection = false;
            });
          },
          onDone: () {
            setState(() {
              isLiveDetection = false;
            });
          },
        );
      } else {
        throw Exception('Upload failed: ${uploadResponse.statusCode}');
      }
    } catch (e) {
      _showSnackBar('Error: $e');
      setState(() {
        isLoading = false;
        isLiveDetection = false;
      });
    }
  }

  void _playVideoFrames() async {
    if (videoFrames == null || videoFrames!.isEmpty) return;
    
    setState(() {
      isPlayingVideo = true;
      currentVideoFrame = 0;
    });
    
    while (isPlayingVideo && currentVideoFrame < videoFrames!.length) {
      setState(() {
        liveFrameBase64 = videoFrames![currentVideoFrame];
        currentVideoFrame++;
      });
      await Future.delayed(const Duration(milliseconds: 33)); // ~30 FPS
    }
    
    if (currentVideoFrame >= videoFrames!.length) {
      setState(() {
        isPlayingVideo = false;
        currentVideoFrame = 0;
      });
    }
  }
  
  void _pauseVideo() {
    setState(() {
      isPlayingVideo = false;
    });
  }
  
  void _resumeVideo() {
    _playVideoFrames();
  }

  Future<void> detectVideoComplete() async {
    if (selectedFile == null || selectedClasses.isEmpty) {
      _showSnackBar('Please select a file and at least one category');
      return;
    }

    setState(() {
      isLoading = true;
      liveFrameBase64 = null;
      processedImagePath = null;
      processedVideoPath = null;
      videoFrames = null;
    });

    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$backendUrl/detect/video/process'),
      );

      request.files.add(
        await http.MultipartFile.fromPath('file', selectedFile!.path),
      );
      request.fields['classes'] = jsonEncode(selectedClasses);

      var response = await request.send();
      
      if (response.statusCode == 200) {
        var bytes = await response.stream.toBytes();
        var tempDir = Directory.systemTemp;
        var videoFile = File('${tempDir.path}/processed_video.mp4');
        await videoFile.writeAsBytes(bytes);
        
        setState(() {
          processedVideoPath = videoFile.path;
        });
        
        var resultsHeader = response.headers['x-detection-results'];
        if (resultsHeader != null) {
          setState(() {
            detectionResults = jsonDecode(resultsHeader);
          });
        }
        
        // Extract frames from video for in-app playback
        _showSnackBar('Extracting frames for playback...');
        await _extractVideoFrames(videoFile.path);
        
        _showSnackBar('Video ready! Click play to watch');
      } else {
        throw Exception('Processing failed: ${response.statusCode}');
      }
    } catch (e) {
      _showSnackBar('Error: $e');
    } finally {
      setState(() {
        isLoading = false;
      });
    }
  }

  Future<void> _extractVideoFrames(String videoPath) async {
    try {
      // Use ffmpeg to extract frames
      final tempDir = Directory.systemTemp;
      final framesDir = Directory('${tempDir.path}/video_frames_${DateTime.now().millisecondsSinceEpoch}');
      await framesDir.create();

      // Extract every frame as JPEG (adjust -r for frame rate)
      final result = await Process.run(
        'ffmpeg',
        [
          '-i', videoPath,
          '-vf', 'fps=30', // 30 frames per second
          '${framesDir.path}/frame_%04d.jpg',
        ],
      );

      if (result.exitCode == 0) {
        // Load all frames
        final frameFiles = framesDir.listSync()
          ..sort((a, b) => a.path.compareTo(b.path));
        
        final List<String> frames = [];
        for (var file in frameFiles) {
          if (file is File) {
            final bytes = await file.readAsBytes();
            final base64 = base64Encode(bytes);
            frames.add('data:image/jpeg;base64,$base64');
          }
        }

        setState(() {
          videoFrames = frames;
          if (frames.isNotEmpty) {
            liveFrameBase64 = frames[0];
          }
        });

        // Clean up temp frames
        await framesDir.delete(recursive: true);
      } else {
        _showSnackBar('Could not extract frames. Using external player option.');
      }
    } catch (e) {
      _showSnackBar('Frame extraction unavailable. Using external player option.');
    }
  }

  void _showSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      ),
    );
  }

  @override
  void dispose() {
    wsChannel?.sink.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Scaffold(
      backgroundColor: theme.colorScheme.background,
      appBar: AppBar(
        title: const Text('Drone Human Detection', style: TextStyle(fontWeight: FontWeight.w600)),
        centerTitle: true,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Preview Area - Always 16:9
            Container(
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: theme.colorScheme.outline.withOpacity(0.2),
                  width: 2,
                ),
                color: theme.colorScheme.surfaceVariant.withOpacity(0.3),
              ),
              child: AspectRatio(
                aspectRatio: 16 / 9,
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(14),
                  child: _buildPreviewContent(theme),
                ),
              ),
            ),
            
            if (isLiveDetection && totalFrames > 0) ...[
              const SizedBox(height: 16),
              Column(
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
            ],
            
            const SizedBox(height: 24),
            
            // Category Selection
            Container(
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
                        'Detection Categories',
                        style: theme.textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      if (selectedClasses.isNotEmpty)
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          decoration: BoxDecoration(
                            color: theme.colorScheme.primaryContainer,
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Text(
                            '${selectedClasses.length} selected',
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
                    children: _buildCategoryChips(theme),
                  ),
                  if (!isCategoriesExpanded && yoloClasses.length > 12) ...[
                    const SizedBox(height: 12),
                    Center(
                      child: TextButton.icon(
                        onPressed: () {
                          setState(() {
                            isCategoriesExpanded = true;
                          });
                        },
                        icon: const Icon(Icons.expand_more, size: 20),
                        label: Text('Show ${yoloClasses.length - 12} more'),
                      ),
                    ),
                  ],
                  if (isCategoriesExpanded) ...[
                    const SizedBox(height: 12),
                    Center(
                      child: TextButton.icon(
                        onPressed: () {
                          setState(() {
                            isCategoriesExpanded = false;
                          });
                        },
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
                          onPressed: () {
                            setState(() {
                              selectedClasses = List.from(yoloClasses);
                            });
                          },
                          icon: const Icon(Icons.select_all, size: 18),
                          label: const Text('Select All'),
                          style: OutlinedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 12),
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: () {
                            setState(() {
                              selectedClasses.clear();
                            });
                          },
                          icon: const Icon(Icons.clear, size: 18),
                          label: const Text('Clear All'),
                          style: OutlinedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 12),
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            
            const SizedBox(height: 24),
            
            // Detection Buttons
            if (fileType == 'image') ...[
              FilledButton.icon(
                onPressed: isLoading ? null : detectImage,
                icon: isLoading
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : const Icon(Icons.image_search),
                label: Text(
                  isLoading ? 'Processing...' : 'Detect Objects in Image',
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                ),
                style: FilledButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 18),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ] else if (fileType == 'video') ...[
              FilledButton.icon(
                onPressed: (isLoading || isLiveDetection) ? null : detectVideoLive,
                icon: isLiveDetection
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : const Icon(Icons.play_circle),
                label: Text(
                  isLiveDetection ? 'Live Detection Running...' : 'Live Detection',
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                ),
                style: FilledButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 18),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                onPressed: (isLoading || isLiveDetection) ? null : detectVideoComplete,
                icon: isLoading && !isLiveDetection
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.videocam),
                label: Text(
                  isLoading && !isLiveDetection ? 'Processing...' : 'Process Complete Video',
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                ),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 18),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ],
            
            if (detectionResults != null) ...[
              const SizedBox(height: 24),
              Container(
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
                      children: [
                        Icon(Icons.analytics_outlined, 
                          color: theme.colorScheme.primary,
                          size: 20,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          'Detection Results',
                          style: theme.textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const Spacer(),
                        if (detectionResults!['count'] != null)
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                            decoration: BoxDecoration(
                              color: theme.colorScheme.primaryContainer,
                              borderRadius: BorderRadius.circular(20),
                            ),
                            child: Text(
                              '${detectionResults!['count']} objects',
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
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.surfaceVariant.withOpacity(0.5),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          if (detectionResults!['detections'] != null)
                            ..._buildGroupedDetections(theme)
                          else
                            SelectableText(
                              jsonEncode(detectionResults),
                              style: TextStyle(
                                fontFamily: 'monospace',
                                fontSize: 12,
                                color: theme.colorScheme.onSurfaceVariant,
                              ),
                            ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildPreviewContent(ThemeData theme) {
    // Live detection frame OR playing stored video frames
    if ((isLiveDetection || isPlayingVideo || videoFrames != null) && liveFrameBase64 != null) {
      return Stack(
        alignment: Alignment.center,
        children: [
          Image.memory(
            base64Decode(liveFrameBase64!.split(',')[1]),
            fit: BoxFit.contain,
          ),
          // Show play/pause controls for recorded video
          if (!isLiveDetection && videoFrames != null && videoFrames!.isNotEmpty)
            Positioned(
              bottom: 16,
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.7),
                  borderRadius: BorderRadius.circular(30),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    IconButton(
                      icon: Icon(
                        isPlayingVideo ? Icons.pause : Icons.play_arrow,
                        color: Colors.white,
                        size: 28,
                      ),
                      onPressed: () {
                        if (isPlayingVideo) {
                          _pauseVideo();
                        } else {
                          _resumeVideo();
                        }
                      },
                    ),
                    if (videoFrames!.isNotEmpty)
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 8),
                        child: Text(
                          '${currentVideoFrame}/${videoFrames!.length}',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 12,
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ),
        ],
      );
    }
    
    // Processed video message (fallback)
    if (processedVideoPath != null) {
      return Container(
        color: Colors.black,
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.video_library,
                size: 64,
                color: Colors.white70,
              ),
              const SizedBox(height: 16),
              Text(
                'Video Processed',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 24),
              FilledButton.icon(
                onPressed: () async {
                  // Open with system video player
                  if (Platform.isLinux) {
                    await Process.run('xdg-open', [processedVideoPath!]);
                  } else if (Platform.isMacOS) {
                    await Process.run('open', [processedVideoPath!]);
                  } else if (Platform.isWindows) {
                    await Process.run('start', [processedVideoPath!], runInShell: true);
                  }
                },
                icon: const Icon(Icons.play_circle_outline),
                label: const Text('Open in Video Player'),
                style: FilledButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                ),
              ),
              const SizedBox(height: 12),
              Text(
                processedVideoPath!.split('/').last,
                style: TextStyle(
                  color: Colors.white70,
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ),
      );
    }
    
    // Processed image - Show YOLO annotated image
    if (fileType == 'image' && processedImagePath != null) {
      return Image.memory(
        base64Decode(processedImagePath!.split(',')[1]),
        fit: BoxFit.contain,
      );
    }
    
    // Placeholder
    return Container(
      color: theme.colorScheme.surfaceVariant.withOpacity(0.3),
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: theme.colorScheme.primaryContainer.withOpacity(0.5),
                shape: BoxShape.circle,
              ),
              child: Icon(
                selectedFile == null ? Icons.add_photo_alternate_outlined : Icons.hourglass_empty,
                size: 48,
                color: theme.colorScheme.primary,
              ),
            ),
            const SizedBox(height: 24),
            FilledButton.tonalIcon(
              onPressed: pickFile,
              icon: const Icon(Icons.upload_file),
              label: Text(selectedFile == null ? 'Select File' : 'Change File'),
              style: FilledButton.styleFrom(
                padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            ),
            if (selectedFile != null) ...[
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: theme.colorScheme.surface.withOpacity(0.8),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Column(
                  children: [
                    Text(
                      selectedFile!.path.split('/').last,
                      style: theme.textTheme.bodySmall?.copyWith(
                        fontWeight: FontWeight.w500,
                      ),
                      overflow: TextOverflow.ellipsis,
                      maxLines: 1,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      fileType!.toUpperCase(),
                      style: theme.textTheme.labelSmall?.copyWith(
                        color: theme.colorScheme.primary,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  List<Widget> _buildCategoryChips(ThemeData theme) {
    final displayClasses = isCategoriesExpanded 
        ? yoloClasses 
        : yoloClasses.take(12).toList();
    
    return displayClasses.map((category) {
      bool isSelected = selectedClasses.contains(category);
      return FilterChip(
        label: Text(category),
        selected: isSelected,
        onSelected: (selected) {
          setState(() {
            if (selected) {
              selectedClasses.add(category);
            } else {
              selectedClasses.remove(category);
            }
          });
        },
        showCheckmark: true,
        selectedColor: theme.colorScheme.primaryContainer,
        checkmarkColor: theme.colorScheme.onPrimaryContainer,
        labelStyle: TextStyle(
          fontSize: 13,
          fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
        ),
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
      );
    }).toList();
  }

  List<Widget> _buildGroupedDetections(ThemeData theme) {
    final detections = detectionResults!['detections'] as List;
    
    // Group detections by class
    final Map<String, List<Map<String, dynamic>>> grouped = {};
    for (var detection in detections) {
      final className = detection['class'] as String;
      if (!grouped.containsKey(className)) {
        grouped[className] = [];
      }
      grouped[className]!.add(detection);
    }
    
    // Sort by count (most frequent first)
    final sortedEntries = grouped.entries.toList()
      ..sort((a, b) => b.value.length.compareTo(a.value.length));
    
    return sortedEntries.map((entry) {
      final className = entry.key;
      final items = entry.value;
      
      return _DetectionGroupWidget(
        className: className,
        count: items.length,
        items: items,
        theme: theme,
      );
    }).toList();
  }
}

class _DetectionGroupWidget extends StatefulWidget {
  final String className;
  final int count;
  final List<Map<String, dynamic>> items;
  final ThemeData theme;

  const _DetectionGroupWidget({
    required this.className,
    required this.count,
    required this.items,
    required this.theme,
  });

  @override
  State<_DetectionGroupWidget> createState() => _DetectionGroupWidgetState();
}

class _DetectionGroupWidgetState extends State<_DetectionGroupWidget> {
  bool isExpanded = false;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        InkWell(
          onTap: () {
            setState(() {
              isExpanded = !isExpanded;
            });
          },
          borderRadius: BorderRadius.circular(8),
          child: Container(
            padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 12),
            decoration: BoxDecoration(
              color: widget.theme.colorScheme.surface.withOpacity(0.5),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              children: [
                Icon(
                  isExpanded ? Icons.expand_less : Icons.expand_more,
                  size: 20,
                  color: widget.theme.colorScheme.primary,
                ),
                const SizedBox(width: 12),
                Container(
                  width: 8,
                  height: 8,
                  decoration: BoxDecoration(
                    color: widget.theme.colorScheme.primary,
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    widget.className,
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                      color: widget.theme.colorScheme.onSurface,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: widget.theme.colorScheme.primaryContainer,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '${widget.count}',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: widget.theme.colorScheme.onPrimaryContainer,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
        if (isExpanded) ...[
          const SizedBox(height: 8),
          Container(
            margin: const EdgeInsets.only(left: 32),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: widget.theme.colorScheme.surfaceVariant.withOpacity(0.3),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: widget.theme.colorScheme.outline.withOpacity(0.2),
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: widget.items.map((item) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: Row(
                    children: [
                      Container(
                        width: 4,
                        height: 4,
                        decoration: BoxDecoration(
                          color: widget.theme.colorScheme.primary.withOpacity(0.5),
                          shape: BoxShape.circle,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        'Confidence: ${(item['confidence'] * 100).toStringAsFixed(1)}%',
                        style: TextStyle(
                          fontSize: 12,
                          color: widget.theme.colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                );
              }).toList(),
            ),
          ),
        ],
        const SizedBox(height: 8),
      ],
    );
  }
}