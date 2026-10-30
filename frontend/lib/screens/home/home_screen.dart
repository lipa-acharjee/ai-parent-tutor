
import 'package:flutter/material.dart';

import '../children/children_screen.dart';
import '../shared_videos/shared_video_library_screen.dart';

class HomeScreen extends StatelessWidget {
  final Map<String, dynamic> user;

  const HomeScreen({
    super.key,
    required this.user,
  });

  @override
  Widget build(BuildContext context) {
    final name = user['name'] ?? 'Parent';

    return Scaffold(
      appBar: AppBar(
        title: const Text('AI Parent Tutor'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () {
              // Logout functionality will be implemented here.
            },
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Hello, $name 👋',
              style: const TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 8),

            const Text(
              'Let’s help your child learn concepts, '
              'not just memorize them.',
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey,
              ),
            ),

            const SizedBox(height: 30),

            // My Children
            Card(
              child: ListTile(
                leading: const Icon(
                  Icons.child_care,
                  size: 40,
                ),
                title: const Text(
                  'My Children',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                subtitle: const Text(
                  'View and manage your children',
                ),
                trailing: const Icon(Icons.arrow_forward_ios),
                onTap: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => const ChildrenScreen(),
                    ),
                  );
                },
              ),
            ),

            const SizedBox(height: 16),

            // Learning
            Card(
              child: ListTile(
                leading: const Icon(
                  Icons.menu_book,
                  size: 40,
                ),
                title: const Text(
                  'Learning',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                subtitle: const Text(
                  'Continue your child’s learning',
                ),
                trailing: const Icon(Icons.arrow_forward_ios),
                onTap: () {
                 // Learning navigation will be implemented here.
                },
              ),
            ),

            const SizedBox(height: 16),

            // Shared Videos
            Card(
              child: ListTile(
                leading: const Icon(
                  Icons.video_library,
                  size: 40,
                  color: Colors.indigo,
                ),
                title: const Text(
                  'Shared Videos',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                subtitle: const Text(
                  'Explore educational videos shared by parents',
                ),
                trailing: const Icon(Icons.arrow_forward_ios),
                onTap: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) =>
                          const SharedVideoLibraryScreen(),
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
