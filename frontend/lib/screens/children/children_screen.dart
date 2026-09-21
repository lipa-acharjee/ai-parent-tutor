
import 'package:flutter/material.dart';

import '../../services/api_service.dart';
import '../chapters/chapter_list_screen.dart';
import 'add_child_screen.dart';

class ChildrenScreen extends StatefulWidget {
  const ChildrenScreen({super.key});

  @override
  State<ChildrenScreen> createState() => _ChildrenScreenState();
}

class _ChildrenScreenState extends State<ChildrenScreen> {
  bool _isLoading = true;
  String? _error;
  List<dynamic> _children = [];

  @override
  void initState() {
    super.initState();
    _loadChildren();
  }

  Future<void> _loadChildren() async {
    try {
      final children = await ApiService.getChildren();

      debugPrint('CHILDREN FROM API: $children');

      if (!mounted) return;

      setState(() {
        _children = children;
        _isLoading = false;
        _error = null;
      });
    } catch (e) {
      debugPrint('GET CHILDREN ERROR: $e');

      if (!mounted) return;

      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<void> _openAddChildScreen() async {
    debugPrint('ADD CHILD BUTTON: Opening Add Child screen');

    final result = await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => const AddChildScreen(),
      ),
    );

    debugPrint('ADD CHILD SCREEN RESULT: $result');

    // If a child was successfully created,
    // reload the children from the API.
    if (result == true && mounted) {
      debugPrint('ADD CHILD: Reloading children...');

      setState(() {
        _isLoading = true;
      });

      await _loadChildren();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Children'),
      ),

      floatingActionButton: FloatingActionButton(
        onPressed: _openAddChildScreen,
        child: const Icon(Icons.add),
      ),

      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(
        child: CircularProgressIndicator(),
      );
    }

    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Text(
            _error!,
            textAlign: TextAlign.center,
          ),
        ),
      );
    }

    if (_children.isEmpty) {
      return const Center(
        child: Text(
          'No children added yet.',
          style: TextStyle(
            fontSize: 18,
          ),
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadChildren,
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: _children.length,
        itemBuilder: (context, index) {
          final child = _children[index];

          return Card(
            margin: const EdgeInsets.only(bottom: 12),
            child: ListTile(
              leading: const CircleAvatar(
                child: Icon(Icons.child_care),
              ),

              title: Text(
                child['name'] ?? 'Unknown',
                style: const TextStyle(
                  fontWeight: FontWeight.bold,
                ),
              ),

              subtitle: Text(
                'Grade ${child['grade'] ?? ''} • '
                '${child['language'] ?? ''}',
              ),

              trailing: const Icon(
                Icons.arrow_forward_ios,
                size: 18,
              ),

              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => ChapterListScreen(
                      child: Map<String, dynamic>.from(child),
                    ),
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }
}
