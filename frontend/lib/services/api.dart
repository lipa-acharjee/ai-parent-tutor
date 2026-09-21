import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
class ApiService {
  final String baseUrl;
  final storage = const FlutterSecureStorage();
  ApiService({this.baseUrl='http://10.0.2.2:8000'});
  Future<Map<String,dynamic>> login(String email,String password) async {
    final r=await http.post(Uri.parse('$baseUrl/api/v1/auth/login'),headers:{'Content-Type':'application/json'},body:jsonEncode({'email':email,'password':password}));
    if(r.statusCode>=300) throw Exception(r.body);
    final d=jsonDecode(r.body); await storage.write(key:'access_token',value:d['access_token']); return d;
  }
  Future<List<dynamic>> children() async {
    final t=await storage.read(key:'access_token'); final r=await http.get(Uri.parse('$baseUrl/api/v1/children'),headers:{'Authorization':'Bearer $t'}); if(r.statusCode>=300) throw Exception(r.body); return jsonDecode(r.body);
  }
}
