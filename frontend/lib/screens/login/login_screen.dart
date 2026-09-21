import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:google_sign_in_web/web_only.dart' as google_web;

import '../../services/api_service.dart';
import '../../services/auth_service.dart';
import '../home/home_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();

  final TextEditingController _emailController =
      TextEditingController();

  final TextEditingController _passwordController =
      TextEditingController();

  final GoogleSignIn _googleSignIn = GoogleSignIn.instance;

  bool _isLoading = false;
  bool _googleInitialized = false;

  StreamSubscription<GoogleSignInAuthenticationEvent>?
      _googleAuthSubscription;

  @override
  void initState() {
    super.initState();

    _initializeGoogleSignIn();
  }

  // ============================================================
  // GOOGLE SIGN-IN INITIALIZATION
  // ============================================================

  Future<void> _initializeGoogleSignIn() async {
    try {
      debugPrint('GOOGLE: Starting initialization...');

      await _googleSignIn.initialize();

      debugPrint('GOOGLE: Initialization completed');

      _googleAuthSubscription =
          _googleSignIn.authenticationEvents.listen(
        _handleGoogleAuthenticationEvent,
        onError: (Object error) {
          debugPrint(
            'GOOGLE AUTHENTICATION EVENT ERROR: $error',
          );
        },
      );

      debugPrint(
        'GOOGLE: Authentication listener registered',
      );

      if (mounted) {
        setState(() {
          _googleInitialized = true;
        });
      }
    } catch (e, stackTrace) {
      debugPrint(
        'GOOGLE INITIALIZATION ERROR: $e',
      );

      debugPrint(
        'GOOGLE STACK TRACE: $stackTrace',
      );
    }
  }

  // ============================================================
  // GOOGLE AUTHENTICATION EVENT
  // ============================================================

  Future<void> _handleGoogleAuthenticationEvent(
    GoogleSignInAuthenticationEvent event,
  ) async {
    debugPrint(
      'GOOGLE AUTH EVENT: ${event.runtimeType}',
    );

    if (event is GoogleSignInAuthenticationEventSignIn) {
      final GoogleSignInAccount googleUser = event.user;

      debugPrint(
        'GOOGLE USER: ${googleUser.email}',
      );

      await _completeGoogleLogin(googleUser);
    } else if (event
        is GoogleSignInAuthenticationEventSignOut) {
      debugPrint(
        'GOOGLE: User signed out',
      );
    }
  }

  // ============================================================
  // COMPLETE GOOGLE LOGIN
  // ============================================================

  Future<void> _completeGoogleLogin(
    GoogleSignInAccount googleUser,
  ) async {
    if (_isLoading) {
      return;
    }

    if (mounted) {
      setState(() {
        _isLoading = true;
      });
    }

    try {
      debugPrint(
        'GOOGLE: Getting authentication information...',
      );

      final GoogleSignInAuthentication googleAuth =
          googleUser.authentication;

      final String? idToken = googleAuth.idToken;

      if (idToken == null || idToken.isEmpty) {
        throw Exception(
          'Google did not return an ID token.',
        );
      }

      debugPrint(
        'GOOGLE: ID token received',
      );

      debugPrint(
        'GOOGLE: Sending ID token to backend...',
      );

      final result = await ApiService.googleLogin(
        idToken,
      );

      debugPrint(
        'GOOGLE: Backend login successful',
      );

      // --------------------------------------------------------
      // SAVE APPLICATION TOKENS
      // --------------------------------------------------------

      await AuthService.saveTokens(
        accessToken: result['access_token'],
        refreshToken: result['refresh_token'],
      );

      debugPrint(
        'GOOGLE: Application tokens saved',
      );

      // --------------------------------------------------------
      // GET CURRENT USER
      // --------------------------------------------------------

      final user = await ApiService.getMe();

      debugPrint(
        'GOOGLE: CURRENT USER: $user',
      );

      if (!mounted) {
        return;
      }

      // --------------------------------------------------------
      // GO TO HOME SCREEN
      // --------------------------------------------------------

      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => HomeScreen(
            user: user,
          ),
        ),
      );
    } catch (e, stackTrace) {
      debugPrint(
        'GOOGLE BACKEND LOGIN ERROR: $e',
      );

      debugPrint(
        'GOOGLE BACKEND STACK TRACE: $stackTrace',
      );

      if (!mounted) {
        return;
      }

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Google login failed: $e',
          ),
          duration: const Duration(seconds: 8),
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
  // EMAIL / PASSWORD LOGIN
  // ============================================================

  Future<void> _login() async {
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
      debugPrint(
        'LOGIN: Sending email/password to backend...',
      );

      final result = await ApiService.login(
        _emailController.text.trim(),
        _passwordController.text,
      );

      debugPrint(
        'LOGIN: Backend login successful',
      );

      await AuthService.saveTokens(
        accessToken: result['access_token'],
        refreshToken: result['refresh_token'],
      );

      debugPrint(
        'LOGIN: Application tokens saved',
      );

      final user = await ApiService.getMe();

      debugPrint(
        'LOGIN: CURRENT USER: $user',
      );

      if (!mounted) {
        return;
      }

      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => HomeScreen(
            user: user,
          ),
        ),
      );
    } catch (e, stackTrace) {
      debugPrint(
        'LOGIN ERROR: $e',
      );

      debugPrint(
        'LOGIN STACK TRACE: $stackTrace',
      );

      if (!mounted) {
        return;
      }

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Login failed: $e',
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
  // DISPOSE
  // ============================================================

  @override
  void dispose() {
    _googleAuthSubscription?.cancel();

    _emailController.dispose();
    _passwordController.dispose();

    super.dispose();
  }

  // ============================================================
  // UI
  // ============================================================

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade100,
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(
                maxWidth: 450,
              ),
              child: Card(
                elevation: 4,
                child: Padding(
                  padding: const EdgeInsets.all(28),
                  child: Form(
                    key: _formKey,
                    child: Column(
                      crossAxisAlignment:
                          CrossAxisAlignment.stretch,
                      children: [
                        // ------------------------------------------------
                        // APP ICON
                        // ------------------------------------------------

                        const Icon(
                          Icons.school,
                          size: 70,
                          color: Colors.blue,
                        ),

                        const SizedBox(height: 16),

                        // ------------------------------------------------
                        // TITLE
                        // ------------------------------------------------

                        const Text(
                          'AI Parent Tutor',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontSize: 28,
                            fontWeight: FontWeight.bold,
                          ),
                        ),

                        const SizedBox(height: 8),

                        Text(
                          'Learn smarter with your child',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontSize: 15,
                            color: Colors.grey.shade600,
                          ),
                        ),

                        const SizedBox(height: 32),

                        // ------------------------------------------------
                        // EMAIL
                        // ------------------------------------------------

                        TextFormField(
                          controller: _emailController,
                          keyboardType:
                              TextInputType.emailAddress,
                          decoration: const InputDecoration(
                            labelText: 'Email',
                            hintText:
                                'Enter your email',
                            prefixIcon: Icon(
                              Icons.email_outlined,
                            ),
                            border: OutlineInputBorder(),
                          ),
                          validator: (value) {
                            if (value == null ||
                                value.trim().isEmpty) {
                              return 'Please enter your email';
                            }

                            if (!value.contains('@')) {
                              return 'Please enter a valid email';
                            }

                            return null;
                          },
                        ),

                        const SizedBox(height: 16),

                        // ------------------------------------------------
                        // PASSWORD
                        // ------------------------------------------------

                        TextFormField(
                          controller: _passwordController,
                          obscureText: true,
                          decoration: const InputDecoration(
                            labelText: 'Password',
                            hintText:
                                'Enter your password',
                            prefixIcon: Icon(
                              Icons.lock_outline,
                            ),
                            border: OutlineInputBorder(),
                          ),
                          validator: (value) {
                            if (value == null ||
                                value.isEmpty) {
                              return 'Please enter your password';
                            }

                            return null;
                          },
                        ),

                        const SizedBox(height: 24),

                        // ------------------------------------------------
                        // LOGIN BUTTON
                        // ------------------------------------------------

                        SizedBox(
                          height: 52,
                          child: ElevatedButton(
                            onPressed:
                                _isLoading ? null : _login,
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
                                    'Login',
                                    style: TextStyle(
                                      fontSize: 16,
                                    ),
                                  ),
                          ),
                        ),

                        const SizedBox(height: 24),

                        // ------------------------------------------------
                        // OR DIVIDER
                        // ------------------------------------------------

                        Row(
                          children: [
                            Expanded(
                              child: Divider(
                                color:
                                    Colors.grey.shade400,
                              ),
                            ),
                            Padding(
                              padding:
                                  const EdgeInsets.symmetric(
                                horizontal: 12,
                              ),
                              child: Text(
                                'OR',
                                style: TextStyle(
                                  color:
                                      Colors.grey.shade600,
                                ),
                              ),
                            ),
                            Expanded(
                              child: Divider(
                                color:
                                    Colors.grey.shade400,
                              ),
                            ),
                          ],
                        ),

                        const SizedBox(height: 24),

                        // ------------------------------------------------
                        // GOOGLE LOGIN BUTTON
                        // ------------------------------------------------
                        //
                        // google_sign_in_web requires Google's
                        // rendered sign-in button on Web.
                        //

                        if (kIsWeb)
                          SizedBox(
                            width: double.infinity,
                            height: 52,
                            child: google_web.renderButton(),
                          ),

                        if (!kIsWeb)
                          SizedBox(
                            height: 52,
                            child: OutlinedButton.icon(
                              onPressed: _googleInitialized &&
                                      !_isLoading
                                  ? () async {
                                      try {
                                        await _googleSignIn
                                            .authenticate();
                                      } catch (e) {
                                        debugPrint(
                                          'GOOGLE MOBILE LOGIN ERROR: $e',
                                        );

                                        if (!mounted) {
                                          return;
                                        }

                                        ScaffoldMessenger.of(
                                          context,
                                        ).showSnackBar(
                                          SnackBar(
                                            content: Text(
                                              'Google login failed: $e',
                                            ),
                                          ),
                                        );
                                      }
                                    }
                                  : null,
                              icon: const Icon(
                                Icons.login,
                              ),
                              label: const Text(
                                'Continue with Google',
                              ),
                            ),
                          ),

                        const SizedBox(height: 24),

                        // ------------------------------------------------
                        // CREATE ACCOUNT
                        // ------------------------------------------------

                        TextButton(
                          onPressed: () {
                            ScaffoldMessenger.of(
                              context,
                            ).showSnackBar(
                              const SnackBar(
                                content: Text(
                                  'Account registration will be added soon.',
                                ),
                              ),
                            );
                          },
                          child: const Text(
                            'Create an account',
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