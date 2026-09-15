# Architecture and reference audit

## Reference audit

Inspected Eipckz/music-theory-master at `b880c55086f8822cb0ea70897e750b38180c1800`, fetched September 14, 2026. The clone's working tree was clean. Read the README, CLAUDE guidance, design brand guide, current-home screenshot, and the requested adaptive, curriculum, exercise, UI, audio and storage entry points. Read packaging guidance and representative persistence tests. The reference application itself was not launched during this audit.

The reference uses Python/PyQt6, SQLite, an Elo/BKT/FSRS-lite progression system, teach-then-drill screens and an ink-green/ivory palette. `melodic_dictation` returns MIDI pitches as its answer and requests uniform `beats: 1.0`. Its pitch-list answer contract cannot represent the required rhythm-aware answer. Its staff view supplies useful drawing conventions but not this editor's duration/onset state.

Reused as design guidance: palette, native controls, manuscript-centered layout, separate teaching and practice, local storage principles. Rebuilt: music model, renderer/editor, synth scheduling, alignment/grading, attempts, session state and progression evidence. No original app database is opened. No original app source modules are imported. MIT reference notice is retained.

## Modules

| Module | Responsibility |
|---|---|
| `music.py` | Immutable events and scores; rational quarter-note time; deterministic generators; tie normalization; validation |
| `audio.py` | Sample-buffer synthesis and sounddevice output; exact event-to-sample scheduling; WAV export |
| `grading.py` | Independent attack, duration/rest and pitch scores; edit-distance alignment; notation observations |
| `editor.py` | Native QPainter staff, sequential entry, selection, pitch drag, duration correction, undo/redo |
| `curriculum.py` | Nine compact lessons, worked examples and three-day planning text |
| `storage.py` | App-specific SQLite, JSON evidence, idempotent submission, backup/restore, comparable-item progression |
| `ui.py` | Today/Learn/Practice/Progress/Settings, audio state, draft gates and export UI |
| `selftest.py` | Packaged Qt interaction smoke test with isolated demonstration data |

## Data model

An event retains exact onset, duration or explicit unknown duration, written diatonic step or unknown pitch, accidental, rest status, tie-to-next flag and voice. Tuplet metadata is reserved; the current editor does not offer tuplets. Only voice zero is accepted by imports. Score context retains meter, bars, key, BPM, beat unit, seed, generation level and model version.

Measure length is numerator * 4 / denominator. Seconds per quarter is 60 / BPM / beat-unit-in-quarter-notes. Pure-domain tests cover 3/4 and 6/8 with dotted-quarter tempo. The visible curriculum and editor context are intentionally restricted to C major, treble clef, 4/4 for this release.

Unknown durations use one provisional beat for layout only. They are not scored as one-beat answers. Reflow preserves all events when editing produces an overflow. The blank editor receives a score context with an empty event tuple. Its spacing cannot expose the target note count. Entered dense scores enlarge horizontally based on the answer itself.

## Playback state

The musical clock is a pre-rendered PCM buffer, not a GUI timer. A Qt timer only marks the expected end of playback. A completed target hearing opens a writing interval; Save hearing draft must be pressed before the next hearing. Stop consumes the exposure and marks interrupted playback as assistance. Errors invalidate independent evidence. A restart during playback is recorded as an interruption. Device availability is checked before output; hardware audibility and every possible midstream failure cannot be inferred from a successful API call.

## Persistence and privacy

Default path: platform local application data / TheoryDictationMaster / progress.sqlite3. `--data-dir` selects an explicit alternative. The default is separate from the reference app and does not use a synced Documents folder. No network or microphone service is initialized by the application.

Attempts include the target, answer, policy, seed/version, content fingerprint, assistance, exposure count, completed hearings, timed drafts, confidence, scores and grading/adaptation versions. UUID primary keys make repeated submissions idempotent. The active session is autosaved after edits and playback changes. JSON backup input is bounded and checked; restore first creates a safety backup. Corrupt databases are reported without deleting the original.

## Current limits

This is a usable single-line core, not a completed implementation of every phase in the original brief. The roadmap tracks adaptive scheduling depth, course customization, benchmark comparisons, advanced notation and optional modules. Automated GUI tests and screenshots are meaningful checks, not proof of comprehensive accessibility or musical engraving quality.
