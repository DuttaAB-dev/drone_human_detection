import 'package:flutter/material.dart';
import 'package:media_kit/media_kit.dart';
import 'dart:ui';

import 'screens/home.dart';
import 'themes/app_theme.dart';

// --- Constants ---
const String kBackendUrl = 'http://localhost:3000';
const List<String> kYoloClasses = [
  'pedestrian',
  'people',
  'car',
  'bicycle',
  'van',
  'truck',
  'tricycle',
  'motor',
  'bus',
  'awning-tricycle',
];
const Map<String, Color> kYoloClassColors = {
  'pedestrian': Color(0xFF042AFF), // Deep Blue
  'people': Color(0xFF0BDBEB), // Cyan
  'car': Color(0xFF00DFB7), // Off-White/Light Gray
  'bicycle': Color(0xFFF3F3F3), // Mint Green
  'van': Color(0xFF111F68), // Navy Blue
  'truck': Color(0xFFCCED00), // Pink
  'tricycle': Color(0xFFFF444F), // Red
  'motor': Color(0xFFFF6BEE), // Yellow-Green
  'bus': Color(0xFF00F645), // Bright Green
  'awning-tricycle': Color(0xFFBDD400), // Lime
};
const List<String> kYoloFilters = [
  "gamma-correction",
  "clahe",
  "dehaze",
  "sharpen",
  "bilateral-filter",
];

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  DartPluginRegistrant.ensureInitialized();
  MediaKit.ensureInitialized();
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'DHD',
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.dark,
      home: const HomeScreen(),
    );
  }
}
