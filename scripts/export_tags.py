"""Export cover tags from simulation to tags.json."""
import json
import sys
sys.path.insert(0, 'scripts')
from cover_match_simulation import COVER_POOL

data = {}
for cat, entries in COVER_POOL.items():
    data[cat] = []
    for filename, tags in entries:
        entry = {'file': f'{filename}.svg'}
        for dim in ['cat', 'sub', 'fmt', 'vibe']:
            entry[dim] = sorted(tags[dim])
        data[cat].append(entry)

path = 'scustack-web/public/covers/tags.json'
with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

total = sum(len(v) for v in data.values())
print(f'{total} covers across {len(data)} categories written to {path}')
for cat, entries in data.items():
    sub = sum(1 for e in entries if e['sub'])
    gen = len(entries) - sub
    print(f'  {cat}: {len(entries)} ({sub} subject, {gen} generic)')
