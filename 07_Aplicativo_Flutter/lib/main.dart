import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';

import 'app.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SemanticsBinding.instance.ensureSemantics();
  runApp(const EventPassApp());
}
