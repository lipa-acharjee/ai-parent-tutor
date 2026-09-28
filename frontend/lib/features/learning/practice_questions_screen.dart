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
  int currentQuestionIndex = 0;

  String? selectedAnswer;

  bool isSubmitting = false;
  bool showResult = false;

  Map<String, dynamic>? evaluationResult;

  List<dynamic> questions = [];

  @override
  void initState() {
    super.initState();

    _loadQuestions();
  }

  // ============================================================
  // LOAD QUESTIONS
  // ============================================================

  void _loadQuestions() {
    try {
      List<dynamic> loadedQuestions = [];

      final rawQuestions =
          widget.lesson['questions'];

      // --------------------------------------------------------
      // Top-level questions
      // --------------------------------------------------------

      if (rawQuestions is List) {
        loadedQuestions = rawQuestions;
      }

      // --------------------------------------------------------
      // Top-level questions object
      // {
      //   "questions": [...]
      // }
      // --------------------------------------------------------

      else if (rawQuestions is Map) {
        final nestedQuestions =
            rawQuestions['questions'];

        if (nestedQuestions is List) {
          loadedQuestions = nestedQuestions;
        }
      }

      // --------------------------------------------------------
      // Fallback: payload.questions
      // --------------------------------------------------------

      if (loadedQuestions.isEmpty) {
        final payload =
            widget.lesson['payload'];

        if (payload is Map) {
          final payloadQuestions =
              payload['questions'];

          if (payloadQuestions is List) {
            loadedQuestions =
                payloadQuestions;
          } else if (payloadQuestions is Map) {
            final nestedQuestions =
                payloadQuestions['questions'];

            if (nestedQuestions is List) {
              loadedQuestions =
                  nestedQuestions;
            }
          }
        }
      }

      debugPrint(
        '========== PRACTICE SCREEN =========='
      );

      debugPrint(
        'LESSON RECEIVED: ${widget.lesson}'
      );

      debugPrint(
        'QUESTIONS FOUND: ${loadedQuestions.length}'
      );

      for (int i = 0;
          i < loadedQuestions.length;
          i++) {
        debugPrint(
          'QUESTION ${i + 1}: ${loadedQuestions[i]}'
        );
      }

      debugPrint(
        '======================================'
      );

      if (!mounted) return;

      setState(() {
        questions = loadedQuestions;
      });
    } catch (e) {
      debugPrint(
        'ERROR LOADING QUESTIONS: $e'
      );

      if (!mounted) return;

      setState(() {
        questions = [];
      });
    }
  }

  // ============================================================
  // CURRENT QUESTION
  // ============================================================

  dynamic get currentQuestion {
    if (questions.isEmpty) {
      return null;
    }

    if (currentQuestionIndex >= questions.length) {
      return null;
    }

    return questions[currentQuestionIndex];
  }

  // ============================================================
  // QUESTION TEXT
  // ============================================================

  String _getQuestionText() {
    final question = currentQuestion;

    if (question is Map) {
      return question['question']?.toString() ?? '';
    }

    return '';
  }

  // ============================================================
  // QUESTION ID
  // ============================================================

  String _getQuestionId() {
    final question = currentQuestion;

    if (question is Map) {
      return question['id']?.toString() ?? '';
    }

    return '';
  }

  // ============================================================
  // GET OPTIONS
  // ============================================================

  List<String> _getOptions() {
    final question = currentQuestion;

    if (question is! Map) {
      return [];
    }

    final rawOptions =
        question['options'];

    if (rawOptions is! List) {
      return [];
    }

    final options = <String>[];

    for (final option in rawOptions) {
      // --------------------------------------------------------
      // Option is a simple string
      // --------------------------------------------------------

      if (option is String) {
        final value = option.trim();

        if (value.isNotEmpty) {
          options.add(value);
        }

        continue;
      }

      // --------------------------------------------------------
      // Option is an object
      // Example:
      // {
      //   "label": "Earth"
      // }
      // --------------------------------------------------------

      if (option is Map) {
        final label =
            option['label']?.toString().trim();

        if (label != null &&
            label.isNotEmpty) {
          options.add(label);
        }
      }
    }

    return options;
  }

  // ============================================================
  // SUBMIT ANSWER
  // ============================================================

  Future<void> _submitAnswer() async {
    if (selectedAnswer == null ||
        selectedAnswer!.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Please select an answer first.',
          ),
        ),
      );

      return;
    }

    final questionId =
        _getQuestionId();

    final childId =
        widget.child['id']?.toString();

    if (questionId.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Question ID is missing.',
          ),
        ),
      );

      return;
    }

    if (childId == null ||
        childId.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Child ID is missing.',
          ),
        ),
      );

      return;
    }

    setState(() {
      isSubmitting = true;
    });

    try {
      final result =
          await ApiService.submitAnswer(
        questionId: questionId,
        childId: childId,
        answer: selectedAnswer!,
      );

      if (!mounted) return;

      setState(() {
        evaluationResult = result;
        showResult = true;
        isSubmitting = false;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        isSubmitting = false;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Could not check answer: $e',
          ),
        ),
      );
    }
  }

  // ============================================================
  // NEXT QUESTION
  // ============================================================

  void _nextQuestion() {
    if (currentQuestionIndex >=
        questions.length - 1) {
      _showCompletionDialog();
      return;
    }

    setState(() {
      currentQuestionIndex++;
      selectedAnswer = null;
      evaluationResult = null;
      showResult = false;
    });
  }

  // ============================================================
  // TRY AGAIN
  // ============================================================

  void _tryAgain() {
    setState(() {
      selectedAnswer = null;
      evaluationResult = null;
      showResult = false;
    });
  }

  // ============================================================
  // COMPLETION
  // ============================================================

  void _showCompletionDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) {
        return AlertDialog(
          title: const Text(
            'Practice Complete! 🎉',
          ),
          content: const Text(
            'Great work! You have completed '
            'all the practice questions.',
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(context).pop();
                Navigator.of(context).pop();
              },
              child: const Text('Done'),
            ),
          ],
        );
      },
    );
  }

  // ============================================================
  // RESULT COLOR
  // ============================================================

  Color _resultColor() {
    final score =
        evaluationResult?['score'];

    if (score is num && score > 0) {
      return Colors.green;
    }

    return Colors.orange;
  }

  // ============================================================
  // FEEDBACK TEXT
  // ============================================================

  String _feedbackText() {
    final result =
        evaluationResult;

    if (result == null) {
      return '';
    }

    if (result['feedback'] != null) {
      return result['feedback'].toString();
    }

    if (result['explanation'] != null) {
      return result['explanation'].toString();
    }

    if (result['message'] != null) {
      return result['message'].toString();
    }

    return result.toString();
  }

  // ============================================================
  // BUILD
  // ============================================================

  @override
  Widget build(BuildContext context) {
    final childName =
        widget.child['name']?.toString() ??
            'Child';

    // ----------------------------------------------------------
    // No questions
    // ----------------------------------------------------------

    if (questions.isEmpty) {
      return Scaffold(
        appBar: AppBar(
          title: const Text(
            'Practice Questions',
          ),
        ),
        body: const Center(
          child: Padding(
            padding: EdgeInsets.all(20),
            child: Text(
              'No practice questions are available.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 18,
              ),
            ),
          ),
        ),
      );
    }

    final questionText =
        _getQuestionText();

    final options =
        _getOptions();

    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Practice Questions',
        ),
      ),

      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),

        child: Column(
          crossAxisAlignment:
              CrossAxisAlignment.start,

          children: [
            // --------------------------------------------------
            // CHILD GREETING
            // --------------------------------------------------

            Text(
              'Hi $childName 👋',
              style: const TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 8),

            Text(
              'Let’s check what you learned!',
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey.shade700,
              ),
            ),

            const SizedBox(height: 24),

            // --------------------------------------------------
            // PROGRESS
            // --------------------------------------------------

            LinearProgressIndicator(
              value:
                  (currentQuestionIndex + 1) /
                      questions.length,
            ),

            const SizedBox(height: 12),

            Text(
              'Question '
              '${currentQuestionIndex + 1} '
              'of ${questions.length}',
              style: const TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.w600,
              ),
            ),

            const SizedBox(height: 24),

            // --------------------------------------------------
            // QUESTION
            // --------------------------------------------------

            Card(
              elevation: 2,

              child: Padding(
                padding:
                    const EdgeInsets.all(20),

                child: Text(
                  questionText,

                  style: const TextStyle(
                    fontSize: 20,
                    height: 1.5,
                    fontWeight:
                        FontWeight.w600,
                  ),
                ),
              ),
            ),

            const SizedBox(height: 20),

            // --------------------------------------------------
            // OPTIONS
            // --------------------------------------------------

            if (options.isNotEmpty)
              ...options.asMap().entries.map(
                (entry) {
                  final optionIndex =
                      entry.key;

                  final option =
                      entry.value;

                  final optionLetter =
                      String.fromCharCode(
                    65 + optionIndex,
                  );

                  final isSelected =
                      selectedAnswer ==
                          option;

                  return Padding(
                    padding:
                        const EdgeInsets.only(
                      bottom: 12,
                    ),

                    child: InkWell(
                      onTap: showResult
                          ? null
                          : () {
                              setState(() {
                                selectedAnswer =
                                    option;
                              });
                            },

                      borderRadius:
                          BorderRadius.circular(
                        12,
                      ),

                      child: Container(
                        width:
                            double.infinity,

                        padding:
                            const EdgeInsets.all(
                          16,
                        ),

                        decoration:
                            BoxDecoration(
                          borderRadius:
                              BorderRadius
                                  .circular(12),

                          border: Border.all(
                            width: 2,

                            color: isSelected
                                ? Theme.of(
                                    context,
                                  )
                                    .colorScheme
                                    .primary
                                : Colors
                                    .grey
                                    .shade300,
                          ),
                        ),

                        child: Row(
                          children: [
                            Radio<String>(
                              value: option,

                              groupValue:
                                  selectedAnswer,

                              onChanged:
                                  showResult
                                      ? null
                                      : (value) {
                                          setState(() {
                                            selectedAnswer =
                                                value;
                                          });
                                        },
                            ),

                            Container(
                              width: 30,
                              height: 30,

                              alignment:
                                  Alignment.center,

                              decoration:
                                  BoxDecoration(
                                shape:
                                    BoxShape.circle,

                                color: isSelected
                                    ? Theme.of(
                                        context,
                                      )
                                        .colorScheme
                                        .primary
                                    : Colors
                                        .grey
                                        .shade200,
                              ),

                              child: Text(
                                optionLetter,

                                style: TextStyle(
                                  fontWeight:
                                      FontWeight.bold,

                                  color: isSelected
                                      ? Colors.white
                                      : Colors.black87,
                                ),
                              ),
                            ),

                            const SizedBox(
                              width: 12,
                            ),

                            Expanded(
                              child: Text(
                                option,

                                style:
                                    const TextStyle(
                                  fontSize: 16,
                                  height: 1.4,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  );
                },
              ),

            // --------------------------------------------------
            // NO OPTIONS
            // --------------------------------------------------

            if (options.isEmpty)
              Container(
                width: double.infinity,

                padding:
                    const EdgeInsets.all(16),

                decoration: BoxDecoration(
                  borderRadius:
                      BorderRadius.circular(12),

                  color:
                      Colors.orange.shade50,

                  border: Border.all(
                    color:
                        Colors.orange.shade300,
                  ),
                ),

                child: const Text(
                  'This question was generated '
                  'without answer choices. '
                  'We need to update the AI '
                  'question generator to create '
                  'multiple-choice answers.',
                  style: TextStyle(
                    fontSize: 16,
                    height: 1.5,
                  ),
                ),
              ),

            const SizedBox(height: 20),

            // --------------------------------------------------
            // RESULT
            // --------------------------------------------------

            if (showResult &&
                evaluationResult != null)
              Container(
                width: double.infinity,

                padding:
                    const EdgeInsets.all(18),

                decoration:
                    BoxDecoration(
                  color: _resultColor()
                      .withValues(
                    alpha: 0.10,
                  ),

                  borderRadius:
                      BorderRadius.circular(
                    12,
                  ),

                  border: Border.all(
                    color:
                        _resultColor(),
                  ),
                ),

                child: Column(
                  crossAxisAlignment:
                      CrossAxisAlignment.start,

                  children: [
                    Text(
                      (evaluationResult?[
                                      'score']
                                  is num &&
                              (evaluationResult![
                                          'score']
                                      as num) >
                                  0)
                          ? '🎉 Great job!'
                          : '💡 Let’s learn from this',

                      style: TextStyle(
                        fontSize: 20,
                        fontWeight:
                            FontWeight.bold,
                        color:
                            _resultColor(),
                      ),
                    ),

                    const SizedBox(height: 10),

                    Text(
                      _feedbackText(),

                      style:
                          const TextStyle(
                        fontSize: 16,
                        height: 1.5,
                      ),
                    ),
                  ],
                ),
              ),

            const SizedBox(height: 24),

            // --------------------------------------------------
            // BUTTON
            // --------------------------------------------------

            SizedBox(
              width: double.infinity,
              height: 55,

              child: ElevatedButton(
                onPressed: isSubmitting
                    ? null
                    : showResult
                        ? _nextQuestion
                        : options.isEmpty
                            ? null
                            : _submitAnswer,

                child: isSubmitting
                    ? const SizedBox(
                        width: 24,
                        height: 24,

                        child:
                            CircularProgressIndicator(
                          strokeWidth: 2,
                        ),
                      )

                    : Text(
                        showResult
                            ? currentQuestionIndex ==
                                    questions.length -
                                        1
                                ? 'Finish'
                                : 'Next Question'
                            : 'Check Answer',

                        style:
                            const TextStyle(
                          fontSize: 18,
                        ),
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
