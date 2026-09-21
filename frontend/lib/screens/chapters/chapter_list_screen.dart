import 'package:flutter/material.dart';

import '../../services/api_service.dart';
import 'chapter_upload_screen.dart';
import '../learning/learn_chapter_screen.dart';

class ChapterListScreen extends StatefulWidget {
  final Map<String, dynamic> child;

  const ChapterListScreen({
    super.key,
    required this.child,
  });

  @override
  State<ChapterListScreen> createState() =>
      _ChapterListScreenState();
}

class _ChapterListScreenState
    extends State<ChapterListScreen> {
  bool _isLoading = true;
  String? _error;
  List<dynamic> _chapters = [];

  final TextEditingController _topicController =
      TextEditingController();

  bool _isCreatingChapter = false;

  // Keeps track of the chapter currently being deleted.
  String? _deletingChapterId;

  @override
  void initState() {
    super.initState();
    _loadChapters();
  }

  @override
  void dispose() {
    _topicController.dispose();
    super.dispose();
  }

  // ============================================================
  // LOAD CHAPTERS
  // ============================================================

  Future<void> _loadChapters() async {
    try {
      debugPrint('CHILD DATA: ${widget.child}');

      final childId =
          widget.child['id'].toString();

      final chapters =
          await ApiService.getChapters(childId);

      if (!mounted) return;

      setState(() {
        _chapters = chapters;
        _isLoading = false;
        _error = null;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  // ============================================================
  // CREATE CHAPTER WITH AI
  // ============================================================

  Future<void> _createChapterWithAI() async {
    final topic =
        _topicController.text.trim();

    if (topic.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Please enter what you would like your child to learn.',
          ),
        ),
      );
      return;
    }

    final childId =
        widget.child['id']?.toString();

    final grade =
        widget.child['grade']?.toString();

    debugPrint(
      'CHILD DATA: ${widget.child}',
    );

    if (childId == null || childId.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Child ID is missing.',
          ),
        ),
      );
      return;
    }

    if (grade == null || grade.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Child grade is missing.',
          ),
        ),
      );
      return;
    }

    setState(() {
      _isCreatingChapter = true;
    });

    try {
      await ApiService.createChapterFromText(
        childId: childId,
        text: topic,
        grade: grade,
      );

      if (!mounted) return;

      _topicController.clear();

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            '✨ Chapter created successfully!',
          ),
        ),
      );

      await _loadChapters();
    } catch (e) {
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Failed to create chapter: $e',
          ),
        ),
      );
    } finally {
      if (!mounted) return;

      setState(() {
        _isCreatingChapter = false;
      });
    }
  }

  // ============================================================
  // DELETE CHAPTER
  // ============================================================

  Future<void> _deleteChapter(
    dynamic chapter,
  ) async {
    final chapterId =
        chapter['id']?.toString();

    final title =
        chapter['title']?.toString() ??
            'this chapter';

    if (chapterId == null || chapterId.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Chapter ID is missing.',
          ),
        ),
      );
      return;
    }

    // ----------------------------------------------------------
    // Confirmation dialog
    // ----------------------------------------------------------

    final confirmed =
        await showDialog<bool>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: const Text(
            'Delete Chapter?',
          ),
          content: Text(
            'Are you sure you want to delete "$title"?\n\n'
            'This will also remove its lessons, questions, '
            'and stored files.',
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.pop(
                  dialogContext,
                  false,
                );
              },
              child: const Text(
                'Cancel',
              ),
            ),
            FilledButton(
              onPressed: () {
                Navigator.pop(
                  dialogContext,
                  true,
                );
              },
              child: const Text(
                'Delete',
              ),
            ),
          ],
        );
      },
    );

    if (confirmed != true) {
      return;
    }

    // ----------------------------------------------------------
    // Delete
    // ----------------------------------------------------------

    if (!mounted) return;

    setState(() {
      _deletingChapterId = chapterId;
    });

    try {
      await ApiService.deleteChapter(
        chapterId,
      );

      if (!mounted) return;

      // Remove immediately from the local list.
      setState(() {
        _chapters.removeWhere(
          (item) =>
              item['id']?.toString() ==
              chapterId,
        );
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            '🗑️ "$title" deleted successfully.',
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Failed to delete chapter: $e',
          ),
        ),
      );
    } finally {
      if (!mounted) return;

      setState(() {
        _deletingChapterId = null;
      });
    }
  }

  // ============================================================
  // OPEN UPLOAD SCREEN
  // ============================================================

  Future<void> _openUploadScreen() async {
    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) =>
            ChapterUploadScreen(
          child:
              Map<String, dynamic>.from(
            widget.child,
          ),
        ),
      ),
    );

    _loadChapters();
  }

  @override
  Widget build(BuildContext context) {
    final childName =
        widget.child['name']?.toString() ??
            'Child';

    final grade =
        widget.child['grade']?.toString() ??
            '';

    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Chapters',
        ),
      ),

      floatingActionButton:
          FloatingActionButton.extended(
        onPressed: _openUploadScreen,
        icon: const Icon(
          Icons.upload_file,
        ),
        label: const Text(
          'Upload',
        ),
      ),

      body: RefreshIndicator(
        onRefresh: _loadChapters,
        child: _buildBody(
          childName,
          grade,
        ),
      ),
    );
  }

  // ============================================================
  // BODY
  // ============================================================

  Widget _buildBody(
    String childName,
    String grade,
  ) {
    if (_isLoading) {
      return ListView(
        children: const [
          SizedBox(
            height: 300,
            child: Center(
              child: CircularProgressIndicator(),
            ),
          ),
        ],
      );
    }

    if (_error != null) {
      return ListView(
        padding: const EdgeInsets.all(20),
        children: [
          const SizedBox(
            height: 100,
          ),

          const Icon(
            Icons.error_outline,
            size: 60,
          ),

          const SizedBox(
            height: 20,
          ),

          Text(
            _error!,
            textAlign: TextAlign.center,
          ),

          const SizedBox(
            height: 20,
          ),

          Center(
            child: ElevatedButton(
              onPressed: _loadChapters,
              child: const Text(
                'Try Again',
              ),
            ),
          ),
        ],
      );
    }

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _buildCreateChapterCard(),

        const SizedBox(
          height: 24,
        ),

        Text(
          '$childName • Grade $grade',
          style: const TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
        ),

        const SizedBox(
          height: 6,
        ),

        Text(
          '${_chapters.length} chapter'
          '${_chapters.length == 1 ? '' : 's'}',
          style: TextStyle(
            color: Colors.grey.shade700,
          ),
        ),

        const SizedBox(
          height: 16,
        ),

        if (_chapters.isEmpty)
          _buildEmptyChapterMessage()
        else
          ..._chapters.map(
            (chapter) =>
                _buildChapterCard(chapter),
          ),
      ],
    );
  }

  // ============================================================
  // CREATE CHAPTER CARD
  // ============================================================

  Widget _buildCreateChapterCard() {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment:
              CrossAxisAlignment.start,
          children: [
            const Text(
              '✨ Create a Chapter with AI',
              style: TextStyle(
                fontSize: 21,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(
              height: 10,
            ),

            const Text(
              'What would you like your child to learn?',
              style: TextStyle(
                fontSize: 16,
              ),
            ),

            const SizedBox(
              height: 16,
            ),

            TextField(
              controller: _topicController,
              enabled:
                  !_isCreatingChapter,
              textInputAction:
                  TextInputAction.done,
              onSubmitted: (_) {
                if (!_isCreatingChapter) {
                  _createChapterWithAI();
                }
              },
              decoration:
                  InputDecoration(
                hintText:
                    'e.g. The Solar System',
                border:
                    OutlineInputBorder(
                  borderRadius:
                      BorderRadius.circular(
                    10,
                  ),
                ),
                prefixIcon:
                    const Icon(
                  Icons.auto_stories,
                ),
              ),
            ),

            const SizedBox(
              height: 16,
            ),

            SizedBox(
              width: double.infinity,
              child:
                  ElevatedButton.icon(
                onPressed:
                    _isCreatingChapter
                        ? null
                        : _createChapterWithAI,
                icon:
                    _isCreatingChapter
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child:
                                CircularProgressIndicator(
                              strokeWidth: 2,
                            ),
                          )
                        : const Icon(
                            Icons.auto_awesome,
                          ),
                label: Text(
                  _isCreatingChapter
                      ? 'Creating Chapter...'
                      : '✨ Create Chapter',
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ============================================================
  // EMPTY CHAPTER MESSAGE
  // ============================================================

  Widget _buildEmptyChapterMessage() {
    return Column(
      children: [
        const SizedBox(
          height: 30,
        ),

        const Icon(
          Icons.menu_book_outlined,
          size: 80,
        ),

        const SizedBox(
          height: 20,
        ),

        const Text(
          'No chapters uploaded yet.',
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: 16,
          ),
        ),

        const SizedBox(
          height: 25,
        ),

        ElevatedButton.icon(
          onPressed: _openUploadScreen,
          icon: const Icon(
            Icons.upload_file,
          ),
          label: const Text(
            'Upload First Chapter',
          ),
        ),
      ],
    );
  }

  // ============================================================
  // CHAPTER CARD
  // ============================================================

  Widget _buildChapterCard(
    dynamic chapter,
  ) {
    final title =
        chapter['title']?.toString() ??
            'Untitled Chapter';

    final subject =
        chapter['subject']?.toString() ??
            '';

    final grade =
        chapter['grade']?.toString() ??
            '';

    final status =
        chapter['status']?.toString() ??
            'unknown';

    final chapterId =
        chapter['id']?.toString();

    final isDeleting =
        chapterId != null &&
        chapterId == _deletingChapterId;

    return Card(
      margin: const EdgeInsets.only(
        bottom: 12,
      ),
      child: ListTile(
        contentPadding:
            const EdgeInsets.all(16),

        leading: const CircleAvatar(
          radius: 25,
          child: Icon(
            Icons.menu_book,
          ),
        ),

        title: Text(
          title,
          style: const TextStyle(
            fontWeight:
                FontWeight.bold,
            fontSize: 17,
          ),
        ),

        subtitle: Padding(
          padding:
              const EdgeInsets.only(
            top: 6,
          ),
          child: Text(
            '$subject • Grade $grade\n'
            'Status: $status',
          ),
        ),

        trailing: isDeleting
            ? const SizedBox(
                width: 24,
                height: 24,
                child:
                    CircularProgressIndicator(
                  strokeWidth: 2,
                ),
              )
            : const Icon(
                Icons.arrow_forward_ios,
                size: 18,
              ),

        onTap: isDeleting
            ? null
            : () {
                _showChapterOptions(
                  chapter,
                );
              },
      ),
    );
  }

  // ============================================================
  // CHAPTER OPTIONS
  // ============================================================

  void _showChapterOptions(
    dynamic chapter,
  ) {
    final title =
        chapter['title']?.toString() ??
            'Chapter';

    showModalBottomSheet(
      context: context,
      builder: (sheetContext) {
        return SafeArea(
          child: Wrap(
            children: [
              // ------------------------------------------------
              // Learn
              // ------------------------------------------------

              ListTile(
                leading: const Icon(
                  Icons.menu_book,
                ),
                title: Text(
                  'Learn $title',
                ),
                onTap: () {
                  Navigator.pop(
                    sheetContext,
                  );

                  Navigator.push(
                    this.context,
                    MaterialPageRoute(
                      builder: (context) =>
                          LearnChapterScreen(
                        chapter:
                            Map<String, dynamic>.from(
                          chapter,
                        ),
                        child:
                            Map<String, dynamic>.from(
                          widget.child,
                        ),
                      ),
                    ),
                  );
                },
              ),

              // ------------------------------------------------
              // Practice Questions
              // ------------------------------------------------

              ListTile(
                leading: const Icon(
                  Icons.quiz,
                ),
                title: const Text(
                  'Practice Questions',
                ),
                onTap: () {
                  Navigator.pop(
                    sheetContext,
                  );

                  ScaffoldMessenger.of(
                    this.context,
                  ).showSnackBar(
                    const SnackBar(
                      content: Text(
                        'Questions screen will be connected next.',
                      ),
                    ),
                  );
                },
              ),

              // ------------------------------------------------
              // DELETE
              // ------------------------------------------------

              ListTile(
                leading: const Icon(
                  Icons.delete_outline,
                ),
                title: const Text(
                  'Delete Chapter',
                ),
                textColor: Colors.red,
                iconColor: Colors.red,
                onTap: () {
                  Navigator.pop(
                    sheetContext,
                  );

                  _deleteChapter(
                    chapter,
                  );
                },
              ),

              // ------------------------------------------------
              // Cancel
              // ------------------------------------------------

              ListTile(
                leading: const Icon(
                  Icons.close,
                ),
                title: const Text(
                  'Cancel',
                ),
                onTap: () {
                  Navigator.pop(
                    sheetContext,
                  );
                },
              ),
            ],
          ),
        );
      },
    );
  }
}