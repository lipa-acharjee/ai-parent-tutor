import 'package:flutter/material.dart';

import '../../services/api_service.dart';

class AddChildScreen extends StatefulWidget {
  const AddChildScreen({super.key});

  @override
  State<AddChildScreen> createState() =>
      _AddChildScreenState();
}

class _AddChildScreenState extends State<AddChildScreen> {
  final GlobalKey<FormState> _formKey =
      GlobalKey<FormState>();

  final TextEditingController _nameController =
      TextEditingController();

  final TextEditingController _gradeController =
      TextEditingController();

  String _language = 'English';

  bool _isLoading = false;

  @override
  void dispose() {
    _nameController.dispose();
    _gradeController.dispose();

    super.dispose();
  }

  // ============================================================
  // CREATE CHILD
  // ============================================================

  Future<void> _createChild() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    if (_isLoading) {
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      debugPrint('ADD CHILD: Creating child...');

      final child = await ApiService.createChild(
        name: _nameController.text.trim(),
        grade: _gradeController.text.trim(),
        language: _language,
      );

      debugPrint(
        'ADD CHILD: Child created successfully: $child',
      );

      if (!mounted) {
        return;
      }

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Child added successfully!',
          ),
        ),
      );

      // Return to My Children screen.
      // The previous screen will reload the children list.
      Navigator.pop(context, true);
    } catch (e, stackTrace) {
      debugPrint(
        'ADD CHILD ERROR: $e',
      );

      debugPrint(
        'ADD CHILD STACK TRACE: $stackTrace',
      );

      if (!mounted) {
        return;
      }

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Failed to add child: $e',
          ),
          duration: const Duration(seconds: 6),
        ),
      );
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  // ============================================================
  // UI
  // ============================================================

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Add Child'),
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(
                maxWidth: 500,
              ),
              child: Card(
                elevation: 3,
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Form(
                    key: _formKey,
                    child: Column(
                      crossAxisAlignment:
                          CrossAxisAlignment.stretch,
                      children: [
                        const Icon(
                          Icons.child_care,
                          size: 70,
                          color: Colors.blue,
                        ),

                        const SizedBox(height: 16),

                        const Text(
                          'Add Your Child',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontSize: 26,
                            fontWeight: FontWeight.bold,
                          ),
                        ),

                        const SizedBox(height: 8),

                        Text(
                          'Enter your child\'s details',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            color: Colors.grey.shade600,
                          ),
                        ),

                        const SizedBox(height: 32),

                        // ------------------------------------------------
                        // CHILD NAME
                        // ------------------------------------------------

                        TextFormField(
                          controller: _nameController,
                          textCapitalization:
                              TextCapitalization.words,
                          decoration: const InputDecoration(
                            labelText: 'Child Name',
                            hintText:
                                'Enter child name',
                            prefixIcon: Icon(
                              Icons.person_outline,
                            ),
                            border: OutlineInputBorder(),
                          ),
                          validator: (value) {
                            if (value == null ||
                                value.trim().isEmpty) {
                              return 'Please enter child name';
                            }

                            return null;
                          },
                        ),

                        const SizedBox(height: 20),

                        // ------------------------------------------------
                        // GRADE
                        // ------------------------------------------------

                        TextFormField(
                          controller: _gradeController,
                          decoration: const InputDecoration(
                            labelText: 'Grade',
                            hintText:
                                'Example: 2',
                            prefixIcon: Icon(
                              Icons.school_outlined,
                            ),
                            border: OutlineInputBorder(),
                          ),
                          validator: (value) {
                            if (value == null ||
                                value.trim().isEmpty) {
                              return 'Please enter grade';
                            }

                            return null;
                          },
                        ),

                        const SizedBox(height: 20),

                        // ------------------------------------------------
                        // LANGUAGE
                        // ------------------------------------------------

                        DropdownButtonFormField<String>(
                          value: _language,
                          decoration:
                              const InputDecoration(
                            labelText: 'Language',
                            prefixIcon: Icon(
                              Icons.language,
                            ),
                            border: OutlineInputBorder(),
                          ),
                          items: const [
                            DropdownMenuItem(
                              value: 'English',
                              child: Text('English'),
                            ),
                            DropdownMenuItem(
                              value: 'Hindi',
                              child: Text('Hindi'),
                            ),
                            DropdownMenuItem(
                              value: 'Bengali',
                              child: Text('Bengali'),
                            ),
                          ],
                          onChanged: _isLoading
                              ? null
                              : (value) {
                                  if (value == null) {
                                    return;
                                  }

                                  setState(() {
                                    _language = value;
                                  });
                                },
                        ),

                        const SizedBox(height: 30),

                        // ------------------------------------------------
                        // SAVE BUTTON
                        // ------------------------------------------------

                        SizedBox(
                          height: 52,
                          child: ElevatedButton(
                            onPressed:
                                _isLoading
                                    ? null
                                    : _createChild,
                            child: _isLoading
                                ? const SizedBox(
                                    width: 24,
                                    height: 24,
                                    child:
                                        CircularProgressIndicator(
                                      strokeWidth: 2,
                                    ),
                                  )
                                : const Text(
                                    'Save Child',
                                    style: TextStyle(
                                      fontSize: 16,
                                    ),
                                  ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}