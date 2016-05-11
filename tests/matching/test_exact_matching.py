import unittest

from pydmrs._exceptions import PydmrsTypeError
from pydmrs.components import InstanceSortinfo, RealPred
from pydmrs.core import Link, DictDmrs, Node
from pydmrs.examples import examples_dmrs
from pydmrs.matching import general_matching


def the_mouse():
    dmrs = DictDmrs()
    dmrs.add_node(Node(nodeid=1, pred=RealPred('the', 'q')))
    dmrs.add_node(Node(nodeid=2, pred=RealPred('mouse', 'n', '1'),
                       sortinfo=InstanceSortinfo(pers='3', num='sg', ind='+')))
    dmrs.add_link(Link(start=1, end=2, rargname='RSTR', post='H'))
    return dmrs


class TestGeneralMatching(unittest.TestCase):
    def setUp(self):
        self.large_dmrs = examples_dmrs.the_dog_chases_the_cat_and_the_cat_chases_the_mouse()
        self.small_dmrs = examples_dmrs.the_dog_chases_the_cat()
        self.cat_dmrs = examples_dmrs.the_cat()
        self.reverse_dmrs = examples_dmrs.the_cat_chases_the_dog()

    def test_find_best_matches(self):
        # Match "the cat" onto "the dog chases the cat" (exact fit)
        matches = general_matching.find_best_matches(self.cat_dmrs, self.small_dmrs)

        self.assertEqual(len(matches), 1)
        self.assertListEqual(matches[0].nodeid_pairs, [(2, 5), (1, 4)])
        self.assertListEqual(matches[0].link_pairs, [(Link(1, 2, 'RSTR', 'H'), Link(4, 5, 'RSTR', 'H'))])

        # Match "the cat chases the dog" onto "the dog chases the cat" (inexact fit)
        matches = general_matching.find_best_matches(self.small_dmrs, self.reverse_dmrs)
        self.assertEqual(len(matches), 1)
        self.assertListEqual(matches[0].nodeid_pairs, [(5, 2), (4, 1), (3, 3), (2, 5), (1, 4)])
        self.assertListEqual(matches[0].link_pairs, [(Link(4, 5, 'RSTR', 'H'), Link(1, 2, 'RSTR', 'H')),
                                                     (Link(1, 2, 'RSTR', 'H'), Link(4, 5, 'RSTR', 'H'))])

        # No match found
        matches = general_matching.find_best_matches(the_mouse(), self.reverse_dmrs)
        self.assertIsNone(matches)

        # More than one match found.
        matches = general_matching.find_best_matches(self.cat_dmrs, self.large_dmrs)
        self.assertEqual(len(matches), 2)
        self.assertListEqual(matches[0].nodeid_pairs, [(2, 5), (1, 4)])
        self.assertListEqual(matches[0].link_pairs, [(Link(1, 2, 'RSTR', 'H'), Link(4, 5, 'RSTR', 'H'))])
        self.assertListEqual(matches[1].nodeid_pairs, [(2, 8), (1, 7)])
        self.assertListEqual(matches[1].link_pairs, [(Link(1, 2, 'RSTR', 'H'), Link(7, 8, 'RSTR', 'H'))])

    def test_get_matched_subgraph(self):
        match = general_matching.find_best_matches(self.cat_dmrs, self.small_dmrs)[0]
        subgraph = general_matching.get_matched_subgraph(self.small_dmrs, match)
        expected = DictDmrs(nodes=[Node(nodeid=4, pred=RealPred('the', 'q')),
                                   Node(nodeid=5, pred=RealPred('cat', 'n', '1'),
                                        sortinfo=InstanceSortinfo(pers='3', num='sg', ind='+'))],
                            links=[Link(start=4, end=5, rargname='RSTR', post='H')])
        self.assertListEqual(subgraph.nodes, expected.nodes)
        self.assertListEqual(subgraph.links, expected.links)

    def test_get_recall_fscore(self):
        exact_matches = general_matching.find_best_matches(self.cat_dmrs, self.small_dmrs)
        inexact_matches = general_matching.find_best_matches(self.small_dmrs, self.reverse_dmrs)
        # Exact
        self.assertEqual(general_matching.get_recall(exact_matches[0], self.cat_dmrs), 1)
        self.assertEqual(general_matching.get_fscore(exact_matches[0], self.cat_dmrs), 1)
        # Inexact
        self.assertAlmostEqual(general_matching.get_recall(inexact_matches[0], self.small_dmrs), 7 / 9)
        self.assertAlmostEqual(general_matching.get_fscore(inexact_matches[0], self.small_dmrs), 0.875)

        # List of matches instead of Match.
        with self.assertRaises(PydmrsTypeError):
            general_matching.get_recall(exact_matches, self.cat_dmrs)
        with self.assertRaises(PydmrsTypeError):
            general_matching.get_fscore(exact_matches, self.cat_dmrs)
