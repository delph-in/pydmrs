from pydmrs.components import Pred, RealPred, GPred, Sortinfo, EventSortinfo, InstanceSortinfo
from pydmrs.core import Link, Node, ListDmrs
from pydmrs.mapping.mapping import AnchorNode, OptionalNode, SubgraphNode


def parse_graphlang(string, cls=ListDmrs, queries=None, equalities=None, anchors=None):
    if queries is None:
        queries = {}
    if equalities is None:
        equalities = {}
    if anchors is None:
        anchors = {}
    nodeid = 1
    nodes = []
    links = []
    index = None
    top = None
    refs = {}
    lines = (item for line in string.split('\n') for item in line.split(';') if item)
    for line in lines:
        last_id = -1
        r = 0
        start = True
        while r < len(line):
            l = r  # position of link
            while l < len(line) and line[l] == ' ':
                l += 1
            if l >= len(line):
                break
            if start:
                m = l
            else:
                m = line.index(' ', l) + 1  # position of node (+ sortinfo)
                while line[m] == ' ':
                    m += 1
            r1 = line.find('<', m)  # position of next link
            r2 = line.find('>', m)
            if r1 < m and r2 < m:
                r = len(line) - 1
            else:
                if r1 < m:
                    r = r2
                elif r1 < r2 or r2 < m:
                    r = r1
                else:
                    r = r2
                r = line.rindex(' ', 0, r)
            while line[r] == ' ':
                r -= 1
            r += 1
            if line[m] == ':':
                ref = line[m+1:r]
                assert ref in refs, 'Invalid reference id.'
                current_id = refs[ref]
            else:
                # TODO: index node?
                if line[m] == '*' and line[m+1] == '*':  # index node
                    assert index is None
                    index = nodeid
                    m += 2
                if line[m] == '*':  # top node
                    assert top is None
                    top = nodeid
                    m += 1
                node, ref_id, ref_name = _parse_node(line[m:r], nodeid, queries, equalities, anchors)
                nodes.append(node)
                current_id = nodeid
                nodeid += 1
                if ref_id is not None:
                    refs[ref_id] = current_id
                refs[ref_name] = current_id
            if not start:
                m = line.index(' ', l, m)
                link = _parse_link(line[l:m], last_id, current_id, queries, equalities)
                links.append(link)
            last_id = current_id
            start = False
    return cls(nodes=nodes, links=links, index=index, top=top)


special_values = ('?', '=')


def _parse_value(string, underspecified, queries, equalities, retriever):
    if not string or string[0] not in special_values:
        return string
    if string in special_values:
        return underspecified
    if string[1] == string[0]:
        return string[1:]
    if string[0] == '?':
        assert string[1:] not in queries
        queries[string[1:]] = retriever
    elif string[0] == '=':
        if string[1:] in equalities:
            equalities[string[1:]].append(retriever)
        else:
            equalities[string[1:]] = [retriever]
    return underspecified


def _parse_node(string, nodeid, queries, equalities, anchors):
    m = string.find('(')
    if m < 0:
        m = string.find(' ')
    if m < 0:
        l = string.find(':')
    else:
        l = string.find(':', 0, m)
    if l < 0:
        ref_id = None
        l = 0
    else:
        ref_id = string[:l]
        l += 1
        while string[l] == ' ':
            l += 1
    if string[l:l+4] == 'node' and (len(string) - l == 4 or string[l+4] in special_values):
        value = _parse_value(string[l+4:], None, queries, equalities, (lambda matching, dmrs: dmrs[matching[nodeid]]))
        assert not value
        pred = Pred()
        carg = '?'
        sortinfo = Sortinfo()
        ref_name = 'node'
    elif m < 0:
        pred, ref_name = _parse_pred(string[l:], nodeid, queries, equalities)
        carg = None
        sortinfo = None
    else:
        pred, ref_name = _parse_pred(string[l:m], nodeid, queries, equalities)
        if string[m] == '(':
            r = string.index(')', m)
            if string[m+1] == '"' and string[r-1] == '"':
                carg = string[m+2:r-1]
            else:
                carg = string[m+1:r]
            assert '"' not in carg
            carg = _parse_value(carg, None, queries, equalities, (lambda matching, dmrs: dmrs[matching[nodeid]].carg))
            m = r + 1
        else:
            carg = None
        if m < len(string) and string[m] == ' ':
            while string[m] == ' ':
                m += 1
            sortinfo = _parse_sortinfo(string[m:], nodeid, queries, equalities)
        else:
            sortinfo = None
    if not ref_id:
        ref_id = None
        node = Node(nodeid, pred, sortinfo=sortinfo, carg=carg)
    else:
        if ref_id[0] == '[' and ref_id[-1] == ']':
            ref_id = ref_id[1:-1]
            node = AnchorNode(ref_id, nodeid, pred, sortinfo=sortinfo, carg=carg)
        elif ref_id[0] == '(' and ref_id[-1] == ')':
            ref_id = ref_id[1:-1]
            node = OptionalNode(ref_id, nodeid, pred, sortinfo=sortinfo, carg=carg)
        elif ref_id[0] == '{' and ref_id[-1] == '}':
            ref_id = ref_id[1:-1]
            node = SubgraphNode(ref_id, nodeid, pred, sortinfo=sortinfo, carg=carg)
        else:
            assert False, 'Invalid anchor node type.'
        assert ref_id not in anchors, 'Reference ids have to be unique.'
        anchors[ref_id] = node
    return node, ref_id, ref_name


def _parse_pred(string, nodeid, queries, equalities):
    assert string.islower(), 'Predicates must be lower-case.'
    assert ' ' not in string, 'Predicates must not contain spaces.'
    if string[0] == '"' and string[-1] == '"':
        string = string[1:-1]
    assert '"' not in string, 'Predicates must not contain quotes.'
    assert string[0] != '\'', 'Predicates with opening single-quote have been deprecated.'
    if (string[:4] == 'pred' and (len(string) == 4 or string[4] in special_values)) or (string[:8] == 'predsort' and (len(string) == 8 or string[8] in special_values)):
        i = 8 if string[:8] == 'predsort' else 4
        value = _parse_value(string[i:], None, queries, equalities, (lambda matching, dmrs: dmrs[matching[nodeid]].pred))
        assert not value
        return Pred(), string[:i]
    rel_suffix = ''
    if string[-4:] == '_rel':
        string = string[:-4]
        rel_suffix = '_rel'
    if string[0] != '_':
        name = _parse_value(string, '?', queries, equalities, (lambda matching, dmrs: dmrs[matching[nodeid]].pred.name))
        return GPred(name), name + rel_suffix
    values = string[1:].rsplit('_', 2)
    count = len(values)
    assert count > 0, 'Invalid number of arguments for RealPred.'
    if count == 1:
        values.insert(0, '?')
        values.append('unknown')
    elif count == 2:
        values.append(None)
    lemma = _parse_value(values[0], '?', queries, equalities, (lambda matching, dmrs: dmrs[matching[nodeid]].pred.lemma))
    pos = _parse_value(values[1], 'u', queries, equalities, (lambda matching, dmrs: dmrs[matching[nodeid]].pred.pos))  # u ???
    sense = _parse_value(values[2], 'unknown', queries, equalities, (lambda matching, dmrs: dmrs[matching[nodeid]].pred.sense))  # unknown ???
    if count == 1:
        ref_name = '_{}{}'.format(pos, rel_suffix)
    elif count == 2:
        ref_name = '_{}_{}{}'.format(lemma, pos, rel_suffix)
    else:
        ref_name = '_{}_{}_{}{}'.format(lemma, pos, sense, rel_suffix)
    return RealPred(lemma, pos, sense), ref_name


_parse_instance_shortform = {
    'p': ('pers', {'_': None, '?': 'u', '1': '1', '2': '2', '3': '3', 'o': '1-or-3'}),
    'n': ('num', {'_': None, '?': 'u', 's': 'sg', 'p': 'pl'}),
    'g': ('gend', {'_': None, '?': 'u', 'f': 'f', 'm': 'm', 'n': 'n', 'o': 'm-or-f'}),
    'i': ('ind', {'_': None, '?': 'u', '+': '+', '-': '-'}),
    't': ('pt', {'_': None, '?': 'u', 's': 'std', 'z': 'zero', 'r': 'refl'})}

_parse_event_shortform = {
    's': ('sf', {'_': None, '?': 'u', 'p': 'prop', 'q': 'ques', 'o': 'prop-or-ques', 'c': 'comm'}),
    't': ('tense', {'_': None, '?': 'u', 'u': 'untensed', 't': 'tensed', 'p': 'pres', 'a': 'past', 'f': 'fut'}),
    'm': ('mood', {'_': None, '?': 'u', 'i': 'indicative', 's': 'subjunctive'}),
    'p': ('perf', {'_': None, '?': 'u', '+': '+', '-': '-'}),
    'r': ('prog', {'_': None, '?': 'u', '+': '+', '-': '-', 'b': 'bool'})}


def _parse_sortinfo(string, nodeid, queries, equalities):
    assert string.islower(), 'Sortinfos must be lower-case.'
    assert ' ' not in string, 'Sortinfos must not contain spaces.'
    assert string[0] in 'iex', 'Invalid sortinfo type.'
    if len(string) == 1:
        if string[0] == 'e':
            return EventSortinfo()
        elif string[0] == 'x':
            return InstanceSortinfo()
        else:
            return Sortinfo()
    if string[1] in special_values:
        value = _parse_value(string[1:], None, queries, equalities, (lambda matching, dmrs: dmrs[matching[nodeid]].sortinfo))
        assert not value
        if string[0] == 'e':
            return EventSortinfo('u', 'u', 'u', 'u', 'u')
        elif string[0] == 'x':
            return InstanceSortinfo('u', 'u', 'u', 'u', 'u')
        else:
            return Sortinfo()
    assert string[0] in 'ex', 'Sortinfo type i cannot be specified.'
    assert string[1] == '[' and string[-1] == ']', 'Square brackets missing.'
    if '=' in string:  # explicit key-value specification
        if string[0] == 'e':
            sortinfo = EventSortinfo()
            shortform = _parse_event_shortform
        else:
            sortinfo = InstanceSortinfo()
            shortform = _parse_instance_shortform
        for kv in string[2:-1].split(','):
            key, value = kv.split('=')
            if key in shortform:
                key, values = shortform[key]
                sortinfo[key] = values[value]
            else:
                sortinfo[key] = _parse_value(value, 'u', queries, equalities, (lambda matching, dmrs: dmrs[matching[nodeid]].sortinfo[key]))
        return sortinfo
    else:  # implicit specification
        assert len(string) == 8, 'Invalid number of short-hand sortinfo arguments.'
        if string[0] == 'e':
            sf = _parse_event_shortform['s'][1][string[2]]
            tense = _parse_event_shortform['t'][1][string[3]]
            mood = _parse_event_shortform['m'][1][string[4]]
            perf = _parse_event_shortform['p'][1][string[5]]
            prog = _parse_event_shortform['r'][1][string[6]]
            return EventSortinfo(sf, tense, mood, perf, prog)
        else:
            pers = _parse_instance_shortform['p'][1][string[2]]
            num = _parse_instance_shortform['n'][1][string[3]]
            gend = _parse_instance_shortform['g'][1][string[4]]
            ind = _parse_instance_shortform['i'][1][string[5]]
            pt = _parse_instance_shortform['t'][1][string[6]]
            return InstanceSortinfo(pers, num, gend, ind, pt)


def _parse_link(string, left_nodeid, right_nodeid, queries, equalities):
    assert ' ' not in string, 'Links must not contain spaces.'
    l = 0
    r = len(string) - 1
    if string[l] == '<':  # pointing left
        start = right_nodeid
        end = left_nodeid
        l += 1
    elif string[r] == '>':  # pointing right
        start = left_nodeid
        end = right_nodeid
        r -= 1
    else:  # invalid link
        assert False, 'Link must have a direction.'
    assert string[l] in '-=' and string[r] in '-=', 'Link line must consist of either "-" or "=".'
    link_char = string[l]
    while l < len(string) and string[l] == link_char:  # arbitrary left length
        l += 1
    while r >= 0 and string[r] == link_char:  # arbitrary right length
        r -= 1
    if l + 1 < r:  # explicit specification
        r += 1
        if string[l:r] == 'rstr':  # rargname RSTR uniquely determines post H
            rargname = 'rstr'
            post = 'h'
        elif string[l:r] == 'eq':  # post EQ uniquely determines rargname None
            rargname = None
            post = 'eq'
        else:
            m = string.find('/', l, r)
            if m >= 0:
                if l == m and m + 1 == r:
                    rargname = None
                    post = None
                elif l == m:
                    rargname = None
                    post = _parse_value(string[m+1:r], '?', queries, equalities, (lambda matching, dmrs: ','.join(link.post for link in dmrs.get_out(matching[start], itr=True) if link.end == matching[end])))
                elif m + 1 == r:
                    rargname = _parse_value(string[l:m], '?', queries, equalities, (lambda matching, dmrs: ','.join(link.rargname for link in dmrs.get_out(matching[start], itr=True) if link.end == matching[end])))
                    post = None
                else:
                    # problem: doesn't combine rargname and post
                    rargname = _parse_value(string[l:m], '?', queries, equalities, (lambda matching, dmrs: ','.join(link.rargname for link in dmrs.get_out(matching[start], itr=True) if link.end == matching[end])))
                    post = _parse_value(string[m+1:r], '?', queries, equalities, (lambda matching, dmrs: ','.join(link.post for link in dmrs.get_out(matching[start], itr=True) if link.end == matching[end])))
            else:
                rargname = _parse_value(string[l:r], '?', queries, equalities, (lambda matching, dmrs: ','.join(link.labelstring for link in dmrs.get_out(matching[start], itr=True) if link.end == matching[end])))
                post = None
        return Link(start, end, rargname, post)
    if l > r:  # no specification symbol
        if link_char == '=':
            rargname = None
            post = 'eq'
        else:
            rargname = 'rstr'
            post = 'h'
    else:
        if string[l] == '?':  # no equal constraint
            rargname = '?'
            post = '?'
            value = _parse_value(string[l:r+1], None, queries, equalities, (lambda matching, dmrs: ','.join(link.labelstring for link in dmrs.get_out(matching[start], itr=True) if link.end == matching[end])))
            assert not value
        elif l == r:  # one specification symbol, i.e. variable link
            if link_char == '=':
                post = 'eq'
            else:
                post = 'neq'
        elif l + 1 == r:  # two specification symbol, i.e. handle link
            assert string[r] == 'h', 'Second link specification symbol must be "h".'
            if link_char == '=':
                post = 'heq'
            else:
                post = 'h'
        else:
            assert False  # never reached
        if string[l] == 'n':  # ARG/ARGN (underspecified ARG)
            rargname = 'arg'
        elif string[l] in '1234':  # ARG{1,2,3,4}
            rargname = 'arg' + string[l]
        elif string[l] in 'lr':  # {L,R}-{INDEX,HNDL}
            if l == r:
                rargname = string[l].upper() + '-index'
            else:
                rargname = string[l].upper() + '-hndl'
        elif string[l] != '?':
            assert False, 'Invalid link specification symbol.'
    return Link(start, end, rargname, post)


if __name__ == '__main__':
    import sys
    assert len(sys.argv) <= 2 and sys.stdin.isatty() == (len(sys.argv) == 2), 'Invalid arguments.'
    if sys.stdin.isatty():
        sys.stdout.write(parse_graphlang(sys.argv[1]).dumps_xml(encoding='utf-8') + '\n')
    else:
        for line in sys.stdin:
            sys.stdout.write(parse_graphlang(line).dumps_xml(encoding='utf-8') + '\n')
