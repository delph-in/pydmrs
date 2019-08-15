
from delphin import ace
from delphin.mrs import from_dmrs
from delphin.dmrs import from_mrs
from delphin.codecs import simplemrs, dmrx

from pydmrs.core import ListDmrs
from pydmrs.utils import load_config, get_config_option

DEFAULT_CONFIG_FILE = 'default_interface.conf'

config = load_config(DEFAULT_CONFIG_FILE)
DEFAULT_ERG_FILE = get_config_option(config, 'Grammar', 'ERG')


def parse(sentence, cls=ListDmrs, erg_file=DEFAULT_ERG_FILE):
    results = []
    for result in ace.parse(erg_file, sentence).results():  # cmdargs=['-r', 'root_informal']
        mrs = result.mrs()
        _dmrs = from_mrs(mrs)
        dmrs_xml = dmrx.encode(_dmrs)
        dmrs = cls.loads_xml(dmrs_xml)
        results.append(dmrs)
    return results


def generate(dmrs, erg_file=DEFAULT_ERG_FILE):
    dmrs_xml = dmrs.dumps_xml(encoding='utf-8')
    _dmrs = dmrx.decode(dmrs_xml)
    _mrs = from_dmrs(_dmrs)
    mrs = simplemrs.encode(_mrs)
    results = []
    for result in ace.generate(erg_file, mrs).results():
        sentence = result['surface']
        results.append(sentence)
    return results
