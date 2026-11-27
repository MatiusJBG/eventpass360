/// Dart 3 algebraic UI state for exhaustive pattern matching across screens.
library;

sealed class UiState<T> {
  const UiState();
}

final class UiLoading<T> extends UiState<T> {
  const UiLoading();
}

final class UiSuccess<T> extends UiState<T> {
  final T data;
  const UiSuccess(this.data);
}

final class UiError<T> extends UiState<T> {
  final String message;
  const UiError(this.message);
}
