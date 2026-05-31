import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../widgets/health_badge.dart';

/// Monitoring Screen - System health, metrics, and logs
class MonitoringScreen extends StatefulWidget {
  const MonitoringScreen({super.key});

  @override
  State<MonitoringScreen> createState() => _MonitoringScreenState();
}

class _MonitoringScreenState extends State<MonitoringScreen> {
  Map<String, dynamic> _health = {};
  Map<String, dynamic> _metrics = {};
  Map<String, dynamic> _logStats = {};
  List<dynamic> _logs = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    final results = await Future.wait([
      ApiService.fetchHealth(),
      ApiService.fetchMetrics(),
      ApiService.fetchLogStats(),
      ApiService.fetchLogs(limit: 20),
    ]);
    setState(() {
      _health = results[0];
      _metrics = results[1];
      _logStats = results[2];
      _logs = results[3] as List<dynamic>;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('📈 Monitoring'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadData),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadData,
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  // Health Section
                  _buildSection('❤️ System Health', [
                    _buildHealthCard(),
                    if (_health['components'] != null)
                      ..._buildComponentCards(),
                    if (_health['alerts'] != null && (_health['alerts'] as List).isNotEmpty)
                      _buildAlertsCard(),
                  ]),

                  const SizedBox(height: 20),

                  // Metrics Section
                  _buildSection('⚡ Performance', [
                    _buildMetricRow('FPS', '${_metrics['fps'] ?? 0}'),
                    _buildMetricRow('Frame Processing', '${_metrics['frame_processing_ms']?['avg']?.toStringAsFixed(1) ?? 0}ms'),
                    _buildMetricRow('Detection', '${_metrics['detection_ms']?['avg']?.toStringAsFixed(1) ?? 0}ms'),
                    _buildMetricRow('Total Frames', '${_metrics['total_frames'] ?? 0}'),
                    _buildMetricRow('Error Rate', '${((_metrics['error_rate'] ?? 0) * 100).toStringAsFixed(2)}%'),
                  ]),

                  const SizedBox(height: 20),

                  // Log Stats Section
                  _buildSection('📝 Log Statistics', [
                    _buildMetricRow('Total Logs', '${_logStats['total_logs'] ?? 0}'),
                    _buildMetricRow('Errors', '${_logStats['errors'] ?? 0}', color: Colors.red),
                    _buildMetricRow('Warnings', '${_logStats['warnings'] ?? 0}', color: Colors.orange),
                  ]),

                  const SizedBox(height: 20),

                  // Recent Logs
                  _buildSection('📋 Recent Logs', [
                    if (_logs.isEmpty)
                      const Padding(
                        padding: EdgeInsets.all(16),
                        child: Text('No logs yet', style: TextStyle(color: Colors.grey)),
                      )
                    else
                      ..._logs.take(10).map((log) => _buildLogEntry(log)),
                  ]),
                ],
              ),
      ),
    );
  }

  Widget _buildSection(String title, List<Widget> children) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(children: children),
          ),
        ),
      ],
    );
  }

  Widget _buildHealthCard() {
    final score = _health['score'] ?? 100;
    final status = _health['status'] ?? 'unknown';
    final color = score >= 80 ? Colors.green : score >= 50 ? Colors.orange : Colors.red;

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          CircularProgressIndicator(
            value: score / 100,
            color: color,
            backgroundColor: color.withOpacity(0.2),
          ),
          const SizedBox(width: 16),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Score: $score/100', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: color)),
              Text('Status: ${status.toUpperCase()}', style: TextStyle(color: color)),
            ],
          ),
        ],
      ),
    );
  }

  List<Widget> _buildComponentCards() {
    final components = _health['components'] as Map<String, dynamic>;
    return components.entries.map((e) {
      final data = e.value as Map<String, dynamic>;
      final status = data['status'] ?? 'unknown';
      final color = status == 'healthy' ? Colors.green : status == 'degraded' ? Colors.orange : Colors.red;
      return ListTile(
        dense: true,
        leading: Icon(Icons.circle, color: color, size: 10),
        title: Text(e.key.replaceAll('_', ' '), style: const TextStyle(fontSize: 13)),
        trailing: Text('${data['avg'] ?? 0}ms', style: TextStyle(color: Colors.grey[400])),
      );
    }).toList();
  }

  Widget _buildAlertsCard() {
    final alerts = _health['alerts'] as List;
    return Container(
      margin: const EdgeInsets.only(top: 8),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: Colors.red.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('⚠️ Alerts', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.orange)),
          ...alerts.map((a) => Text('• $a', style: const TextStyle(fontSize: 12))),
        ],
      ),
    );
  }

  Widget _buildMetricRow(String label, String value, {Color? color}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(color: Colors.grey[400])),
          Text(value, style: TextStyle(fontWeight: FontWeight.bold, color: color ?? Colors.white)),
        ],
      ),
    );
  }

  Widget _buildLogEntry(dynamic log) {
    final level = (log['level'] ?? 'INFO').toString();
    final color = level == 'ERROR' ? Colors.red : level == 'WARNING' ? Colors.orange : Colors.blue;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        children: [
          Container(
            width: 50,
            child: Text(level, style: TextStyle(fontSize: 10, color: color, fontWeight: FontWeight.bold)),
          ),
          Expanded(
            child: Text(
              '[${log['component'] ?? ''}] ${log['message'] ?? ''}',
              style: const TextStyle(fontSize: 11, fontFamily: 'monospace'),
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}
