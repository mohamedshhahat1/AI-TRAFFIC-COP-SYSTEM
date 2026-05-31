import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/event_service.dart';
import '../services/api_service.dart';

/// Events Screen - Live Event Bus stream + event history
class EventsScreen extends StatefulWidget {
  const EventsScreen({super.key});

  @override
  State<EventsScreen> createState() => _EventsScreenState();
}

class _EventsScreenState extends State<EventsScreen> {
  Map<String, dynamic> _eventMetrics = {};

  @override
  void initState() {
    super.initState();
    _loadMetrics();
  }

  Future<void> _loadMetrics() async {
    final metrics = await ApiService.fetchEventMetrics();
    setState(() => _eventMetrics = metrics);
  }

  @override
  Widget build(BuildContext context) {
    final eventService = context.watch<EventService>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('🔥 Event Bus'),
        actions: [
          IconButton(
            icon: const Icon(Icons.delete_sweep),
            onPressed: () => eventService.clearEvents(),
            tooltip: 'Clear events',
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadMetrics,
          ),
        ],
      ),
      body: Column(
        children: [
          // Connection status + metrics
          Container(
            padding: const EdgeInsets.all(12),
            color: eventService.isConnected 
                ? Colors.green.withOpacity(0.1) 
                : Colors.red.withOpacity(0.1),
            child: Row(
              children: [
                Icon(
                  eventService.isConnected ? Icons.wifi : Icons.wifi_off,
                  color: eventService.isConnected ? Colors.green : Colors.red,
                  size: 18,
                ),
                const SizedBox(width: 8),
                Text(
                  eventService.isConnected ? 'Connected to Event Bus' : 'Disconnected',
                  style: TextStyle(
                    color: eventService.isConnected ? Colors.green : Colors.red,
                    fontWeight: FontWeight.bold,
                    fontSize: 13,
                  ),
                ),
                const Spacer(),
                Text(
                  '${eventService.events.length} events',
                  style: TextStyle(color: Colors.grey[400], fontSize: 12),
                ),
              ],
            ),
          ),

          // Event Bus Metrics
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                _buildMetricChip('Emitted', '${_eventMetrics['total_emitted'] ?? 0}', Colors.blue),
                const SizedBox(width: 8),
                _buildMetricChip('Handled', '${_eventMetrics['total_handled'] ?? 0}', Colors.green),
                const SizedBox(width: 8),
                _buildMetricChip('Failed', '${_eventMetrics['total_failed'] ?? 0}', Colors.red),
                const SizedBox(width: 8),
                _buildMetricChip('Rate', '${_eventMetrics['success_rate'] ?? 0}%', Colors.purple),
              ],
            ),
          ),

          // Live event stream
          Expanded(
            child: eventService.events.isEmpty
                ? const Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.bolt, size: 48, color: Colors.grey),
                        SizedBox(height: 12),
                        Text('Waiting for events...', style: TextStyle(color: Colors.grey)),
                        SizedBox(height: 4),
                        Text(
                          'Events will appear here in real-time\nwhen the AI pipeline is running',
                          textAlign: TextAlign.center,
                          style: TextStyle(color: Colors.grey, fontSize: 12),
                        ),
                      ],
                    ),
                  )
                : ListView.builder(
                    itemCount: eventService.events.length,
                    padding: const EdgeInsets.symmetric(horizontal: 8),
                    itemBuilder: (ctx, i) => _buildEventCard(eventService.events[i]),
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetricChip(String label, String value, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 8),
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(
          children: [
            Text(value, style: TextStyle(fontWeight: FontWeight.bold, color: color, fontSize: 16)),
            Text(label, style: TextStyle(fontSize: 10, color: Colors.grey[400])),
          ],
        ),
      ),
    );
  }

  Widget _buildEventCard(Map<String, dynamic> event) {
    final type = event['type'] ?? 'unknown';
    final topic = event['topic'] ?? type;
    final priority = event['priority'] ?? 'NORMAL';
    final data = event['data'] as Map<String, dynamic>? ?? {};

    final color = _priorityColor(priority);
    final icon = _typeIcon(type);

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 3),
      child: ListTile(
        dense: true,
        leading: Container(
          width: 36, height: 36,
          decoration: BoxDecoration(
            color: color.withOpacity(0.15),
            borderRadius: BorderRadius.circular(8),
          ),
          alignment: Alignment.center,
          child: Text(icon, style: const TextStyle(fontSize: 18)),
        ),
        title: Text(
          topic,
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
        ),
        subtitle: Text(
          data.entries.take(3).map((e) => '${e.key}: ${e.value}').join(' • '),
          style: TextStyle(fontSize: 11, color: Colors.grey[400]),
          overflow: TextOverflow.ellipsis,
        ),
        trailing: Container(
          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
          decoration: BoxDecoration(
            color: color.withOpacity(0.1),
            borderRadius: BorderRadius.circular(4),
          ),
          child: Text(
            priority,
            style: TextStyle(fontSize: 9, color: color, fontWeight: FontWeight.bold),
          ),
        ),
      ),
    );
  }

  Color _priorityColor(String p) {
    switch (p) {
      case 'EMERGENCY': return Colors.red;
      case 'CRITICAL': return Colors.red;
      case 'HIGH': return Colors.orange;
      case 'NORMAL': return Colors.blue;
      case 'LOW': return Colors.grey;
      default: return Colors.grey;
    }
  }

  String _typeIcon(String t) {
    switch (t) {
      case 'violation': return '🚨';
      case 'accident_risk': return '⚠️';
      case 'congestion': return '🚦';
      case 'tracking': return '🚗';
      case 'system': return '⚙️';
      default: return '📡';
    }
  }
}
