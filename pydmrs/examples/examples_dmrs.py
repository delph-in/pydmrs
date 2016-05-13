from pydmrs.components import Pred, GPred, RealPred, Sortinfo, EventSortinfo, InstanceSortinfo
from pydmrs.core import Node, Link, DictDmrs


def the():
    dmrs = DictDmrs()
    dmrs.add_node(Node(pred=RealPred('the', 'q')))  # node id set automatically
    return dmrs


def the_cat():
    dmrs = DictDmrs(surface='the cat')
    dmrs.add_node(Node(nodeid=1, pred=RealPred('the', 'q'), cfrom=0, cto=3))
    dmrs.add_node(Node(nodeid=2, pred=RealPred('cat', 'n', '1'), cfrom=4, cto=7,
                       sortinfo=InstanceSortinfo(pers='3', num='sg',
                                                 ind='+')))  # underspecified sortinfo
    dmrs.add_link(Link(start=1, end=2, rargname='RSTR', post='H'))
    return dmrs


def the_mouse():
    dmrs = DictDmrs(surface='the mouse')
    dmrs.add_node(Node(nodeid=1, pred=RealPred('the', 'q'), cfrom=0, cto=3))
    dmrs.add_node(Node(nodeid=2, pred=RealPred('mouse', 'n', '1'), cfrom=4, cto=9,
                       sortinfo=InstanceSortinfo(pers='3', num='sg', ind='+')))
    dmrs.add_link(Link(start=1, end=2, rargname='RSTR', post='H'))
    return dmrs


def dog_cat():
    dmrs = DictDmrs(surface='dog cat')
    dmrs.add_node(Node(pred=RealPred('dog', 'n', '1'), cfrom=0, cto=3,
                       sortinfo=InstanceSortinfo(pers='3', num='sg', ind='+')))
    dmrs.add_node(Node(pred=RealPred('cat', 'n', '1'), cfrom=4, cto=7,
                       sortinfo=InstanceSortinfo(pers='3', num='sg', ind='+')))
    return dmrs


def the_dog_chases_the_cat():
    return DictDmrs(
        surface='the dog chases the cat',
        nodes=[Node(nodeid=1, pred=RealPred('the', 'q'), cfrom=0, cto=3),
               Node(nodeid=2, pred=RealPred('dog', 'n', '1'), cfrom=4, cto=7,
                    sortinfo=InstanceSortinfo(pers='3', num='sg', ind='+')),
               Node(nodeid=3, pred=RealPred('chase', 'v', '1'), cfrom=8, cto=14,
                    sortinfo=EventSortinfo(sf='prop', tense='pres', mood='indicative')),
               Node(nodeid=4, pred=RealPred('the', 'q'), cfrom=15, cto=18),
               Node(nodeid=5, pred=RealPred('cat', 'n', '1'), cfrom=19, cto=22,
                    sortinfo=InstanceSortinfo(pers='3', num='sg', ind='+'))],
        links=[Link(start=1, end=2, rargname='RSTR', post='H'),
               Link(start=3, end=2, rargname='ARG1', post='NEQ'),
               Link(start=3, end=5, rargname='ARG2', post='NEQ'),
               Link(start=4, end=5, rargname='RSTR', post='H')],
        index=3,
        top=3)


def the_cat_chases_the_dog():
    return DictDmrs(
        surface='the cat chases the dog',
        nodes=[Node(nodeid=1, pred=RealPred('the', 'q'), cfrom=0, cto=3),
               Node(nodeid=2, pred=RealPred('cat', 'n', '1'), cfrom=4, cto=7,
                    sortinfo=InstanceSortinfo(pers='3', num='sg', ind='+')),
               Node(nodeid=3, pred=RealPred('chase', 'v', '1'), cfrom=8, cto=14,
                    sortinfo=EventSortinfo(sf='prop', tense='pres', mood='indicative')),
               Node(nodeid=4, pred=RealPred('the', 'q'), cfrom=15, cto=18),
               Node(nodeid=5, pred=RealPred('dog', 'n', '1'), cfrom=19, cto=22,
                    sortinfo=InstanceSortinfo(pers='3', num='sg', ind='+'))],
        links=[Link(start=1, end=2, rargname='RSTR', post='H'),
               Link(start=3, end=2, rargname='ARG1', post='NEQ'),
               Link(start=3, end=5, rargname='ARG2', post='NEQ'),
               Link(start=4, end=5, rargname='RSTR', post='H')],
        index=3,
        top=3)


def the_dog_chases_the_mouse():
    return DictDmrs(
        nodes=[Node(nodeid=1, pred=RealPred('the', 'q')),
               Node(nodeid=2, pred=RealPred('dog', 'n', '1'),
                    sortinfo=InstanceSortinfo(pers='3', num='sg', ind='+')),
               Node(nodeid=3, pred=RealPred('chase', 'v', '1'),
                    sortinfo=EventSortinfo(sf='prop', tense='pres', mood='indicative')),
               Node(nodeid=4, pred=RealPred('the', 'q')),
               Node(nodeid=5, pred=RealPred('mouse', 'n', '1'),
                    sortinfo=InstanceSortinfo(pers='3', num='sg', ind='+'))],
        links=[Link(start=1, end=2, rargname='RSTR', post='H'),
               Link(start=3, end=2, rargname='ARG1', post='NEQ'),
               Link(start=3, end=5, rargname='ARG2', post='NEQ'),
               Link(start=4, end=5, rargname='RSTR', post='H')],
        index=3,
        top=3)


def the_dog_chases_the_cat_and_the_mouse():
    return DictDmrs(
        nodes=[Node(nodeid=1, pred=RealPred('the', 'q')),
               Node(nodeid=2, pred=RealPred('dog', 'n', '1'),
                    sortinfo=InstanceSortinfo(pers='3', num='sg', ind='+')),
               Node(nodeid=3, pred=RealPred('chase', 'v', '1'),
                    sortinfo=EventSortinfo(sf='prop', tense='pres', mood='indicative')),
               Node(nodeid=4, pred=RealPred('the', 'q')),
               Node(nodeid=5, pred=RealPred('cat', 'n', '1'),
                    sortinfo=InstanceSortinfo(pers='3', num='sg', ind='+')),
               Node(nodeid=6, pred=GPred('udef_q')),
               Node(nodeid=7, pred=RealPred('and', 'c'),
                    sortinfo=InstanceSortinfo(pers='3', num='pl')),
               Node(nodeid=8, pred=RealPred('the', 'q')),
               Node(nodeid=9, pred=RealPred('mouse', 'n', '1'),
                    sortinfo=InstanceSortinfo(pers='3', num='sg', ind='+'))],
        links=[Link(start=1, end=2, rargname='RSTR', post='H'),
               Link(start=3, end=2, rargname='ARG1', post='NEQ'),
               Link(start=3, end=7, rargname='ARG2', post='NEQ'),
               Link(start=4, end=5, rargname='RSTR', post='H'),
               Link(start=6, end=7, rargname='RSTR', post='H'),
               Link(start=7, end=5, rargname='L-INDEX', post='NEQ'),
               Link(start=7, end=9, rargname='R-INDEX', post='NEQ'),
               Link(start=8, end=9, rargname='RSTR', post='H')],
        index=3,
        top=3)


def the_dog_chases_the_cat_and_the_cat_chases_the_mouse():
    return DictDmrs(
        nodes=[Node(nodeid=1, pred=RealPred('the', 'q')),
               Node(nodeid=2, pred=RealPred('dog', 'n', '1'),
                    sortinfo=InstanceSortinfo(pers='3', num='sg', ind='+')),
               Node(nodeid=3, pred=RealPred('chase', 'v', '1'),
                    sortinfo=EventSortinfo(sf='prop', tense='pres', mood='indicative')),
               Node(nodeid=4, pred=RealPred('the', 'q')),
               Node(nodeid=5, pred=RealPred('cat', 'n', '1'),
                    sortinfo=InstanceSortinfo(pers='3', num='sg', ind='+')),
               Node(nodeid=6, pred=RealPred('and', 'c'),
                    sortinfo=InstanceSortinfo(pers='3', num='pl')),
               Node(nodeid=7, pred=RealPred('the', 'q')),
               Node(nodeid=8, pred=RealPred('cat', 'n', '1'),
                    sortinfo=InstanceSortinfo(pers='3', num='sg', ind='+')),
               Node(nodeid=9, pred=RealPred('chase', 'v', '1'),
                    sortinfo=EventSortinfo(sf='prop', tense='pres', mood='indicative')),
               Node(nodeid=10, pred=RealPred('the', 'q')),
               Node(nodeid=11, pred=RealPred('mouse', 'n', '1'),
                    sortinfo=InstanceSortinfo(pers='3', num='sg', ind='+'))],
        links=[Link(start=1, end=2, rargname='RSTR', post='H'),
               Link(start=3, end=2, rargname='ARG1', post='NEQ'),
               Link(start=3, end=5, rargname='ARG2', post='NEQ'),
               Link(start=4, end=5, rargname='RSTR', post='H'),
               Link(start=6, end=3, rargname='L-INDEX', post='NEQ'),
               Link(start=6, end=3, rargname='L-HNDL', post='H'),
               Link(start=6, end=9, rargname='R-INDEX', post='NEQ'),
               Link(start=6, end=9, rargname='R-HNDL', post='H'),
               Link(start=7, end=8, rargname='RSTR', post='H'),
               Link(start=9, end=8, rargname='ARG1', post='NEQ'),
               Link(start=9, end=11, rargname='ARG2', post='NEQ'),
               Link(start=10, end=11, rargname='RSTR', post='H')],
        index=6,
        top=6)


def predsort():
    dmrs = DictDmrs()
    dmrs.add_node(Node(pred=Pred(), sortinfo=Sortinfo()))  # underspecified predicate and sortinfo
    return dmrs


def noun():
    dmrs = DictDmrs()
    dmrs.add_node(
        Node(pred=RealPred('?', 'n', 'unknown'), sortinfo=Sortinfo()))  # underspecified noun and sortinfo
    return dmrs
