from collections import namedtuple
try:
    from collections.abc import Mapping
except ImportError:  # Python v3.2 or less
    from collections import Mapping
from functools import total_ordering
from warnings import warn
from pydmrs._exceptions import *


@total_ordering
class Pred(object):
    """
    A superclass for all Pred classes
    """

    __slots__ = ()  # Suppress __dict__

    def __str__(self):
        """
        Returns 'predsort', the type name for predicates in Delph-in grammars
        """
        return 'predsort'

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
    def normalise_string(string):
        """
        Normalises a predicate string
        """
        # Disallow spaces
        if ' ' in string:
            raise PydmrsValueError('Predicates must not contain spaces')
        # Strip surrounding quotes and disallow other quotes
        if string[0] == '"' and string[-1] == '"':
            string = string[1:-1]
        if string[0] == "'":
            warn('Predicates with opening single-quote have been deprecated', PydmrsWarning)
            string = string[1:]
        if '"' in string or "'" in string:
            raise PydmrsValueError('Predicates must not contain quotes')
        # Force lower case
        if not string.islower():
            warn('Predicates must be lower-case', PydmrsWarning)
            string = string.lower()
        # Strip trailing '_rel'
        if string[-4:] == '_rel':
            string = string[:-4]
        
        return string
    
    @classmethod
    def from_string(cls, string):
        """
        Instantiates a pred from a string, normalising as necessary
        """
        normalised = cls.normalise_string(string)
        return cls.from_normalised_string(normalised)

    @staticmethod
    def from_normalised_string(string):
        """
        Instantiates a suitable type of Pred, from a string
        """
        if string[0] == '_':
            return RealPred.from_normalised_string(string)
        else:
            return GPred.from_normalised_string(string)


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
        if not lemma:
            raise PydmrsValueError('a RealPred must have non-empty lemma')
        if not pos:
            raise PydmrsValueError('a RealPred must have non-empty pos')
        return super().__new__(cls, lemma, pos, sense)

    def __str__(self):
        """
        Return a string, with leading underscore
        """
        if self.sense:
            return "_{}_{}_{}".format(*self)
        else:
            return "_{}_{}".format(*self)

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
        return isinstance(other, RealPred) \
            and (self.lemma == '?' or self.lemma == other.lemma) \
            and (self.pos in 'u' or self.pos == other.pos) \
            and (self.sense == '?' or self.sense == other.sense)

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
    def from_normalised_string(string):
        """
        Create a new instance from a normalised string.
        :param string: Input string
        :return: RealPred object
        """
        # Require initial underscore
        if string[0] != '_':
            raise PydmrsValueError("RealPred strings must begin with an underscore")
        # Split into 2 or 3 parts
        # This allows the lemma to contain underscores, which sometimes happens in the ERG
        parts = string[1:].rsplit('_', 2)
        # Require at least 2 parts
        if len(parts) < 2:
            raise PydmrsValueError("RealPred strings must have a part of speech separated by an underscore")
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
        if not name:
            raise PydmrsValueError('a GPred must have non-empty name')
        return super().__new__(cls, name)

    def __str__(self):
        """
        Return a string
        """
        return str(self.name)

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
    def from_normalised_string(string):
        """
        Create a new instance from a normalised string.
        """
        if string[0] == '_':
            raise PydmrsValueError("GPred strings must not begin with an underscore")
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
        return isinstance(other, type(self)) and len(self) == len(other) \
            and all(key in other and self[key] == other[key] for key in self)

    def __le__(self, other):
        """
        Checks whether this Sortinfo underspecifies or equals the other Sortinfo
        """
        return isinstance(other, type(self)) \
            and (self.cvarsort == 'i' or self.cvarsort == other.cvarsort) \
            and all(self[key] == 'u' or (key in other and self[key] == other[key]) \
                    for key in self if key != 'cvarsort')

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
            raise PydmrsKeyError

    def __setitem__(self, key, value):
        """
        Sets the value of a property
        """
        raise PydmrsKeyError

    @property
    def cvarsort(self):
        return 'i'

    @staticmethod
    def from_dict(dictionary):
        """
        Instantiates a suitable type of Sortinfo from a dictionary
        """
        dictionary = {key.lower(): value.lower() for key, value in dictionary.items()}
        if 'cvarsort' not in dictionary:
            raise PydmrsValueError('Sortinfo must have cvarsort')
        cvarsort = dictionary['cvarsort']
        # Correct cvarsort if features are evidence for 'x' or 'e':
        if cvarsort not in 'ex' and len(dictionary) > 1:
            if any(key in dictionary for key in ('sf', 'tense', 'mood', 'perf', 'prog')):  # event evidence
                cvarsort = 'e'
            elif any(key in dictionary for key in ('pers', 'num', 'gend', 'ind', 'pt', 'prontype')):  # instance evidence
                cvarsort = 'x'
        if cvarsort == 'e':
            return EventSortinfo(dictionary.get('sf', None),
                                 dictionary.get('tense', None),
                                 dictionary.get('mood', None),
                                 dictionary.get('perf', None),
                                 dictionary.get('prog', None))
        elif cvarsort == 'x':
            return InstanceSortinfo(dictionary.get('pers', None),
                                    dictionary.get('num', None),
                                    dictionary.get('gend', None),
                                    dictionary.get('ind', None),
                                    dictionary.get('pt', None))
        else:
            # This needs to be updated so that the underspecified cvarsorts i, u, and p are distinguished
            return Sortinfo()

    @staticmethod
    def from_string(string):
        """
        Instantiates a suitable type of Sortinfo from a string
        """
        if string == 'i':
            return Sortinfo()
        if not (string[1] == '[' and string[-1] == ']'):
            raise PydmrsValueError('Sortinfo string must include features in square brackets')
        values = [tuple(value.strip().split('=')) for value in string[2:-1].split(',')]
        dictionary = {key.lower(): value.lower() for key, value in values}
        if string[0] == 'e':
            return EventSortinfo(dictionary.get('sf', None),
                                 dictionary.get('tense', None),
                                 dictionary.get('mood', None),
                                 dictionary.get('perf', None),
                                 dictionary.get('prog', None))
        elif string[0] == 'x':
            return InstanceSortinfo(dictionary.get('pers', None),
                                    dictionary.get('num', None),
                                    dictionary.get('gend', None),
                                    dictionary.get('ind', None),
                                    dictionary.get('pt', None))
        else:
            # This needs to be updated to deal with the underspecified cvarsorts u and p.
            raise PydmrsValueError('Unrecognised cvarsort')


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
        return "EventSortinfo({}, {}, {}, {}, {})".format(repr(self.sf),
                                                          repr(self.tense),
                                                          repr(self.mood),
                                                          repr(self.perf),
                                                          repr(self.prog))

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
            raise PydmrsKeyError

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
            raise PydmrsKeyError

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
        return "InstanceSortinfo({}, {}, {}, {}, {})".format(repr(self.pers),
                                                             repr(self.num),
                                                             repr(self.gend),
                                                             repr(self.ind),
                                                             repr(self.pt))

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
            raise PydmrsKeyError

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
            raise PydmrsKeyError

    @property
    def cvarsort(self):
        return 'x'
