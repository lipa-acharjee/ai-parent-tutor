import 'dart:convert';


import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'package:flutter/foundation.dart';

import 'auth_service.dart';

class ChapterImage {
  final String name;
  final List<int> bytes;

  const ChapterImage({
    required this.name,
    required this.bytes,
  });
}

class ApiService {
  static const String baseUrl =
      'http://localhost:8000';


static Future<Map<String, dynamic>> createChapterFromText({
  required String childId,
  required String text,
  required String grade,
}) async {
  final token = await AuthService.getAccessToken();

  debugPrint('CREATE CHAPTER - TOKEN EXISTS: ${token != null && token.isNotEmpty}');
  debugPrint('CREATE CHAPTER - CHILD ID: $childId');
  debugPrint('CREATE CHAPTER - GRADE: $grade');

  if (token == null || token.isEmpty) {
    throw Exception(
      'No access token found. Please login again.',
    );
  }

  final response = await http.post(
    Uri.parse(
      '$baseUrl/api/v1/chapters/from-text',
    ),
    headers: {
      'Authorization': 'Bearer $token',
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: {
      'child_id': childId,
      'text': text,
      'grade': grade,
    },
  );

  debugPrint(
    'CREATE CHAPTER STATUS: ${response.statusCode}',
  );

  debugPrint(
    'CREATE CHAPTER RESPONSE: ${response.body}',
  );

  if (response.statusCode >= 200 &&
      response.statusCode < 300) {
    final data = jsonDecode(response.body);

    if (data is Map<String, dynamic>) {
      return data;
    }

    throw Exception(
      'Unexpected chapter creation response format',
    );
  }

  String errorMessage;

  try {
    final errorData = jsonDecode(response.body);

    if (errorData is Map<String, dynamic> &&
        errorData['detail'] != null) {
      errorMessage = errorData['detail'].toString();
    } else {
      errorMessage = response.body;
    }
  } catch (_) {
    errorMessage = response.body;
  }

  throw Exception(
    'Failed to create chapter '
    '(${response.statusCode}): '
    '$errorMessage',
  );
}


static  Future<void> deleteChapter(String chapterId) async {
  final token = await AuthService.getAccessToken();

  if (token == null || token.isEmpty) {
    throw Exception('You are not logged in.');
  }

  final response = await http.delete(
    Uri.parse('$baseUrl/api/v1/chapters/$chapterId'),
    headers: {
      'Authorization': 'Bearer $token',
    },
  );

  debugPrint(
    'DELETE chapter response: ${response.statusCode} ${response.body}',
  );

  if (response.statusCode != 200) {
    throw Exception(
      'Could not delete chapter: ${response.body}',
    );
  }
}

  // ============================================================
  // GET CHAPTERS
  // ============================================================

  static Future<List<dynamic>> getChapters(
    String childId,
  ) async {
    final token =
        await AuthService.getAccessToken();

    if (token == null || token.isEmpty) {
      throw Exception(
        'No access token found',
      );
    }

    final uri = Uri.parse(
      '$baseUrl/api/v1/chapters?child_id=$childId',
    );

    final response = await http.get(
      uri,
      headers: {
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(
        response.body,
      );

      if (data is List) {
        return data;
      }

      throw Exception(
        'Unexpected chapters response format',
      );
    }

    String errorMessage;

    try {
      final errorData =
          jsonDecode(response.body);

      if (errorData is Map<String, dynamic> &&
          errorData['detail'] != null) {
        errorMessage =
            errorData['detail'].toString();
      } else {
        errorMessage = response.body;
      }
    } catch (_) {
      errorMessage = response.body;
    }

    throw Exception(
      'Failed to get chapters '
      '(${response.statusCode}): '
      '$errorMessage',
    );
  }

  // ============================================================
  // LOGIN
  // ============================================================

  static Future<Map<String, dynamic>> login(
    String email,
    String password,
  ) async {
    final response = await http.post(
      Uri.parse(
        '$baseUrl/api/v1/auth/login',
      ),
      headers: {
        'Content-Type':
            'application/x-www-form-urlencoded',
      },
      body: {
        'username': email,
        'password': password,
      },
    );

    if (response.statusCode == 200) {
      return jsonDecode(
        response.body,
      );
    }

    throw Exception(
      'Login failed: ${response.body}',
    );
  }


  // ============================================================
  // GOOGLE LOGIN
  // ============================================================

  static Future<Map<String, dynamic>> googleLogin(
    String idToken,
  ) async {
    final response = await http.post(
      Uri.parse(
        '$baseUrl/api/v1/auth/google',
      ),
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'id_token': idToken,
      }),
    );

    debugPrint(
      'GOOGLE LOGIN STATUS: ${response.statusCode}',
    );

    debugPrint(
      'GOOGLE LOGIN RESPONSE: ${response.body}',
    );

    if (response.statusCode >= 200 &&
        response.statusCode < 300) {
      final data = jsonDecode(response.body);

      if (data is Map<String, dynamic>) {
        return data;
      }

      throw Exception(
        'Unexpected Google login response format',
      );
    }

    String errorMessage;

    try {
      final errorData = jsonDecode(response.body);

      if (errorData is Map<String, dynamic> &&
          errorData['detail'] != null) {
        errorMessage =
            errorData['detail'].toString();
      } else {
        errorMessage = response.body;
      }
    } catch (_) {
      errorMessage = response.body;
    }

    throw Exception(
      'Google login failed '
      '(${response.statusCode}): '
      '$errorMessage',
    );
  }



  // ============================================================
  // GET CURRENT USER
  // ============================================================

  static Future<Map<String, dynamic>> getMe() async {
    final token =
        await AuthService.getAccessToken();

    if (token == null || token.isEmpty) {
      throw Exception(
        'No access token found',
      );
    }

    final response = await http.get(
      Uri.parse(
        '$baseUrl/api/v1/auth/me',
      ),
      headers: {
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode == 200) {
      return jsonDecode(
        response.body,
      );
    }

    throw Exception(
      'Failed to get user: ${response.body}',
    );
  }

  // ============================================================
  // GET CHILDREN
  // ============================================================

  static Future<List<dynamic>> getChildren() async {
    final token =
        await AuthService.getAccessToken();

    if (token == null || token.isEmpty) {
      throw Exception(
        'No access token found',
      );
    }

    final response = await http.get(
      Uri.parse(
        '$baseUrl/api/v1/children',
      ),
      headers: {
        'Authorization': 'Bearer $token',
      },
    );

    debugPrint(
      'GET CHILDREN STATUS: ${response.statusCode}',
    );

    debugPrint(
      'GET CHILDREN RESPONSE: ${response.body}',
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);

      if (data is List) {
        return data;
      }

      throw Exception(
        'Unexpected children response format',
      );
    }

    throw Exception(
      'Failed to get children: ${response.body}',
    );
  }

  // ============================================================
  // CREATE CHILD
  // ============================================================

  static Future<Map<String, dynamic>> createChild({
    required String name,
    required String grade,
    String language = 'English',
  }) async {
    final token =
        await AuthService.getAccessToken();

    if (token == null || token.isEmpty) {
      throw Exception(
        'No access token found. Please login again.',
      );
    }

    debugPrint('CREATE CHILD: $name');
    debugPrint('CREATE CHILD GRADE: $grade');
    debugPrint('CREATE CHILD LANGUAGE: $language');

    final response = await http.post(
      Uri.parse(
        '$baseUrl/api/v1/children',
      ),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'name': name,
        'grade': grade,
        'language': language,
      }),
    );

    debugPrint(
      'CREATE CHILD STATUS: ${response.statusCode}',
    );

    debugPrint(
      'CREATE CHILD RESPONSE: ${response.body}',
    );

    if (response.statusCode == 200 ||
        response.statusCode == 201) {
      final data = jsonDecode(response.body);

      if (data is Map<String, dynamic>) {
        return data;
      }

      throw Exception(
        'Unexpected create child response format',
      );
    }

    throw Exception(
      'Failed to create child: ${response.body}',
    );
  }

  // ============================================================
  // UPLOAD CHAPTER - PDF
  //
  // Backend:
  //
  // POST /api/v1/chapters
  //
  // Form fields:
  // child_id
  // title
  // subject
  // grade
  // files = one PDF
  // ============================================================

  static Future<Map<String, dynamic>> uploadChapter({
    required String childId,
    required String title,
    required String subject,
    required String grade,
    required List<int> fileBytes,
    required String fileName,
  }) async {
    final token =
        await AuthService.getAccessToken();

    if (token == null || token.isEmpty) {
      throw Exception(
        'No access token found',
      );
    }

    if (fileBytes.isEmpty) {
      throw Exception(
        'PDF file is empty.',
      );
    }

    final request = http.MultipartRequest(
      'POST',
      Uri.parse(
        '$baseUrl/api/v1/chapters',
      ),
    );

    request.headers['Authorization'] =
        'Bearer $token';

    request.fields['child_id'] =
        childId;

    request.fields['title'] =
        title;

    request.fields['subject'] =
        subject;

    request.fields['grade'] =
        grade;

    request.files.add(
      http.MultipartFile.fromBytes(
        'files',
        fileBytes,
        filename: fileName,
        contentType: MediaType(
          'application',
          'pdf',
        ),
      ),
    );

    final streamedResponse =
        await request.send();

    final response =
        await http.Response.fromStream(
      streamedResponse,
    );

    if (response.statusCode >= 200 &&
        response.statusCode < 300) {
      final data =
          jsonDecode(response.body);

      if (data is Map<String, dynamic>) {
        return data;
      }

      throw Exception(
        'Unexpected chapter upload response format',
      );
    }

    String errorMessage;

    try {
      final errorData =
          jsonDecode(response.body);

      if (errorData is Map<String, dynamic> &&
          errorData['detail'] != null) {
        errorMessage =
            errorData['detail'].toString();
      } else {
        errorMessage = response.body;
      }
    } catch (_) {
      errorMessage = response.body;
    }

    throw Exception(
      'Chapter PDF upload failed '
      '(${response.statusCode}): '
      '$errorMessage',
    );
  }

  // ============================================================
  // UPLOAD CHAPTER - MULTIPLE JPG/JPEG IMAGES
  //
  // file_picker 12.2.0:
  //
  // PlatformFile does NOT have .bytes.
  // Use:
  //
  // await file.readAsBytes()
  // ============================================================

  static Future<Map<String, dynamic>> uploadChapterImages({
    required String childId,
    required String title,
    required String subject,
    required String grade,
    required List<ChapterImage> imageFiles,
  }) async {
    final token =
        await AuthService.getAccessToken();

    if (token == null || token.isEmpty) {
      throw Exception(
        'No access token found',
      );
    }

    if (imageFiles.isEmpty) {
      throw Exception(
        'Please select at least one JPG/JPEG image.',
      );
    }

    final request = http.MultipartRequest(
      'POST',
      Uri.parse(
        '$baseUrl/api/v1/chapters',
      ),
    );

    request.headers['Authorization'] =
        'Bearer $token';

    request.fields['child_id'] =
        childId;

    request.fields['title'] =
        title;

    request.fields['subject'] =
        subject;

    request.fields['grade'] =
        grade;

    for (final file in imageFiles) {
  final bytes = file.bytes;

  if (bytes.isEmpty) {
    throw Exception(
      'Could not read image: '
      '${file.name}',
    );
  }

  final extension =
      file.name.split('.').last.toLowerCase();

      
      
      final contentType =
          extension == 'png'
              ? MediaType(
                  'image',
                  'png',
                )
              : MediaType(
                  'image',
                  'jpeg',
                );

      request.files.add(
        http.MultipartFile.fromBytes(
          'files',
          bytes,
          filename: file.name,
          contentType: contentType,
        ),
      );
    }

    final streamedResponse =
        await request.send();

    final response =
        await http.Response.fromStream(
      streamedResponse,
    );

    if (response.statusCode >= 200 &&
        response.statusCode < 300) {
      final data =
          jsonDecode(response.body);

      if (data is Map<String, dynamic>) {
        return data;
      }

      throw Exception(
        'Unexpected chapter upload response format',
      );
    }

    String errorMessage;

    try {
      final errorData =
          jsonDecode(response.body);

      if (errorData is Map<String, dynamic> &&
          errorData['detail'] != null) {
        errorMessage =
            errorData['detail'].toString();
      } else {
        errorMessage = response.body;
      }
    } catch (_) {
      errorMessage = response.body;
    }

    throw Exception(
      'Chapter image upload failed '
      '(${response.statusCode}): '
      '$errorMessage',
    );
  }

  // ============================================================
  // GENERATE AI LESSON
  // ============================================================

  static Future<Map<String, dynamic>> generateLesson({
    required String chapterId,
    required String topic,
    required int studentAge,
    required int numberOfQuestions,
  }) async {
    final token =
        await AuthService.getAccessToken();

    if (token == null || token.isEmpty) {
      throw Exception(
        'No access token found',
      );
    }

    final uri = Uri.parse(
      '$baseUrl/api/v1/lessons/generate'
      '?chapter_id=$chapterId',
    );

    final response = await http.post(
      uri,
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'topic': topic,
        'student_age': studentAge,
        'number_of_questions':
            numberOfQuestions,
      }),
    );

    if (response.statusCode >= 200 &&
        response.statusCode < 300) {
      final data =
          jsonDecode(response.body);

      if (data is Map<String, dynamic>) {
        return data;
      }

      throw Exception(
        'Unexpected lesson generation response format',
      );
    }

    String errorMessage;

    try {
      final errorData =
          jsonDecode(response.body);

      if (errorData is Map<String, dynamic> &&
          errorData['detail'] != null) {
        errorMessage =
            errorData['detail'].toString();
      } else {
        errorMessage = response.body;
      }
    } catch (_) {
      errorMessage = response.body;
    }

    throw Exception(
      'Lesson generation failed '
      '(${response.statusCode}): '
      '$errorMessage',
    );
  }

  // ============================================================
  // CHECK LESSON GENERATION JOB
  // ============================================================

  static Future<Map<String, dynamic>>
      getLessonJobStatus(
    String jobId,
  ) async {
    final token =
        await AuthService.getAccessToken();

    if (token == null || token.isEmpty) {
      throw Exception(
        'No access token found',
      );
    }

    final uri = Uri.parse(
      '$baseUrl/api/v1/lessons/jobs/$jobId',
    );

    final response = await http.get(
      uri,
      headers: {
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode == 200) {
      final data =
          jsonDecode(response.body);

      if (data is Map<String, dynamic>) {
        return data;
      }

      throw Exception(
        'Unexpected job status response format',
      );
    }

    String errorMessage;

    try {
      final errorData =
          jsonDecode(response.body);

      if (errorData is Map<String, dynamic> &&
          errorData['detail'] != null) {
        errorMessage =
            errorData['detail'].toString();
      } else {
        errorMessage = response.body;
      }
    } catch (_) {
      errorMessage = response.body;
    }

    throw Exception(
      'Failed to get lesson job status '
      '(${response.statusCode}): '
      '$errorMessage',
    );
  }

  // ============================================================
  // GET GENERATED LESSON
  // ============================================================

  static Future<Map<String, dynamic>> getLesson(
    String lessonId,
  ) async {
    final token =
        await AuthService.getAccessToken();

    if (token == null || token.isEmpty) {
      throw Exception(
        'No access token found',
      );
    }

    final uri = Uri.parse(
      '$baseUrl/api/v1/lessons/$lessonId',
    );

    final response = await http.get(
      uri,
      headers: {
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode == 200) {
      final data =
          jsonDecode(response.body);

      if (data is Map<String, dynamic>) {
        return data;
      }

      throw Exception(
        'Unexpected lesson response format',
      );
    }

    String errorMessage;

    try {
      final errorData =
          jsonDecode(response.body);

      if (errorData is Map<String, dynamic> &&
          errorData['detail'] != null) {
        errorMessage =
            errorData['detail'].toString();
      } else {
        errorMessage = response.body;
      }
    } catch (_) {
      errorMessage = response.body;
    }

    throw Exception(
      'Failed to get lesson '
      '(${response.statusCode}): '
      '$errorMessage',
    );
  }

  // ============================================================
  // SUBMIT ANSWER
  // ============================================================

  static Future<Map<String, dynamic>>
      submitAnswer({
    required String questionId,
    required String childId,
    required String answer,
  }) async {
    final token =
        await AuthService.getAccessToken();

    if (token == null || token.isEmpty) {
      throw Exception(
        'No access token found',
      );
    }

    final uri = Uri.parse(
      '$baseUrl/api/v1/learning/answer',
    );

    final response = await http.post(
      uri,
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'question_id': questionId,
        'child_id': childId,
        'answer': answer,
      }),
    );

    if (response.statusCode >= 200 &&
        response.statusCode < 300) {
      final data =
          jsonDecode(response.body);

      if (data is Map<String, dynamic>) {
        return data;
      }

      throw Exception(
        'Unexpected answer response format',
      );
    }

    String errorMessage;

    try {
      final errorData =
          jsonDecode(response.body);

      if (errorData is Map<String, dynamic> &&
          errorData['detail'] != null) {
        errorMessage =
            errorData['detail'].toString();
      } else {
        errorMessage = response.body;
      }
    } catch (_) {
      errorMessage = response.body;
    }

    throw Exception(
      'Failed to submit answer '
      '(${response.statusCode}): '
      '$errorMessage',
    );
  }
}