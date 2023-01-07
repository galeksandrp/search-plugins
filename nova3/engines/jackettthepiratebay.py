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

class jackettthepiratebay(jackett.jackett):
    name = 'JackettThe Pirate Bay'
    jackettIndexerName = 'thepiratebay'


if __name__ == "__main__":
    jackett_se = jackettthepiratebay()
    jackett_se.search("ubuntu server", 'software')
