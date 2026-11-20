from pathlib import Path
import json
from engine import main
ROOT=Path(__file__).parent
main()
r=json.loads((ROOT/'results.json').read_text())
html=(ROOT/'report-template.html').read_text().replace('__RESULTS__',json.dumps(r).replace('</','<\\/'))
(ROOT/'index.html').write_text(html)
print('Built index.html from Python projection')
