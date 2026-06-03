import 'dart:convert';
import 'package:http/http.dart' as http;

/// API Service - communicates with FastAPI backend
/// Covers: violations, vehicles, analytics, monitoring, events, health, camera
class ApiService {
  static const String baseUrl = 'http://10.0.2.2:8000/api'; // Android emulator
  // Use 'http://localhost:8000/api' for iOS simulator or web

  // ==================== Core APIs ====================

  static Future<Map<String, dynamic>> fetchStats() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/analytics/'));
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
    } catch (e) {
      print('API Error (stats): $e');
    }
    return {};
  }

  static Future<List<dynamic>> fetchViolations({int limit = 50, String? type, String? severity}) async {
    try {
      var url = '$baseUrl/violations/?limit=$limit';
      if (type != null && type.isNotEmpty) url += '&type=$type';
      if (severity != null && severity.isNotEmpty) url += '&severity=$severity';
      final response = await http.get(Uri.parse(url));
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return data['violations'] ?? [];
      }
    } catch (e) {
      print('API Error (violations): $e');
    }
    return [];
  }

  static Future<List<dynamic>> fetchVehicles({int limit = 50}) async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/vehicles/?limit=$limit'));
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return data['vehicles'] ?? [];
      }
    } catch (e) {
      print('API Error (vehicles): $e');
    }
    return [];
  }

  // ==================== Monitoring APIs ====================

  static Future<Map<String, dynamic>> fetchHealth() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/analytics/health'));
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
    } catch (e) {
      print('API Error (health): $e');
    }
    return {'status': 'unreachable', 'score': 0, 'components': {}, 'alerts': []};
  }

  static Future<Map<String, dynamic>> fetchMetrics() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/analytics/metrics'));
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
    } catch (e) {
      print('API Error (metrics): $e');
    }
    return {};
  }

  static Future<Map<String, dynamic>> fetchLogStats() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/analytics/logs/stats'));
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
    } catch (e) {
      print('API Error (log stats): $e');
    }
    return {};
  }

  static Future<List<dynamic>> fetchLogs({int limit = 30, String? level}) async {
    try {
      var url = '$baseUrl/analytics/logs?limit=$limit';
      if (level != null) url += '&level=$level';
      final response = await http.get(Uri.parse(url));
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return data['logs'] ?? [];
      }
    } catch (e) {
      print('API Error (logs): $e');
    }
    return [];
  }

  // ==================== Event Bus APIs ====================

  static Future<Map<String, dynamic>> fetchEventMetrics() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/events/metrics'));
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
    } catch (e) {
      print('API Error (event metrics): $e');
    }
    return {};
  }

  static Future<List<dynamic>> fetchEventHistory({String topic = 'violation.*', int limit = 20}) async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/events/history?topic=$topic&limit=$limit'));
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return data['events'] ?? [];
      }
    } catch (e) {
      print('API Error (event history): $e');
    }
    return [];
  }

  // ==================== Camera Control ====================

  static Future<Map<String, dynamic>> fetchCameraStats() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/camera/stats'));
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
    } catch (e) {
      print('API Error (camera stats): $e');
    }
    return {"running": false, "fps": 0, "frame": 0, "tracks": 0};
  }

  static Future<bool> startCamera({String source = 'data/videos/traffic.mp4'}) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/camera/start?source=${Uri.encodeComponent(source)}'),
      );
      return response.statusCode == 200;
    } catch (e) {
      print('API Error (start camera): $e');
      return false;
    }
  }

  static Future<bool> stopCamera() async {
    try {
      final response = await http.post(Uri.parse('$baseUrl/camera/stop'));
      return response.statusCode == 200;
    } catch (e) {
      print('API Error (stop camera): $e');
      return false;
    }
  }
}
