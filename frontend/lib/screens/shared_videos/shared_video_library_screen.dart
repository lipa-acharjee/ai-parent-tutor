import 'package:flutter/material.dart';

import '../../services/api_service.dart';
import 'upload_shared_video_screen.dart';
import 'shared_video_player_screen.dart';

class SharedVideoLibraryScreen extends StatefulWidget {
  const SharedVideoLibraryScreen({super.key});

  @override
  State<SharedVideoLibraryScreen> createState() =>
      _SharedVideoLibraryScreenState();
}

class _SharedVideoLibraryScreenState
    extends State<SharedVideoLibraryScreen> {
  List<dynamic> _videos = [];

  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _loadVideos();
  }

  // ============================================================
  // LOAD VIDEOS
  // ============================================================

  Future<void> _loadVideos() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final videos = await ApiService.getSharedVideos();

      if (!mounted) return;

      setState(() {
        _videos = videos;
        _isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        _errorMessage = e.toString();
        _isLoading = false;
      });
    }
  }

  // ============================================================
  // OPEN UPLOAD SCREEN
  // ============================================================

  Future<void> _openUploadScreen() async {
    final result = await Navigator.push<bool>(
      context,
      MaterialPageRoute(
        builder: (_) => const UploadSharedVideoScreen(),
      ),
    );

    if (result == true) {
      _loadVideos();
    }
  }

  // ============================================================
  // OPEN PLAYER
  // ============================================================

  Future<void> _openVideo(Map<String, dynamic> video) async {
    final videoId = video['id']?.toString();

    if (videoId == null || videoId.isEmpty) {
      _showMessage('Invalid video information.');
      return;
    }

    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => SharedVideoPlayerScreen(
          videoId: videoId,
          topic: video['topic']?.toString() ?? 'Learning Video',
          grade: video['grade']?.toString() ?? '',
        ),
      ),
    );
  }

  // ============================================================
  // MESSAGE
  // ============================================================

  void _showMessage(String message) {
    if (!mounted) return;

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  // ============================================================
  // BUILD
  // ============================================================

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Shared Videos'),
        centerTitle: true,
        actions: [
          IconButton(
            tooltip: 'Refresh',
            onPressed: _isLoading ? null : _loadVideos,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),

      floatingActionButton: FloatingActionButton.extended(
        onPressed: _openUploadScreen,
        icon: const Icon(Icons.video_call_outlined),
        label: const Text('Upload Video'),
      ),

      body: RefreshIndicator(
        onRefresh: _loadVideos,
        child: _buildBody(theme),
      ),
    );
  }

  // ============================================================
  // BODY
  // ============================================================

  Widget _buildBody(ThemeData theme) {
    if (_isLoading && _videos.isEmpty) {
      return const Center(
        child: CircularProgressIndicator(),
      );
    }

    if (_errorMessage != null && _videos.isEmpty) {
      return _buildErrorState();
    }

    if (_videos.isEmpty) {
      return _buildEmptyState();
    }

    return ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 100),
      children: [
        Text(
          'Learning videos for your family',
          style: theme.textTheme.headlineSmall?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),

        const SizedBox(height: 6),

        Text(
          'Explore educational videos shared for your children’s grades.',
          style: theme.textTheme.bodyMedium?.copyWith(
            color: Colors.grey.shade600,
          ),
        ),

        const SizedBox(height: 20),

        if (_errorMessage != null) ...[
          Text(
            'Could not refresh videos: $_errorMessage',
            style: const TextStyle(color: Colors.red),
          ),
          const SizedBox(height: 12),
        ],

        ..._videos.map((item) {
          final video = Map<String, dynamic>.from(item as Map);
          return _buildVideoCard(video);
        }),
      ],
    );
  }

  // ============================================================
  // VIDEO CARD
  // ============================================================

  Widget _buildVideoCard(Map<String, dynamic> video) {
    final topic = video['topic']?.toString() ?? 'Untitled Video';
    final grade = video['grade']?.toString() ?? 'Grade not specified';
    final filename =
        video['original_filename']?.toString() ?? 'Video file';

    final createdAt = video['created_at']?.toString();

    String dateLabel = '';

    if (createdAt != null) {
      final date = DateTime.tryParse(createdAt)?.toLocal();

      if (date != null) {
        dateLabel =
            '${date.day}/${date.month}/${date.year}';
      }
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      elevation: 2,
      clipBehavior: Clip.antiAlias,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),

      child: InkWell(
        onTap: () => _openVideo(video),

        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              height: 145,
              width: double.infinity,
              color: Theme.of(context)
                  .colorScheme
                  .primaryContainer
                  .withValues(alpha: 0.45),

              child: Stack(
                alignment: Alignment.center,
                children: [
                  const Icon(
                    Icons.video_library_outlined,
                    size: 65,
                    color: Colors.indigo,
                  ),

                  Container(
                    decoration: const BoxDecoration(
                      color: Colors.black54,
                      shape: BoxShape.circle,
                    ),
                    padding: const EdgeInsets.all(12),
                    child: const Icon(
                      Icons.play_arrow,
                      color: Colors.white,
                      size: 34,
                    ),
                  ),
                ],
              ),
            ),

            Padding(
              padding: const EdgeInsets.all(16),

              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,

                children: [
                  Text(
                    topic,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontSize: 17,
                      fontWeight: FontWeight.bold,
                    ),
                  ),

                  const SizedBox(height: 10),

                  Row(
                    children: [
                      const Icon(
                        Icons.school_outlined,
                        size: 17,
                        color: Colors.indigo,
                      ),

                      const SizedBox(width: 6),

                      Text(
                        grade,
                        style: const TextStyle(
                          fontWeight: FontWeight.w600,
                          color: Colors.indigo,
                        ),
                      ),

                      const Spacer(),

                      if (dateLabel.isNotEmpty)
                        Text(
                          dateLabel,
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.grey.shade600,
                          ),
                        ),
                    ],
                  ),

                  const SizedBox(height: 8),

                  Text(
                    filename,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey.shade600,
                    ),
                  ),

                  const SizedBox(height: 12),

                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton.icon(
                      onPressed: () => _openVideo(video),
                      icon: const Icon(Icons.play_circle_outline),
                      label: const Text('Watch Video'),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ============================================================
  // EMPTY STATE
  // ============================================================

  Widget _buildEmptyState() {
    return ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.all(28),

      children: [
        const SizedBox(height: 80),

        Icon(
          Icons.video_library_outlined,
          size: 80,
          color: Colors.grey.shade400,
        ),

        const SizedBox(height: 24),

        const Text(
          'No shared videos yet',
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: 21,
            fontWeight: FontWeight.bold,
          ),
        ),

        const SizedBox(height: 10),

        Text(
          'Educational videos shared for your children’s '
          'grades will appear here.',
          textAlign: TextAlign.center,
          style: TextStyle(
            color: Colors.grey.shade600,
            fontSize: 14,
          ),
        ),

        const SizedBox(height: 24),

        Center(
          child: OutlinedButton.icon(
            onPressed: _openUploadScreen,
            icon: const Icon(Icons.cloud_upload_outlined),
            label: const Text('Upload First Video'),
          ),
        ),
      ],
    );
  }

  // ============================================================
  // ERROR STATE
  // ============================================================

  Widget _buildErrorState() {
    return ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.all(28),

      children: [
        const SizedBox(height: 100),

        const Icon(
          Icons.cloud_off_outlined,
          size: 65,
          color: Colors.red,
        ),

        const SizedBox(height: 20),

        const Text(
          'Could not load shared videos',
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),

        const SizedBox(height: 12),

        Text(
          _errorMessage ?? 'An unexpected error occurred.',
          textAlign: TextAlign.center,
        ),

        const SizedBox(height: 24),

        Center(
          child: ElevatedButton.icon(
            onPressed: _loadVideos,
            icon: const Icon(Icons.refresh),
            label: const Text('Try Again'),
          ),
        ),
      ],
    );
  }
}
