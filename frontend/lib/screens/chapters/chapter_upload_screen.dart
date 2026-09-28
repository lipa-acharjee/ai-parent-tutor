import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../../services/api_service.dart';

enum ChapterInputType {
  pdf,
  images,
}

// ============================================================
// LOCAL IMAGE DATA
//
// We don't use PlatformFile for storing selected images because
// file_picker 12.2.0 does not expose .bytes or .size.
//
// We read the bytes using readAsBytes() and store them here.
// ============================================================

class _SelectedImage {
  final String name;
  final List<int> bytes;
  final int size;

  const _SelectedImage({
    required this.name,
    required this.bytes,
    required this.size,
  });
}

class ChapterUploadScreen extends StatefulWidget {
  final Map<String, dynamic> child;

  const ChapterUploadScreen({
    super.key,
    required this.child,
  });

  @override
  State<ChapterUploadScreen> createState() =>
      _ChapterUploadScreenState();
}

class _ChapterUploadScreenState
    extends State<ChapterUploadScreen> {
  final _formKey = GlobalKey<FormState>();

  final _titleController = TextEditingController();
  final _subjectController = TextEditingController();
  final _customPromptController =
    TextEditingController();

  ChapterInputType _inputType = ChapterInputType.pdf;

  // ============================================================
  // PDF
  // ============================================================

  List<int>? _fileBytes;
  String? _fileName;
  int? _fileSize;

  // ============================================================
  // MULTIPLE IMAGES
  // ============================================================

  final List<_SelectedImage> _imageFiles = [];

  bool _isUploading = false;

  String? _statusMessage;
  String? _errorMessage;

  @override
  void dispose() {
    _titleController.dispose();
    _subjectController.dispose();
    _customPromptController.dispose();
    super.dispose();
  }

  // ============================================================
  // SELECT PDF
  // ============================================================

  Future<void> _pickPdf() async {
    try {
      final file = await FilePicker.pickFile(
        type: FileType.custom,
        allowedExtensions: ['pdf'],
      );

      if (file == null) {
        return;
      }

      final bytes = await file.readAsBytes();

      if (bytes.isEmpty) {
        if (!mounted) return;

        setState(() {
          _errorMessage =
              'Could not read the selected PDF file.';
          _fileBytes = null;
          _fileName = null;
          _fileSize = null;
        });

        return;
      }

      if (!mounted) return;

      setState(() {
        _fileBytes = bytes;
        _fileName = file.name;
        _fileSize = bytes.length;

        _imageFiles.clear();

        _errorMessage = null;
        _statusMessage = null;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        _errorMessage =
            'Could not select the PDF: $e';
      });
    }
  }

  // ============================================================
  // SELECT MULTIPLE JPG/JPEG IMAGES
  // ============================================================

  Future<void> _pickImages() async {
    try {
      final result = await FilePicker.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['jpg', 'jpeg'],
        allowMultiple: true,
      );

      if (result == null || result.isEmpty) {
        return;
      }

      final selected = <_SelectedImage>[];

      for (final file in result) {
        try {
          final bytes = await file.readAsBytes();

          if (bytes.isNotEmpty) {
            selected.add(
              _SelectedImage(
                name: file.name,
                bytes: bytes,
                size: bytes.length,
              ),
            );
          }
        } catch (_) {
          // Ignore files that cannot be read.
        }
      }

      if (selected.isEmpty) {
        if (!mounted) return;

        setState(() {
          _errorMessage =
              'Could not read the selected images.';
        });

        return;
      }

      // Preserve predictable page order.
      selected.sort(
        (a, b) => _naturalFileNameCompare(
          a.name,
          b.name,
        ),
      );

      if (!mounted) return;

      setState(() {
        _imageFiles
          ..clear()
          ..addAll(selected);

        _fileBytes = null;
        _fileName = null;
        _fileSize = null;

        _errorMessage = null;
        _statusMessage = null;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        _errorMessage =
            'Could not select the images: $e';
      });
    }
  }

  // ============================================================
  // NATURAL FILE NAME SORT
  // ============================================================

  int _naturalFileNameCompare(
    String a,
    String b,
  ) {
    final aLower = a.toLowerCase();
    final bLower = b.toLowerCase();

    final regex = RegExp(r'(\d+)');

    final aMatch = regex.firstMatch(aLower);
    final bMatch = regex.firstMatch(bLower);

    if (aMatch != null && bMatch != null) {
      final aNumber =
          int.tryParse(aMatch.group(1)!) ?? 0;

      final bNumber =
          int.tryParse(bMatch.group(1)!) ?? 0;

      if (aNumber != bNumber) {
        return aNumber.compareTo(bNumber);
      }
    }

    return aLower.compareTo(bLower);
  }

  // ============================================================
  // REMOVE IMAGE
  // ============================================================

  void _removeImage(int index) {
    setState(() {
      _imageFiles.removeAt(index);
      _errorMessage = null;
      _statusMessage = null;
    });
  }

  // ============================================================
  // UPLOAD CHAPTER
  // ============================================================

  Future<void> _uploadChapter() async {
    FocusScope.of(context).unfocus();

    setState(() {
      _errorMessage = null;
      _statusMessage = null;
    });

    if (!_formKey.currentState!.validate()) {
      return;
    }

    // ----------------------------------------------------------
    // Validate selected file(s)
    // ----------------------------------------------------------

    if (_inputType == ChapterInputType.pdf) {
      if (_fileBytes == null ||
          _fileBytes!.isEmpty) {
        setState(() {
          _errorMessage =
              'Please select a PDF chapter.';
        });

        return;
      }
    } else {
      if (_imageFiles.isEmpty) {
        setState(() {
          _errorMessage =
              'Please select at least one JPG/JPEG page.';
        });

        return;
      }
    }

    setState(() {
      _isUploading = true;

      _statusMessage =
          _inputType == ChapterInputType.pdf
              ? 'Uploading chapter PDF...'
              : 'Uploading ${_imageFiles.length} chapter pages...';
    });

    try {
      Map<String, dynamic> result;

      if (_inputType == ChapterInputType.pdf) {
        result = await ApiService.uploadChapter(
          childId: widget.child['id'].toString(),
          title: _titleController.text.trim(),
          subject: _subjectController.text.trim(),
          grade: widget.child['grade'].toString(),
          fileBytes: _fileBytes!,
          fileName: _fileName ?? 'chapter.pdf',
        );
      } else {
        result = await ApiService.uploadChapterImages(
        childId: widget.child['id'].toString(),
        title: _titleController.text.trim(),
        subject: _subjectController.text.trim(),
        grade: widget.child['grade'].toString(),
        customPrompt:
            _customPromptController.text.trim(),
        imageFiles: _imageFiles
            .map(
              (file) => ChapterImage(
                name: file.name,
                bytes: file.bytes,
              ),
            )
            .toList(),
      );
      }

      if (!mounted) {
        return;
      }

      setState(() {
        _isUploading = false;
        _statusMessage =
            'Chapter uploaded successfully!';
      });

      await _showSuccessDialog(result);
    } catch (e) {
      if (!mounted) {
        return;
      }

      setState(() {
        _isUploading = false;
        _statusMessage = null;
        _errorMessage = e.toString();
      });
    }
  }

  // ============================================================
  // SUCCESS DIALOG
  // ============================================================

  Future<void> _showSuccessDialog(
    Map<String, dynamic> result,
  ) async {
    await showDialog<void>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Row(
            children: [
              Icon(
                Icons.check_circle,
                color: Colors.green,
              ),
              SizedBox(width: 10),
              Text('Chapter Ready'),
            ],
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment:
                CrossAxisAlignment.start,
            children: [
              Text(
                'File: ${result['filename'] ?? _fileName ?? 'chapter_images.pdf'}',
              ),
              const SizedBox(height: 8),
              Text(
                'Pages: ${result['pages'] ?? 'N/A'}',
              ),
              const SizedBox(height: 8),
              Text(
                'Status: ${result['status'] ?? 'unknown'}',
              ),
              const SizedBox(height: 8),
              Text(
                'Chapter ID: ${result['chapter_id'] ?? 'N/A'}',
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(context).pop();
              },
              child: const Text('OK'),
            ),
          ],
        );
      },
    );
  }

  // ============================================================
  // BUILD
  // ============================================================

   Widget _buildCustomPromptField() {
  return Column(
    crossAxisAlignment:
        CrossAxisAlignment.stretch,
    children: [
      const SizedBox(height: 20),

      const Text(
        'Optional Instructions for AI',
        style: TextStyle(
          fontSize: 16,
          fontWeight: FontWeight.bold,
        ),
      ),

      const SizedBox(height: 8),

      TextFormField(
        controller:
            _customPromptController,
        enabled: !_isUploading,
        minLines: 4,
        maxLines: 7,
        maxLength: 3000,
        decoration: const InputDecoration(
          border: OutlineInputBorder(),
          hintText:
              'Tell the AI how you want this chapter taught.\n\n'
              'Examples:\n'
              '• Explain difficult terms in more detail.\n'
              '• Focus more on the water cycle.\n'
              '• Create 10 questions.\n'
              '• Make the questions more difficult.',
          prefixIcon: Padding(
            padding:
                EdgeInsets.only(
              bottom: 70,
            ),
            child: Icon(
              Icons.auto_awesome,
            ),
          ),
          alignLabelWithHint: true,
        ),
      ),

      const SizedBox(height: 6),

      const Text(
        'This is optional. Leave it empty to use the normal AI teaching settings.',
        style: TextStyle(
          fontSize: 12,
        ),
      ),
    ],
  );
}


  @override
  Widget build(BuildContext context) {
    final childName =
        widget.child['name']?.toString() ?? 'Child';

    final childGrade =
        widget.child['grade']?.toString() ?? '';

    return Scaffold(
      appBar: AppBar(
        title: const Text('Upload Chapter'),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment:
                  CrossAxisAlignment.stretch,
              children: [
                // ==================================================
                // CHILD
                // ==================================================

                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Row(
                      children: [
                        const CircleAvatar(
                          child: Icon(
                            Icons.child_care,
                          ),
                        ),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Column(
                            crossAxisAlignment:
                                CrossAxisAlignment.start,
                            children: [
                              const Text(
                                'Child',
                                style: TextStyle(
                                  fontSize: 13,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                childName,
                                style: const TextStyle(
                                  fontSize: 18,
                                  fontWeight:
                                      FontWeight.bold,
                                ),
                              ),
                              Text(
                                'Grade $childGrade',
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 20),

                // ==================================================
                // CHAPTER TITLE
                // ==================================================

                TextFormField(
                  controller: _titleController,
                  enabled: !_isUploading,
                  decoration: const InputDecoration(
                    labelText: 'Chapter Title',
                    hintText:
                        'Enter the chapter name',
                    border: OutlineInputBorder(),
                    prefixIcon:
                        Icon(Icons.menu_book),
                  ),
                  validator: (value) {
                    if (value == null ||
                        value.trim().isEmpty) {
                      return 'Please enter chapter title';
                    }

                    return null;
                  },
                ),

                const SizedBox(height: 16),

                // ==================================================
                // SUBJECT
                // ==================================================

                TextFormField(
                  controller: _subjectController,
                  enabled: !_isUploading,
                  decoration: const InputDecoration(
                    labelText: 'Subject',
                    hintText:
                        'Example: EVS, Mathematics, English',
                    border: OutlineInputBorder(),
                    prefixIcon:
                        Icon(Icons.subject),
                  ),
                  validator: (value) {
                    if (value == null ||
                        value.trim().isEmpty) {
                      return 'Please enter subject';
                    }

                    return null;
                  },
                ),

                const SizedBox(height: 20),

                // ==================================================
                // INPUT TYPE
                // ==================================================

                const Text(
                  'Chapter Source',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),

                const SizedBox(height: 8),

                Card(
                  child: Column(
                    children: [
                      RadioListTile<ChapterInputType>(
                        value: ChapterInputType.pdf,
                        groupValue: _inputType,
                        enabled: !_isUploading,
                        title: const Text('PDF'),
                        subtitle: const Text(
                          'Upload one complete chapter PDF',
                        ),
                        secondary: const Icon(
                          Icons.picture_as_pdf,
                        ),
                        onChanged: (value) {
                          if (value == null) {
                            return;
                          }

                          setState(() {
                            _inputType = value;
                            _errorMessage = null;
                            _statusMessage = null;
                          });
                        },
                      ),
                      RadioListTile<ChapterInputType>(
                        value: ChapterInputType.images,
                        groupValue: _inputType,
                        enabled: !_isUploading,
                        title: const Text(
                          'Multiple JPG/JPEG Images',
                        ),
                        subtitle: const Text(
                          'Upload textbook pages as images',
                        ),
                        secondary: const Icon(
                          Icons.photo_library,
                        ),
                        onChanged: (value) {
                          if (value == null) {
                            return;
                          }

                          setState(() {
                            _inputType = value;
                            _errorMessage = null;
                            _statusMessage = null;
                          });
                        },
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 16),

                // ==================================================
                // PDF
                // ==================================================

                if (_inputType ==
                    ChapterInputType.pdf)
                  _buildPdfSelector(),

                // ==================================================
                // MULTIPLE IMAGES
                // ==================================================

                if (_inputType ==
                    ChapterInputType.images)
                  _buildImageSelector(),

                if (_inputType ==
                    ChapterInputType.images)
                  _buildCustomPromptField(),

                const SizedBox(height: 24),

                // ==================================================
                // ERROR
                // ==================================================

                if (_errorMessage != null)
                  Container(
                    padding:
                        const EdgeInsets.all(12),
                    margin:
                        const EdgeInsets.only(
                      bottom: 16,
                    ),
                    decoration: BoxDecoration(
                      borderRadius:
                          BorderRadius.circular(8),
                      color: Colors.red
                          .withValues(alpha: 0.1),
                    ),
                    child: Row(
                      crossAxisAlignment:
                          CrossAxisAlignment.start,
                      children: [
                        const Icon(
                          Icons.error_outline,
                          color: Colors.red,
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            _errorMessage!,
                          ),
                        ),
                      ],
                    ),
                  ),

                // ==================================================
                // STATUS
                // ==================================================

                if (_statusMessage != null)
                  Container(
                    padding:
                        const EdgeInsets.all(12),
                    margin:
                        const EdgeInsets.only(
                      bottom: 16,
                    ),
                    decoration: BoxDecoration(
                      borderRadius:
                          BorderRadius.circular(8),
                      color: Colors.green
                          .withValues(alpha: 0.1),
                    ),
                    child: Row(
                      children: [
                        const Icon(
                          Icons.check_circle_outline,
                          color: Colors.green,
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            _statusMessage!,
                          ),
                        ),
                      ],
                    ),
                  ),

                // ==================================================
                // UPLOAD BUTTON
                // ==================================================

                SizedBox(
                  height: 52,
                  child: ElevatedButton.icon(
                    onPressed:
                        _isUploading
                            ? null
                            : _uploadChapter,
                    icon: _isUploading
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child:
                                CircularProgressIndicator(
                              strokeWidth: 2,
                            ),
                          )
                        : const Icon(
                            Icons.cloud_upload,
                          ),
                    label: Text(
                      _isUploading
                          ? 'Uploading...'
                          : 'Upload Chapter',
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  // ============================================================
  // PDF SELECTOR UI
  // ============================================================

  Widget _buildPdfSelector() {
    return Column(
      crossAxisAlignment:
          CrossAxisAlignment.stretch,
      children: [
        const Text(
          'Chapter PDF',
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        InkWell(
          onTap:
              _isUploading ? null : _pickPdf,
          borderRadius:
              BorderRadius.circular(12),
          child: Container(
            padding:
                const EdgeInsets.all(18),
            decoration: BoxDecoration(
              border: Border.all(
                color: Colors.grey,
              ),
              borderRadius:
                  BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                const Icon(
                  Icons.picture_as_pdf,
                  size: 40,
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment:
                        CrossAxisAlignment.start,
                    children: [
                      Text(
                        _fileName == null
                            ? 'Choose PDF'
                            : _fileName!,
                        style:
                            const TextStyle(
                          fontWeight:
                              FontWeight.bold,
                        ),
                        overflow:
                            TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        _fileSize == null
                            ? 'Only PDF files are supported'
                            : _formatFileSize(
                                _fileSize!,
                              ),
                      ),
                    ],
                  ),
                ),
                const Icon(
                  Icons.upload_file,
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  // ============================================================
  // IMAGE SELECTOR UI
  // ============================================================

  Widget _buildImageSelector() {
    return Column(
      crossAxisAlignment:
          CrossAxisAlignment.stretch,
      children: [
        const Text(
          'Textbook Pages',
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        InkWell(
          onTap:
              _isUploading ? null : _pickImages,
          borderRadius:
              BorderRadius.circular(12),
          child: Container(
            padding:
                const EdgeInsets.all(18),
            decoration: BoxDecoration(
              border: Border.all(
                color: Colors.grey,
              ),
              borderRadius:
                  BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                const Icon(
                  Icons.photo_library,
                  size: 40,
                ),
                const SizedBox(width: 14),
                const Expanded(
                  child: Column(
                    crossAxisAlignment:
                        CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Choose JPG/JPEG Pages',
                        style: TextStyle(
                          fontWeight:
                              FontWeight.bold,
                        ),
                      ),
                      SizedBox(height: 4),
                      Text(
                        'Select multiple textbook pages',
                      ),
                    ],
                  ),
                ),
                const Icon(
                  Icons.add_photo_alternate,
                ),
              ],
            ),
          ),
        ),
        if (_imageFiles.isNotEmpty) ...[
          const SizedBox(height: 16),
          Text(
            '${_imageFiles.length} page(s) selected',
            style: const TextStyle(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          ...List.generate(
            _imageFiles.length,
            (index) {
              final file = _imageFiles[index];

              return Card(
                margin:
                    const EdgeInsets.only(
                  bottom: 8,
                ),
                child: ListTile(
                  leading: CircleAvatar(
                    child: Text(
                      '${index + 1}',
                    ),
                  ),
                  title: Text(
                    file.name,
                    overflow:
                        TextOverflow.ellipsis,
                  ),
                  subtitle: Text(
                    _formatFileSize(file.size),
                  ),
                  trailing: IconButton(
                    icon: const Icon(
                      Icons.delete_outline,
                    ),
                    onPressed: _isUploading
                        ? null
                        : () => _removeImage(
                              index,
                            ),
                  ),
                ),
              );
            },
          ),
        ],
      ],
    );
  }

  // ============================================================
  // FILE SIZE
  // ============================================================

  String _formatFileSize(int bytes) {
    if (bytes < 1024) {
      return '$bytes B';
    }

    if (bytes < 1024 * 1024) {
      return '${(bytes / 1024).toStringAsFixed(1)} KB';
    }

    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }
}