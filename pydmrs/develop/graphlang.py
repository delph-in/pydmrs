from pydmrs.components import Pred, RealPred, GPred, Sortinfo, EventSortinfo, InstanceSortinfo
from pydmrs.core import Link, Node, ListDmrs
from pydmrs.mapping.mapping import AnchorNode, SubgraphNode


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
        start = True
        while r < len(line):
            l = r + 1  # position of link
            while line[l] == ' ':
                l += 1
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
                if ref.isdigit():
                    ref = int(ref)
                    assert ref in ref_ids, 'Invalid reference id.'
                    current_id = ref_ids[ref]
                else:
                    assert ref in ref_names, 'Invalid reference name.'
                    current_id = ref_names[ref]
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
                node, ref_id, ref_name = _parse_node(line[m:r], nodeid, queries)
                nodes.append(node)
                current_id = nodeid
                nodeid += 1
                if ref_id is not None:
                    ref_ids[ref_id] = current_id
                ref_names[ref_name] = current_id
            if not start:
                m = line.index(' ', l, m)
                link = _parse_link(line[l:m], last_id, current_id, queries)
                links.append(link)
            last_id = current_id
            start = False
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
    m = string.find('(')
    if m < 0:
        m = string.find(' ')
    if m < 0:
        l = string.find(':')
    else:
        l = string.find(':', 0, m)
    if l >= 0:
        ref_id = string[:l]
        l += 1
        while string[l] == ' ':
            l += 1
    else:
        ref_id = None
    if string[l:l+4] == 'node' and (len(string) - l == 4 or string[l+4] == '?'):
        value, query_key = _parse_value(pred[l+4:], None)
        assert value is None
        if query_key:
            assert query_key not in queries
            queries[query_key] = lambda matching, dmrs: dmrs[matching[nodeid]]
        pred = Pred()
        carg = '?'
        sortinfo = Sortinfo()
        ref_name = 'node'
    elif m < 0:
        pred, ref_name = _parse_pred(string[l:m], nodeid, queries)
        carg = None
        sortinfo = None
    else:
        pred, ref_name = _parse_pred(string[l:m], nodeid, queries)
        if string[m] == '(':
            r = string.index(')', m)
            if string[m+1] == '"' and string[r-1] == '"':
                carg = string[m+2:r-1]
            else:
                carg = string[m+1:r]
            assert '"' not in carg
            carg, query_key = _parse_value(carg, None)
            if query_key:
                assert query_key not in queries
                queries[query_key] = lambda matching, dmrs: dmrs[matching[nodeid]].carg
            m = r + 1
        else:
            carg = None
        if string[m] == ' ':
            while string[m] == ' ':
                m += 1
            sortinfo = _parse_sortinfo(string[l:], nodeid, queries)
        else:
            sortinfo = None


    if not ref_id:
        ref_id = None
        node = Node(nodeid, pred, sortinfo=sortinfo, carg=carg)
    elif ref_id[0] == '[' and ref_id[-1] == ']':
        ref_id = int(ref_id[1:-1])
        node = AnchorNode(ref_id, nodeid, pred, sortinfo=sortinfo, carg=carg)
    elif ref_id[0] == '{' and ref_id[-1] == '}':
        ref_id = int(ref_id[1:-1])
        node = SubgraphNode(ref_id, nodeid, pred, sortinfo=sortinfo, carg=carg)
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
    if (string[:4] == 'pred' and (len(string) == 4 or string[4] == '?')) or (string[:8] == 'predsort' and (len(string) == 8 or string[8] == '?')):
        i = 8 if string[:8] == 'predsort' else 4
        value, query_key = _parse_value(string[i:], None)
        assert value is None
        if query_key:
            assert query_key not in queries
            queries[query_key] = lambda matching, dmrs: dmrs[matching[nodeid]].pred
        return Pred(), string[:i]
    rel_suffix = ''
    if string[-4:] == '_rel':
        string = string[:-4]
        rel_suffix = '_rel'
    if string[0] != '_':
        name, query_key = _parse_value(string, '?')
        if query_key:
            assert query_key not in queries
            queries[query_key] = lambda matching, dmrs: dmrs[matching[nodeid]].pred.name
        return GPred(name), name + rel_suffix
    values = string[1:].rsplit('_', 2)
    count = len(values)
    assert count > 0, 'Invalid number of arguments for RealPred.'
    if count == 1:
        values.insert(0, '?')
        values.append('?')
    elif count == 2:
        values.append(None)
    lemma, query_key = _parse_value(values[0], '?')
    if query_key:
        assert query_key not in queries
        queries[query_key] = lambda matching, dmrs: dmrs[matching[nodeid]].pred.lemma
    pos, query_key = _parse_value(values[1], 'u')
    if query_key:
        assert query_key not in queries
        queries[query_key] = lambda matching, dmrs: dmrs[matching[nodeid]].pred.pos
    sense, query_key = _parse_value(values[2], None)
    if query_key:
        assert query_key not in queries
        queries[query_key] = lambda matching, dmrs: dmrs[matching[nodeid]].pred.sense
    if count == 1:
        ref_name = '_{}{}'.format(pos, rel_suffix)
    elif count == 2:
        ref_name = '_{}_{}{}'.format(lemma, pos, rel_suffix)
    else:
        ref_name = '_{}_{}_{}{}'.format(lemma, pos, sense, rel_suffix)
    return RealPred(lemma, pos, sense), ref_name


_parse_instance_shorthand = {
    'p': ('pers', {'_': None, '?': 'u', '1': '1', '2': '2', '3': '3', 'o': '1-or-3'}),
    'n': ('num', {'_': None, '?': 'u', 's': 'sg', 'p': 'pl'}),
    'g': ('gend', {'_': None, '?': 'u', 'f': 'f', 'm': 'm', 'n': 'n', 'o': 'm-or-f'}),
    'i': ('ind', {'_': None, '?': 'u', '+': '+', '-': '-'}),
    't': ('pt', {'_': None, '?': 'u', 's': 'std', 'z': 'zero', 'r': 'refl'})}

_parse_event_shorthand = {
    's': ('sf', {'_': None, '?': 'u', 'p': 'prop', 'q': 'ques', 'o': 'prop-or-ques', 'c': 'comm'}),
    't': ('tense', {'_': None, '?': 'u', 'u': 'untensed', 't': 'tensed', 'p': 'pres', 'a': 'past', 'f': 'fut'}),
    'm': ('mood', {'_': None, '?': 'u', 'i': 'indicative', 's': 'subjunctive'}),
    'p': ('perf', {'_': None, '?': 'u', '+': '+', '-': '-'}),
    'r': ('prog', {'_': None, '?': 'u', '+': '+', '-': '-', 'b': 'bool'})}


def _parse_sortinfo(string, nodeid, queries):
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
    if string[1] == '?':
        value, query_key = _parse_value(string[1:], None)
        assert value is None
        if query_key:
            assert query_key not in queries
            queries[query_key] = lambda matching, dmrs: dmrs[matching[nodeid]].sortinfo
        if string[0] == 'e':
            return EventSortinfo('u', 'u', 'u', 'u', 'u')
        elif string[0] == 'x':
            return InstanceSortinfo('u', 'u', 'u', 'u', 'u')
        else:
            return Sortinfo()
    assert string[0] in 'ex', 'Sortinfo type i cannot be specified.'
    assert string[1] == '[' and string[-1] == ']', 'Square brackets missing.'
    if '=' not in string:  # explicit key-value specification
        if string[0] == 'e':
            sortinfo = EventSortinfo()
            shorthand = _parse_event_shorthand
        else:
            sortinfo = InstanceSortinfo()
            shorthand = _parse_instance_shorthand
        for kv in string[2:-1].split(','):
            key, value = kv.split('=')
            if key in shorthand:
                key, values = shorthand[key]
                sortinfo[key] = values[value]
            else:
                sortinfo[key], query_key = _parse_value(value, 'u')
                if query_key:
                    assert query_key not in queries
                    queries[query_key] = lambda matching, dmrs: dmrs[matching[nodeid]].sortinfo[key]
        return sortinfo
    else:  # implicit specification
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


def _parse_link(string, left_nodeid, right_nodeid, queries):
    assert string.islower(), 'Links must be lower-case.'
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
                if l == m:
                    rargname = rargname_query_key = None
                else:
                    rargname, rargname_query_key = _parse_value(string[l:m], '?')
                if m + 1 == r:
                    post, post_query_key = None
                else:
                    post, post_query_key = _parse_value(string[m+1:r], '?')
            else:
                rargname, rargname_query_key = _parse_value(string[l:r], '?')
                post = post_query_key = None
            if rargname_query_key:
                assert rargname_query_key not in queries
                queries[rargname_query_key] = lambda matching, dmrs: ','.join(link.rargname for link in dmrs.get_out(matching[start], post=(None if post_query_key else post), itr=True) if link.end == matching[end])
            if post_query_key:
                assert post_query_key not in queries
                queries[post_query_key] = lambda matching, dmrs: ','.join(link.post for link in dmrs.get_out(matching[start], rargname=(None if rargname_query_key else rargname), itr=True) if link.end == matching[end])
        return Link(start, end, rargname, post)
    if l > r:  # no specification symbol
        if link_char == '=':
            rargname = None
            post = 'eq'
        else:
            rargname = 'rstr'
            post = 'h'
    else:
        if string[l] == '?':
            rargname = '?'
            post = '?'
            value, query_key = _parse_value(string[l:r+1], None)
            assert value is None
            if query_key:
                assert query_key not in queries
                queries[query_key] = lambda matching, dmrs: ','.join(link.labelstring for link in dmrs.get_out(matching[start], itr=True) if link.end == matching[end])
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
