from pathlib import Path
import os
from PyInstaller.utils.hooks import collect_data_files

if os.name == 'nt':
    os.environ['PATH'] = str(Path(os.environ.get('SystemRoot','C:/Windows'))/'System32') + os.pathsep + os.environ.get('PATH','')
datas=[('LICENSE','.'),('THIRD-PARTY-NOTICES.md','.'),('licenses','licenses')]
a=Analysis(['run.py'],pathex=[],binaries=[],datas=datas,hiddenimports=['sounddevice','tdm.selftest'],
           excludes=['tkinter','matplotlib','scipy'],noarchive=False)
a.binaries=[item for item in a.binaries if 'asio' not in item[0].lower()]
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,a.binaries,a.datas,[],name='TheoryDictationMaster',debug=False,
        strip=False,upx=False,console=False,disable_windowed_traceback=False)
