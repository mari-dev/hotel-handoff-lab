"""Package only reviewed application files and preinstalled Linux dependencies."""
from pathlib import Path
import hashlib
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1]
APP_FILES=('judge_lambda.py','authentication.py','bedrock_config.py','invoice_intake.py','server.py',
           'invoice_store.py','evidence_monitor.py','sample_documents.py','followup.py')

def main():
    folder=ROOT/'results/judge-package'
    if not (folder/'strands').is_dir():
        raise SystemExit('Install locked Linux Python 3.13 dependencies into results/judge-package first')
    for name in APP_FILES:
        shutil.copy2(ROOT/name,folder/name)
    shutil.copytree(ROOT/'web',folder/'web',dirs_exist_ok=True)
    output=ROOT/'results/judge-demo.zip'
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(folder.rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix!='.pyc':
                archive.write(path,path.relative_to(folder))
    digest=hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix('.sha256').write_text(digest+'  '+output.name+'\n')
    print(f'Prepared {output.name}: {output.stat().st_size} bytes; SHA256 {digest}')

if __name__=='__main__':
    main()
