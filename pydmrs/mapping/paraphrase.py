import sys
from pydmrs.mapping.mapping import dmrs_mapping


def read_paraphases_file(filename):
    """
    """
    paraphrases = []
    file = open(filename, 'r')
    lines = iter(file)
    for line in lines:
        try:
            # GRAPHLANG !!!!!!!!! equalities etc
            paraphrases.append((line, next(lines)))
        except StopIteration:
            assert False, 'Invalid paraphrases file format.'
        try:
            assert not next(lines)
        except StopIteration:
            break
    return paraphrases


def paraphrase(dmrs_iter, paraphrases):
    """
    """
    for dmrs in dmrs_iter:
        assert isinstance(dmrs, Dmrs), 'Object in dmrs_iter is not a Dmrs.'
        for (search_dmrs, replace_dmrs) in paraphrases:
            dmrs_mapping(dmrs, search_dmrs, replace_dmrs, equalities=!!!, copy_dmrs=False)
        yield dmrs


if __name__ == '__main__':
    assert len(sys.argv) == 2 and not sys.stdin.isatty(), 'Invalid arguments'
    paraphrases = read_paraphrase_file(sys.argv[1])
    dmrs_iter = (ListDmrs.loads_xml(line[:-1]) for line in sys.stdin)
    sys.stdout.write(str(next(dmrs_query(dmrs_iter, search_dmrs, results_as_dict=True))) + '\n')
