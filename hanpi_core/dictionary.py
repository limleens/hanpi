"""Load the bundled CC-CEDICT as UTF-8, independent of the OS code page."""
from dataclasses import dataclass
from functools import lru_cache
import gzip
import importlib.metadata
import logging
from pathlib import Path
import sys

LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class DictionaryStatus:
    ready: bool
    entries: int
    version: str
    interpreter: str
    error: str = ''

    @property
    def message(self):
        if self.ready:
            return f'CC-CEDICT {self.version}: {self.entries:,} entries loaded as UTF-8.'
        return (f'Full CC-CEDICT unavailable: {self.error}. Limited starter vocabulary is active. '
                f'Using {self.interpreter}. Run "{self.interpreter}" -m pip install -r requirements.txt, '
                'then restart Hanpi. Run scripts/check_environment.py for details.')


@lru_cache(maxsize=1)
def _load():
    version = 'not installed'
    try:
        import pycccedict.cccedict as module
        version = importlib.metadata.version('pycccedict')
        path = Path(module.__file__).parent / 'data' / 'cedict_1_0_ts_utf-8_mdbg.txt.gz'
        # pycccedict 1.2.0's constructor omits encoding, which fails on Windows
        # CP1252 (and ASCII locales). Reuse its pinned parser with explicit UTF-8.
        dictionary = module.CcCedict.__new__(module.CcCedict)
        with gzip.open(path, 'rt', encoding='utf-8-sig', errors='strict') as stream:
            dictionary._parse_file(stream)
        count = len(dictionary.get_entries())
        if count < 100000 or not dictionary.get_entry('咖啡'):
            raise ValueError('Bundled dictionary is incomplete or invalid')
        return dictionary, DictionaryStatus(True, count, version, sys.executable)
    except Exception as exc:
        LOG.exception('CC-CEDICT initialization failed in %s', sys.executable)
        return None, DictionaryStatus(False, 0, version, sys.executable, f'{type(exc).__name__}: {exc}')


def get_dictionary():
    return _load()[0]


def dictionary_status():
    return _load()[1]
