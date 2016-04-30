import unittest

from pydmrs.core import (
    Link, LinkLabel,
    Node, PointerNode,
    Dmrs, ListDmrs,
    SetDict, DictDmrs,
    PointerMixin, ListPointDmrs, DictPointDmrs,
    SortDictDmrs,
    filter_links
)


class TestLink(unittest.TestCase):
    """
    Test methods of Link and LinkLabel classes
    """
    
    def test_Link_new(self):
        """
        Links should have exactly four slots (start, end, rargname, post).
        The constructor should take either positional or keyword arguments.
        The slots should be accessible by attribute names.
        """
        # Check four arguments
        self.assert_ex_link(Link(0, 1, 'RSTR', 'H'))
        self.assert_ex_link(Link(start=0, end=1, rargname='RSTR', post='H'))
        
        # Check wrong numbers of arguments
        with self.assertRaises(TypeError):
            Link(0, 1, 2)
        with self.assertRaises(TypeError):
            Link(0, 1, 2, 3, 4)
    
    # Helper function for test_Link_new
    def assert_ex_link(self, link):
        self.assertEqual(link.start, 0)
        self.assertEqual(link.end, 1)
        self.assertEqual(link.rargname, 'RSTR')
        self.assertEqual(link.post, 'H')
    
    def test_Link_str(self):
        """
        The 'informal' string representation of a Link
        should show a labelled arrow pointing from the start to the end
        """
        link = Link(0, 1, 'RSTR', 'H')
        self.assertEqual(str(link), "(0 - RSTR/H -> 1)")
    
    def test_Link_repr(self):
        """
        The 'official' string representation of a Link
        should evaluate to an equivalent Link
        """
        link = Link(0, 1, 'RSTR', 'H')
        self.assertEqual(link, eval(repr(link)))
    
    def test_Link_label(self):
        """
        The label of a link should be a LinkLabel
        """
        link = Link(0, 1, 'RSTR', 'H')
        label = LinkLabel('RSTR', 'H')
        self.assertIsInstance(link.label, LinkLabel)
        self.assertEqual(link.label, label)
    
    def test_Link_labelstring(self):
        """
        The labelstring of a link should be its label's string 
        """
        link = Link(0, 1, 'RSTR', 'H')
        labelstring = 'RSTR/H'
        self.assertEqual(link.labelstring, labelstring)
    
    def test_Link_copy(self):
        """
        copy.copy should return an equal Link
        copy.deepcopy should also return an equal Link
        """
        from copy import copy, deepcopy
        link = Link(0, 1, 'RSTR', 'H')
        link_copy = copy(link)
        link_deep = deepcopy(link)
        self.assertEqual(link, link_copy)
        self.assertEqual(link, link_deep)
        self.assertIsNot(link, link_copy)
        self.assertIsNot(link, link_deep)
        # Note that it doesn't make sense to check
        # if link.end is not link_deep.end,
        # because identical strings and ints are considered to be the same
    
    def test_LinkLabel_new(self):
        """
        LinkLabels should have exactly two slots (rargname, post).
        The constructor should take either positional or keyword arguments.
        The slots should be accessible by attribute names.
        """
        # Check two arguments
        self.assert_rstr_h(LinkLabel('RSTR', 'H'))
        self.assert_rstr_h(LinkLabel(rargname='RSTR', post='H'))
        
        # Check wrong numbers of arguments
        with self.assertRaises(TypeError):
            Link(0, 1, 2)
        with self.assertRaises(TypeError):
            Link(0, 1, 2, 3, 4)
    
    # Helper function for test_LinkLabel_new
    def assert_rstr_h(self, linklabel):
        self.assertEqual(linklabel.rargname, 'RSTR')
        self.assertEqual(linklabel.post, 'H')
    
    def test_LinkLabel_str(self):
        """
        The 'informal' string representation of a LinkLabel
        should have a slash between the rargname and post
        """
        label = LinkLabel('RSTR', 'H')
        self.assertEqual(str(label), "RSTR/H")
    
    def test_LinkLabel_repr(self):
        """
        The 'official' string representation of a LinkLabel
        should evaluate to an equivalent LinkLabel
        """
        label = LinkLabel('RSTR', 'H')
        self.assertEqual(label, eval(repr(label)))
    
    def test_LinkLabel_copy(self):
        """
        copy.copy should return an equal LinkLabel
        copy.deepcopy should also return an equal LinkLabel
        """
        from copy import copy, deepcopy
        label = LinkLabel('RSTR', 'H')
        label_copy = copy(label)
        label_deep = deepcopy(label)
        self.assertEqual(label, label_copy)
        self.assertEqual(label, label_deep)
        self.assertIsNot(label, label_copy)
        self.assertIsNot(label, label_deep)
        # Note that it doesn't make sense to check
        # if label.post is not label_deep.post,
        # because identical strings are considered to be the same


class TestNode(unittest.TestCase):
    """
    Test methods for Node class.
    """
    def test_Node_eq(self):
        # Unspecified nodes are always equal.
        node1 = Node()
        node2 = Node()
        self.assertEqual(node1, node2)

        sortinfo1 = {'cvarsort': 'e', 'tense': 'past'}
        sortinfo2 = {'cvarsort': 'e', 'tense': 'pres'}

        # Two nodes are equal if they have the same pred, sortinfo and carg, even if all the other elements are different
        node1 = Node(nodeid = 23, pred='the_q', sortinfo=sortinfo1, cfrom=2, cto=22, carg='Kim', surface='cat', base='x')
        node2 = Node(nodeid=25, pred='the_q', sortinfo=sortinfo1, cfrom=15, carg='Kim', surface='mad', base='w')
        self.assertEqual(node1, node2)

        # Different carg
        node2 = Node(pred='the_q', sortinfo=sortinfo1, carg='Jane')
        self.assertNotEqual(node1, node2)

        # Different pred
        node2 = Node(pred='_smile_v', sortinfo=sortinfo1, carg='Kim')
        self.assertNotEqual(node1, node2)

        # Different sortinfo.
        node2 = Node(pred='_smile_v', sortinfo=sortinfo2, carg='Kim')
        self.assertNotEqual(node1, node2)
