import urllib.request
import json

resp = urllib.request.urlopen('http://localhost:8000/api/csvs')
data = json.loads(resp.read())
print('CSV files returned by server:')
for csv in data.get('csvs', []):
    print(f'  - {csv["id"]}')

if 'test_success_note.csv' in [c['id'] for c in data.get('csvs', [])]:
    print('\n✓ test_success_note.csv IS in the list')
else:
    print('\n✗ test_success_note.csv NOT in the list')
