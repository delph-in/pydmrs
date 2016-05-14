import unittest
import warnings

from pydmrs._exceptions import PydmrsTypeError, PydmrsValueError
from pydmrs.components import Pred, GPred, Sortinfo, EventSortinfo, InstanceSortinfo
from pydmrs.core import (
    Link, LinkLabel,
    Node, span_pred_key, abstractSortDictDmrs)
from pydmrs.examples import examples_dmrs


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

        # Check None values
        self.assertIsNone(Link(0, 1, '', 'H').rargname)
        self.assertIsNone(Link(0, 1, 'RSTR', 'NONE').post)
        self.assertIsNone(Link(0, 1, 'NULL', 'H').rargname)
        self.assertIsNone(Link(0, 1, 'RSTR', 'NIL').post)

        # Check wrong numbers of arguments
        with self.assertRaises(TypeError):
            Link(0, 1, 2)
        with self.assertRaises(TypeError):
            Link(0, 1, 2, 3, 4)

        # Check equal start and end
        with self.assertRaises(Warning):
            warnings.simplefilter('error')
            Link(0, 0, 1, 2)
        warnings.resetwarnings()

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
            LinkLabel(0, 1, 2)
        with self.assertRaises(TypeError):
            LinkLabel(0, 1, 2, 3, 4)

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

    def test_Node_init(self):
        node = Node(nodeid=13, pred='the_q', surface='cat', base='x', cfrom=23, cto=27,
                    carg='Kim', )
        self.assertEqual(node.nodeid, 13)
        self.assertEqual(node.surface, 'cat')
        self.assertEqual(node.base, 'x')

        self.assertEqual(node.cfrom, 23)
        self.assertEqual(node.cto, 27)
        # Incorrect span
        with self.assertRaises(PydmrsValueError):
            Node(cfrom=22, cto=7)

        self.assertEqual(node.carg, 'Kim')
        # Fix carg with  "".
        self.assertEqual(Node(carg='"Kim"').carg, 'Kim')
        # Unaccounted " in carg
        with self.assertRaises(PydmrsValueError):
            Node(carg='"Kim')

        # String pred.
        self.assertEqual(node.pred, GPred('the_q'))
        # Other pred
        self.assertEqual(Node(pred=GPred('the_q')).pred, GPred('the_q'))

        # Allow None for sortinfo.
        self.assertEqual(Node().sortinfo, None)
        # Dict sortinfo
        self.assertEqual(Node(sortinfo={'cvarsort': 'i', 'pers': '3'}).sortinfo,
                         InstanceSortinfo(pers='3'))
        # Sortinfo sortinfo
        self.assertEqual(Node(sortinfo=InstanceSortinfo(pers='3')).sortinfo,
                         InstanceSortinfo(pers='3'))
        # List sortinfo
        self.assertEqual(Node(sortinfo=[('cvarsort', 'i'), ('pers', '3')]).sortinfo,
                         InstanceSortinfo(pers='3'))
        # But nothing else.
        with self.assertRaises(PydmrsTypeError):
            Node(sortinfo="x[pers=3, num=sg, ind=+]")

    def test_Node_str(self):
        node = Node()
        self.assertEqual(str(node), "None")
        node = Node(nodeid=2, pred='_dog_n_1',
                    sortinfo=dict(cvarsort='i', pers='3', num='sg', ind='+'), carg='Pat')
        self.assertEqual(str(node), '_dog_n_1(Pat) x[pers=3, num=sg, ind=+]')

    def test_Node_eq(self):
        # Unspecified nodes are always equal.
        node1 = Node()
        node2 = Node()
        self.assertEqual(node1, node2)

        sortinfo1 = {'cvarsort': 'e', 'tense': 'past'}
        sortinfo2 = {'cvarsort': 'e', 'tense': 'pres'}

        # Two nodes are equal if they have the same pred, sortinfo and carg,
        # even if all the other elements are different
        node1 = Node(nodeid=23, pred='the_q', sortinfo=sortinfo1, cfrom=2, cto=22, carg='Kim',
                     surface='cat', base='x')
        node2 = Node(nodeid=25, pred='the_q', sortinfo=sortinfo1, cfrom=15, carg='Kim',
                     surface='mad', base='w')
        self.assertEqual(node1, node2)

        # Different carg
        node2 = Node(pred='the_q', sortinfo=sortinfo1, carg='Jane')
        self.assertNotEqual(node1, node2)

        # Different pred
        node2 = Node(pred='_smile_v', sortinfo=sortinfo1, carg='Kim')
        self.assertNotEqual(node1, node2)

        # Different sortinfo.
        node2 = Node(pred='_the_q', sortinfo=sortinfo2, carg='Kim')
        self.assertNotEqual(node1, node2)

    def test_Node_underspecification(self):
        with self.assertRaises(TypeError):
            Node(pred='_the_q').is_more_specific(4)
        # complete underspecification
        self.assertFalse(Node().is_more_specific(Node()))
        self.assertFalse(Node().is_less_specific(Node()))
        # pred underspecification
        self.assertFalse(Node(pred=Pred()).is_more_specific(Node()))
        self.assertTrue(Node(pred=Pred()).is_less_specific(Node()))
        self.assertTrue(Node().is_more_specific(Node(pred=Pred())))
        self.assertFalse(Node().is_less_specific(Node(pred=Pred())))
        self.assertFalse(Node(pred=Pred()).is_more_specific(Node(pred=Pred())))
        self.assertFalse(Node(pred=Pred()).is_less_specific(Node(pred=Pred())))
        self.assertFalse(Node(pred=Pred()).is_more_specific(Node(pred=GPred(name='abc'))))
        self.assertTrue(Node(pred=Pred()).is_less_specific(Node(pred=GPred(name='abc'))))
        self.assertTrue(Node(pred=GPred(name='abc')).is_more_specific(Node(pred=Pred())))
        self.assertFalse(Node(pred=GPred(name='abc')).is_less_specific(Node(pred=Pred())))
        # carg underspecification
        self.assertFalse(Node(carg='?').is_more_specific(Node()))
        self.assertTrue(Node(carg='?').is_less_specific(Node()))
        self.assertTrue(Node().is_more_specific(Node(carg='?')))
        self.assertFalse(Node().is_less_specific(Node(carg='?')))
        self.assertFalse(Node(carg='?').is_more_specific(Node(carg='?')))
        self.assertFalse(Node(carg='?').is_less_specific(Node(carg='?')))
        self.assertFalse(Node(carg='?').is_more_specific(Node(carg='abc')))
        self.assertTrue(Node(carg='?').is_less_specific(Node(carg='abc')))
        self.assertTrue(Node(carg='abc').is_more_specific(Node(carg='?')))
        self.assertFalse(Node(carg='abc').is_less_specific(Node(carg='?')))
        # sortinfo underspecification
        self.assertFalse(Node(sortinfo=Sortinfo()).is_more_specific(Node()))
        self.assertTrue(Node(sortinfo=Sortinfo()).is_less_specific(Node()))
        self.assertTrue(Node().is_more_specific(Node(sortinfo=Sortinfo())))
        self.assertFalse(Node().is_less_specific(Node(sortinfo=Sortinfo())))
        self.assertFalse(Node(sortinfo=Sortinfo()).is_more_specific(Node(sortinfo=Sortinfo())))
        self.assertFalse(Node(sortinfo=Sortinfo()).is_less_specific(Node(sortinfo=Sortinfo())))
        self.assertFalse(
            Node(sortinfo=Sortinfo()).is_more_specific(Node(sortinfo=EventSortinfo(sf='abc'))))
        self.assertTrue(
            Node(sortinfo=Sortinfo()).is_less_specific(Node(sortinfo=EventSortinfo(sf='abc'))))
        self.assertTrue(
            Node(sortinfo=EventSortinfo(sf='abc')).is_more_specific(Node(sortinfo=Sortinfo())))
        self.assertFalse(
            Node(sortinfo=EventSortinfo(sf='abc')).is_less_specific(Node(sortinfo=Sortinfo())))
        # mixed specification
        self.assertFalse(Node(pred=Pred()).is_more_specific(Node(carg='?')))
        self.assertFalse(Node(pred=Pred()).is_less_specific(Node(carg='?')))
        self.assertFalse(Node(pred=Pred()).is_more_specific(Node(sortinfo=Sortinfo())))
        self.assertFalse(Node(pred=Pred()).is_less_specific(Node(sortinfo=Sortinfo())))
        self.assertFalse(Node(carg='?').is_more_specific(Node(sortinfo=Sortinfo())))
        self.assertFalse(Node(carg='?').is_less_specific(Node(sortinfo=Sortinfo())))

    def test_Node_span(self):
        node = Node(cfrom=2, cto=15)
        self.assertEqual(node.span, (2, 15))

    def test_Node_isgpred_realpred_node(self):
        gnode = Node(pred='the_q')
        realnode = Node(pred='_cat_n')
        self.assertTrue(gnode.is_gpred_node)
        self.assertTrue(realnode.is_realpred_node)
        self.assertFalse(gnode.is_realpred_node)
        self.assertFalse(realnode.is_gpred_node)


class TestDmrs(unittest.TestCase):
    def setUp(self):
        self.test_dmrs = examples_dmrs.the_dog_chases_the_cat()

    def test_contains(self):
        self.assertTrue(4 in self.test_dmrs)
        self.assertFalse(16 in self.test_dmrs)

    def test_iter_outgoing(self):
        with self.assertRaises(PydmrsValueError):
            self.test_dmrs.iter_outgoing(15)

        self.test_dmrs.add_link(Link(3, 4, 'None', 'EQ'))
        out_it = self.test_dmrs.iter_outgoing(3)
        # Check that an iterator returned
        self.assertTrue(hasattr(out_it, '__next__'))
        # EQ link counted as outgoing
        self.assertCountEqual(list(out_it), [Link(3, 5, 'ARG2', 'NEQ'), Link(3, 2, 'ARG1', 'NEQ'),
                                             Link(3, 4, None, 'EQ')])
        # TODO: Treat EQ links symmetrically or not at all, as long as it's consistent.
        # Test e.g.
        # self.test_dmrs.add_link(Link(4, 3, 'None', 'EQ'))
        # out_it = self.test_dmrs.iter_outgoing(3)
        # self.assertIn(Link(4, 3, 'None', 'EQ'), list(out_it))

        # No outgoing links
        out_it = self.test_dmrs.iter_outgoing(2)
        with self.assertRaises(StopIteration):
            next(out_it)

    def test_iter_incoming(self):
        with self.assertRaises(PydmrsValueError):
            self.test_dmrs.iter_incoming(15)

        self.test_dmrs.add_link(Link(4, 2, 'None', 'EQ'))
        in_it = self.test_dmrs.iter_incoming(2)
        # Check that an iterator returned
        self.assertTrue(hasattr(in_it, '__next__'))
        # EQ link counted as incoming
        self.assertCountEqual(list(in_it), [Link(1, 2, 'RSTR', 'H'), Link(3, 2, 'ARG1', 'NEQ'),
                                            Link(4, 2, None, 'EQ')])

        # TODO: Treat EQ links somehow.
        # Test e.g.
        # self.test_dmrs.add_link(Link(2, 4, 'None', 'EQ'))
        # in_it = self.test_dmrs.iter_incoming(2)
        # self.assertIn(Link(2, 4, 'None', 'EQ'), list(in_it))

        # No incoming links
        in_it = self.test_dmrs.iter_incoming(3)
        with self.assertRaises(StopIteration):
            next(in_it)
