import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'screens/home.dart';
import 'screens/violations.dart';
import 'screens/monitoring.dart';
import 'screens/events.dart';
import 'screens/results.dart';
import 'services/event_service.dart';

void main() {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => EventService()),
      ],
      child: const TrafficCopApp(),
    ),
  );
}

class TrafficCopApp extends StatelessWidget {
  const TrafficCopApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AI Traffic Cop',
      theme: ThemeData(
        brightness: Brightness.dark,
        primarySwatch: Colors.blue,
        scaffoldBackgroundColor: const Color(0xFF1E1E2E),
        cardColor: const Color(0xFF2D2D3F),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF4285F4),
          secondary: Color(0xFF34A853),
          error: Color(0xFFEA4335),
        ),
      ),
      home: const MainScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class MainScreen extends StatefulWidget {
  const MainScreen({super.key});

  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  int _selectedIndex = 0;

  final _pages = const [
    HomeScreen(),
    ViolationsScreen(),
    MonitoringScreen(),
    EventsScreen(),
    ResultsScreen(),
  ];

  @override
  void initState() {
    super.initState();
    context.read<EventService>().connect();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _pages[_selectedIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: (i) => setState(() => _selectedIndex = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.dashboard), label: 'Dashboard'),
          NavigationDestination(icon: Icon(Icons.warning_amber), label: 'Violations'),
          NavigationDestination(icon: Icon(Icons.monitor_heart), label: 'Monitoring'),
          NavigationDestination(icon: Icon(Icons.bolt), label: 'Events'),
          NavigationDestination(icon: Icon(Icons.analytics), label: 'Results'),
        ],
      ),
    );
  }
}
