import 'package:flutter/material.dart';
import '../services/api_service.dart';

class ViolationsScreen extends StatefulWidget {
  const ViolationsScreen({super.key});

  @override
  State<ViolationsScreen> createState() => _ViolationsScreenState();
}

class _ViolationsScreenState extends State<ViolationsScreen> {
  List<dynamic> _violations = [];

  @override
  void initState() {
    super.initState();
    _loadViolations();
  }

  Future<void> _loadViolations() async {
    final data = await ApiService.fetchViolations();
    setState(() => _violations = data);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('🚨 Violations')),
      body: RefreshIndicator(
        onRefresh: _loadViolations,
        child: _violations.isEmpty
            ? const Center(child: Text('No violations recorded'))
            : ListView.builder(
                itemCount: _violations.length,
                itemBuilder: (ctx, i) => _buildViolationTile(_violations[i]),
              ),
      ),
    );
  }

  Widget _buildViolationTile(Map<String, dynamic> v) {
    final severity = v['severity'] ?? 'low';
    final color = {
      'critical': Colors.red,
      'high': Colors.orange,
      'medium': Colors.yellow,
      'low': Colors.green,
    }[severity] ?? Colors.grey;

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      child: ListTile(
        leading: CircleAvatar(backgroundColor: color, radius: 8),
        title: Text(v['type']?.toString().replaceAll('_', ' ') ?? 'Unknown'),
        subtitle: Text('Vehicle #${v['track_id']} | ${v['speed']?.toStringAsFixed(1) ?? 0} km/h'),
        trailing: Text(severity.toUpperCase(), style: TextStyle(color: color, fontWeight: FontWeight.bold)),
      ),
    );
  }
}
