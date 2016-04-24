from collections import namedtuple
try:
    from collections.abc import Mapping
except ImportError:  # Python v3.2 or less
    from collections import Mapping
from functools import total_ordering
from itertools import chain
from warnings import warn

from pydmrs._exceptions import *


@total_ordering
class Pred(object):
    """
    A superclass for all Pred classes.
    Instances of Pred denote a completely underspecified predicate.
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
            warn('Predicates with opening single-quote have been deprecated', PydmrsDeprecationWarning)
            string = string[1:]
        if '"' in string:
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
        if ' ' in lemma or ' ' in pos or (sense and ' ' in sense):
            raise PydmrsValueError('the values of a RealPred must not contain spaces')
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
            and (self.pos == 'u' or self.pos == other.pos) \
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
    A superclass for all Sortinfo classes.
    Instances of Sortinfo denote completely underspecified sortinfo
    """
    __slots__ = ()
    cvarsort = 'i'

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
        return 1

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

    def iter_specified(self):
        """
        Return (feature, value) pairs where value is not None
        """
        yield ('cvarsort', 'i')

    @staticmethod
    def from_dict(dictionary):
        """
        Instantiates a suitable type of Sortinfo from a dictionary,
        mapping from features to values (including cvarsort)
        """
        # Convert all keys to lowercase (so that we can check if certain keys exist)
        # Values are left untouched until the object is constructed (e.g. in case of None)
        dictionary = {key.lower(): value for key, value in dictionary.items()}
        # Find the cvarsort
        try:
            cvarsort = dictionary['cvarsort'].lower()
        except KeyError:
            raise PydmrsValueError('Sortinfo must have cvarsort')
        # Correct cvarsort if features are evidence for 'x' or 'e':
        if cvarsort not in 'ex' and len(dictionary) > 1:
            if any(key in dictionary for key in EventSortinfo.__slots__):  # event evidence
                cvarsort = dictionary['cvarsort'] = 'e'
            elif any(key in dictionary for key in InstanceSortinfo.__slots__):  # instance evidence
                cvarsort = dictionary['cvarsort'] = 'x'
        # Instantiate an appropriate type of Sortinfo
        if cvarsort == 'e':
            return EventSortinfo.from_dict(dictionary)
        elif cvarsort == 'x':
            if 'prontype' in dictionary:
                dictionary['pt'] = dictionary.pop('prontype')
            return InstanceSortinfo.from_dict(dictionary)
        else:
            # This needs to be updated so that the underspecified cvarsorts i, u, and p are distinguished
            return Sortinfo()
    
    @classmethod
    def from_string(cls, string):
        """
        Instantiate from a string of the form:
        cvarsort[feature1=value1, feature2=value2, ...]
        """
        # Force lowercase
        string = string.lower()
        # Dictionary mapping from features to values
        dictionary = {'cvarsort' : string[0]}
        if len(string) > 1:
            if not (string[1] == '[' and string[-1] == ']'):
                raise PydmrsValueError('Sortinfo string must include features in square brackets')
            for item in string[2:-1].split(','):
                key, value = item.split('=')
                dictionary[key.strip()] = value.strip()
        # Convert the dictionary
        return cls.from_dict(dictionary)


class FeaturedSortinfo(Sortinfo):
    """
    Sortinfo with features.
    Subclasses of FeaturedSortinfo must specify __slots__ and cvarsort
    """
    __slots__ = ()
    
    # The following two methods allow users to add features to subclasses
    # The __slots__ of all parent classes are combined into a single tuple
    # This tuple is accessible under .features, and is only calculated once per class
    # (If it's necessary to access a class's features before _get_all_features is called,)
    # (we could use a metaclass, or class decorator, but just using inheritance is simpler)
    
    @classmethod
    def _get_all_features(cls):
        """
        Combine the __slots__ of all superclasses.
        The result is memoized with the features attribute
        """
        features = tuple(chain.from_iterable(getattr(parent, '__slots__', ()) for parent in cls.__mro__))
        setattr(cls, 'features', features)
        return features
    
    @property
    def features(self):
        """
        Return the class's features attribute, if it exists,
        or else calculate it and then return it.
        """
        return getattr(type(self), 'features', type(self)._get_all_features())
    
    # For convenience, we can also get features which are not None
    
    def iter_specified(self):
        """
        Return (feature, value) pairs where value is not None
        """
        for feat in self.features:
            val = self[feat]
            if val is not None:
                yield (feat, val)
    
    # Container methods
    
    def __iter__(self):
        """
        Iterate through all features, including 'cvarsort'
        """
        yield 'cvarsort'
        for feat in self.features:
            yield feat
    
    def __len__(self):
        """
        Return the number of features, including 'cvarsort'
        """
        return 1 + len(self.features)
    
    def __contains__(self, feature):
        """
        Check if a feature is present in the class
        """
        if feature == 'cvarsort':
            return True
        else:
            return feature in self.features

    # Setters and getters
    # Allows both attribute and dictionary access
    # Features and values must all be lowercase
    
    def __setattr__(self, feature, value):
        """
        Set the value of a feature, converting it to lowercase unless it's None
        """
        feature = feature.lower()
        if value is not None:
            super().__setattr__(feature, value.lower())
        else:
            super().__setattr__(feature, None)
        
    def __setitem__(self, feature, value):
        """
        Set items as attributes
        """
        setattr(self, feature, value)
    
    def __getitem__(self, feature):
        """
        Get the value of a feature, including 'cvarsort'
        """
        feature = feature.lower()
        if feature == 'cvarsort':
            return self.cvarsort
        elif feature in self.features:
            return getattr(self, feature)
        else:
            raise PydmrsKeyError("{} has no feature {}".format(type(self), feature))
    
    def __init__(self, *args, **kwargs):
        """
        Initialise values of features, from positional or keyword arguments
        If a feature is not given, its value is set to None
        """
        if len(args) > len(self.features):
            raise PydmrsTypeError("{} takes {} arguments, but {} were given".format(type(self).__name__,
                                                                                    len(self.features),
                                                                                    len(args)))
        for i, value in enumerate(args):
            setattr(self, self.features[i], value)
        for feature, value in kwargs.items():
            setattr(self, feature, value)
        for feature in self.features:
            if not hasattr(self, feature):
                setattr(self, feature, None)
    
    # Conversion to strings and dicts
    
    def __str__(self):
        """
        Returns a string of the form:
        cvarsort[feature1=value1, feature2=value2, ...]
        """
        return '{}[{}]'.format(self.cvarsort,
                               ', '.join('{}={}'.format(*pair) for pair in self.iter_specified()))
    
    def __repr__(self):
        """
        Return a string that can be evaluated
        """
        return '{}({})'.format(type(self).__name__, ', '.join(repr(self[feat]) for feat in self.features))
    
    def as_dict(self):
        """
        Return a dict mapping from features to values, including 'cvarsort'
        """
        return dict(self.items())
    
    # Conversion from strings and dicts
    # Note that cls.from_string (inherited from Sortinfo) will call cls.from_dict
    
    @classmethod
    def from_dict(cls, dictionary):
        """
        Instantiate from a dictionary mapping features to values
        """
        if 'cvarsort' in dictionary and dictionary['cvarsort'] != cls.cvarsort:
            raise PydmrsValueError('{} must have cvarsort {}, not {}'.format(cls.__name__,
                                                                             cls.cvarsort,
                                                                             dictionary['cvarsort']))
        return cls(**{key:value for key, value in dictionary.items() if key != 'cvarsort'})


class EventSortinfo(FeaturedSortinfo):
    """
    Event sortinfo
    """
    cvarsort = 'e'
    __slots__ = ('sf', 'tense', 'mood', 'perf', 'prog')
    # Sentence force, tense, mood, perfect, progressive


class InstanceSortinfo(FeaturedSortinfo):
    """
    Instance sortinfo
    """
    cvarsort = 'x'
    __slots__ = ('pers', 'num', 'gend', 'ind', 'pt')
    # Person, number, gender, individuated, pronoun type

