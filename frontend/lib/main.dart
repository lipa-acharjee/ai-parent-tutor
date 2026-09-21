import 'package:flutter/material.dart';
import 'screens/login/login_screen.dart';

void main() {
  runApp(const AIParentTutorApp());
}

class AIParentTutorApp extends StatelessWidget {
  const AIParentTutorApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'AI Parent Tutor',
      theme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: Colors.indigo,
      ),
      home: const LoginScreen(),
    );
  }
}