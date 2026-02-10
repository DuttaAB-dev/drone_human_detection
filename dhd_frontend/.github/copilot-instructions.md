## Purpose

This project is a Flutter desktop/mobile frontend for a YOLO-based object detection service.
These instructions are targeted at AI coding agents (Copilot-style) so they can be immediately productive in this repo.

## Big picture (what to know first)
- Frontend: Flutter app in `lib/main.dart`. It provides a UI to pick an image/video, select detection classes and POST to the backend.
- Backend contract: the app POSTs multipart/form-data to `POST /detect` on the configured `backendUrl` (default `http://localhost:3000` in `lib/main.dart`).
  - Request: `file` multipart, plus fields `classes` (JSON array string) and `fileType` (`image` or `video`).
  - Image response: JSON containing detection metadata and (optionally) `image` pointing to the processed image path.
  - Video response: server returns video bytes; detection metadata may be sent in header `x-detection-results` as a JSON string.

## Where to look (key files)
- `lib/main.dart` — main UI, upload flow, `yoloClasses` list, `backendUrl` and all client-side logic.
- `pubspec.yaml` — project dependencies and `dependency_overrides` (note `file_selector_linux`).
- `linux/CMakeLists.txt` — desktop packaging details and registered plugin list (includes `file_selector_linux`).
- `runner/` (linux runner) — native entrypoint and packaging rules (see `add_subdirectory("runner")` in `linux/CMakeLists.txt`).

## Build, run and debug workflows (explicit)
- Install deps: `flutter pub get`.
- Run in debug: `flutter run` (specify `-d linux`, `-d windows`, `-d android`, etc. as appropriate).
- Build desktop release (Linux): `flutter build linux --release`.
  - CMake config sets the runtime output directory to `intermediates_do_not_run` and installs a relocatable bundle under the build bundle dir. See `linux/CMakeLists.txt` for details.
- When testing detection integration, ensure the backend is reachable at the `backendUrl` (default `http://localhost:3000`). If backend is remote, change `backendUrl` in `lib/main.dart` or inject via environment/config.

## Project-specific conventions and patterns
- Uses `file_selector` + `file_selector_linux` (note: not `file_picker`). The project overrides `file_selector_linux` in `pubspec.yaml`.
- UI: Material 3 (see ThemeData/useMaterial3) and `themeMode` default set to dark in `MyApp`.
- `yoloClasses` is a canonical, hard-coded list in `lib/main.dart`; selection state is kept in `selectedClasses` and sent as JSON-encoded string in the multipart field `classes`.
- Video handling: frontend expects raw processed video bytes from `/detect` and looks for `x-detection-results` header for metadata.

## Common edits an agent might perform (and where)
- Change backend URL or add config: `lib/main.dart` (variable `backendUrl`). Prefer adding a small config file or using build-time environment variables for non-hardcoded changes.
- Add/remove detection categories: `lib/main.dart` (`yoloClasses` list).
- Change file selection behavior: look at `pickFile()` which uses `openFile(acceptedTypeGroups: ...)`.
- Add tests: project currently has `test/widget_test.dart`; follow Flutter test patterns and add widget/unit tests under `test/`.

## Troubleshooting tips for runtime errors
- If file selection fails on Linux, verify `file_selector_linux` plugin is included in `linux/CMakeLists.txt` plugin list and `dependency_overrides` in `pubspec.yaml`.
- If upload fails, confirm backend is running and reachable at `backendUrl` and that `/detect` accepts the multipart fields `file`, `classes`, `fileType`.
- For processed-video debugging: the app writes received bytes to a temp file (`Directory.systemTemp`) and initializes `VideoPlayerController` — check temp file permissions and content if playback fails.

## Example snippets (from repo)
- Send classes in multipart: `request.fields['classes'] = jsonEncode(selectedClasses);`
- Backend URL placeholder: `final String backendUrl = 'http://localhost:3000';` (see `lib/main.dart`).

## When in doubt
- Inspect `lib/main.dart` to find the exact client-side contract. Inspect backend `/detect` implementation (if part of the multi-repo) to confirm headers and response shape.

---
If any of these sections are unclear or you want more detail (CI, packaging steps for a specific platform, or a suggested environment variable strategy), tell me which part to expand. 