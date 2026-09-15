# Third-party notices

Theory Dictation Master is distributed under GPL-3.0-only. See LICENSE.

## Reference application

The interface palette and teach-then-drill structure were informed by Music Theory Master, copyright (c) 2026 Eipckz, MIT licensed. The reference revision was b880c55086f8822cb0ea70897e750b38180c1800. Its Python modules were inspected but were not copied into this application's runtime. Its MIT notice is retained in licenses/MusicTheoryMaster-MIT.txt.

## Runtime dependencies

- PyQt6 6.10.2: GPL v3, Riverbank Computing. License in licenses/PyQt6-GPL.txt. Source: https://www.riverbankcomputing.com/software/pyqt/download
- Qt 6.10.2: LGPL v3 and applicable module licenses, The Qt Company and contributors. License in licenses/Qt-LGPL.txt. Corresponding Qt source: https://download.qt.io/archive/qt/6.10/6.10.2/single/
- PyQt6-sip 13.12.0: licenses/PyQt6-sip.txt.
- NumPy 2.3.5 and bundled numerical libraries: licenses/NumPy.txt contains their notices. Source: https://github.com/numpy/numpy/releases/tag/v2.3.5
- sounddevice 0.5.5: MIT, Matthias Geier. Includes PortAudio binaries. Notices: licenses/sounddevice.txt and licenses/PortAudio.txt. Source: https://github.com/spatialaudio/python-sounddevice/tree/0.5.5
- CFFI 2.1.1: MIT. licenses/CFFI.txt. Source: https://foss.heptapod.net/pypy/cffi
- Python: PSF license; licenses/Python.txt. Source: https://www.python.org/downloads/source/

The Windows executable is produced with PyInstaller, which permits distribution of bundled applications under their chosen license through its bootloader exception. The full application source and build instructions accompany each release. No SoundFont, sampled piano, remote font, or stock media is bundled. The synthesis code produces a simple local harmonic tone.

GIF/video documentation depicts generated demonstration exercises and scripted UI actions. It does not report the user's personal learning results.
