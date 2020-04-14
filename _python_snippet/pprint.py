import pprint
import json
from urllib.request import urlopen

with urlopen('https://pypi.org/pypi/sampleproject/json') as resp:
    project_info = json.load(resp)['info']
    pprint.pprint(project_info)

pprint.pprint(project_info, depth=1, width=60)