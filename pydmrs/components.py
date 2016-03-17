from collections import namedtuple
from collections.abc import Mapping
from functools import total_ordering
from pydmrs._exceptions import *


@total_ordering
class Pred(object):
    """
    A superclass for all Pred classes
    """

    __slots__ = ()  # Suppress __dict__

    def __str__(self):
        """
        Returns 'rel'
        """
        return 'rel'

    def __repr__(self):
        """
        Returns a string representation
        """
        return 'Pred()'

    def __eq__(self, other):
        """
        Checks whether the other object is of type Pred
        """
        return type(other) == Pred

    def __le__(self, other):
        """
        Checks whether this Pred underspecifies or equals the other Pred
        """
        return isinstance(other, Pred)

    @staticmethod
    def from_string(string):
        """
        Instantiates a suitable type of Pred, from a string
        """
        if not string.islower():
            raise PydmrsValueError('Predicates must be lower-case.')
        if ' ' in string:
            raise PydmrsValueError('Predicates must not contain spaces.')
        if string[0] == '"' and string[-1] == '"':
            string = string[1:-1]
        if '"' in string:
            raise PydmrsValueError('Predicates must not contain quotes.')
        if string[0] == '\'':
            raise PydmrsValueError('Predicates with opening single-quote have been deprecated.')
        if string == 'rel':
            return Pred()
        elif string[0] == '_':
            return RealPred.from_string(string)
        else:
            return GPred.from_string(string)


class RealPred(namedtuple('RealPredNamedTuple', ('lemma', 'pos', 'sense')), Pred):
    """
    Real predicate, with a lemma, part of speech, and (optional) sense
    """

    __slots__ = ()  # Suppress __dict__

    def __new__(cls, lemma, pos, sense=None):
        """
        Create a new instance, allowing the sense to be optional,
        and requiring non-empty lemma and pos
        """
        assert lemma
        assert pos
        return super().__new__(cls, lemma, pos, sense)

    def __str__(self):
        """
        Return a string, with leading underscore, and trailing '_rel'
        """
        if self.sense:
            return "_{}_{}_{}_rel".format(*self)
        else:
            return "_{}_{}_rel".format(*self)

    def __repr__(self):
        """
        Return a string, as "RealPred(lemma, pos, sense)"
        """
        if self.sense:
            return "RealPred({}, {}, {})".format(*(repr(x) for x in self))
        else:
            return "RealPred({}, {})".format(*(repr(x) for x in self))

    def __le__(self, other):
        """
        Checks whether this RealPred underspecifies or equals the other RealPred
        """
        return isinstance(other, RealPred) and (self.lemma == '?' or self.lemma == other.lemma) and (self.pos in 'u' or self.pos == other.pos) and (not self.sense or self.sense == other.sense)

    def __lt__(self, other):
        """
        Checks whether this RealPred underspecifies the other RealPred
        """
        return self <= other and self != other

    def __ge__(self, other):
        """
        Checks whether the other RealPred underspecifies or equals this RealPred
        """
        return type(other) == Pred or (isinstance(other, RealPred) and other <= self)

    def __gt__(self, other):
        """
        Checks whether the other RealPred underspecifies this RealPred
        """
        return self <= other and self != other

    @staticmethod
    def from_string(string):
        """
        Create a new instance from a string,
        stripping a trailing _rel if it exists.
        :param string: Input string
        :return: RealPred object
        """
        if string[0] != '_':
            raise PydmrsValueError("RealPred strings must begin with an underscore")
        if string[-4:] == '_rel':
            string = string[:-4]
        parts = string[1:].rsplit('_', maxsplit=2)
        if len(parts) < 2 or len(parts) > 3:
            raise PydmrsValueError("Invalid number of arguments for RealPred.")
        if parts[1] == '?':
            parts[1] == 'u'
        return RealPred(*parts)


class GPred(namedtuple('GPredNamedTuple', ('name')), Pred):
    """
    Grammar predicate, with a rel name
    """

    __slots__ = ()  # Suppress __dict__

    def __new__(cls, name):
        """
        Create a new instance, requiring non-empty name
        """
        assert name
        return super().__new__(cls, name)

    def __str__(self):
        """
        Return a string, with trailing '_rel'
        """
        return "{}_rel".format(self.name)

    def __repr__(self):
        """
        Return a string, as "GPred(name)"
        """
        return "GPred({})".format(repr(self.name))

    def __le__(self, other):
        """
        Checks whether this GPred underspecifies or equals the other GPred
        """
        return isinstance(other, GPred) and (self.name == '?' or self.name == other.name)

    def __lt__(self, other):
        """
        Checks whether this GPred underspecifies the other GPred
        """
        return self <= other and self != other

    def __ge__(self, other):
        """
        Checks whether the other GPred underspecifies or equals this GPred
        """
        return type(other) == Pred or (isinstance(other, GPred) and other <= self)

    def __gt__(self, other):
        """
        Checks whether the other GPred underspecifies this GPred
        """
        return self <= other and self != other

    @staticmethod
    def from_string(string):
        """
        Create a new instance from a string,
        stripping a trailing '_rel' if it exists.
        """
        if string[0] == '_':
            raise PydmrsValueError("GPred strings must not begin with an underscore")
        if string[-4:] == '_rel':
            return GPred(string[:-4])
        else:
            return GPred(string)


@total_ordering
class Sortinfo(Mapping):
    """
    A superclass for all Sortinfo classes
    """
    __slots__ = ()

    def __str__(self):
        """
        Returns 'i'
        """
        return 'i'

    def __repr__(self):
        """
        Returns a string representation
        """
        return 'Sortinfo()'

    def __eq__(self, other):
        """
        Checks two Sortinfos for equality
        """
        return isinstance(other, type(self)) and len(self) == len(other) and all(key in other and self[key] == other[key] for key in self)

    def __le__(self, other):
        """
        Checks whether this Sortinfo underspecifies or equals the other Sortinfo
        """
        return isinstance(other, type(self)) and (self.cvarsort == 'i' or self.cvarsort == other.cvarsort) and all(self[key] == 'u' or (key in other and self[key] == other[key]) for key in self if key != 'cvarsort')

    def __iter__(self):
        """
        Returns an iterator over the properties
        """
        yield 'cvarsort'

    def __len__(self):
        """
        Returns the size
        """
        return sum(1 for _ in self)

    def __getitem__(self, key):
        """
        Returns the value of a property
        """
        key = key.lower()
        if key == 'cvarsort':
            return 'i'
        else:
            raise KeyError

    def __setitem__(self, key, value):
        """
        Sets the value of a property
        """
        raise KeyError

    @property
    def cvarsort(self):
        return 'i'

    @staticmethod
    def from_dict(dictionary):
        """
        Instantiates a suitable type of Sortinfo from a dictionary
        """
        if not dictionary:
            return None
        dictionary = {key.lower(): value.lower() for key, value in dictionary.items()}
        assert 'cvarsort' in dictionary
        # correcting cvarsort if specification evidence given
        cvarsort = dictionary['cvarsort']
        if cvarsort not in 'eix' or (cvarsort == 'i' and len(dictionary) > 1):
            if any(key in dictionary for key in ('sf', 'tense', 'mood', 'perf', 'prog')):  # event evidence
                cvarsort = 'e'
            elif any(key in dictionary for key in ('pers', 'num', 'gend', 'ind', 'pt', 'prontype')):  # instance evidence
                cvarsort = 'x'
            else:  # no evidence
                cvarsort = 'i'
        if cvarsort == 'i':
            assert len(dictionary) == 1
            return Sortinfo()
        elif cvarsort == 'e':
            assert all(key in ('cvarsort', 'sf', 'tense', 'mood', 'perf', 'prog') for key in dictionary)
            return EventSortinfo(dictionary.get('sf', None), dictionary.get('tense', None), dictionary.get('mood', None), dictionary.get('perf', None), dictionary.get('prog', None))
        elif cvarsort == 'x':
            assert all(key in ('cvarsort', 'pers', 'num', 'gend', 'ind', 'pt', 'prontype') for key in dictionary)
            return InstanceSortinfo(dictionary.get('pers', None), dictionary.get('num', None), dictionary.get('gend', None), dictionary.get('ind', None), dictionary.get('pt', None) or dictionary.get('prontype', None))
        else:
            raise PydmrsValueError('Invalid sortinfo dictionary.')

    @staticmethod
    def from_string(string):
        """
        Instantiates a suitable type of Sortinfo from a string
        """
        if not string:
            return None
        if string == 'i':
            return Sortinfo()
        assert string[0] in 'ex' and string[1] == '[' and string[-1] == ']'
        values = [tuple(value.strip().split('=')) for value in string[2:-1].split(',')]
        dictionary = {key.lower(): value.lower() for key, value in values}
        if string[0] == 'e':
            return EventSortinfo(dictionary.get('sf', None), dictionary.get('tense', None), dictionary.get('mood', None), dictionary.get('perf', None), dictionary.get('prog', None))
        else:
            return InstanceSortinfo(dictionary.get('pers', None), dictionary.get('num', None), dictionary.get('gend', None), dictionary.get('ind', None), dictionary.get('pt', None))


class EventSortinfo(Sortinfo):
    """
    Event sortinfo
    """
    __slots__ = ('sf', 'tense', 'mood', 'perf', 'prog')

    def __init__(self, sf, tense, mood, perf, prog):
        """
        Create a new instance
        """
        self.sf = sf.lower() if sf else sf
        self.tense = tense.lower() if tense else tense
        self.mood = mood.lower() if mood else mood
        self.perf = perf.lower() if perf else perf
        self.prog = prog.lower() if prog else prog

    def __str__(self):
        """
        Returns '?'
        """
        return 'e[{}]'.format(', '.join('{}={}'.format(key, self[key]) for key in self if key != 'cvarsort'))

    def __repr__(self):
        """
        Return a string representation
        """
        return "EventSortinfo({}, {}, {}, {}, {})".format(repr(self.sf), repr(self.tense), repr(self.mood), repr(self.perf), repr(self.prog))

    def __iter__(self):
        """
        Returns an iterator over the properties
        """
        return (attr for attr in ('cvarsort', 'sf', 'tense', 'mood', 'perf', 'prog') if self[attr])

    def __getitem__(self, key):
        """
        Returns the value of a property
        """
        key = key.lower()
        if key == 'cvarsort':
            return 'e'
        elif key == 'sf':
            return self.sf
        elif key == 'tense':
            return self.tense
        elif key == 'mood':
            return self.mood
        elif key == 'perf':
            return self.perf
        elif key == 'prog':
            return self.prog
        else:
            raise KeyError

    def __setitem__(self, key, value):
        """
        Sets the value of a property
        """
        key = key.lower()
        value = value.lower() if value else value
        if key == 'sf':
            self.sf = value
        elif key == 'tense':
            self.tense = value
        elif key == 'mood':
            self.mood = value
        elif key == 'perf':
            self.perf = value
        elif key == 'prog':
            self.prog = value
        else:
            raise KeyError

    @property
    def cvarsort(self):
        return 'e'


class InstanceSortinfo(Sortinfo):
    """
    Instance sortinfo
    """
    __slots__ = ('pers', 'num', 'gend', 'ind', 'pt')

    def __init__(self, pers, num, gend, ind, pt):
        """
        Create a new instance
        """
        self.pers = pers.lower() if pers else pers
        self.num = num.lower() if num else num
        self.gend = gend.lower() if gend else gend
        self.ind = ind.lower() if ind else ind
        self.pt = pt.lower() if pt else pt

    def __str__(self):
        """
        Returns '?'
        """
        return 'x[{}]'.format(', '.join('{}={}'.format(key, self[key]) for key in self if key != 'cvarsort'))

    def __repr__(self):
        """
        Return a string representation
        """
        return "InstanceSortinfo({}, {}, {}, {}, {})".format(repr(self.pers), repr(self.num), repr(self.gend), repr(self.ind), repr(self.pt))

    def __iter__(self):
        """
        Returns an iterator over the properties
        """
        return (attr for attr in ('cvarsort', 'pers', 'num', 'gend', 'ind', 'pt') if self[attr])

    def __getitem__(self, key):
        """
        Returns the value of a property
        """
        key = key.lower()
        if key == 'cvarsort':
            return 'x'
        elif key == 'pers':
            return self.pers
        elif key == 'num':
            return self.num
        elif key == 'gend':
            return self.gend
        elif key == 'ind':
            return self.ind
        elif key == 'pt':
            return self.pt
        else:
            raise KeyError

    def __setitem__(self, key, value):
        """
        Sets the value of a property
        """
        key = key.lower()
        value = value.lower() if value else value
        if key == 'pers':
            self.pers = value
        elif key == 'num':
            self.num = value
        elif key == 'gend':
            self.gend = value
        elif key == 'ind':
            self.ind = value
        elif key == 'pt':
            self.pt = value
        else:
            raise KeyError

    @property
    def cvarsort(self):
        return 'x'
