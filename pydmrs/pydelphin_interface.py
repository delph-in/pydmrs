from pydmrs.core import ListDmrs
from delphin.interfaces import ace
from delphin.mrs import simplemrs, dmrx


erg_file = 'erg.dat'


def parse(sentence, cls=ListDmrs):
    results = []
    for result in ace.parse(erg_file, sentence)['RESULTS']:  # cmdargs=['-r', 'root_informal']
        mrs = result['MRS']
        xmrs = simplemrs.loads_one(mrs)
        dmrs_xml = dmrx.dumps_one(xmrs)[11:-12]
        dmrs = cls.loads_xml(dmrs_xml)
        results.append(dmrs)
    return results


def generate(dmrs):
    dmrs_xml = '<dmrs-list>' + dmrs.dumps_xml(encoding='utf-8') + '</dmrs-list>'
    xmrs = dmrx.loads_one(dmrs_xml)
    mrs = simplemrs.dumps_one(xmrs)
    results = []
    for result in ace.generate(erg_file, mrs)['RESULTS']:
        sentence = result['SENT']
        results.append(sentence)
    return results
