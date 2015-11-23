from collections import namedtuple
from xml.etree.ElementTree import XML 


class Pred(object):
    """
    A superclass for all Pred classes
    """
    @property
    def string(self):
        raise NotImplementedError
    
    @staticmethod
    def from_string(string):
        """
        Instantiates a suitable type of Pred, from a string
        """
        assert string[-4:] == '_rel'
        if string[0] != '_':
            return GPred(string[:-4])
        else:
            parts = string[1:-4].split('_')
            return RealPred(*parts)


class RealPred(Pred, namedtuple('RealPred',('lemma','pos','sense'))):
    """
    Real predicate, with a lemma, part of speech, and (optional) sense
    """
    def __new__(cls, lemma, pos, sense=None):
        """
        Create a new instance, allowing the sense to be optional
        """
        return super(RealPred, cls).__new__(cls, lemma, pos, sense)
    
    @property
    def string(self):
        """
        Return a string, with leading underscore, and trailing '_rel'
        """
        if self.sense:
            return "_{}_{}_{}_rel".format(*self)
        else:
            return "_{}_{}_rel".format(*self)


class GPred(Pred, namedtuple('GPred',('name'))):
    """
    Grammar predicate, with a rel name
    """
    @property
    def string(self):
        """
        Return a string, with trailing '_rel'
        """
        return "{}_rel".format(*self)



class LinkLabel(namedtuple('LinkLabel',('rargname','post'))):
    """
    A label for a link
    """
    @property
    def string(self):
        return "{}/{}".format(*self)

class Link(namedtuple('Link',('start','end','rargname','post'))):
    """
    A link
    """
    @property
    def label(self):
        return LinkLabel(self.rargname, self.post)
    
    @property
    def labelstring(self):
        return "{}/{}".format(self.rargname, self.post)



class Node(object):
    """
    A superclass for all Node classes
    """
    @property
    def span(self):
        return (self.cfrom, self.cto)


class ListNode(Node):
    """
    A node implemented with a list for the sortinfo
    """
    def __init__(self, nodeid, pred, sortinfo=None, cfrom=None, cto=None, surface=None, base=None, carg=None):
        self.nodeid = nodeid
        self.pred = pred
        self.sortinfo = sortinfo
        self.cfrom = cfrom
        self.cto = cto
        self.surface = surface
        self.base = base
        self.carg = carg
    
    def dict_node(self, graph=None):
        """
        Convert to a DictNode
        """
        return DictNode(self.nodeid, self.pred, self.sortinfo, self.cfrom, self.cto, self.surface, self.base, self.carg, graph)


class DictNode(Node):
    """
    A node implemented with a dict for the sortinfo,
    and a pointer to the DMRS graph to access links
    """
    def __init__(self, nodeid, pred, sortinfo=None, cfrom=None, cto=None, surface=None, base=None, carg=None, graph=None):
        self.nodeid = nodeid
        self.pred = pred
        self.cfrom = cfrom
        self.cto = cto
        self.surface = surface
        self.base = base
        self.carg = carg
        self._graph = graph
        if sortinfo:
            if isinstance(sortinfo, list):
                self.sortinfo = {x:y for x,y in sortinfo}
            else:
                assert isinstance(sortinfo, dict)
                self.sortinfo = sortinfo
        else:
            self.sortinfo = {}
    
    def list_node(self):
        """
        Convert to a ListNode
        """
        return ListNode(self.nodeid, self.pred, self.sortinfo.items(), self.cfrom, self.cto, self.carg, self.cvtype)
    
    @property
    def incoming(self):
        """
        Incoming links, indexed by nodeids
        """
        # If there are no incoming links, return an empty dict
        return self._graph.incoming.get(self.nodeid, {})
    
    @property
    def outgoing(self):
        """
        Outgoing links, indexed by nodeids
        """
        # If there are no outgoing links, return an empty dict
        return self._graph.outgoing.get(self.nodeid, {})
    
    def in_label(self, label, post=None):
        """
        Find all incoming links with a given label
        """
        if post:
            label = LinkLabel(label, post)
        return search_keys(self.incoming, label)
    
    def out_label(self, label, post=None):
        """
        Find all outgoing links with a given label
        """
        if post:
            label = LinkLabel(label, post)
        return search_keys(self.outgoing, label)

def search_keys(dictionary, target):
    """
    For a dictionary of sets,
    search for keys whose values contain the target
    """
    output = set()
    for key, valueset in dictionary.items():
        if target in valueset:
            output.add(key)
    return output



class Dmrs(object):
    """
    A superclass for all DMRS classes
    """
    @classmethod
    def loads(cls, bytestring):
        """
        Currently processes "<dmrs>...</dmrs>"
        To be updated for "<dmrslist>...</dmrslist>"...
        """
        xml = XML(bytestring)
        
        dmrs_cfrom = int(xml.get('cfrom'))
        dmrs_cto = int(xml.get('cto'))
        dmrs_surface = xml.get('surface')
        ident = xml.get('ident')
        index = xml.get('index')
        if ident: ident = int(ident)
        if index: index = int(index)
        top = None
        
        nodes = []
        links = []
        
        for elem in xml:
            if elem.tag == 'node':
                nodeid = int(elem.get('nodeid'))
                cfrom = int(elem.get('cfrom'))
                cto = int(elem.get('cto'))
                surface = elem.get('surface')
                base = elem.get('base')
                carg = elem.get('carg')
                
                pred = None
                sortinfo = None
                for sub in elem:
                    if sub.tag == 'realpred':
                        pred = RealPred(sub.get('lemma'),sub.get('pos'),sub.get('sense'))
                    elif sub.tag == 'gpred':
                        pred = GPred(sub.text[:-4])
                    elif sub.tag == 'sortinfo':
                        sortinfo = sub.items()
                    else:
                        raise ValueError(sub.tag)
                
                nodes.append(cls.Node(nodeid, pred, sortinfo, cfrom, cto, surface, base, carg))
            
            elif elem.tag == 'link':
                start = int(elem.get('from'))
                end = int(elem.get('to'))
                
                if start == 0:
                    top = end
                
                else:
                    rargname = None
                    post = None
                    for sub in elem:
                        if sub.tag == 'rargname':
                            rargname = sub.text
                        elif sub.tag == 'post':
                            post = sub.text
                        else:
                            raise ValueError(sub.tag)
                    links.append(Link(start, end, rargname, post))
            else:
                raise ValueError(elem.tag)
        
        return cls(nodes, links, dmrs_cfrom, dmrs_cto, dmrs_surface, ident, index, top)
    
    @classmethod
    def load(cls, filehandle):
        """
        Load a DMRS from a file
        NB: read as a bytestring!
        """
        return cls.loads(filehandle.read())
    
    @classmethod
    def dumps(cls, dmrs):
        pass
        # Get the nodes and links, then write them out...
    
    @classmethod
    def dump(cls, filehandle, dmrs):
        filehandle.write(cls.dumps(dmrs))


class ListDmrs(Dmrs):
    """
    A DMRS graph implemented with lists for nodes and links
    """
    
    Node = ListNode  # Called in inherited class methods
    
    def __init__(self, nodes, links, cfrom=None, cto=None, surface=None, ident=None, index=None, top=None):
        self.nodes = nodes
        self.links = links
        self.cfrom = cfrom
        self.cto = cto
        self.surface = surface
        self.ident = ident
        self.index = index
        self.top = top
    
    def dict_dmrs(self):
        """
        Convert to a DictDmrs
        """
        return DictDmrs(self.nodes, self.links, self.cfrom, self.cto, self.surface, self.ident, self.index, self.top)


class DoubleDict(dict):
    """
    A dict of dicts, mapping to sets.
    Used to store links in the DictDmrs class below.
    """
    def add(self, key1, key2, value):
        """
        Add an entry, creating new dicts or sets as necessary,
        i.e. self[key1][key2].add(value) with defaults
        """
        self.setdefault(key1,{}).setdefault(key2,set()).add(value)
    
    def trim(self, key1, key2, value):
        """
        Remove an entry, cleaning up empty dicts or sets
        """
        if not value in self[key1][key2]:
            raise KeyError((key1, key2, value))
        n = len(self[key1][key2])
        if n > 1:
            self[key1][key2].remove(value)
        elif len(self[key1]) > 1:
            self[key1].pop(key2)
        else:
            self.pop(key1)
    
    def trim_all(self, key1, key2):
        """
        Remove a whole set, not just a single element
        """
        if not self[key1][key2]:
            raise KeyError((key1, key2))
        if len(self[key1]) > 1:
            self[key1].pop(key2)
        else:
            self.pop(key1)

class DictDmrs(Dmrs):
    """
    A DMRS graph implemented with dicts for nodes and links
    """
    
    Node = DictNode  # Called in inherited class methods
    
    def __init__(self, nodes, links, cfrom=None, cto=None, surface=None, ident=None, index=None, top=None):
        """
        Initialise dictionaries from lists
        """
        # Initialise simple attributes
        self.cfrom = cfrom
        self.cto = cto
        self.surface = surface
        self.ident = ident
        
        # Initialise nodes
        self._nodes = {}
        for n in nodes:
            # Allow the list of nodes to be DictNodes, ListNodes, or tuples
            if isinstance(n, DictNode):
                self._nodes[n.nodeid] = n
                n._graph = self
            elif isinstance(n, ListNode):
                self._nodes[n.nodeid] = n.dict_node(graph=self)
            else:
                self._nodes[n[0]] = DictNode(*n, graph=self)
                
        # Initialise links
        self.outgoing = DoubleDict()
        self.incoming = DoubleDict()
        for start, end, rargname, post in links:
            label = LinkLabel(rargname, post)
            self.add_link(start, end, label)
        
        # Allow index and top to be a nodeid, or a node, or None
        if index:
            if index in self:
                self.index = self[index]
            elif index.nodeid in self:
                self.index = index
            else:
                raise ValueError(index)
        else:
            self.top = None
        if top:
            if top in self:
                self.top = self[top]
            elif top.nodeid in self:
                self.top = top
            else:
                raise ValueError(top)
        else:
            self.top = None
    
    def __getitem__(self, nodeid):
        """
        Allow accessing nodes as self[nodeid]
        """
        return self._nodes[nodeid]
    
    def __iter__(self):
        """
        Allow iterating over nodes using 'in'
        """
        return self._nodes.__iter__()
    
    def iter_links(self):
        """
        Iterate through all links.
        """
        for start, outdict in self.outgoing.items():
            for end, labelset in outdict.items():
                for label in labelset:
                    yield Link(start, end, *label)
    
    @property
    def links(self):
        return list(self.iter_links())
    
    @property
    def nodes(self):
        return list(self._nodes.values())
    
    def add_link(self, start, end, label, post=None):
        """
        Safely add a link.
        If (start, end, label) is given, adds a link from start to end with that label
        If (start, end, rargname, post) is given, the label is (rargname, post)
        """
        if not (start in self and end in self):
            raise KeyError((start, end))
        if post:
            rargname = label
            label = LinkLabel(rargname, post)
        self.outgoing.add(start, end, label)
        self.incoming.add(end, start, label)
    
    def add_links(self, iterable):
        """
        Safely add a number of links
        """
        for link in iterable:
            self.add_link(*link)
    
    def remove_link(self, start, end, label=None, post=None):
        """
        Safely remove a link.
        If (start, end) is given, removes all links from start to end
        If (start, end, label) is given, removes the link from start to end with that label
        If (start, end, rargname, post) is given, removes the link with label (rargname, post)
        """
        if label:
            if post:
                rargname = label
                label = LinkLabel(rargname,post)
            self.outgoing.trim(start, end, label)
            self.incoming.trim(end, start, label)
        else:
            self.outgoing.trim_all(start, end)
            self.incoming.trim_all(end, start)
    
    def remove_links(self, iterable):
        """
        Safely remove a number of links.
        """
        for link in iterable:
            self.remove_link(*link)
    
    def list_dmrs(self):
        """
        Convert to a ListDmrs
        """
        list_nodes = [n.list_node() for n in self._nodes.values()]
        return ListDmrs(list_nodes, self.links, self.top.nodeid)