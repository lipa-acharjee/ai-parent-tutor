import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';

import '../../services/api_service.dart';

class SharedVideoPlayerScreen extends StatefulWidget {
  final String videoId;
  final String topic;
  final String grade;

  const SharedVideoPlayerScreen({
    super.key,
    required this.videoId,
    required this.topic,
    required this.grade,
  });

  @override
  State<SharedVideoPlayerScreen> createState() =>
      _SharedVideoPlayerScreenState();
}

class _SharedVideoPlayerScreenState extends State<SharedVideoPlayerScreen> {
  VideoPlayerController? _controller;

  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _loadVideo();
  }

  Future<void> _loadVideo() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final response =
          await ApiService.getSharedVideoPlayback(widget.videoId);

      final videoUrl = response['video_url']?.toString();

      if (videoUrl == null || videoUrl.isEmpty) {
        throw Exception('The server did not provide a video URL.');
      }

      final controller = VideoPlayerController.networkUrl(
        Uri.parse(videoUrl),
      );

      await controller.initialize();

      if (!mounted) {
        await controller.dispose();
        return;
      }

      final oldController = _controller;
      _controller = controller;

      await oldController?.dispose();

      setState(() {
        _isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        _isLoading = false;
        _errorMessage = 'Unable to load video. Please try again.\n$e';
      });
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final controller = _controller;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Shared Video'),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _errorMessage != null
              ? _buildError()
              : controller == null
                  ? _buildError()
                  : _buildPlayer(controller),
    );
  }

  Widget _buildPlayer(VideoPlayerController controller) {
    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 20),

          AspectRatio(
            aspectRatio: controller.value.aspectRatio > 0
                ? controller.value.aspectRatio
                : 16 / 9,
            child: VideoPlayer(controller),
          ),

          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(
                      Icons.school_outlined,
                      color: Theme.of(context).colorScheme.primary,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      widget.grade,
                      style: Theme.of(context).textTheme.labelLarge,
                    ),
                  ],
                ),

                const SizedBox(height: 12),

                Text(
                  widget.topic,
                  style: Theme.of(context).textTheme.headlineSmall,
                ),

                const SizedBox(height: 24),

                Center(
                  child: IconButton.filled(
                    iconSize: 36,
                    padding: const EdgeInsets.all(16),
                    onPressed: () {
                      setState(() {
                        if (controller.value.isPlaying) {
                          controller.pause();
                        } else {
                          controller.play();
                        }
                      });
                    },
                    icon: Icon(
                      controller.value.isPlaying
                          ? Icons.pause
                          : Icons.play_arrow,
                    ),
                  ),
                ),

                const SizedBox(height: 16),

                VideoProgressIndicator(
                  controller,
                  allowScrubbing: true,
                  padding: const EdgeInsets.symmetric(vertical: 8),
                ),

                const SizedBox(height: 8),

                ValueListenableBuilder<VideoPlayerValue>(
                  valueListenable: controller,
                  builder: (context, value, child) {
                    return Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(_formatDuration(value.position)),
                        Text(_formatDuration(value.duration)),
                      ],
                    );
                  },
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildError() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(
              Icons.error_outline,
              size: 56,
              color: Colors.redAccent,
            ),
            const SizedBox(height: 16),
            Text(
              _errorMessage ?? 'Unable to load this video.',
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 20),
            ElevatedButton.icon(
              onPressed: _loadVideo,
              icon: const Icon(Icons.refresh),
              label: const Text('Try Again'),
            ),
          ],
        ),
      ),
    );
  }

  String _formatDuration(Duration duration) {
    String twoDigits(int value) => value.toString().padLeft(2, '0');

    final minutes = twoDigits(duration.inMinutes.remainder(60));
    final seconds = twoDigits(duration.inSeconds.remainder(60));

    if (duration.inHours > 0) {
      return '${duration.inHours}:$minutes:$seconds';
    }

    return '$minutes:$seconds';
  }
}
