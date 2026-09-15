"""Launch with --data-dir PATH for explicit portable data operation."""
import argparse
import sys
import traceback
from pathlib import Path
from PyQt6.QtWidgets import QApplication,QMessageBox
from tdm.storage import Store,default_dir
from tdm.ui import Window

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--data-dir');parser.add_argument('--self-test',action='store_true');parser.add_argument('--capture');args=parser.parse_args()
    app=QApplication(sys.argv);app.setApplicationName('TheoryDictationMaster');app.setOrganizationName('TheoryDictationMaster')
    def report(exc_type,exc,tb):
        folder=Path(args.data_dir) if args.data_dir else default_dir();folder.mkdir(parents=True,exist_ok=True)
        (folder/'error.log').write_text(''.join(traceback.format_exception(exc_type,exc,tb)),encoding='utf-8')
        QMessageBox.warning(None,'Recoverable application error',f'{exc}\nDetails saved to {folder / "error.log"}.')
    sys.excepthook=report
    if args.self_test:
        from tdm.selftest import run
        try:
            run(args.data_dir,args.capture);return 0
        except Exception:
            import tempfile
            folder=Path(args.data_dir) if args.data_dir else Path(tempfile.mkdtemp(prefix='tdm-test-failed-'))
            folder.mkdir(parents=True,exist_ok=True)
            (folder/'self-test-failure.txt').write_text(traceback.format_exc(),encoding='utf-8')
            return 1
    try:window=Window(Store(args.data_dir))
    except Exception as exc:
        QMessageBox.critical(None,'Could not open progress',f'{exc}\nYour original file was not deleted. Choose a separate --data-dir or restore a known backup.');return 1
    window.show();return app.exec()

if __name__=='__main__':sys.exit(main())
