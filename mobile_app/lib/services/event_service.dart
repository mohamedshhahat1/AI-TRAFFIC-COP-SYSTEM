import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

/// Event Service - WebSocket connection to live Event Bus stream
/// Receives real-time: violations, accident risks, congestion changes, tracking updates
class EventService extends ChangeNotifier {
  WebSocketChannel? _channel;
  bool _isConnected = false;
  final List<Map<String, dynamic>> _events = [];
  int _violationCount = 0;
  int _riskCount = 0;
  String _congestionLevel = 'free';

  bool get isConnected => _isConnected;
  List<Map<String, dynamic>> get events => _events;
  int get violationCount => _violationCount;
  int get riskCount => _riskCount;
  String get congestionLevel => _congestionLevel;

  static const String wsUrl = 'ws://10.0.2.2:8000/ws/live';
  // Use 'ws://localhost:8000/ws/live' for iOS/web

  void connect() {
    try {
      _channel = WebSocketChannel.connect(Uri.parse(wsUrl));
      _isConnected = true;
      notifyListeners();

      _channel!.stream.listen(
        (message) {
          _handleMessage(message);
        },
        onDone: () {
          _isConnected = false;
          notifyListeners();
          // Auto-reconnect after 5 seconds
          Future.delayed(const Duration(seconds: 5), connect);
        },
        onError: (error) {
          _isConnected = false;
          notifyListeners();
          Future.delayed(const Duration(seconds: 5), connect);
        },
      );
    } catch (e) {
      _isConnected = false;
      debugPrint('WebSocket error: $e');
      Future.delayed(const Duration(seconds: 5), connect);
    }
  }

  void _handleMessage(dynamic message) {
    try {
      final data = json.decode(message as String) as Map<String, dynamic>;
      
      // Add to event list (max 100)
      _events.insert(0, data);
      if (_events.length > 100) _events.removeLast();

      // Update counters based on event type
      final type = data['type'] ?? '';
      if (type == 'violation') {
        _violationCount++;
      } else if (type == 'accident_risk') {
        _riskCount++;
      } else if (type == 'congestion') {
        _congestionLevel = data['data']?['level'] ?? 'free';
      }

      notifyListeners();
    } catch (e) {
      debugPrint('Event parse error: $e');
    }
  }

  void disconnect() {
    _channel?.sink.close();
    _isConnected = false;
    notifyListeners();
  }

  void clearEvents() {
    _events.clear();
    notifyListeners();
  }

  @override
  void dispose() {
    disconnect();
    super.dispose();
  }
}
