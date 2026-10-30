import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';

import '../../services/api_service.dart';

class _SelectedVideo {
  final String name;
  final List<int> bytes;
  final int size;

  _SelectedVideo({
    required this.name,
    required this.bytes,
    required this.size,
  });
}

class UploadSharedVideoScreen extends StatefulWidget {
  const UploadSharedVideoScreen({super.key});

  @override
  State<UploadSharedVideoScreen> createState() =>
      _UploadSharedVideoScreenState();
}

class _UploadSharedVideoScreenState
    extends State<UploadSharedVideoScreen> {
  final _formKey = GlobalKey<FormState>();
  final _topicController = TextEditingController();

  List<String> _grades = [];
  String? _selectedGrade;

  _SelectedVideo? _selectedVideo;

  bool _isLoadingChildren = true;
  bool _isUploading = false;

  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _loadChildren();
  }

  @override
  void dispose() {
    _topicController.dispose();
    super.dispose();
  }

  // ============================================================
  // LOAD CHILDREN AND AVAILABLE GRADES
  // ============================================================

  Future<void> _loadChildren() async {
    try {
      final children = await ApiService.getChildren();

      final grades = children
          .map((child) => child['grade']?.toString().trim() ?? '')
          .where((grade) => grade.isNotEmpty)
          .toSet()
          .toList();

      if (!mounted) return;

      setState(() {
        _grades = grades;
        _selectedGrade = grades.isNotEmpty ? grades.first : null;
        _isLoadingChildren = false;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        _isLoadingChildren = false;
        _errorMessage = e.toString();
      });
    }
  }

  // ============================================================
  // SELECT MP4 VIDEO
  // ============================================================

  Future<void> _pickVideo() async {
    try {
      final file = await FilePicker.pickFile(
        type: FileType.custom,
        allowedExtensions: ['mp4'],
      );

      if (file == null) return;

      final bytes = await file.readAsBytes();

      if (bytes.isEmpty) {
        _showMessage('Could not read the selected video.');
        return;
      }

      if (!mounted) return;

      setState(() {
        _selectedVideo = _SelectedVideo(
          name: file.name,
          bytes: bytes,
          size: bytes.length,
        );
      });
    } catch (e) {
      _showMessage('Could not select video: $e');
    }
  }

  // ============================================================
  // UPLOAD VIDEO
  // ============================================================

  Future<void> _uploadVideo() async {
    if (!_formKey.currentState!.validate()) return;

    if (_selectedVideo == null) {
      _showMessage('Please select a video first.');
      return;
    }

    if (_selectedGrade == null) {
      _showMessage('No grade is available for upload.');
      return;
    }

    setState(() {
      _isUploading = true;
    });

    try {
      await ApiService.uploadSharedVideo(
        topic: _topicController.text.trim(),
        grade: _selectedGrade!,
        fileBytes: _selectedVideo!.bytes,
        fileName: _selectedVideo!.name,
      );

      if (!mounted) return;

      Navigator.pop(context, true);
    } catch (e) {
      if (!mounted) return;

      setState(() {
        _isUploading = false;
      });

      _showMessage(
        e.toString().replaceFirst('Exception: ', ''),
      );
    }
  }

  // ============================================================
  // MESSAGE
  // ============================================================

  void _showMessage(String message) {
    if (!mounted) return;

    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text(message),
          behavior: SnackBarBehavior.floating,
        ),
      );
  }

  // ============================================================
  // FILE SIZE
  // ============================================================

  String _formatFileSize(int bytes) {
    if (bytes < 1024 * 1024) {
      return '${(bytes / 1024).toStringAsFixed(1)} KB';
    }

    return '${(bytes / (1024 * 1024)).toStringAsFixed(2)} MB';
  }

  // ============================================================
  // BUILD SCREEN
  // ============================================================

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Upload Shared Video'),
        centerTitle: true,
      ),
      body: _isLoadingChildren
          ? const Center(
              child: CircularProgressIndicator(),
            )
          : _errorMessage != null
              ? _buildErrorState()
              : _grades.isEmpty
                  ? _buildNoGradesState()
                  : _buildUploadForm(theme),
    );
  }

  // ============================================================
  // UPLOAD FORM
  // ============================================================

  Widget _buildUploadForm(ThemeData theme) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Form(
        key: _formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 8),

            Text(
              'Share a learning video',
              style: theme.textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 8),

            Text(
              'Upload an educational video that parents '
              'with children in the selected grade can watch.',
              style: theme.textTheme.bodyMedium?.copyWith(
                color: Colors.grey.shade600,
              ),
            ),

            const SizedBox(height: 28),

            const Text(
              'Video Topic',
              style: TextStyle(
                fontWeight: FontWeight.w600,
                fontSize: 15,
              ),
            ),

            const SizedBox(height: 10),

            TextFormField(
              controller: _topicController,
              decoration: InputDecoration(
                hintText: 'e.g. Introduction to Mathematics',
                prefixIcon: const Icon(Icons.menu_book_outlined),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              textCapitalization: TextCapitalization.sentences,
              validator: (value) {
                if (value == null || value.trim().isEmpty) {
                  return 'Please enter the video topic.';
                }

                if (value.trim().length > 200) {
                  return 'Topic cannot exceed 200 characters.';
                }

                return null;
              },
            ),

            const SizedBox(height: 24),

            const Text(
              'Select Grade',
              style: TextStyle(
                fontWeight: FontWeight.w600,
                fontSize: 15,
              ),
            ),

            const SizedBox(height: 10),

            DropdownButtonFormField<String>(
              initialValue: _selectedGrade,
              decoration: InputDecoration(
                prefixIcon: const Icon(Icons.school_outlined),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              items: _grades.map((grade) {
                return DropdownMenuItem<String>(
                  value: grade,
                  child: Text(grade),
                );
              }).toList(),
              onChanged: _isUploading
                  ? null
                  : (value) {
                      setState(() {
                        _selectedGrade = value;
                      });
                    },
            ),

            const SizedBox(height: 28),

            const Text(
              'Select Video',
              style: TextStyle(
                fontWeight: FontWeight.w600,
                fontSize: 15,
              ),
            ),

            const SizedBox(height: 10),

            InkWell(
              onTap: _isUploading ? null : _pickVideo,
              borderRadius: BorderRadius.circular(14),
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(
                  horizontal: 20,
                  vertical: 28,
                ),
                decoration: BoxDecoration(
                  color: theme.colorScheme.primaryContainer
                      .withValues(alpha: 0.25),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(
                    color: theme.colorScheme.primary
                        .withValues(alpha: 0.35),
                  ),
                ),
                child: Column(
                  children: [
                    Icon(
                      Icons.video_library_outlined,
                      size: 48,
                      color: theme.colorScheme.primary,
                    ),
                    const SizedBox(height: 12),
                    Text(
                      _selectedVideo == null
                          ? 'Choose an MP4 video'
                          : 'Change selected video',
                      style: const TextStyle(
                        fontWeight: FontWeight.w600,
                        fontSize: 16,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      'Supported format: MP4',
                      style: TextStyle(
                        color: Colors.grey.shade600,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ),
            ),

            if (_selectedVideo != null) ...[
              const SizedBox(height: 14),
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: Colors.green.withValues(alpha: 0.08),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: Colors.green.withValues(alpha: 0.3),
                  ),
                ),
                child: Row(
                  children: [
                    const Icon(
                      Icons.video_file,
                      color: Colors.green,
                      size: 32,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            _selectedVideo!.name,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            _formatFileSize(_selectedVideo!.size),
                            style: TextStyle(
                              color: Colors.grey.shade600,
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      onPressed: _isUploading
                          ? null
                          : () {
                              setState(() {
                                _selectedVideo = null;
                              });
                            },
                      icon: const Icon(
                        Icons.close,
                        color: Colors.red,
                      ),
                    ),
                  ],
                ),
              ),
            ],

            const SizedBox(height: 30),

            SizedBox(
              width: double.infinity,
              height: 54,
              child: ElevatedButton.icon(
                onPressed: _isUploading ? null : _uploadVideo,
                icon: _isUploading
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Icon(Icons.cloud_upload_outlined),
                label: Text(
                  _isUploading
                      ? 'Uploading video...'
                      : 'Upload Video',
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                style: ElevatedButton.styleFrom(
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),

            const SizedBox(height: 16),

            Center(
              child: Text(
                'Your video will be shared with parents '
                'whose children belong to the selected grade.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey.shade600,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ============================================================
  // ERROR STATE
  // ============================================================

  Widget _buildErrorState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(
              Icons.error_outline,
              color: Colors.red,
              size: 48,
            ),
            const SizedBox(height: 16),
            const Text(
              'Could not load children',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 18,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              _errorMessage!,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () {
                setState(() {
                  _isLoadingChildren = true;
                  _errorMessage = null;
                });

                _loadChildren();
              },
              child: const Text('Try Again'),
            ),
          ],
        ),
      ),
    );
  }

  // ============================================================
  // NO GRADES STATE
  // ============================================================

  Widget _buildNoGradesState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(
              Icons.school_outlined,
              size: 56,
              color: Colors.grey,
            ),
            const SizedBox(height: 16),
            const Text(
              'No children found',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Please add a child and their grade '
              'before uploading a shared video.',
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Go Back'),
            ),
          ],
        ),
      ),
    );
  }
}
