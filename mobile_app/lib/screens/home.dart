import 'package:flutter/material.dart';
import '../services/api_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  Map<String, dynamic> _stats = {};

  @override
  void initState() {
    super.initState();
    _loadStats();
  }

  Future<void> _loadStats() async {
    final stats = await ApiService.fetchStats();
    setState(() => _stats = stats);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('🚔 AI Traffic Cop'),
        centerTitle: true,
      ),
      body: RefreshIndicator(
        onRefresh: _loadStats,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _buildStatCard('🚗', 'Vehicles', '${_stats['total_vehicles'] ?? 0}'),
            _buildStatCard('🚨', 'Violations', '${_stats['total_violations'] ?? 0}'),
            _buildStatCard('⚡', 'Avg Speed', '${_stats['avg_speed'] ?? 0} km/h'),
            _buildStatCard('🚦', 'Congestion', '${_stats['congestion_level'] ?? 'Free'}'),
            const SizedBox(height: 20),
            const Text('System Status', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            _buildStatusTile('AI Engine', true),
            _buildStatusTile('Camera Feed', true),
            _buildStatusTile('Alert System', true),
          ],
        ),
      ),
    );
  }

  Widget _buildStatCard(String icon, String label, String value) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        leading: Text(icon, style: const TextStyle(fontSize: 28)),
        title: Text(value, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
        subtitle: Text(label),
      ),
    );
  }

  Widget _buildStatusTile(String name, bool active) {
    return ListTile(
      leading: Icon(Icons.circle, color: active ? Colors.green : Colors.red, size: 12),
      title: Text(name),
      trailing: Text(active ? 'Active' : 'Offline'),
    );
  }
}
