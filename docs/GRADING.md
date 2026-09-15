# Grading and evidence

## Components

- **Attack timing:** F1 overlap of exact sounding-note onset sets. Ties merge into one attack; repeated untied notes remain separate.
- **Durations/rests:** F1 overlap of exact `(onset, duration, rest-or-sound)` segments after valid ties merge. Pitch is excluded.
- **Pitch:** `1 - edit_distance / max(target_notes, answer_notes)`. Levenshtein alignment uses insertion, deletion and substitution costs of one. Rhythm is excluded. A missing pitch therefore creates one edit rather than shifting every later comparison.
- **Notation conventions:** a coarse separate check for written spelling of correctly aligned sounding pitches and unsplit barline crossings. It is not a comprehensive engraving grade.
- **Integrated:** the minimum assessed listening component. Incomplete sketches cannot earn integrated success. Rhythm-only tasks omit pitch assessment, and explicitly unknown pitches are allowed.

Scores describe exact symbolic transcription, not millisecond performance timing. There is no microphone grading or tapping score. Octave differences count as pitch differences. Enharmonic sounding equivalence can retain pitch credit while spelling is discussed separately. Equivalent ties and a longer note receive sound credit. Untied reattacks differ.

Alignment can have more than one optimal path, particularly with repeated pitches. The app marks that ambiguity and avoids pretending to know the exact local pitch confusion. Rhythm feedback names the first missing or extra score-time attack. Score-time positions are measured in quarter-note units from zero, not displayed beat numbers.

## Independent evidence

Only complete, audio-valid, unassisted independent submissions are eligible for confirmed progression. A self-check, guided example, one-pitch reveal, answer playback before submission, external WAV export, interrupted hearing or lesson visited during an active heard exercise cannot establish independent mastery. A target content fingerprint counts once within a condition group. Repeated listening before one submission is exposure, not another exercise.

Comparable groups include level, bars, BPM, meter, support, mode, hearing allowance and assessed components. UI summary averages that mix conditions are labeled descriptive. They are not presented as improvement estimates.

## Initial adjustable heuristics

The engineering default is two blocks of eight unfamiliar items with at least seven passing in each block. Passing requires at least 90% on every assessed pitch/rhythm component. A successful gate advances the confirmed level by one. The internal `pass_threshold` setting can be adjusted in the local store; a friendly threshold editor is not yet supplied.

Five comparable independent attempts averaging below 70% produce a support recommendation. Support is offered without erasing unrelated history. The user can choose Easier, Stay here or Challenge. Those choices change exploratory practice and do not manufacture confirmed progress.

Current limitations: these thresholds have not been validated on real learner data. Due reminders are scheduled 20 minutes after submissions; automatic later-day sequencing, retained labels, condition-matched baseline/follow-up charts and separate mastery estimators for all eight requested skills remain planned. No claim of mastery in three days is made.
