import 'package:flutter/material.dart';
import '../services/api_service.dart';

class ViolationsScreen extends StatefulWidget {
  const ViolationsScreen({super.key});

  @override
  State<ViolationsScreen> createState() => _ViolationsScreenState();
}

class _ViolationsScreenState extends State<ViolationsScreen> {
  List<dynamic> _violations = [];
  String _typeFilter = '';
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadViolations();
  }

  Future<void> _loadViolations() async {
    setState(() => _isLoading = true);
    final data = await ApiService.fetchViolations(
      limit: 50,
      type: _typeFilter.isEmpty ? null : _typeFilter,
    );
    setState(() {
      _violations = data;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('🚨 Violations'),
        actions: [
          PopupMenuButton<String>(
            icon: const Icon(Icons.filter_list),
            onSelected: (value) {
              setState(() => _typeFilter = value);
              _loadViolations();
            },
            itemBuilder: (_) => [
              const PopupMenuItem(value: '', child: Text('All Types')),
              const PopupMenuItem(value: 'speed_violation', child: Text('🏎️ Speed')),
              const PopupMenuItem(value: 'red_light_violation', child: Text('🚦 Red Light')),
              const PopupMenuItem(value: 'lane_violation', child: Text('🛣️ Lane')),
              const PopupMenuItem(value: 'parking_violation', child: Text('🚫 Parking')),
            ],
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadViolations,
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : _violations.isEmpty
                ? const Center(child: Text('No violations recorded'))
                : ListView.builder(
                    itemCount: _violations.length,
                    padding: const EdgeInsets.all(8),
                    itemBuilder: (ctx, i) => _buildViolationCard(_violations[i]),
                  ),
      ),
    );
  }

  Widget _buildViolationCard(Map<String, dynamic> v) {
    final severity = v['severity'] ?? 'low';
    final type = v['type'] ?? 'unknown';
    final color = _severityColor(severity);
    final icon = _typeIcon(type);

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: color.withOpacity(0.2),
          child: Text(icon, style: const TextStyle(fontSize: 20)),
        ),
        title: Text(
          type.replaceAll('_', ' ').toUpperCase(),
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
        ),
        subtitle: Text(
          'Vehicle #${v['track_id']} • ${v['vehicle_class'] ?? 'car'} • ${(v['speed'] ?? 0).toStringAsFixed(1)} km/h',
          style: TextStyle(color: Colors.grey[400], fontSize: 12),
        ),
        trailing: Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: color.withOpacity(0.15),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Text(
            severity.toUpperCase(),
            style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.bold),
          ),
        ),
      ),
    );
  }

  Color _severityColor(String s) {
    switch (s) {
      case 'critical': return Colors.red;
      case 'high': return Colors.orange;
      case 'medium': return Colors.yellow;
      case 'low': return Colors.green;
      default: return Colors.grey;
    }
  }

  String _typeIcon(String t) {
    switch (t) {
      case 'speed_violation': return '🏎️';
      case 'red_light_violation': return '🚦';
      case 'lane_violation': return '🛣️';
      case 'parking_violation': return '🚫';
      default: return '⚠️';
    }
  }
}
