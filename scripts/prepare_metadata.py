"""Download public master mappings only; never fetches account information."""
import json, sys, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research/upstream/nikke-calc-master'))
from scraper import profile_fetch as source
result = {'id_map': source._fetch_id_map(), 'favorites': source._fetch_favorite_map(), 'names': {}}
try:
    request = urllib.request.Request('https://nikke-api-gunwoos-projects.vercel.app/api/nikkes?fields=resourceId,name&limit=500', headers={'User-Agent': 'NikkeTools/0.1'})
    names = json.load(urllib.request.urlopen(request, timeout=30))
    result['names'] = {str(c['resourceId']): c['name'].get('ja') for c in names['characters']}
except Exception as exc:
    print('Japanese names unavailable: ' + str(exc), file=sys.stderr)
print(json.dumps(result, ensure_ascii=True))
