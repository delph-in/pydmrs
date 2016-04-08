import unittest, warnings

from pydmrs.components import (
    Pred, RealPred, GPred,
    Sortinfo, EventSortinfo, InstanceSortinfo
)

class TestPred(unittest.TestCase):
    """
    Test methods of Pred class and subclasses
    """
    def test_Pred_new(self):
        """
        Pred() instances denote underpecified preds,
        and should not take any arguments
        """
        with self.assertRaises(TypeError):
            Pred('name')
    
    def test_Pred_str(self):
        """
        The 'informal' string representation of a Pred should be
        'predsort', the type name for predicates in Delph-in grammars
        """
        self.assertEqual(str(Pred()), 'predsort')
    
    def test_Pred_repr(self):
        """
        The 'official' string representation of Pred()
        should evaluate to Pred()
        """
        self.assertEqual(eval(repr(Pred())), Pred())
    
    def test_Pred_normalise_string(self):
        """
        Pred strings should be normalised - see comments below
        """
        # Remove quotes from quoted preds
        self.assertEqual(Pred.normalise_string('"pron"'), 'pron')
        with self.assertRaises(DeprecationWarning):
            warnings.simplefilter('error')
            self.assertEqual(Pred.normalise_string("'pron"), "pron")
        warnings.resetwarnings()
        
        # No internal spaces or quotes
        with self.assertRaises(ValueError):
            Pred.normalise_string('pred name')
        with self.assertRaises(ValueError):
            Pred.normalise_string('pred"name')
        # Force lower case
        self.assertEqual(Pred.normalise_string('PRON'), 'pron')
        # Strip trailing _rel
        self.assertEqual(Pred.normalise_string('pron_rel'), 'pron')
    
    def test_Pred_from_normalised_string(self):
        """
        Pred.from_normalised_string should instantiate RealPreds or GPreds
        depending on whether there is a leading underscore
        """
        # Check the preds are of the right type
        cat_pred = Pred.from_normalised_string('_cat_n_1')
        the_pred = Pred.from_normalised_string('the_q')
        self.assertIsInstance(cat_pred, RealPred)
        self.assertIsInstance(the_pred, GPred)

        # Check the preds are the equivalent to initialising directly 
        cat_realpred = RealPred.from_normalised_string('_cat_n_1')
        the_gpred = GPred.from_normalised_string('the_q')
        self.assertEqual(cat_pred, cat_realpred)
        self.assertEqual(the_pred, the_gpred)
    
    def test_Pred_from_string(self):
        """
        Pred.from_string should normalise the string as necessary
        """
        cat_pred = RealPred.from_normalised_string('_cat_n_1')
        self.assertEqual(Pred.from_string('_cat_n_1_rel'), cat_pred)
        self.assertEqual(Pred.from_string('"_cat_n_1_rel"'), cat_pred)
        self.assertEqual(Pred.from_string('_CAT_N_1_REL'), cat_pred)
        
        the_pred = GPred.from_normalised_string('the')
        self.assertEqual(Pred.from_string('the_rel'), the_pred)
        self.assertEqual(Pred.from_string('"the_rel"'), the_pred)
        self.assertEqual(Pred.from_string('THE_REL'), the_pred)
    
    def test_Pred_cmp_self(self):
        """
        All Pred instances should be equal. 
        """
        p1 = Pred()
        p2 = Pred()
        self.assertEqual(p1, p2)
        self.assertLessEqual(p1, p2)
        self.assertGreaterEqual(p1, p2)
        self.assertFalse(p1 < p2)
        self.assertFalse(p1 > p2)
        self.assertFalse(p1 != p2)
    
    def test_Pred_cmp_subclasses(self):
        """
        Any Pred instance should be less than instances of subclasses. 
        """
        p = Pred()
        cat = RealPred('cat','n','1')
        pron = GPred('pron')
        self.assertLess(p, cat)
        self.assertLess(p, pron)
        self.assertLessEqual(p, cat)
        self.assertLessEqual(p, pron)
        self.assertNotEqual(p, cat)
        self.assertNotEqual(p, pron)

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
        should have a leading underscore
        """
        thestring = '_the_q'
        catstring = '_cat_n_1'
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
        """
        pronstring = 'pron'
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


class TestSortinfo(unittest.TestCase):
    """
    Test methods of SortInfo and subclasses
    """
    def test_Sortinfo_basic(self):
        """
        Basic properties
        """
        sortinfo = Sortinfo()
        self.assertEqual(str(sortinfo), 'i')
        self.assertEqual(eval(repr(sortinfo)), sortinfo)
        self.assertEqual(sortinfo.cvarsort, 'i')
        self.assertEqual(sortinfo['cvarsort'], 'i')
        with self.assertRaises(KeyError):
            sortinfo['tense']
        with self.assertRaises(AttributeError):
            sortinfo.num
        with self.assertRaises(TypeError):
            Sortinfo('info')
    
    def test_Sortinfo_from_string(self):
        """
        Initialise EventSortinfo or InstanceSortinfo as appropriate
        """
        event_string = "e[tense=past]"
        self.assertEqual(Sortinfo.from_string(event_string),
                         EventSortinfo.from_string(event_string))
        instance_string = "x[num=pl]"
        self.assertEqual(Sortinfo.from_string(instance_string),
                         InstanceSortinfo.from_string(instance_string))
    
    def test_Sortinfo_from_dict(self):
        """
        Initialise EventSortinfo or InstanceSortinfo as appropriate
        """
        sortinfo_dict = {'cvarsort': 'i'}
        self.assertEqual(Sortinfo.from_dict(sortinfo_dict),
                         Sortinfo())
        event_dict = {'cvarsort': 'e', 'tense': 'past'}
        self.assertEqual(Sortinfo.from_dict(event_dict),
                         EventSortinfo.from_dict(event_dict))
        instance_dict = {'cvarsort': 'x', 'num': 'pl'}
        self.assertEqual(Sortinfo.from_dict(instance_dict),
                         InstanceSortinfo.from_dict(instance_dict))
        wrong_sort_sortinfo_dict = {'cvarsort': 'u'}
        self.assertEqual(Sortinfo.from_dict(wrong_sort_sortinfo_dict),
                         Sortinfo.from_dict(sortinfo_dict))
        wrong_sort_event_dict = {'cvarsort': 'i', 'tense': 'past'}
        self.assertEqual(Sortinfo.from_dict(wrong_sort_event_dict),
                         Sortinfo.from_dict(event_dict))
        wrong_sort_instance_dict = {'cvarsort': 'u', 'num': 'pl'}
        self.assertEqual(Sortinfo.from_dict(wrong_sort_instance_dict),
                         Sortinfo.from_dict(instance_dict))
    
    def test_EventSortinfo_init(self):
        """
        Events have five features:
        'sf', 'tense', 'mood', 'perf', 'prog'
        """
        event = EventSortinfo('prop', 'past', 'indicative', '-', '-')
        self.assertEqual(event.cvarsort, 'e')
        self.assertEqual(event.sf, 'prop')
        self.assertEqual(event.tense, 'past')
        self.assertEqual(event.mood, 'indicative')
        self.assertEqual(event.perf, '-')
        self.assertEqual(event.prog, '-')
        self.assertEqual(event['cvarsort'], 'e')
        self.assertEqual(event['sf'], 'prop')
        self.assertEqual(event['tense'], 'past')
        self.assertEqual(event['mood'], 'indicative')
        self.assertEqual(event['perf'], '-')
        self.assertEqual(event['prog'], '-')
        event.tense = 'present'
        self.assertEqual(event['tense'], 'present')
        event['perf'] = '+'
        self.assertEqual(event.perf, '+')
        with self.assertRaises((AttributeError, KeyError)):
            event['cvarsort'] = 'x'
        with self.assertRaises((AttributeError, KeyError)):
            event.cvarsort = 'x'
        with self.assertRaises(KeyError):
            event['num']
        with self.assertRaises(AttributeError):
            event.num
        with self.assertRaises(TypeError):
            EventSortinfo('1','2','3','4','5','6')
    
    def test_InstanceSortinfo_init(self):
        """
        Instances have five features:
        'pers', 'num', 'gend', 'ind', 'pt'
        as well as cvarsort
        """
        instance = InstanceSortinfo('3', 'sg', 'f', '+', '+')
        self.assertEqual(instance.cvarsort, 'x')
        self.assertEqual(instance.pers, '3')
        self.assertEqual(instance.num, 'sg')
        self.assertEqual(instance.gend, 'f')
        self.assertEqual(instance.ind, '+')
        self.assertEqual(instance.pt, '+')
        self.assertEqual(instance['cvarsort'], 'x')
        self.assertEqual(instance['pers'], '3')
        self.assertEqual(instance['num'], 'sg')
        self.assertEqual(instance['gend'], 'f')
        self.assertEqual(instance['ind'], '+')
        self.assertEqual(instance['pt'], '+')
        instance.num = 'pl'
        self.assertEqual(instance['num'], 'pl')
        instance['pt'] = '-'
        self.assertEqual(instance.pt, '-')
        with self.assertRaises((AttributeError, KeyError)):
            instance['cvarsort'] = 'e'
        with self.assertRaises((AttributeError, KeyError)):
            instance.cvarsort = 'e'
        with self.assertRaises(KeyError):
            instance['tense']
        with self.assertRaises(AttributeError):
            instance.tense
        with self.assertRaises(TypeError):
            InstanceSortinfo('1','2','3','4','5','6')
    
    def test_Sortinfo_subclasses_iter(self):
        """
        Subclasses of Sortinfo should iter over feature names, including 'cvarsort'
        """
        event = EventSortinfo('prop', 'past', 'indicative', '-', '-')
        instance = InstanceSortinfo('3', 'sg', 'f', '+', '+')
        self.assertEqual(list(iter(event)),
                         ['cvarsort', 'sf', 'tense', 'mood', 'perf', 'prog'])
        self.assertEqual(event.features,
                         ('sf', 'tense', 'mood', 'perf', 'prog'))
        self.assertEqual(list(iter(instance)),
                         ['cvarsort', 'pers', 'num', 'gend', 'ind', 'pt'])
        self.assertEqual(instance.features,
                         ('pers', 'num', 'gend', 'ind', 'pt'))
    
    def test_Sortinfo_subclasses_str(self):
        """
        Strings of sortinfo objects should be of the form:
        cvarsort[feature1=value1, feature2=value2, ...]
        """
        event = EventSortinfo('prop', 'past', 'indicative', '-', '-')
        event_string = 'e[sf=prop, tense=past, mood=indicative, perf=-, prog=-]'
        self.assertEqual(str(event), event_string)
        self.assertEqual(event, EventSortinfo.from_string(event_string))
        instance = InstanceSortinfo('3', 'sg', 'f', '+', '+')
        instance_string = 'x[pers=3, num=sg, gend=f, ind=+, pt=+]'
        self.assertEqual(str(instance), instance_string)
        self.assertEqual(instance, InstanceSortinfo.from_string(instance_string))
    
    def test_Sortinfo_subclasses_repr(self):
        """
        Repr strings should evaluate to equivalent objects
        """
        event = EventSortinfo('prop', 'past', 'indicative', '-', '-')
        self.assertEqual(event, eval(repr(event)))
        instance = InstanceSortinfo('3', 'sg', 'f', '+', '+')
        self.assertEqual(instance, eval(repr(instance)))
    
    def test_Sortinfo_subclasses_dict(self):
        """
        Dicts of sortinfo objects should map from features to values,
        including 'cvarsort' as a feature
        """
        event = EventSortinfo('prop', 'past', 'indicative', '-', '-')
        event_dict = {'cvarsort':'e', 'sf':'prop', 'tense':'past', 'mood':'indicative', 'perf':'-', 'prog':'-'}
        self.assertEqual(event.as_dict(), event_dict)
        self.assertEqual(event, EventSortinfo.from_dict(event_dict))
        instance = InstanceSortinfo('3', 'sg', 'f', '+', '+')
        instance_dict = {'cvarsort':'x', 'pers':'3', 'num':'sg', 'gend':'f', 'ind':'+', 'pt':'+'}
        self.assertEqual(instance.as_dict(), instance_dict)
        self.assertEqual(instance, InstanceSortinfo.from_dict(instance_dict))
    
