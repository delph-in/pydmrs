import unittest
from pydmrs.components import Pred, RealPred, GPred


class TestPred(unittest.TestCase):
    """
    Test methods of Pred class and subclasses
    """

    def test_Pred_from_string(self):
        """
        Pred.from_string should instantiate RealPreds or GPreds
        depending on whether there is a leading underscore
        """
        # Check the preds are of the right type
        cat_pred = Pred.from_string('_cat_n_1_rel')
        the_pred = Pred.from_string('the_q_rel')
        self.assertIsInstance(cat_pred, RealPred)
        self.assertIsInstance(the_pred, GPred)

        # Check the preds are the equivalent to initialising directly 
        cat_realpred = RealPred.from_string('_cat_n_1_rel')
        the_gpred = GPred.from_string('the_q_rel')
        self.assertEqual(cat_pred, cat_realpred)
        self.assertEqual(the_pred, the_gpred)

    def test_Pred_subclasses(self):
        """
        RealPred and GPred should be subclasses of Pred
        """
        self.assertTrue(issubclass(RealPred, Pred))
        self.assertTrue(issubclass(GPred, Pred))

    def test_RealPred_new(self):
        """
        RealPreds should be able to have exactly two slots (lemma and pos)
        or exactly three slots (lemma, pos, and sense).
        The constructor should take either positional or keyword arguments.
        The slots should be accessible by attribute names.
        """
        # Check two arguments
        self.assert_the(RealPred('the', 'q'))
        self.assert_the(RealPred(lemma='the', pos='q'))

        # Check three arguments
        self.assert_cat(RealPred('cat', 'n', '1'))
        self.assert_cat(RealPred(lemma='cat', pos='n', sense='1'))

        # Check wrong numbers of arguments
        with self.assertRaises(TypeError):
            RealPred('cat')
        with self.assertRaises(TypeError):
            RealPred('cat', 'n', '1', '2')

    # Helper functions for test_RealPred_new
    def assert_the(self, pred):
        self.assertEqual(pred.lemma, 'the')
        self.assertEqual(pred.pos, 'q')
        self.assertIsNone(pred.sense)

    def assert_cat(self, pred):
        self.assertEqual(pred.lemma, 'cat')
        self.assertEqual(pred.pos, 'n')
        self.assertEqual(pred.sense, '1')

    def test_RealPred_eq(self):
        """
        RealPreds should be equal if lemma, pos, and sense are equal.
        RealPreds should be hashable.
        """
        the1 = RealPred('the','q')
        the2 = RealPred('the','q')
        cat1 = RealPred('cat','n','1')
        cat2 = RealPred('cat','n','1')
        catnone = RealPred('cat','n')
        # Check equality
        self.assertEqual(the1, the2)
        self.assertEqual(cat1, cat2)
        self.assertNotEqual(cat1, the1)
        self.assertNotEqual(cat1, catnone)
        self.assertNotEqual(the1, catnone)
        # Check hashability
        mydict = {the1: 1}
        self.assertEqual(mydict[the2], 1)

    def test_RealPred_immutable(self):
        """
        RealPreds should be immutable
        """
        the = RealPred('the','q')
        cat = RealPred('cat','n','1')
        with self.assertRaises(AttributeError):
            the.lemma = 1
        with self.assertRaises(AttributeError):
            cat.lemma = 1

    def test_RealPred_from_string(self):
        """
        RealPred.from_string should instantiate RealPreds
        """
        # Two slots
        the_rel = RealPred.from_string('_the_q_rel')
        the = RealPred.from_string('_the_q')
        self.assertEqual(RealPred('the','q'), the_rel)
        self.assertEqual(RealPred('the','q'), the)
        self.assertIsInstance(the_rel, RealPred)
        self.assertIsInstance(the, RealPred)
        # Three slots
        cat_rel = RealPred.from_string('_cat_n_1_rel')
        cat = RealPred.from_string('_cat_n_1')
        self.assertEqual(RealPred('cat','n','1'), cat_rel)
        self.assertEqual(RealPred('cat','n','1'), cat)
        self.assertIsInstance(cat_rel, RealPred)
        self.assertIsInstance(cat, RealPred)
        # Intermediate underscores in lemma
        nowhere_near_rel = RealPred.from_string('_nowhere_near_x_deg_rel')
        nowhere_near = RealPred.from_string('_nowhere_near_x_deg')
        self.assertEqual(RealPred('nowhere_near','x','deg'), nowhere_near_rel)
        self.assertEqual(RealPred('nowhere_near','x','deg'), nowhere_near)
        self.assertIsInstance(nowhere_near_rel, RealPred)
        self.assertIsInstance(nowhere_near, RealPred)
        # Too few slots, no leading underscore, or not a string
        with self.assertRaises(ValueError):
            RealPred.from_string("_the_rel")
        with self.assertRaises(ValueError):
            RealPred.from_string("_the")
        with self.assertRaises(ValueError):
            RealPred.from_string("udef_q_rel")
        with self.assertRaises(TypeError):
            RealPred.from_string(1)

    def test_RealPred_str(self):
        """
        The 'informal' string representation of a RealPred
        should have a leading underscore and trailing _rel
        """
        thestring = '_the_q_rel'
        catstring = '_cat_n_1_rel'
        self.assertEqual(str(RealPred.from_string(thestring)), thestring)
        self.assertEqual(str(RealPred.from_string(catstring)), catstring)

    def test_RealPred_repr(self):
        """
        The 'official' string representation of a RealPred
        should evaluate to an equivalent RealPred
        """
        the = RealPred('the','q')
        cat = RealPred('cat','n','1')
        self.assertEqual(the, eval(repr(the)))
        self.assertEqual(cat, eval(repr(cat)))
    
    def test_RealPred_copy(self):
        """
        copy.copy should return an equal RealPred
        copy.deepcopy should also return an equal RealPred
        """
        from copy import copy, deepcopy
        the = RealPred('the','q')
        cat = RealPred('cat','n','1')
        the_copy = copy(the)
        the_deep = deepcopy(the)
        cat_copy = copy(cat)
        cat_deep = deepcopy(cat)
        self.assertEqual(the, the_copy)
        self.assertEqual(the, the_deep)
        self.assertEqual(cat, cat_copy)
        self.assertEqual(cat, cat_deep)
        self.assertIsNot(the, the_copy)
        self.assertIsNot(the, the_deep)
        self.assertIsNot(cat, cat_copy)
        self.assertIsNot(cat, cat_deep)
        # Note that it doesn't make sense to check
        # if the.lemma is not the_deep.lemma,
        # because identical strings are considered to be the same
    
    def test_GPred_new(self):
        """
        GPreds should require exactly one slot (name).
        The constructor should take either a positional or a keyword argument.
        The slot should be accessible as an attribute.
        """
        # Check one argument
        self.assertEqual(GPred('pron').name, 'pron')
        self.assertEqual(GPred(name='pron').name, 'pron')
        
        # Check wrong numbers of arguments
        with self.assertRaises(TypeError):
            GPred()
        with self.assertRaises(TypeError):
            GPred('udef', 'q')

    def test_GPred_eq(self):
        """
        GPreds should be equal if their names are equal.
        GPreds should be hashable.
        """
        pron1 = GPred('pron')
        pron2 = GPred('pron')
        udef = GPred('udef_q')
        # Check equality
        self.assertEqual(pron1, pron2)
        self.assertNotEqual(pron1, udef)
        # Check hashability
        mydict = {pron1: 1}
        self.assertEqual(mydict[pron2], 1)

    def test_GPred_immutable(self):
        """
        GPreds should be immutable
        """
        pron = GPred('pron')
        with self.assertRaises(AttributeError):
            pron.name = 1

    def test_GPred_from_string(self):
        """
        GPred.from_string should instantiate GPreds
        It requires a string without a leading underscore
        """
        # No intermediate underscores
        pron_rel = GPred.from_string('pron_rel')
        pron = GPred.from_string('pron')
        self.assertEqual(GPred('pron'), pron_rel)
        self.assertEqual(GPred('pron'), pron)
        self.assertIsInstance(pron_rel, GPred)
        self.assertIsInstance(pron, GPred)
        # Intermediate underscores
        udef_q_rel = GPred.from_string('udef_q_rel')
        udef_q = GPred.from_string('udef_q')
        self.assertEqual(GPred('udef_q'), udef_q_rel)
        self.assertEqual(GPred('udef_q'), udef_q)
        self.assertIsInstance(udef_q_rel, GPred)
        self.assertIsInstance(udef_q, GPred)
        # Leading underscore or not a string
        with self.assertRaises(ValueError):
            GPred.from_string("_the_q_rel")
        with self.assertRaises(TypeError):
            GPred.from_string(1)

    def test_GPred_str(self):
        """
        The 'informal' string representation of a GPred
        should have a trailing _rel
        """
        pronstring = 'pron_rel'
        self.assertEqual(str(GPred.from_string(pronstring)), pronstring)

    def test_GPred_repr(self):
        """
        The 'official' string representation of a GPred
        should evaluate to an equivalent GPred
        """
        pron_pred = GPred('pron')
        self.assertEqual(pron_pred, eval(repr(pron_pred)))
    
    def test_GPred_copy(self):
        """
        copy.copy should return an equal GPred
        copy.deepcopy should also return an equal GPred
        """
        from copy import copy, deepcopy
        pron = GPred('pron')
        pron_copy = copy(pron)
        pron_deep = deepcopy(pron)
        self.assertEqual(pron, pron_copy)
        self.assertEqual(pron, pron_deep)
        self.assertIsNot(pron, pron_copy)
        self.assertIsNot(pron, pron_deep)
        # Note that it doesn't make sense to check
        # if pron.name is not pron_deep.name,
        # because identical strings are considered to be the same
