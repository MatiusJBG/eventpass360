import 'dart:async';

import 'package:flutter/material.dart';

import '../../domain/ui_state.dart';
import '../core/widgets/feedback_views.dart';
import '../core/widgets/status_badges.dart';

enum FieldType {
  text,
  email,
  password,
  integer,
  decimal,
  optionalInteger,
  dropdown,
  isoDate,
}

class CrudOption {
  final dynamic value;
  final String label;

  const CrudOption(this.value, this.label);
}

class CrudField {
  final String name;
  final String label;
  final FieldType type;
  final bool required;
  final bool requiredOnCreateOnly;
  final num? min;
  final num? max;
  final String? helperText;
  final Future<List<CrudOption>> Function()? loadOptions;

  const CrudField(
    this.name,
    this.label, {
    this.type = FieldType.text,
    this.required = true,
    this.requiredOnCreateOnly = false,
    this.min,
    this.max,
    this.helperText,
    this.loadOptions,
  });
}

class CrudRecord {
  final int id;
  final String title;
  final String subtitle;
  final bool estado;
  final Map<String, dynamic> values;
  final Widget? extraBadge;

  const CrudRecord({
    required this.id,
    required this.title,
    required this.subtitle,
    required this.estado,
    required this.values,
    this.extraBadge,
  });
}

class AdminCrudPanel extends StatefulWidget {
  final String title;
  final String entityLabel;
  final List<CrudField> fields;
  final bool serverSearch;
  final bool allowEstadoToggleOnEdit;
  final String? Function(Map<String, dynamic> payload)? crossFieldValidator;
  final Future<List<CrudRecord>> Function(String? query) load;
  final Future<void> Function(Map<String, dynamic> body) create;
  final Future<void> Function(int id, Map<String, dynamic> body) update;
  final Future<void> Function(int id) delete;

  const AdminCrudPanel({
    super.key,
    required this.title,
    required this.entityLabel,
    required this.fields,
    this.serverSearch = false,
    this.allowEstadoToggleOnEdit = true,
    this.crossFieldValidator,
    required this.load,
    required this.create,
    required this.update,
    required this.delete,
  });

  @override
  State<AdminCrudPanel> createState() => _AdminCrudPanelState();
}

class _AdminCrudPanelState extends State<AdminCrudPanel> {
  final _searchCtrl = TextEditingController();
  Timer? _debounce;

  UiState<List<CrudRecord>> _state = const UiLoading();
  String _query = '';
  int? _deletingId;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _searchCtrl.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() => _state = const UiLoading());
    try {
      final items = await widget.load(
        widget.serverSearch && _query.isNotEmpty ? _query : null,
      );
      if (mounted) setState(() => _state = UiSuccess(items));
    } catch (e) {
      if (mounted) setState(() => _state = UiError(e.toString()));
    }
  }

  void _onSearchChanged(String value) {
    setState(() => _query = value.trim());
    if (widget.serverSearch) {
      _debounce?.cancel();
      _debounce = Timer(const Duration(milliseconds: 350), _load);
    }
  }

  Future<void> _openForm([CrudRecord? existing]) async {
    final optionsMap = <String, List<CrudOption>>{};
    try {
      for (final field in widget.fields) {
        if (field.type == FieldType.dropdown && field.loadOptions != null) {
          optionsMap[field.name] = await field.loadOptions!();
        }
      }
    } catch (e) {
      if (mounted) {
        showAppSnack(
          context,
          'No se pudieron cargar las opciones: $e',
          error: true,
        );
      }
      return;
    }

    if (!mounted) return;

    final saved = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (_) => _CrudFormDialog(
        entityLabel: widget.entityLabel,
        fields: widget.fields,
        optionsMap: optionsMap,
        existing: existing,
        allowEstadoToggleOnEdit: widget.allowEstadoToggleOnEdit,
        crossFieldValidator: widget.crossFieldValidator,
        onSubmit: (payload) async {
          if (existing == null) {
            await widget.create(payload);
          } else {
            await widget.update(existing.id, payload);
          }
        },
      ),
    );

    if (saved == true && mounted) {
      showAppSnack(
        context,
        existing == null
            ? '${widget.entityLabel} creado correctamente'
            : '${widget.entityLabel} actualizado correctamente',
      );
      await _load();
    }
  }

  Future<void> _deleteRecord(CrudRecord record) async {
    final ok = await ConfirmDialog.show(
      context,
      title: 'Eliminar ${widget.entityLabel.toLowerCase()}',
      message:
          '¿Deseas eliminar o desactivar "${record.title}"? Esta acción afectará el catálogo.',
      confirmLabel: 'Eliminar',
    );
    if (!ok || !mounted) return;

    setState(() => _deletingId = record.id);
    try {
      await widget.delete(record.id);
      if (!mounted) return;
      showAppSnack(context, '${widget.entityLabel} eliminado/desactivado');
      await _load();
    } catch (e) {
      if (mounted) showAppSnack(context, e.toString(), error: true);
    } finally {
      if (mounted) setState(() => _deletingId = null);
    }
  }

  List<CrudRecord> _filterLocal(List<CrudRecord> items) {
    if (widget.serverSearch || _query.isEmpty) return items;
    final lower = _query.toLowerCase();
    return items
        .where(
          (r) =>
              r.title.toLowerCase().contains(lower) ||
              r.subtitle.toLowerCase().contains(lower),
        )
        .toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _openForm(),
        icon: const Icon(Icons.add),
        label: Text('Nuevo ${widget.entityLabel.toLowerCase()}'),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 6),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _searchCtrl,
                    decoration: InputDecoration(
                      hintText: 'Buscar en ${widget.title.toLowerCase()}...',
                      prefixIcon: const Icon(Icons.search),
                      isDense: true,
                      suffixIcon: _query.isEmpty
                          ? null
                          : IconButton(
                              tooltip: 'Limpiar',
                              icon: const Icon(Icons.clear),
                              onPressed: () {
                                _searchCtrl.clear();
                                _onSearchChanged('');
                                if (widget.serverSearch) _load();
                              },
                            ),
                    ),
                    onChanged: _onSearchChanged,
                    onSubmitted: (_) {
                      if (widget.serverSearch) {
                        _debounce?.cancel();
                        _load();
                      }
                    },
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  tooltip: 'Recargar',
                  icon: const Icon(Icons.refresh),
                  onPressed: _load,
                ),
              ],
            ),
          ),
          Expanded(
            child: switch (_state) {
              UiLoading() => LoadingView(
                  label: 'Cargando ${widget.title.toLowerCase()}...',
                ),
              UiError(:final message) => ErrorStateView(
                  message: message,
                  onRetry: _load,
                ),
              UiSuccess(:final data) => _buildList(_filterLocal(data)),
            },
          ),
        ],
      ),
    );
  }

  Widget _buildList(List<CrudRecord> items) {
    if (items.isEmpty) {
      return EmptyStateView(
        message: 'No hay registros en ${widget.title.toLowerCase()}.',
      );
    }

    return RefreshIndicator(
      onRefresh: _load,
      child: ListView.builder(
        padding: const EdgeInsets.fromLTRB(12, 4, 12, 88),
        itemCount: items.length,
        itemBuilder: (context, index) {
          final record = items[index];
          final deleting = _deletingId == record.id;

          return Card(
            margin: const EdgeInsets.only(bottom: 10),
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Wrap(
                          spacing: 8,
                          runSpacing: 6,
                          crossAxisAlignment: WrapCrossAlignment.center,
                          children: [
                            Text(
                              record.title,
                              style: Theme.of(context)
                                  .textTheme
                                  .titleMedium
                                  ?.copyWith(fontWeight: FontWeight.bold),
                            ),
                            StatusBadge.fromBool(record.estado),
                            if (record.extraBadge != null) record.extraBadge!,
                          ],
                        ),
                        if (record.subtitle.isNotEmpty) ...[
                          const SizedBox(height: 6),
                          Text(
                            record.subtitle,
                            style: Theme.of(context)
                                .textTheme
                                .bodyMedium
                                ?.copyWith(color: Colors.grey.shade700),
                          ),
                        ],
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      IconButton(
                        tooltip: 'Editar',
                        icon: const Icon(Icons.edit_outlined),
                        onPressed: deleting ? null : () => _openForm(record),
                      ),
                      if (deleting)
                        const Padding(
                          padding: EdgeInsets.all(12),
                          child: SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          ),
                        )
                      else
                        IconButton(
                          tooltip: 'Eliminar / Desactivar',
                          icon: const Icon(
                            Icons.delete_outline,
                            color: Colors.red,
                          ),
                          onPressed: () => _deleteRecord(record),
                        ),
                    ],
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}

class _CrudFormDialog extends StatefulWidget {
  final String entityLabel;
  final List<CrudField> fields;
  final Map<String, List<CrudOption>> optionsMap;
  final CrudRecord? existing;
  final bool allowEstadoToggleOnEdit;
  final String? Function(Map<String, dynamic> payload)? crossFieldValidator;
  final Future<void> Function(Map<String, dynamic> payload) onSubmit;

  const _CrudFormDialog({
    required this.entityLabel,
    required this.fields,
    required this.optionsMap,
    required this.existing,
    required this.allowEstadoToggleOnEdit,
    required this.crossFieldValidator,
    required this.onSubmit,
  });

  @override
  State<_CrudFormDialog> createState() => _CrudFormDialogState();
}

class _CrudFormDialogState extends State<_CrudFormDialog> {
  final _formKey = GlobalKey<FormState>();
  final Map<String, TextEditingController> _controllers = {};
  final Map<String, dynamic> _dropdownValues = {};
  final Map<String, bool> _obscureMap = {};

  bool _estado = true;
  bool _saving = false;
  String? _submitError;

  bool get _isEdit => widget.existing != null;

  @override
  void initState() {
    super.initState();
    _estado = widget.existing?.estado ?? true;
    for (final field in widget.fields) {
      final raw = widget.existing?.values[field.name];
      if (field.type == FieldType.dropdown) {
        final opts = widget.optionsMap[field.name] ?? const [];
        final hasMatch = opts.any((o) => o.value == raw);
        _dropdownValues[field.name] =
            hasMatch ? raw : (opts.isNotEmpty ? opts.first.value : null);
      } else if (field.type == FieldType.password) {
        _controllers[field.name] = TextEditingController();
        _obscureMap[field.name] = true;
      } else {
        _controllers[field.name] = TextEditingController(
          text: raw == null ? '' : raw.toString(),
        );
      }
    }
  }

  @override
  void dispose() {
    for (final ctrl in _controllers.values) {
      ctrl.dispose();
    }
    super.dispose();
  }

  Map<String, dynamic> _buildPayload() {
    final payload = <String, dynamic>{};
    for (final field in widget.fields) {
      switch (field.type) {
        case FieldType.dropdown:
          payload[field.name] = _dropdownValues[field.name];
        case FieldType.integer:
          final text = _controllers[field.name]!.text.trim();
          payload[field.name] = int.tryParse(text);
        case FieldType.optionalInteger:
          final text = _controllers[field.name]!.text.trim();
          payload[field.name] = text.isEmpty ? null : int.tryParse(text);
        case FieldType.decimal:
          final text =
              _controllers[field.name]!.text.trim().replaceAll(',', '.');
          payload[field.name] = double.tryParse(text);
        case FieldType.password:
          final text = _controllers[field.name]!.text;
          if (text.isNotEmpty) {
            payload[field.name] = text;
          }
        case FieldType.text:
        case FieldType.email:
        case FieldType.isoDate:
          payload[field.name] = _controllers[field.name]!.text.trim();
      }
    }
    if (_isEdit && widget.allowEstadoToggleOnEdit) {
      payload['estado'] = _estado;
    }
    return payload;
  }

  String? _validateField(CrudField field, String? raw) {
    final value = raw?.trim() ?? '';
    final mustRequire = field.required &&
        !(field.requiredOnCreateOnly && _isEdit) &&
        field.type != FieldType.optionalInteger;

    if (mustRequire && value.isEmpty) {
      return '${field.label} es obligatorio';
    }
    if (value.isEmpty) return null;

    switch (field.type) {
      case FieldType.email:
        if (!RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch(value)) {
          return 'Ingresa un correo electrónico válido';
        }
      case FieldType.password:
        if ((raw ?? '').length < 6) {
          return 'La contraseña debe tener al menos 6 caracteres';
        }
      case FieldType.integer:
      case FieldType.optionalInteger:
        final parsed = int.tryParse(value);
        if (parsed == null) return 'Ingresa un número entero válido';
        if (field.min != null && parsed < field.min!) {
          return 'Debe ser mayor o igual a ${field.min}';
        }
        if (field.max != null && parsed > field.max!) {
          return 'Debe ser menor o igual a ${field.max}';
        }
      case FieldType.decimal:
        final parsed = double.tryParse(value.replaceAll(',', '.'));
        if (parsed == null) return 'Ingresa un número decimal válido';
        if (field.min != null && parsed < field.min!) {
          return 'Debe ser mayor o igual a ${field.min}';
        }
        if (field.max != null && parsed > field.max!) {
          return 'Debe ser menor o igual a ${field.max}';
        }
      case FieldType.isoDate:
        if (DateTime.tryParse(value) == null) {
          return 'Usa formato ISO válido (ej. 2026-12-20T20:00:00)';
        }
      case FieldType.text:
      case FieldType.dropdown:
        break;
    }
    return null;
  }

  Future<void> _save() async {
    setState(() => _submitError = null);
    if (!(_formKey.currentState?.validate() ?? false)) return;

    final payload = _buildPayload();
    final crossError = widget.crossFieldValidator?.call(payload);
    if (crossError != null) {
      setState(() => _submitError = crossError);
      return;
    }

    setState(() => _saving = true);
    try {
      await widget.onSubmit(payload);
      if (mounted) Navigator.of(context).pop(true);
    } catch (e) {
      if (mounted) {
        setState(() {
          _submitError = e.toString();
          _saving = false;
        });
      }
    }
  }

  Widget _buildFieldWidget(CrudField field) {
    if (field.type == FieldType.dropdown) {
      final options = widget.optionsMap[field.name] ?? const [];
      return DropdownButtonFormField<dynamic>(
        initialValue: _dropdownValues[field.name],
        isExpanded: true,
        decoration: InputDecoration(
          labelText: field.label,
          helperText: field.helperText,
        ),
        items: options
            .map(
              (o) => DropdownMenuItem<dynamic>(
                value: o.value,
                child: Text(o.label, overflow: TextOverflow.ellipsis),
              ),
            )
            .toList(),
        validator: (value) {
          if (field.required && value == null) {
            return 'Selecciona ${field.label.toLowerCase()}';
          }
          return null;
        },
        onChanged: _saving
            ? null
            : (v) => setState(() => _dropdownValues[field.name] = v),
      );
    }

    final isPassword = field.type == FieldType.password;
    final obscure = _obscureMap[field.name] ?? false;

    final keyboardType = switch (field.type) {
      FieldType.email => TextInputType.emailAddress,
      FieldType.integer || FieldType.optionalInteger => TextInputType.number,
      FieldType.decimal =>
        const TextInputType.numberWithOptions(decimal: true),
      _ => TextInputType.text,
    };

    return TextFormField(
      controller: _controllers[field.name],
      enabled: !_saving,
      obscureText: isPassword && obscure,
      keyboardType: keyboardType,
      decoration: InputDecoration(
        labelText: field.requiredOnCreateOnly && _isEdit
            ? '${field.label} (opcional)'
            : field.label,
        helperText: field.helperText,
        suffixIcon: isPassword
            ? IconButton(
                icon: Icon(
                  obscure
                      ? Icons.visibility_outlined
                      : Icons.visibility_off_outlined,
                ),
                onPressed: () =>
                    setState(() => _obscureMap[field.name] = !obscure),
              )
            : null,
      ),
      validator: (v) => _validateField(field, v),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(
        _isEdit
            ? 'Editar ${widget.entityLabel.toLowerCase()}'
            : 'Nuevo ${widget.entityLabel.toLowerCase()}',
      ),
      content: SizedBox(
        width: 440,
        child: SingleChildScrollView(
          child: Form(
            key: _formKey,
            autovalidateMode: AutovalidateMode.onUserInteraction,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (_submitError != null) ...[
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(10),
                    margin: const EdgeInsets.only(bottom: 12),
                    decoration: BoxDecoration(
                      color: Colors.red.shade50,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.red.shade200),
                    ),
                    child: Text(
                      _submitError!,
                      style: TextStyle(color: Colors.red.shade800),
                    ),
                  ),
                ],
                for (final field in widget.fields) ...[
                  _buildFieldWidget(field),
                  const SizedBox(height: 12),
                ],
                if (_isEdit && widget.allowEstadoToggleOnEdit)
                  SwitchListTile(
                    contentPadding: EdgeInsets.zero,
                    title: const Text('Registro activo'),
                    subtitle: Text(
                      _estado
                          ? 'Visible y operativo en el sistema'
                          : 'Desactivado (baja lógica)',
                    ),
                    value: _estado,
                    onChanged: _saving
                        ? null
                        : (value) => setState(() => _estado = value),
                  ),
              ],
            ),
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: _saving ? null : () => Navigator.of(context).pop(false),
          child: const Text('Cancelar'),
        ),
        LoadingButton(
          loading: _saving,
          onPressed: _save,
          label: 'Guardar',
          loadingLabel: 'Guardando...',
        ),
      ],
    );
  }
}
