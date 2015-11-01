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
        Allow the sense to be optional
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
    def __init__(self, nodeid, pred, sortinfo, cfrom, cto, carg):
        self.id = nodeid
        self.pred = pred
        self.sortinfo = sortinfo
        self.cfrom = cfrom
        self.cto = cto
        self.span = (cfrom, cto)
        self.carg = carg


class ListNode(Node):
    """
    A node implemented with a list for the sortinfo
    """
    pass

class DictNode(Node):
    """
    A node implemented with a dict for the sortinfo
    """
    pass



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
        return DictDmrs(self.nodes, self.links)


class DoubleDict(dict):
    """
    A dict of dicts, mapping to sets.
    Used to store links in the DictDmrs class below.
    """
    def trim(self, key1, key2, value):
        """
        Remove an entry, avoiding empty dicts or sets
        """
        assert value in self[key1][key2]
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
        assert self[key1][key2]
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
        self.top = top
        self._nodes = {n.id:n for n in nodes}
        self.outgoing = DoubleDict()
        self.incoming = DoubleDict()
        for start, end, rargname, post in links:
            assert start in self
            assert end in self
            label = LinkLabel(rargname, post)
            self.outgoing.setdefault(start,{}).setdefault(end,set()).add(label)
            self.incoming.setdefault(end,{}).setdefault(start,set()).add(label)
    
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
    
    def remove_link(self, start, end, label=None, post=None):
        """
        Safely remove a link.
        If (start, end) are given, removes all links from start to end
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
        return ListDmrs(self.nodes, self.links)