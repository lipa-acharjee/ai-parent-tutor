import 'package:flutter/material.dart';
import '../../services/api_service.dart';

class PracticeQuestionsScreen extends StatefulWidget {
  final Map<String, dynamic> lesson;
  final Map<String, dynamic> child;

  const PracticeQuestionsScreen({
    super.key,
    required this.lesson,
    required this.child,
  });

  @override
  State<PracticeQuestionsScreen> createState() =>
      _PracticeQuestionsScreenState();
}

class _PracticeQuestionsScreenState
    extends State<PracticeQuestionsScreen> {
  final TextEditingController _answerController =
      TextEditingController();

  List<dynamic> _questions = [];

  int _currentIndex = 0;

  bool _loading = true;
  bool _submitting = false;
  bool _finished = false;

  Map<String, dynamic>? _result;

  int _correctAnswers = 0;
  int _totalScore = 0;

  String? _selectedOption;

  @override
  void initState() {
    super.initState();
    _loadQuestions();
  }

  @override
  void dispose() {
    _answerController.dispose();
    super.dispose();
  }

  void _loadQuestions() {
    try {
      List<dynamic> questions = [];

      // First try:
      // lesson["questions"]
      final questionsData = widget.lesson['questions'];

      if (questionsData is List) {
        questions = questionsData;
      } else if (questionsData is Map) {
        final nestedQuestions = questionsData['questions'];

        if (nestedQuestions is List) {
          questions = nestedQuestions;
        }
      }

      // Fallback:
      // lesson["payload"]["questions"]
      if (questions.isEmpty) {
        final payload = widget.lesson['payload'];

        if (payload is Map) {
          final payloadQuestions = payload['questions'];

          if (payloadQuestions is List) {
            questions = payloadQuestions;
          } else if (payloadQuestions is Map) {
            final nestedQuestions =
                payloadQuestions['questions'];

            if (nestedQuestions is List) {
              questions = nestedQuestions;
            }
          }
        }
      }

      setState(() {
        _questions = questions;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _loading = false;
      });

      _showError('Could not load questions: $e');
    }
  }

  Future<void> _submitAnswer() async {
    if (_submitting) return;

    String answer = '';

    // If an option is selected, use that.
    if (_selectedOption != null) {
      answer = _selectedOption!.trim();
    } else {
      answer = _answerController.text.trim();
    }

    if (answer.isEmpty) {
      _showError('Please select or write an answer first.');
      return;
    }

    if (_questions.isEmpty) {
      _showError('No questions available.');
      return;
    }

    final question =
        Map<String, dynamic>.from(_questions[_currentIndex]);

    final questionId = question['id']?.toString();
    final childId = widget.child['id']?.toString();

    if (questionId == null || questionId.isEmpty) {
      _showError('Question ID is missing.');
      return;
    }

    if (childId == null || childId.isEmpty) {
      _showError('Child ID is missing.');
      return;
    }

    setState(() {
      _submitting = true;
    });

    try {
      final result = await ApiService.submitAnswer(
        questionId: questionId,
        childId: childId,
        answer: answer,
      );

      if (!mounted) return;

      final score = _getScore(result);

      if (score > 0) {
        _correctAnswers++;
      }

      _totalScore += score;

      setState(() {
        _result = result;
        _submitting = false;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        _submitting = false;
      });

      _showError(
        e.toString().replaceFirst('Exception: ', ''),
      );
    }
  }

  int _getScore(Map<String, dynamic> result) {
    final score = result['score'];

    if (score is int) {
      return score;
    }

    if (score is double) {
      return score.round();
    }

    if (score is num) {
      return score.toInt();
    }

    return 0;
  }

  void _nextQuestion() {
    if (_currentIndex >= _questions.length - 1) {
      _finishPractice();
      return;
    }

    setState(() {
      _currentIndex++;
      _answerController.clear();
      _selectedOption = null;
      _result = null;
    });
  }

  void _finishPractice() {
    setState(() {
      _finished = true;
    });
  }

  void _restartPractice() {
    setState(() {
      _currentIndex = 0;
      _correctAnswers = 0;
      _totalScore = 0;
      _result = null;
      _finished = false;
      _selectedOption = null;
      _answerController.clear();
    });
  }

  void _showError(String message) {
    if (!mounted) return;

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  Widget _buildLoading() {
    return const Center(
      child: CircularProgressIndicator(),
    );
  }

  Widget _buildNoQuestions() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.quiz_outlined,
              size: 70,
            ),
            const SizedBox(height: 20),
            const Text(
              'No practice questions found',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            Text(
              'This lesson does not contain any practice questions yet.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey.shade700,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildQuestion() {
    final question =
        Map<String, dynamic>.from(_questions[_currentIndex]);

    final questionText =
        question['question']?.toString() ?? 'Question';

    final expectedAnswer =
        question['expected_answer']?.toString() ?? '';

    final explanation =
        question['explanation']?.toString() ?? '';

    final progress =
        (_currentIndex + 1) / _questions.length;

    final options = _getOptions(question);

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Question ${_currentIndex + 1} of ${_questions.length}',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w600,
              color: Colors.grey.shade700,
            ),
          ),

          const SizedBox(height: 10),

          LinearProgressIndicator(
            value: progress,
            minHeight: 8,
            borderRadius: BorderRadius.circular(10),
          ),

          const SizedBox(height: 28),

          Card(
            elevation: 2,
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment:
                    CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Think and answer',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),

                  const SizedBox(height: 14),

                  Text(
                    questionText,
                    style: const TextStyle(
                      fontSize: 21,
                      height: 1.5,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: 24),

          // --------------------------------------------------
          // MULTIPLE CHOICE
          // --------------------------------------------------

          if (options.isNotEmpty)
            _buildOptions(options),

          // --------------------------------------------------
          // WRITTEN ANSWER
          // --------------------------------------------------

          if (options.isEmpty)
            _buildAnswerBox(),

          const SizedBox(height: 20),

          if (_result == null)
            SizedBox(
              width: double.infinity,
              height: 54,
              child: ElevatedButton.icon(
                onPressed:
                    _submitting ? null : _submitAnswer,
                icon: _submitting
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                        ),
                      )
                    : const Icon(Icons.send),
                label: Text(
                  _submitting
                      ? 'AI is evaluating...'
                      : 'Submit Answer',
                  style: const TextStyle(
                    fontSize: 17,
                  ),
                ),
              ),
            ),

          if (_result != null)
            _buildFeedback(
              expectedAnswer: expectedAnswer,
              explanation: explanation,
            ),
        ],
      ),
    );
  }

  List<String> _getOptions(
    Map<String, dynamic> question,
  ) {
    final rawOptions = question['options'];

    if (rawOptions is List) {
      return rawOptions
          .map((option) => option.toString())
          .where((option) => option.trim().isNotEmpty)
          .toList();
    }

    return [];
  }

  Widget _buildOptions(List<String> options) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Choose the best answer:',
          style: TextStyle(
            fontSize: 17,
            fontWeight: FontWeight.bold,
          ),
        ),

        const SizedBox(height: 12),

        ...options.map(
          (option) {
            final selected =
                _selectedOption == option;

            return Card(
              margin: const EdgeInsets.only(bottom: 10),
              child: RadioListTile<String>(
                value: option,
                groupValue: _selectedOption,
                onChanged: _result != null || _submitting
                    ? null
                    : (value) {
                        setState(() {
                          _selectedOption = value;
                        });
                      },
                title: Text(
                  option,
                  style: const TextStyle(
                    fontSize: 16,
                  ),
                ),
                selected: selected,
              ),
            );
          },
        ),
      ],
    );
  }

  Widget _buildAnswerBox() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Write your answer:',
          style: TextStyle(
            fontSize: 17,
            fontWeight: FontWeight.bold,
          ),
        ),

        const SizedBox(height: 12),

        TextField(
          controller: _answerController,
          enabled:
              _result == null && !_submitting,
          maxLines: 6,
          minLines: 4,
          textInputAction:
              TextInputAction.newline,
          decoration: InputDecoration(
            hintText:
                'Write your answer here...',
            alignLabelWithHint: true,
            border: OutlineInputBorder(
              borderRadius:
                  BorderRadius.circular(12),
            ),
            filled: true,
            contentPadding:
                const EdgeInsets.all(16),
          ),
        ),
      ],
    );
  }

  Widget _buildFeedback({
    required String expectedAnswer,
    required String explanation,
  }) {
    final result = _result!;

    final score = _getScore(result);

    final feedback =
        result['feedback']?.toString() ??
        result['message']?.toString() ??
        result['explanation']?.toString() ??
        'Answer evaluated successfully.';

    final isCorrect = score > 0;

    return Column(
      crossAxisAlignment:
          CrossAxisAlignment.start,
      children: [
        Card(
          elevation: 2,
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment:
                  CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(
                      isCorrect
                          ? Icons.check_circle
                          : Icons.info,
                      size: 30,
                    ),

                    const SizedBox(width: 10),

                    Text(
                      isCorrect
                          ? 'Great job!'
                          : 'Let’s learn from this',
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),

                const SizedBox(height: 16),

                Text(
                  'Score: $score',
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),

                const SizedBox(height: 14),

                const Text(
                  'AI Feedback',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),

                const SizedBox(height: 8),

                Text(
                  feedback,
                  style: const TextStyle(
                    fontSize: 16,
                    height: 1.5,
                  ),
                ),
              ],
            ),
          ),
        ),

        const SizedBox(height: 16),

        if (expectedAnswer.isNotEmpty)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment:
                    CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Expected Answer',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),

                  const SizedBox(height: 8),

                  Text(
                    expectedAnswer,
                    style: const TextStyle(
                      fontSize: 15,
                      height: 1.5,
                    ),
                  ),
                ],
              ),
            ),
          ),

        if (explanation.isNotEmpty) ...[
          const SizedBox(height: 12),

          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment:
                    CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Why?',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),

                  const SizedBox(height: 8),

                  Text(
                    explanation,
                    style: const TextStyle(
                      fontSize: 15,
                      height: 1.5,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],

        const SizedBox(height: 24),

        SizedBox(
          width: double.infinity,
          height: 54,
          child: ElevatedButton.icon(
            onPressed: _nextQuestion,
            icon: Icon(
              _currentIndex ==
                      _questions.length - 1
                  ? Icons.done
                  : Icons.arrow_forward,
            ),
            label: Text(
              _currentIndex ==
                      _questions.length - 1
                  ? 'Finish Practice'
                  : 'Next Question',
              style: const TextStyle(
                fontSize: 17,
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildFinished() {
    final totalQuestions = _questions.length;

    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            const Icon(
              Icons.emoji_events,
              size: 90,
            ),

            const SizedBox(height: 20),

            const Text(
              'Practice Complete!',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 12),

            Text(
              'Great work, '
              '${widget.child['name'] ?? 'Student'}!',
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 18,
              ),
            ),

            const SizedBox(height: 30),

            Card(
              elevation: 3,
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  children: [
                    const Text(
                      'Your Result',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                    ),

                    const SizedBox(height: 24),

                    Text(
                      '$_correctAnswers / '
                      '$totalQuestions',
                      style: const TextStyle(
                        fontSize: 42,
                        fontWeight: FontWeight.bold,
                      ),
                    ),

                    const SizedBox(height: 8),

                    const Text(
                      'Questions answered positively',
                      textAlign: TextAlign.center,
                    ),

                    const SizedBox(height: 20),

                    Text(
                      'Total Score: $_totalScore',
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight:
                            FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 30),

            SizedBox(
              width: double.infinity,
              height: 54,
              child: ElevatedButton.icon(
                onPressed: _restartPractice,
                icon: const Icon(Icons.refresh),
                label: const Text(
                  'Practice Again',
                  style: TextStyle(
                    fontSize: 17,
                  ),
                ),
              ),
            ),

            const SizedBox(height: 12),

            SizedBox(
              width: double.infinity,
              height: 54,
              child: OutlinedButton(
                onPressed: () {
                  Navigator.pop(context);
                },
                child: const Text(
                  'Back to Lesson',
                  style: TextStyle(
                    fontSize: 17,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Practice Questions',
        ),
      ),
      body: _loading
          ? _buildLoading()
          : _questions.isEmpty
              ? _buildNoQuestions()
              : _finished
                  ? _buildFinished()
                  : _buildQuestion(),
    );
  }
}
