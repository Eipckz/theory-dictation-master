# Version 1.0.0 validation

## Automated checks

- 21 domain, audio, storage, review and sync tests.
- 6,300 generated phrases checked for deterministic generation and exact bar totals, including 5,600 covering four keys, four meters and seven levels.
- Known-answer compound-meter timing and transposed/minor reference tests.
- Delayed-review timing, non-overlapping comparison groups, assistance exclusion and hearing-draft grading.
- 18 local browser cases across desktop Chromium and a mobile viewport: silent editing, playback, offline reload, WAV export, paper mode, controlled sync, key spelling, meter captions, lessons, presets, corrupt-record recovery, migration and stale-tab protection.
- GitHub Pages CI runs the browser suite in Chromium, mobile Chromium and Linux WebKit before deployment. Check the Actions badge for the published commit's result.

## Visual checks

Actual desktop and mobile renders were inspected. Updated screenshots in `docs/media/web-v1-*` show demonstration content, not the owner's learning results. The 6/8 worked example groups three eighth notes into one dotted-quarter beat and labels both beat positions.

## Limits

Automated playback checks establish audio startup, scheduling and finite PCM output. They do not certify physical speakers or subjective timbre. Mobile viewports are not physical-device tests. Chromium offline reload is tested; Playwright's WebKit offline emulator fails navigation internally, so Safari offline behavior remains unverified.

Sync merge/conflict/reset logic and UI credentials are tested with controlled API responses. This release does not create new credentials or reset the owner's cloud progress. The existing private-repository setup is retained.

Review intervals are transparent heuristics. Tests establish their implementation, not educational efficacy. The generator covers bounded diatonic single-line exercises; advanced harmony and polyphony remain outside this release.
