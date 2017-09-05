from __future__ import unicode_literals
from pydmrs.components import Pred, RealPred, GPred, Sortinfo, EventSortinfo, InstanceSortinfo
from pydmrs.core import Link, Node, ListDmrs
from pydmrs.mapping.mapping import AnchorNode, OptionalNode, SubgraphNode


default_sortinfo_classes = dict(
    e=EventSortinfo,
    x=InstanceSortinfo
)

default_sortinfo_shortforms = dict(
    e=dict(
        sf={'p': 'prop', 'q': 'ques', 'o': 'prop-or-ques', 'c': 'comm'},
        tense={'u': 'untensed', 't': 'tensed', 'p': 'pres', 'a': 'past', 'f': 'fut'},
        mood={'i': 'indicative', 's': 'subjunctive'},
        perf={'+': '+', '-': '-'},
        prog={'+': '+', '-': '-', 'b': 'bool'}
    ),
    x=dict(
        pers={'1': '1', '2': '2', '3': '3', 'o': '1-or-3'},
        num={'s': 'sg', 'p': 'pl'},
        gend={'f': 'f', 'm': 'm', 'n': 'n', 'o': 'm-or-f'},
        ind={'+': '+', '-': '-'},
        pt={'s': 'std', 'z': 'zero', 'r': 'refl'}
    )
)


def parse_graphlang(
    string,
    cls=ListDmrs,
    queries=None,
    equalities=None,
    anchors=None,
    sortinfo_classes=None,
    sortinfo_shortforms=None
):
    if queries is None:
        queries = {}
    if equalities is None:
        equalities = {}
    if anchors is None:
        anchors = {}
    if sortinfo_classes is None:
        sortinfo_classes = default_sortinfo_classes
        assert sortinfo_shortforms is None
        sortinfo_shortforms = default_sortinfo_shortforms
    else:
        if sortinfo_shortforms is None:
            sortinfo_shortforms = dict()
        else:
            assert all(cvarsort in sortinfo_classes for cvarsort in sortinfo_shortforms)
        assert 'i' not in sortinfo_classes
        sortinfo_classes['i'] = Sortinfo
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
                node, ref_ids, ref_name = _parse_node(line[m:r], nodeid, queries, equalities, anchors, sortinfo_classes, sortinfo_shortforms)
                nodes.append(node)
                current_id = nodeid
                nodeid += 1
                if ref_ids is not None:
                    for ref_id in ref_ids:
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


def _parse_node(string, nodeid, queries, equalities, anchors, sortinfo_classes, sortinfo_shortforms):
    m = string.find('(')
    if m < 0:
        m = string.find(' ')
    if m < 0:
        l = string.find(':')
    else:
        l = string.find(':', 0, m)
    if l < 0:
        ref_ids = None
        l = 0
    else:
        ref_ids = string[:l]
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
            sortinfo = _parse_sortinfo(string[m:], nodeid, queries, equalities, sortinfo_classes, sortinfo_shortforms)
        else:
            sortinfo = None
    if not ref_ids:
        ref_ids = None
        node = Node(nodeid, pred, sortinfo=sortinfo, carg=carg)
    else:
        if ref_ids[0] == '[' and ref_ids[-1] == ']':
            ref_ids = ref_ids[1:-1].split(',')
            node = AnchorNode(ref_ids, nodeid, pred, sortinfo=sortinfo, carg=carg)
        elif ref_ids[0] == '(' and ref_ids[-1] == ')':
            ref_ids = ref_ids[1:-1].split(',')
            node = OptionalNode(ref_ids, nodeid, pred, sortinfo=sortinfo, carg=carg)
        elif ref_ids[0] == '{' and ref_ids[-1] == '}':
            ref_ids = ref_ids[1:-1].split(',')
            node = SubgraphNode(ref_ids, nodeid, pred, sortinfo=sortinfo, carg=carg)
        else:
            ref_ids = ref_ids.split(',')
            node = Node(nodeid, pred, sortinfo=sortinfo, carg=carg)
        for ref_id in ref_ids:
            assert ref_id not in anchors, 'Reference ids have to be unique.'
            anchors[ref_id] = node
    return node, ref_ids, ref_name


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


def _parse_sortinfo(string, nodeid, queries, equalities, sortinfo_classes, sortinfo_shortforms):
    assert string.islower(), 'Sortinfos must be lower-case.'
    assert ' ' not in string, 'Sortinfos must not contain spaces.'
    if string[0] == 'i':
        assert len(string) == 1, 'Sortinfo type i cannot be specified.'
        return Sortinfo()
    assert string[0] in sortinfo_classes
    sortinfo = sortinfo_classes[string[0]]()
    if len(string) == 1:
        return sortinfo
    shortform = sortinfo_shortforms.get(string[0], dict())
    index = 1
    if string[1] in special_values:
        index = string.find('[')
        if index > 0:
            value = _parse_value(string[1:index], None, queries, equalities, (lambda matching, dmrs: dmrs[matching[nodeid]].sortinfo))
            assert not value
        else:
            value = _parse_value(string[1:], None, queries, equalities, (lambda matching, dmrs: dmrs[matching[nodeid]].sortinfo))
            assert not value
        for feature in sortinfo_classes[string[0]].features:
            sortinfo[feature] = 'u'
        if index < 0:
            return sortinfo
    assert string[index] == '[' and string[-1] == ']', 'Square brackets missing.'
    if '=' in string:  # explicit key-value specification
        for kv in string[index + 1: -1].split(','):
            key, value = kv.split('=')
            if value == '_':
                value = None
            elif value == '?':
                value = 'u'
            elif key in shortform and value in shortform[key]:
                value = shortform[key][value]
            sortinfo[key] = value
        return sortinfo
    else:  # implicit specification
        assert index == 1  # general underspecification makes no sense
        assert len(string) == len(sortinfo.features) + 3
        for n, feature in enumerate(sortinfo.features, 2):
            value = string[n]
            if value == '_':
                value = None
            elif value == '?':
                value = 'u'
            elif feature in shortform and string[n] in shortform[feature]:
                value = shortform[feature][value]
            sortinfo[feature] = value
        return sortinfo


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
