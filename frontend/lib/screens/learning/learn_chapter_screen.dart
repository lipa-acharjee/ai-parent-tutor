import '../../features/learning/practice_questions_screen.dart';
import 'dart:async';

import '../../lessons/lesson_video_screen.dart';

import 'package:flutter/material.dart';

import '../../services/api_service.dart';

class LearnChapterScreen extends StatefulWidget {
  final Map<String, dynamic> chapter;
  final Map<String, dynamic> child;

  const LearnChapterScreen({
    super.key,
    required this.chapter,
    required this.child,
  });

  @override
  State<LearnChapterScreen> createState() =>
      _LearnChapterScreenState();
}

class _LearnChapterScreenState
    extends State<LearnChapterScreen> {
  bool _loading = false;
  String _statusMessage = '';

  Map<String, dynamic>? _lesson;

  Timer? _pollTimer;

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  // ============================================================
  // START AI LESSON GENERATION
  // ============================================================

  Future<void> _startLearning() async {
  if (_loading) return;

  final chapterId =
      widget.chapter['id']?.toString();

  if (chapterId == null || chapterId.isEmpty) {
    _showError('Chapter ID is missing.');
    return;
  }

  final chapterTitle =
      widget.chapter['title']?.toString() ?? 'Chapter';

  final age = _getStudentAge();

  setState(() {
    _loading = true;
    _statusMessage =
        'Starting your child’s AI lesson...';
    _lesson = null;
  });

  try {
    // --------------------------------------------------------
    // 1. Ask backend for the lesson
    // --------------------------------------------------------

    final job = await ApiService.generateLesson(
      chapterId: chapterId,
      topic: chapterTitle,
      studentAge: age,
      numberOfQuestions: 5,
    );

    final status =
        job['status']?.toString() ?? '';

    final lessonId =
        job['lesson_id']?.toString();

    final jobId =
        job['job_id']?.toString();

    // --------------------------------------------------------
    // 2. Existing lesson found
    // --------------------------------------------------------

    if (status == 'ready' &&
        lessonId != null &&
        lessonId.isNotEmpty) {
      setState(() {
        _statusMessage =
            'Your saved lesson was found. Loading it...';
      });

      final lesson =
          await ApiService.getLesson(lessonId);

      if (!mounted) return;

      setState(() {
        _lesson = lesson;
        _loading = false;
        _statusMessage = '';
      });

      return;
    }

    // --------------------------------------------------------
    // 3. Generation is already running
    // --------------------------------------------------------

    if ((status == 'generating' ||
            status == 'analyzing' ||
            status == 'video_generating') &&
        (jobId == null || jobId.isEmpty) &&
        lessonId != null &&
        lessonId.isNotEmpty) {
      setState(() {
        _statusMessage =
            'Your lesson is already being prepared...';
      });

      await _waitForExistingLesson(lessonId);

      return;
    }

    // --------------------------------------------------------
    // 4. New generation
    // --------------------------------------------------------

    if (jobId == null || jobId.isEmpty) {
      throw Exception(
        'The server did not return a job ID or lesson ID.',
      );
    }

    await _waitForLesson(jobId);
  } catch (e) {
    if (!mounted) return;

    setState(() {
      _loading = false;
      _statusMessage = '';
    });

    _showError(
      e.toString().replaceFirst(
        'Exception: ',
        '',
      ),
    );
  }
}

  // ============================================================
  // POLL LESSON JOB
  // ============================================================

  Future<void> _waitForLesson(
    String jobId,
  ) async {
    const maxAttempts = 120;

    for (int attempt = 0;
        attempt < maxAttempts;
        attempt++) {
      if (!mounted) return;

      setState(() {
        _statusMessage =
            _getProgressMessage(attempt);
      });

      final result =
          await ApiService.getLessonJobStatus(
        jobId,
      );

      final status =
          result['status']?.toString() ?? '';

      // --------------------------------------------------------
      // SUCCESS
      // --------------------------------------------------------

      if (status == 'SUCCESS') {
        final jobResult =
            result['result'];

        if (jobResult is! Map) {
          throw Exception(
            'Lesson generation succeeded, '
            'but no lesson information was returned.',
          );
        }

        final lessonId =
            jobResult['lesson_id']?.toString();

        if (lessonId == null ||
            lessonId.isEmpty) {
          throw Exception(
            'Lesson ID was not returned.',
          );
        }

        setState(() {
          _statusMessage =
              'Your lesson is ready! Loading it...';
        });

        final lesson =
            await ApiService.getLesson(lessonId);

        if (!mounted) return;

        setState(() {
          _lesson = lesson;
          _loading = false;
          _statusMessage = '';
        });

        return;
      }

      // --------------------------------------------------------
      // FAILURE
      // --------------------------------------------------------

      if (status == 'FAILURE') {
        final error =
            result['error']?.toString() ??
                'Lesson generation failed.';

        throw Exception(error);
      }

      // --------------------------------------------------------
      // WAIT
      // --------------------------------------------------------

      await Future.delayed(
        const Duration(seconds: 3),
      );
    }

    throw Exception(
      'Lesson generation is taking longer than expected. '
      'Please try again.',
    );
  }


  Future<void> _waitForExistingLesson(
  String lessonId,
) async {
  const maxAttempts = 120;

  for (int attempt = 0;
      attempt < maxAttempts;
      attempt++) {
    if (!mounted) return;

    setState(() {
      _statusMessage =
          'Preparing your lesson... ${attempt + 1}';
    });

    final lesson =
        await ApiService.getLesson(lessonId);

    final status =
        lesson['status']?.toString() ?? '';

    if (status == 'ready') {
      if (!mounted) return;

      setState(() {
        _lesson = lesson;
        _loading = false;
        _statusMessage = '';
      });

      return;
    }

    if (status == 'failed') {
      throw Exception(
        'Lesson generation failed.',
      );
    }

    await Future.delayed(
      const Duration(seconds: 5),
    );
  }

  throw Exception(
    'Lesson generation is taking too long. Please try again.',
  );
}

  // ============================================================
  // GET CHILD AGE
  // ============================================================

  int _getStudentAge() {
    final possibleAge =
        widget.child['age'];

    if (possibleAge is int) {
      return possibleAge;
    }

    if (possibleAge is String) {
      return int.tryParse(possibleAge) ?? 7;
    }

    return 7;
  }

  // ============================================================
  // PROGRESS MESSAGE
  // ============================================================

  String _getProgressMessage(
    int attempt,
  ) {
    if (attempt < 2) {
      return 'Understanding the chapter...';
    }

    if (attempt < 5) {
      return 'Finding the important concepts...';
    }

    if (attempt < 10) {
      return 'Creating a lesson for your child...';
    }

    if (attempt < 20) {
      return 'Preparing examples and explanations...';
    }

    if (attempt < 40) {
      return 'Preparing interactive questions...';
    }

    return 'Almost ready...';
  }

  // ============================================================
  // ERROR MESSAGE
  // ============================================================

  void _showError(String message) {
    if (!mounted) return;

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        duration: const Duration(seconds: 5),
      ),
    );
  }

  // ============================================================
  // BUILD
  // ============================================================

  @override
  Widget build(BuildContext context) {
    final chapterTitle =
        widget.chapter['title']?.toString() ??
            'Chapter';

    final subject =
        widget.chapter['subject']?.toString() ??
            '';

    final grade =
        widget.chapter['grade']?.toString() ??
            '';

    final childName =
        widget.child['name']?.toString() ??
            'Child';

    return Scaffold(
      appBar: AppBar(
        title: const Text('Learn'),
      ),

      body: _lesson == null
          ? _buildStartScreen(
              childName,
              chapterTitle,
              subject,
              grade,
            )
          : _buildLessonScreen(),
    );
  }

  // ============================================================
  // START SCREEN
  // ============================================================

  Widget _buildStartScreen(
    String childName,
    String chapterTitle,
    String subject,
    String grade,
  ) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,
        children: [
          Text(
            'Hello $childName 👋',
            style: const TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.bold,
            ),
          ),

          const SizedBox(height: 8),

          Text(
            'Let’s learn something interesting today!',
            style: TextStyle(
              fontSize: 16,
              color: Colors.grey.shade700,
            ),
          ),

          const SizedBox(height: 24),

          Card(
            elevation: 2,
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment:
                    CrossAxisAlignment.start,
                children: [
                  const Icon(
                    Icons.menu_book,
                    size: 50,
                  ),

                  const SizedBox(height: 16),

                  Text(
                    chapterTitle,
                    style: const TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                    ),
                  ),

                  const SizedBox(height: 8),

                  Text(
                    '$subject • Grade $grade',
                    style: TextStyle(
                      fontSize: 16,
                      color: Colors.grey.shade700,
                    ),
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: 30),

          const Text(
            'Ready to learn?',
            style: TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.bold,
            ),
          ),

          const SizedBox(height: 12),

          const Text(
            'AI will understand this chapter and '
            'create a simple, engaging lesson '
            'for your child.',
            style: TextStyle(
              fontSize: 16,
              height: 1.5,
            ),
          ),

          const SizedBox(height: 30),

          // ------------------------------------------------------
          // GENERATING
          // ------------------------------------------------------

          if (_loading) ...[
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                borderRadius:
                    BorderRadius.circular(12),
                color: Colors.grey.shade100,
              ),
              child: Column(
                children: [
                  const CircularProgressIndicator(),

                  const SizedBox(height: 18),

                  Text(
                    _statusMessage,
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight:
                          FontWeight.w500,
                    ),
                  ),

                  const SizedBox(height: 8),

                  const Text(
                    'Please wait while AI prepares '
                    'the lesson.',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
            ),
          ] else ...[
            // ----------------------------------------------------
            // START BUTTON
            // ----------------------------------------------------

            SizedBox(
              width: double.infinity,
              height: 55,
              child: ElevatedButton.icon(
                onPressed: _startLearning,
                icon: const Icon(
                  Icons.play_arrow,
                ),
                label: const Text(
                  'Start Learning',
                  style: TextStyle(
                    fontSize: 18,
                  ),
                ),
              ),
            ),
          ],

          const SizedBox(height: 20),

          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              borderRadius:
                  BorderRadius.circular(12),
              color: Colors.grey.shade100,
            ),
            child: const Column(
              crossAxisAlignment:
                  CrossAxisAlignment.start,
              children: [
                Text(
                  'What will happen?',
                  style: TextStyle(
                    fontSize: 17,
                    fontWeight:
                        FontWeight.bold,
                  ),
                ),

                SizedBox(height: 10),

                Text(
                  '• AI understands the uploaded chapter\n'
                  '• Important concepts are identified\n'
                  '• Concepts are explained step by step\n'
                  '• Real-life examples are provided\n'
                  '• Interactive questions are created',
                  style: TextStyle(
                    fontSize: 15,
                    height: 1.6,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ============================================================
  // LESSON SCREEN
  // ============================================================

  Widget _buildLessonScreen() {
    final payload =
        _lesson?['payload'];

    if (payload is! Map) {
      return const Center(
        child: Text(
          'Lesson data is unavailable.',
        ),
      );
    }

    final lesson =
        payload['lesson'];

    if (lesson is! Map) {
      return const Center(
        child: Text(
          'Lesson content is unavailable.',
        ),
      );
    }

    final title =
        lesson['title']?.toString() ??
            'AI Lesson';

    final introduction =
        lesson['introduction']?.toString() ??
            '';

    final explanation =
        lesson['explanation']?.toString() ??
            '';

    final example =
        lesson['example']?.toString() ??
            '';

    final funFact =
        lesson['fun_fact']?.toString() ??
            '';

    final conclusion =
        lesson['conclusion']?.toString() ??
            '';

    final objectives =
        _asStringList(
      lesson['objectives'],
    );

    final keyPoints =
        _asStringList(
      lesson['key_points'],
    );

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(
              fontSize: 28,
              fontWeight: FontWeight.bold,
            ),
          ),

          const SizedBox(height: 20),

          if (introduction.isNotEmpty)
            _lessonCard(
              title: 'Let’s Begin',
              icon: Icons.waving_hand,
              child: Text(
                introduction,
                style: const TextStyle(
                  fontSize: 17,
                  height: 1.6,
                ),
              ),
            ),

          if (objectives.isNotEmpty)
            _lessonCard(
              title: 'What You Will Learn',
              icon: Icons.flag,
              child: _bulletList(
                objectives,
              ),
            ),

          if (explanation.isNotEmpty)
            _lessonCard(
              title: 'Understand the Concept',
              icon: Icons.lightbulb,
              child: Text(
                explanation,
                style: const TextStyle(
                  fontSize: 17,
                  height: 1.7,
                ),
              ),
            ),

          if (example.isNotEmpty)
            _lessonCard(
              title: 'Real-Life Example',
              icon: Icons.public,
              child: Text(
                example,
                style: const TextStyle(
                  fontSize: 17,
                  height: 1.7,
                ),
              ),
            ),

          if (keyPoints.isNotEmpty)
            _lessonCard(
              title: 'Remember These',
              icon: Icons.check_circle,
              child: _bulletList(
                keyPoints,
              ),
            ),

          if (funFact.isNotEmpty)
            _lessonCard(
              title: 'Fun Fact',
              icon: Icons.auto_awesome,
              child: Text(
                funFact,
                style: const TextStyle(
                  fontSize: 17,
                  height: 1.7,
                ),
              ),
            ),

          if (conclusion.isNotEmpty)
            _lessonCard(
              title: 'Quick Recap',
              icon: Icons.refresh,
              child: Text(
                conclusion,
                style: const TextStyle(
                  fontSize: 17,
                  height: 1.7,
                ),
              ),
            ),

          const SizedBox(height: 20),

          // ------------------------------------------------------
          // AI TEACHING VIDEO
          // ------------------------------------------------------

          _builderVideoButton(),

          const SizedBox(height: 16),

          // ------------------------------------------------------
          // PRACTICE QUESTIONS
          // ------------------------------------------------------

          SizedBox(
            width: double.infinity,
            height: 55,
            child: ElevatedButton.icon(
              onPressed: () {
                if (_lesson == null) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('Lesson is not ready yet.'),
                    ),
                  );
                  return;
                }

                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => PracticeQuestionsScreen(
                      lesson: _lesson!,
                      child: widget.child,
                    ),
                  ),
                );
              },
              icon: const Icon(
                Icons.quiz,
              ),
              label: const Text(
                'Practice Questions',
                style: TextStyle(
                  fontSize: 17,
                ),
              ),
            ),
          ),

          const SizedBox(height: 30),

        ],
      ),
    );
  }

  // ============================================================
  // LESSON CARD
  // ============================================================

  Widget _lessonCard({
    required String title,
    required IconData icon,
    required Widget child,
  }) {
    return Card(
      margin: const EdgeInsets.only(
        bottom: 16,
      ),
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment:
              CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon),

                const SizedBox(width: 10),

                Expanded(
                  child: Text(
                    title,
                    style: const TextStyle(
                      fontSize: 19,
                      fontWeight:
                          FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 14),

            child,
          ],
        ),
      ),
    );
  }

  // ============================================================
  // BULLET LIST
  // ============================================================

  Widget _bulletList(
    List<String> items,
  ) {
    return Column(
      crossAxisAlignment:
          CrossAxisAlignment.start,
      children: items.map(
        (item) {
          return Padding(
            padding:
                const EdgeInsets.only(
              bottom: 10,
            ),
            child: Row(
              crossAxisAlignment:
                  CrossAxisAlignment.start,
              children: [
                const Text(
                  '• ',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight:
                        FontWeight.bold,
                  ),
                ),

                Expanded(
                  child: Text(
                    item,
                    style: const TextStyle(
                      fontSize: 16,
                      height: 1.5,
                    ),
                  ),
                ),
              ],
            ),
          );
        },
      ).toList(),
    );
  }

  // ============================================================
  // SAFE STRING LIST
  // ============================================================

  List<String> _asStringList(
    dynamic value,
  ) {
    if (value is! List) {
      return [];
    }

    return value
        .map(
          (item) => item.toString(),
        )
        .toList();
  }

Widget _builderVideoButton() {
  final videoUrl = _lesson?['video_url']?.toString();

  if (videoUrl == null || videoUrl.isEmpty) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        color: Colors.grey.shade100,
      ),
      child: const Row(
        children: [
          Icon(Icons.hourglass_empty),
          SizedBox(width: 12),
          Expanded(
            child: Text(
              'The teaching video is not available yet.',
              style: TextStyle(
                fontSize: 15,
              ),
            ),
          ),
        ],
      ),
    );
  }

  return SizedBox(
    width: double.infinity,
    height: 60,
    child: ElevatedButton.icon(
      onPressed: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => LessonVideoScreen(
              videoUrl: videoUrl,
              title: _lesson?['title']?.toString() ??
                  'AI Teaching Lesson',
            ),
          ),
        );
      },
      icon: const Icon(
        Icons.play_circle_fill,
        size: 30,
      ),
      label: const Text(
        'Watch AI Teaching Video',
        style: TextStyle(
          fontSize: 18,
          fontWeight: FontWeight.bold,
        ),
      ),
    ),
  );
}


}

