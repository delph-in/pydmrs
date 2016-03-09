from pydmrs.components import Pred, RealPred, GPred, Sortinfo, EventSortinfo, InstanceSortinfo
from pydmrs.core import Link, Node, ListDmrs
from pydmrs.mapping.mapping import AnchorNode


def parse_graphlang(string, cls=ListDmrs, queries={}):
    nodeid = 1
    nodes = []
    links = []
    index = None
    top = None
    ref_ids = {}
    ref_names = {}
    lines = (item for line in string.split('\n') for item in line.split(';') if item)
    for line in lines:
        last_id = -1
        r = -1
        while r < len(line):
            l = r + 1  # position of link
            while line[l] == ' ':
                l += 1
            if r == -1:
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
                if ref.isdigit():
                    ref = int(ref)
                    assert ref in ref_ids, 'Invalid reference id.'
                    current_id = ref_ids[ref]
                else:
                    assert ref in ref_names, 'Invalid reference name.'
                    current_id = ref_names[ref]
            else:
                if line[m] == '*':
                    top = nodeid
                    node, ref_id, ref_name = _parse_node(line[m+1:r], nodeid, queries)
                else:
                    node, ref_id, ref_name = _parse_node(line[m:r], nodeid, queries)
                nodes.append(node)
                current_id = nodeid
                nodeid += 1
                if ref_id is not None:
                    ref_ids[ref_id] = current_id
                ref_names[ref_name] = current_id
            if m > l:
                m = line.index(' ', l, m)
                link = _parse_link(line[l:m], last_id, current_id)
                links.append(link)
            last_id = current_id
    return cls(nodes=nodes, links=links, index=index, top=top)


def _parse_value(string, underspec):
    if not string or string[0] != '?':
        return string, None
    if len(string) == 1:
        return underspec, None
    if string[1] == '?':
        return string[1:], None
    return underspec, string[1:]


def _parse_node(string, nodeid, queries):
    ref_id = None
    carg = None
    sortinfo = None
    m = string.find('(', 1)
    if m >= 0:
        r = string.index(')', m)
        carg, query_key = _parse_value(string[m+1:r], None)
        if query_key:
            assert query_key not in queries
            queries[query_key] = lambda matching: matching[nodeid].carg
        r += 1
    else:
        r = string.find(' ')
        if r < 0:
            r = len(string)
        m = r
    l = string.find(':', 0, m)
    if l >= 0:
        ref_id = string[:l]
    l += 1
    while string[l] == ' ':
        l += 1
    pred = string[l:m]
    if pred[:4] == 'node':
        value, query_key = _parse_value(pred[4:], None)
        if query_key:
            assert query_key not in queries
            queries[query_key] = lambda matching: matching[nodeid]
        assert not value
        pred = Pred()
        sortinfo = Sortinfo()
    else:
        pred = _parse_pred(pred, nodeid, queries)
    ref_name = str(pred)
    if r < len(string):
        l = r
        while string[l] == ' ':
            l += 1
        sortinfo = _parse_sortinfo(string[l:], nodeid, queries)
    if not ref_id:
        ref_id = None
        node = Node(nodeid, pred, sortinfo=sortinfo, carg=carg)
    elif ref_id[0] == '[' and ref_id[-1] == ']':
        ref_id = int(ref_id[1:-1])
        node = AnchorNode(ref_id, nodeid, pred, sortinfo=sortinfo, carg=carg)
    else:
        ref_id = int(ref_id)
        node = Node(nodeid, pred, sortinfo=sortinfo, carg=carg)
    return node, ref_id, ref_name


def _parse_pred(string, nodeid, queries):
    assert string.islower(), 'Predicates must be lower-case.'
    assert ' ' not in string, 'Predicates must not contain spaces.'
    if string[0] == '"' and string[-1] == '"':
        string = string[1:-1]
    assert '"' not in string, 'Predicates must not contain quotes.'
    assert string[0] != '\'', 'Predicates with opening single-quote have been deprecated.'
    if string[:3] == 'rel':
        value, query_key = _parse_value(string[3:], None)
        if query_key:
            assert query_key not in queries
            queries[query_key] = lambda matching: matching[nodeid].pred
        assert not value
        return Pred()
    assert string[-4:] == '_rel', 'Predicates must end with "_rel".'
    string = string[:-4]
    if string[0] != '_':
        name, query_key = _parse_value(string, '?')
        if query_key:
            assert query_key not in queries
            queries[query_key] = lambda matching: matching[nodeid].pred.name
        return GPred(string)
    values = string[1:].split('_')
    assert len(values) == 2 or len(values) == 3, 'Invalid number of arguments for RealPred.'
    if len(values) == 2:
        values.append(None)
    lemma, query_key = _parse_value(values[0], '?')
    if query_key:
        assert query_key not in queries
        queries[query_key] = lambda matching: matching[nodeid].pred.lemma
    pos, query_key = _parse_value(values[1], 'u')
    if query_key:
        assert query_key not in queries
        queries[query_key] = lambda matching: matching[nodeid].pred.pos
    sense, query_key = _parse_value(values[2], None)
    if query_key:
        assert query_key not in queries
        queries[query_key] = lambda matching: matching[nodeid].pred.sense
    return RealPred(lemma, pos, sense)


_parse_instance_shorthand = {
    'p': ('pers', {'_': None, '?': 'u', '1': '1', '2': '2', '3': '3', '4': '1-or-3'}),
    'n': ('num', {'_': None, '?': 'u', 's': 'sg', 'p': 'pl'}),
    'g': ('gend', {'_': None, '?': 'u', 'f': 'f', 'm': 'm', 'n': 'n', 'g': 'm-or-f'}),
    'i': ('ind', {'_': None, '?': 'u', '+': '+', '-': '-'}),
    't': ('pt', {'_': None, '?': 'u', 's': 'std', 'z': 'zero', 'r': 'refl'})}

_parse_event_shorthand = {
    's': ('sf', {'?': 'u', 'p': 'prop', 'q': 'ques', 'r': 'prop-or-ques', 'c': 'comm'}),
    't': ('tense', {'_': None, '?': 'u', 'u': 'untensed', 't': 'tensed', 'p': 'pres', 'a': 'past', 'f': 'fut'}),
    'm': ('mood', {'_': None, '?': 'u', 'i': 'indicative', 's': 'subjunctive'}),
    'p': ('perf', {'_': None, '?': 'u', '+': '+', '-': '-'}),
    'r': ('prog', {'_': None, '?': 'u', '+': '+', '-': '-', 'b': 'bool'})}


def _parse_sortinfo(string, nodeid, queries):
    assert string[0] in 'eix', 'Invalid sortinfo type.'
    if len(string) == 1:
        if string[0] == 'e':
            return EventSortinfo(None, None, None, None, None)
        elif string[0] == 'x':
            return InstanceSortinfo(None, None, None, None, None)
        else:
            return Sortinfo()
    if string[1] == '?':
        value, query_key = _parse_value(string[2:], None)
        if query_key:
            assert query_key not in queries
            queries[query_key] = lambda matching: matching[nodeid].sortinfo
        assert not value
        if string[0] == 'e':
            return EventSortinfo('u', 'u', 'u', 'u', 'u')
        elif string[0] == 'x':
            return InstanceSortinfo('u', 'u', 'u', 'u', 'u')
        else:
            return Sortinfo()
    assert string[0] in 'ex', 'Sortinfo type i cannot be specified.'
    assert string[1] == '[' and string[-1] == ']', 'Square brackets missing.'
    string = string.replace(':', '=').replace(';', ',').lower()
    if '=' not in string:
        assert len(string) == 8, 'Invalid number of short-hand sortinfo arguments.'
        if string[0] == 'e':
            sf = _parse_event_shorthand['s'][1][string[2]]
            tense = _parse_event_shorthand['t'][1][string[3]]
            mood = _parse_event_shorthand['m'][1][string[4]]
            perf = _parse_event_shorthand['p'][1][string[5]]
            prog = _parse_event_shorthand['r'][1][string[6]]
            return EventSortinfo(sf, tense, mood, perf, prog)
        else:
            pers = _parse_instance_shorthand['p'][1][string[2]]
            num = _parse_instance_shorthand['n'][1][string[3]]
            gend = _parse_instance_shorthand['g'][1][string[4]]
            ind = _parse_instance_shorthand['i'][1][string[5]]
            pt = _parse_instance_shorthand['t'][1][string[6]]
            return InstanceSortinfo(pers, num, gend, ind, pt)
    elif string.index('=') == 3:
        if string[0] == 'e':
            sortinfo = {'cvarsort': 'e'}
            shorthand = _parse_event_shorthand
        else:
            sortinfo = {'cvarsort': 'x'}
            shorthand = _parse_instance_shorthand
        for kv in string[2:-1].split(','):
            key, value = kv.split('=')
            key, values = shorthand[key]
            value, query_key = _parse_value(values[value], 'u')
            if query_key:
                assert query_key not in queries
                queries[query_key] = lambda matching: matching[nodeid].sortinfo[key]
            sortinfo[key] = value
    else:
        return Sortinfo.from_string(string)


def _parse_link(string, left_nodeid, right_nodeid):
    l = 0
    r = len(string) - 1
    if string[l] == '<':  # pointing left
        link_left = True
        l += 1
    elif string[r] == '>':  # pointing right
        link_left = False
        r -= 1
    else:  # invalid link
        assert False, 'Link must have a direction.'
    assert string[l] in '-=', 'Link line must consist of either "-" or "=".'
    link_char = string[l]
    while l < len(string) and string[l] == link_char:  # arbitrary left length
        l += 1
    while r >= 0 and string[r] == link_char:  # arbitrary right length
        r -= 1
    if l + 1 < r:  # explicit specification
        if string[l:r+1].lower() == 'rstr':  # rargname RSTR uniquely determines post H
            rargname = 'rstr'
            post = 'h'
        elif string[l:r+1].lower() == 'eq':  # post EQ uniquely determines rargname None
            rargname = None
            post = 'eq'
        else:
            assert '/' in string[l:r], 'Explicit link description must contain "/".'
            m = string.index('/', l, r)
            if l == m or string[l:m].lower() == 'none':  # None/EQ link
                rargname = None
            else:
                rargname = string[l:m]
            post = string[m+1:r+1]
        if link_left:
            return Link(right_nodeid, left_nodeid, rargname, post)
        else:
            return Link(left_nodeid, right_nodeid, rargname, post)
    if l > r:  # no specification symbol
        if link_char == '=':
            rargname = None
            post = 'eq'
        else:
            rargname = 'rstr'
            post = 'h'
    else:
        if l == r:  # one specification symbol, i.e. variable link
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
        if string[l] in '?n':  # ARG/ARGN/ARG? (underspecified ARG)
            rargname = 'arg'
        elif string[l] in '123':  # ARG{1,2,3}
            rargname = 'arg' + string[l]
        elif string[l] in 'lr':  # {L,R}-{INDEX,HNDL}
            if l == r:
                rargname = string[l].upper() + '-index'
            else:
                rargname = string[l].upper() + '-hndl'
        elif l <= r:
            assert False, 'Invalid link specification symbol.'
    if link_left:
        return Link(right_nodeid, left_nodeid, rargname, post)
    else:
        return Link(left_nodeid, right_nodeid, rargname, post)


if __name__ == '__main__':
    import sys
    dmrs_str = ' '.join(sys.argv[1:])
    dmrs = parse(dmrs_str)
    print(dmrs.dumps_xml())
