import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'lesson_video_screen.dart';

class TestLessonVideoScreen extends StatefulWidget {
  final String lessonId;

  const TestLessonVideoScreen({
    super.key,
    required this.lessonId,
  });

  @override
  State<TestLessonVideoScreen> createState() =>
      _TestLessonVideoScreenState();
}

class _TestLessonVideoScreenState
    extends State<TestLessonVideoScreen> {
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadLesson();
  }

  Future<void> _loadLesson() async {
    try {
      print('GETTING LESSON: ${widget.lessonId}');

      final lesson =
          await ApiService.getLesson(widget.lessonId);

      print('LESSON RESPONSE: $lesson');

      final videoUrl = lesson['video_url'];

      if (videoUrl == null ||
          videoUrl.toString().isEmpty) {
        throw Exception(
          'Video is not available yet.',
        );
      }

      if (!mounted) return;

      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (_) => LessonVideoScreen(
            videoUrl: videoUrl.toString(),
            title: lesson['title']?.toString() ??
                'AI Lesson',
          ),
        ),
      );
    } catch (e) {
      print('LESSON ERROR: $e');

      if (!mounted) return;

      setState(() {
        _loading = false;
        _error = e.toString();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Loading Lesson'),
      ),
      body: Center(
        child: _loading
            ? const Column(
                mainAxisAlignment:
                    MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 16),
                  Text(
                    'Getting your lesson video...',
                  ),
                ],
              )
            : Padding(
                padding: const EdgeInsets.all(24),
                child: Text(
                  _error ?? 'Unknown error',
                  textAlign: TextAlign.center,
                ),
              ),
      ),
    );
  }
}
