from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
root=Path(__file__).resolve().parents[1]
output=root/'.local/release';output.mkdir(parents=True,exist_ok=True)
if not (root/'monitor/package/pypdf').exists():raise SystemExit('Install the pinned Python requirement into monitor/package first.')
with ZipFile(output/'monitor.zip','w',ZIP_DEFLATED) as z:
 for p in (root/'monitor/package').rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts:z.write(p,p.relative_to(root/'monitor/package'))
 for name in ['handler.py','scanner.py','state.py','source-registry.json']:z.write(root/'monitor'/name,name)
print('Prepared bounded-monitor release ZIP; no credentials included.')
