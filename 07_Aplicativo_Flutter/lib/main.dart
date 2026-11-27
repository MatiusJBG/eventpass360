import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:provider/provider.dart';

import 'app.dart';
import 'core/session.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SemanticsBinding.instance.ensureSemantics();
  runApp(
    ChangeNotifierProvider(
      create: (_) => Session(),
      child: const EventPassApp(),
    ),
  );
}
