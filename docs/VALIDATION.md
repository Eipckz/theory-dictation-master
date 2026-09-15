# Validation record

## Environment

Windows 11 x64, Python 3.14.1, PyQt6/Qt 6.10.2, NumPy 2.3.5, sounddevice 0.5.5 and PyInstaller 6.22.3. Source audit used reference revision b880c55086f8822cb0ea70897e750b38180c1800. Checks were performed September 14-15, 2026.

## Completed checks

- 39 pytest tests passed. Parametrized generation tests cover 100 seeds across seven levels and three meters, 2,100 generated two-bar examples.
- Independently specified rhythm-duration sum, dot/rest scheduling, compound beat-unit conversion, no-click scheduling, PCM bounds, ties versus reattacks, missing-note pitch alignment, unknown answers, ambiguous alignments, assistance exclusion and repeated-content exclusion.
- Qt tests: duration changes, incomplete sketches, undo/redo, hidden target and exam aids, paper self-check classification, interrupted playback/draft gates and default Vocal rest.
- SQLite tests: restart, duplicate submission, backup/restore and corrupt-restore preservation.
- Standalone executable launched with a new isolated data folder and passed the built-in Qt interaction smoke test. It does not need a Python installation from PATH.
- Native application captures at 100% and 150% scaling and a 940x680 logical window were inspected. The staff and coaching area scroll; target and answer use separate tabs.
- Default audio output driver completed a rendered representative phrase and reported no stream status error. This is an API/device check, not an independent listening assessment.
- The documentation walkthrough uses genuine Qt snapshots and scripted demonstration answers. It is not a recording of learner performance.

## Limits

The packaged test runs on the development Windows host with a fresh app-data folder, not on a separate clean VM. Core runtime code has no network dependency; a physical network-disconnection test was not performed. Audio timbre and all output devices were not independently listened to. Automatic vocal grading, harmonic dictation, two-part dictation, cross-platform packaging, detailed accessibility and real-world adaptive calibration were not validated.

See the repository's Actions tab for remote test and build results corresponding to each commit/tag. A release asset is not proof that unimplemented roadmap items have been completed.

