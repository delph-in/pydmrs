from delphin.interfaces import ace
from delphin.mrs import simplemrs, dmrx

from pydmrs.core import ListDmrs
from pydmrs.utils import load_config, get_config_option

DEFAULT_CONFIG_FILE = 'default_interface.conf'

config = load_config(DEFAULT_CONFIG_FILE)
DEFAULT_ERG_FILE = get_config_option(config, 'Grammar', 'ERG')


def parse(sentence, cls=ListDmrs, erg_file=DEFAULT_ERG_FILE):
    results = []
    for result in ace.parse(erg_file, sentence)['RESULTS']:  # cmdargs=['-r', 'root_informal']
        mrs = result['MRS']
        xmrs = simplemrs.loads_one(mrs)
        dmrs_xml = dmrx.dumps_one(xmrs)[11:-12]
        dmrs = cls.loads_xml(dmrs_xml)
        results.append(dmrs)
    return results


def generate(dmrs, erg_file=DEFAULT_ERG_FILE):
    dmrs_xml = '<dmrs-list>' + dmrs.dumps_xml(encoding='utf-8') + '</dmrs-list>'
    xmrs = dmrx.loads_one(dmrs_xml)
    mrs = simplemrs.dumps_one(xmrs)
    results = []
    for result in ace.generate(erg_file, mrs)['RESULTS']:
        sentence = result['SENT']
        results.append(sentence)
    return results
