import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../services/event_service.dart';
import '../widgets/stat_card.dart';
import '../widgets/health_badge.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  Map<String, dynamic> _stats = {};
  Map<String, dynamic> _health = {};
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    final results = await Future.wait([
      ApiService.fetchStats(),
      ApiService.fetchHealth(),
    ]);
    setState(() {
      _stats = results[0];
      _health = results[1];
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final eventService = context.watch<EventService>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('🚔 AI Traffic Cop'),
        centerTitle: true,
        actions: [
          HealthBadge(health: _health),
          const SizedBox(width: 8),
          Icon(
            eventService.isConnected ? Icons.wifi : Icons.wifi_off,
            color: eventService.isConnected ? Colors.green : Colors.red,
          ),
          const SizedBox(width: 16),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadData,
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  // Live Event Banner
                  if (eventService.events.isNotEmpty)
                    _buildLiveEventBanner(eventService),
                  const SizedBox(height: 16),

                  // Stats Cards
                  StatCard(
                    icon: Icons.directions_car,
                    label: 'Vehicles Tracked',
                    value: '${_stats['total_vehicles'] ?? 0}',
                    color: Colors.blue,
                  ),
                  StatCard(
                    icon: Icons.warning_amber,
                    label: 'Total Violations',
                    value: '${_stats['total_violations'] ?? eventService.violationCount}',
                    color: Colors.orange,
                  ),
                  StatCard(
                    icon: Icons.speed,
                    label: 'Average Speed',
                    value: '${_stats['avg_speed'] ?? 0} km/h',
                    color: Colors.cyan,
                  ),
                  StatCard(
                    icon: Icons.traffic,
                    label: 'Congestion',
                    value: eventService.congestionLevel.toUpperCase(),
                    color: _getCongestionColor(eventService.congestionLevel),
                  ),
                  StatCard(
                    icon: Icons.bolt,
                    label: 'Live Events',
                    value: '${eventService.events.length}',
                    color: Colors.purple,
                  ),
                  StatCard(
                    icon: Icons.monitor_heart,
                    label: 'Health Score',
                    value: '${_health['score'] ?? 100}%',
                    color: _getHealthColor(_health['score'] ?? 100),
                  ),

                  const SizedBox(height: 24),
                  const Text('System Status', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 10),
                  _buildStatusTile('AI Pipeline', true),
                  _buildStatusTile('Event Bus', eventService.isConnected),
                  _buildStatusTile('Camera Feed', true),
                  _buildStatusTile('Alert System', true),
                  _buildStatusTile('Monitoring', true),
                ],
              ),
      ),
    );
  }

  Widget _buildLiveEventBanner(EventService eventService) {
    final latest = eventService.events.first;
    final type = latest['type'] ?? 'event';
    final isViolation = type == 'violation';

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isViolation ? Colors.red.withOpacity(0.15) : Colors.blue.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: isViolation ? Colors.red.withOpacity(0.3) : Colors.blue.withOpacity(0.2)),
      ),
      child: Row(
        children: [
          Icon(isViolation ? Icons.warning : Icons.bolt, color: isViolation ? Colors.red : Colors.blue),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '🔥 Live: ${type.replaceAll('_', ' ').toUpperCase()}',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                ),
                Text(
                  latest['data']?.toString().substring(0, 60) ?? '',
                  style: TextStyle(fontSize: 11, color: Colors.grey[400]),
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatusTile(String name, bool active) {
    return ListTile(
      leading: Icon(Icons.circle, color: active ? Colors.green : Colors.red, size: 12),
      title: Text(name),
      trailing: Text(active ? 'Active' : 'Offline',
          style: TextStyle(color: active ? Colors.green : Colors.red)),
    );
  }

  Color _getCongestionColor(String level) {
    switch (level) {
      case 'free': return Colors.green;
      case 'moderate': return Colors.yellow;
      case 'heavy': return Colors.orange;
      case 'gridlock': return Colors.red;
      default: return Colors.grey;
    }
  }

  Color _getHealthColor(dynamic score) {
    final s = (score is int) ? score : 100;
    if (s >= 80) return Colors.green;
    if (s >= 50) return Colors.orange;
    return Colors.red;
  }
}
