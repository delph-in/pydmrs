from collections import namedtuple


class Pred(object):
    """
    A superclass to set the API for all Pred classes
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
    A superclass to set the API for all Node classes
    """
    def __init__(self, nodeid, pred, sortinfo, cfrom, cto, carg, cvtype):
        self.id = nodeid
        self.pred = pred
        self.sortinfo = sortinfo
        self.cfrom = cfrom
        self.cto = cto
        self.carg = carg
        self.cvtype = cvtype
    
    @property
    def span(self):
        if self.cfrom and self.cto:
            return (self.cfrom, self.cto)
        else:
            return None


class ListNode(Node):
    """
    A node implemented with a list for the sortinfo
    """
    def dict_node(self, graph=None):
        """
        Convert to a DictNode
        """
        return DictNode(self.id, self.pred, self.sortinfo, self.cfrom, self.cto, self.carg, self.cvtype, graph)


class DictNode(Node):
    """
    A node implemented with a dict for the sortinfo,
    and a pointer to the DMRS graph to access links
    """
    def __init__(self, nodeid, pred, sortinfo=None, cfrom=None, cto=None, carg=None, cvtype=None, graph=None):
        self.id = nodeid
        self.pred = pred
        self.cfrom = cfrom
        self.cto = cto
        self.carg = carg
        self.cvtype = cvtype
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
        return ListNode(self.id, self.pred, self.sortinfo.items(), self.cfrom, self.cto, self.carg, self.cvtype)
    
    @property
    def incoming(self):
        """
        Incoming links, indexed by nodeids
        """
        return self._graph.incoming[self.id]
    
    @property
    def outgoing(self):
        """
        Outgoing links, indexed by nodeids
        """
        return self._graph.outgoing[self.id]
    
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
    A superclass to set the API for all DMRS classes
    """
    @classmethod
    def loads(cls, string):
        pass
        # Read in the nodes and links, then create a new instance and return it?
    
    @classmethod
    def load(cls, filehandle):
        return cls.loads(filehandle.read())
    
    @classmethod
    def dumps(cls, dmrs):
        pass
        # Get the nodes and links, then write them out?
    
    @classmethod
    def dump(cls, filehandle, dmrs):
        filehandle.write(cls.dumps(dmrs))


class ListDmrs(Dmrs):
    """
    A DMRS graph implemented with lists for nodes and links
    """
    def __init__(self, nodes, links, top=None):
        self.nodes = nodes
        self.links = links
        self.top = top
    
    def dict_dmrs(self):
        """
        Convert to a DictDmrs
        """
        return DictDmrs(self.nodes, self.links, self.top)


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
    def __init__(self, nodes, links, top=None):
        """
        Initialise dictionaries from lists
        """
        # Initialise nodes
        self._nodes = {}
        for n in nodes:
            # Allow the list of nodes to be DictNodes, ListNodes, or tuples
            if isinstance(n, DictNode):
                self._nodes[n.id] = n
                n.graph = self
            elif isinstance(n, ListNode):
                self._nodes[n.id] = n.dict_node(graph=self)
            else:
                self._nodes[n[0]] = DictNode(*n, graph=self)
        # Initialise links
        self.outgoing = DoubleDict()
        self.incoming = DoubleDict()
        for start, end, rargname, post in links:
            label = LinkLabel(rargname, post)
            self.add_link(start, end, label)
        # Allow top to be a nodeid, or a node
        if top in self:
            self.top = self[top]
        else:
            assert top.id in self
    
    def __getitem__(self, nodeid):
        """
        Allow accessing nodes as self[nodeid]
        """
        return self._nodes[nodeid]
    
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
        return ListDmrs(list_nodes, self.links, self.top.id)