#VERSION: 3.5
# AUTHORS: Alexander Georgievskiy (galeksandrp@gmail.com)
# CONTRIBUTORS: 

import sys
from pathlib import Path
try:
    import jackett
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.absolute()))
    import jackett

class jackettnonameclub(jackett.jackett):
    name = 'JackettNoNaMe Club'
    jackettIndexerName = 'noname-club'


if __name__ == "__main__":
    jackett_se = jackettnonameclub()
    jackett_se.search("ubuntu server", 'software')
