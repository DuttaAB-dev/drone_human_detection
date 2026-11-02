import 'package:http/http.dart' as http;
import 'package:web_socket_channel/web_socket_channel.dart';
import 'dart:convert';
import 'dart:io';

class ApiService {
  final String baseUrl;

  // Defaults to localhost, but can be overridden if deployed later
  ApiService({this.baseUrl = 'http://localhost:3000'});

  /// 1. Processes a static image and returns the detection results map.
  Future<Map<String, dynamic>> detectImage(File file, List<String> classes, List<String> filters) async {
    var request = http.MultipartRequest('POST', Uri.parse('$baseUrl/detect/image'));
    request.files.add(await http.MultipartFile.fromPath('file', file.path));
    request.fields['classes'] = jsonEncode(classes);
    request.fields['filters'] = jsonEncode(filters);
    

    var response = await request.send();

    if (response.statusCode == 200) {
      var responseData = await response.stream.bytesToString();
      return jsonDecode(responseData);
    } else {
      throw Exception('Image detection failed: ${response.statusCode}');
    }
  }

  /// 2. Uploads a video and establishes a WebSocket connection for live frame streaming.
  /// Returns the connected WebSocketChannel so the UI can listen to the stream.
  Future<WebSocketChannel> startLiveDetection(File file, List<String> classes, List<String> filters) async {
    // Step A: Upload the video
    var uploadRequest = http.MultipartRequest('POST', Uri.parse('$baseUrl/detect/video/upload'));
    uploadRequest.files.add(await http.MultipartFile.fromPath('file', file.path));
    uploadRequest.fields['classes'] = jsonEncode(classes);
    uploadRequest.fields['filters'] = jsonEncode(filters);

    var uploadResponse = await uploadRequest.send();

    if (uploadResponse.statusCode == 200) {
      var responseData = await uploadResponse.stream.bytesToString();
      var jsonData = jsonDecode(responseData);

      String videoId = jsonData['video_id'];
      String videoPath = jsonData['video_path'];

      // Step B: Connect to WebSocket (dynamically replaces http with ws)
      String wsBaseUrl = baseUrl.replaceFirst('http', 'ws');
      var wsChannel = WebSocketChannel.connect(
        Uri.parse('$wsBaseUrl/ws/detect/video/$videoId'),
      );

      // Step C: Send initial configuration payload
      wsChannel.sink.add(jsonEncode({
        'video_path': videoPath,
        'classes': jsonEncode(classes),
      }));

      return wsChannel;
    } else {
      throw Exception('Upload for live detection failed: ${uploadResponse.statusCode}');
    }
  }

  /// 3. Uploads a video and waits for the complete processed video to return.
  /// Returns a map containing the temporary saved 'videoPath' and the parsed 'results'.
  Future<Map<String, dynamic>> processCompleteVideo(File file, List<String> classes, List<String> filters) async {
    var request = http.MultipartRequest('POST', Uri.parse('$baseUrl/detect/video/process'));
    request.files.add(await http.MultipartFile.fromPath('file', file.path));
    request.fields['classes'] = jsonEncode(classes);
    request.fields['filters'] = jsonEncode(filters);
    

    var response = await request.send();

    if (response.statusCode == 200) {
      // Save the video bytes to a temporary file
      var bytes = await response.stream.toBytes();
      var tempDir = Directory.systemTemp;
      var videoFile = File('${tempDir.path}/processed_video_${DateTime.now().millisecondsSinceEpoch}.mp4');
      await videoFile.writeAsBytes(bytes);

      // Extract the results from the custom header
      Map<String, dynamic>? results;
      var resultsHeader = response.headers['x-detection-results'];
      if (resultsHeader != null) {
        results = jsonDecode(resultsHeader);
      }

      return {
        'videoPath': videoFile.path,
        'results': results,
      };
    } else {
      throw Exception('Complete video processing failed: ${response.statusCode}');
    }
  }
}