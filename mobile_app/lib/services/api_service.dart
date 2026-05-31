import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = 'http://localhost:8000/api';

  static Future<Map<String, dynamic>> fetchStats() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/analytics/'));
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
    } catch (e) {
      print('API Error: $e');
    }
    return {};
  }

  static Future<List<dynamic>> fetchViolations({int limit = 50}) async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/violations/?limit=$limit'));
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return data['violations'] ?? [];
      }
    } catch (e) {
      print('API Error: $e');
    }
    return [];
  }

  static Future<List<dynamic>> fetchVehicles() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/vehicles/'));
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return data['vehicles'] ?? [];
      }
    } catch (e) {
      print('API Error: $e');
    }
    return [];
  }
}
