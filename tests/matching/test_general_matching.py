import unittest

from pydmrs._exceptions import PydmrsTypeError
from pydmrs.components import InstanceSortinfo, RealPred
from pydmrs.core import Link, DictDmrs, Node
from pydmrs.examples import examples_dmrs
from pydmrs.matching import general_matching


class TestMatch(unittest.TestCase):
    def setUp(self):
        self.match = general_matching.Match([(2, 3), (4, 2)], [(Link(4, 5, 'RSTR', 'H'),
                                                           Link(1, 2, 'RSTR', 'H'))])

    def test_Match_init(self):
        self.assertEqual(general_matching.Match().nodeid_pairs, [])
        self.assertEqual(general_matching.Match().link_pairs, [])
        self.assertCountEqual(self.match.nodeid_pairs, [(2, 3), (4, 2)])
        self.assertCountEqual(self.match.link_pairs, [(Link(4, 5, 'RSTR', 'H'),
                                                 Link(1, 2, 'RSTR', 'H'))])

    def test_Match_len(self):
        self.assertEqual(len(self.match), 3)
        self.assertEqual(len(general_matching.Match()), 0)

    def test_Match_add(self):
        self.assertIsNone(self.match.add(general_matching.Match()))
        self.assertCountEqual(self.match.nodeid_pairs, [(2, 3), (4, 2)])
        self.assertCountEqual(self.match.link_pairs, [(Link(4, 5, 'RSTR', 'H'),
                                                      Link(1, 2, 'RSTR', 'H'))])

        incompatible_match = general_matching.Match([(1, 2), (8, 1)], [(Link(1, 8, 'RSTR', 'H'),
                                                                        Link(1, 2, 'RSTR', 'H'))])
        self.match.add(incompatible_match)
        self.assertCountEqual(self.match.nodeid_pairs, [(2, 3), (4, 2), (8, 1)])
        self.assertCountEqual(self.match.link_pairs, [(Link(4, 5, 'RSTR', 'H'),
                                                      Link(1, 2, 'RSTR', 'H'))])

        compatible_match = general_matching.Match([(1, 5), (3, 4)], [(Link(1, 3, 'ARG1', 'NEQ'),
                                                                      Link(1, 5, 'ARG2', 'NEQ'))])
        self.match.add(compatible_match)
        self.assertCountEqual(self.match.nodeid_pairs, [(2, 3), (4, 2), (1, 5), (8, 1), (3, 4)])
        self.assertCountEqual(self.match.link_pairs, [(Link(4, 5, 'RSTR', 'H'),
                                                      Link(1, 2, 'RSTR', 'H')),
                                                     (Link(1, 3, 'ARG1', 'NEQ'),
                                                      Link(1, 5, 'ARG2', 'NEQ'))])


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
        self.assertCountEqual(matches[0].nodeid_pairs, [(2, 5), (1, 4)])
        self.assertCountEqual(matches[0].link_pairs,
                             [(Link(1, 2, 'RSTR', 'H'), Link(4, 5, 'RSTR', 'H'))])

        # Match "the cat chases the dog" onto "the dog chases the cat" (inexact fit)
        matches = general_matching.find_best_matches(self.small_dmrs, self.reverse_dmrs)
        self.assertEqual(len(matches), 1)
        self.assertCountEqual(matches[0].nodeid_pairs, [(5, 2), (4, 1), (3, 3), (2, 5), (1, 4)])
        self.assertCountEqual(matches[0].link_pairs,
                             [(Link(4, 5, 'RSTR', 'H'), Link(1, 2, 'RSTR', 'H')),
                              (Link(1, 2, 'RSTR', 'H'), Link(4, 5, 'RSTR', 'H'))])

        # No match found
        matches = general_matching.find_best_matches(examples_dmrs.the_mouse(), self.reverse_dmrs)
        self.assertIsNone(matches)

        # More than one match found.
        matches = general_matching.find_best_matches(self.cat_dmrs, self.large_dmrs)
        self.assertEqual(len(matches), 2)
        self.assertCountEqual(matches[0].nodeid_pairs, [(2, 5), (1, 4)])
        self.assertCountEqual(matches[0].link_pairs,
                             [(Link(1, 2, 'RSTR', 'H'), Link(4, 5, 'RSTR', 'H'))])
        self.assertCountEqual(matches[1].nodeid_pairs, [(2, 8), (1, 7)])
        self.assertCountEqual(matches[1].link_pairs,
                             [(Link(1, 2, 'RSTR', 'H'), Link(7, 8, 'RSTR', 'H'))])

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
        self.assertAlmostEqual(general_matching.get_recall(inexact_matches[0], self.small_dmrs),
                               7 / 9)
        self.assertAlmostEqual(general_matching.get_fscore(inexact_matches[0], self.small_dmrs),
                               0.875)

        # List of matches instead of Match.
        with self.assertRaises(PydmrsTypeError):
            general_matching.get_recall(exact_matches, self.cat_dmrs)
        with self.assertRaises(PydmrsTypeError):
            general_matching.get_fscore(exact_matches, self.cat_dmrs)

    def test_get_missing_elements(self):
        match = general_matching.find_best_matches(examples_dmrs.the_dog_chases_the_mouse(),
                                                   self.small_dmrs)[0]
        missing = general_matching.get_missing_elements(match,
                                                        examples_dmrs.the_dog_chases_the_mouse())
        self.assertCountEqual(missing, [4, 5, Link(3, 5, 'ARG2', 'NEQ'), Link(4, 5, 'RSTR', 'H')])
