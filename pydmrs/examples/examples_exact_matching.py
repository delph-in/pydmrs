from pydmrs.components import RealPred
from pydmrs.matching.exact_matching import dmrs_exact_matching
import pydmrs.examples.examples_dmrs as examples


if __name__ == '__main__':

    # "the" - "the dog chases the cat"
    assert len(list(dmrs_exact_matching(examples.the(), examples.the_dog_chases_the_cat()))) == 2

    # "the cat" - "the dog chases the cat"
    assert len(list(dmrs_exact_matching(examples.the_cat(), examples.the_dog_chases_the_cat()))) == 1

    # "dog cat" - "the dog chases the cat"
    assert len(list(dmrs_exact_matching(examples.dog_cat(), examples.the_dog_chases_the_cat()))) == 1

    # "the dog chases the cat" - "the dog chases the cat"
    assert len(list(dmrs_exact_matching(examples.the_dog_chases_the_cat(), examples.the_dog_chases_the_cat()))) == 1

    # "the cat chases the dog" - "the dog chases the cat"
    assert not len(list(dmrs_exact_matching(examples.the_cat_chases_the_dog(), examples.the_dog_chases_the_cat())))

    # "the dog chases the cat" - "the dog chases the cat and the mouse"
    assert not len(list(dmrs_exact_matching(examples.the_dog_chases_the_cat(), examples.the_dog_chases_the_cat_and_the_mouse())))

    # "the dog chases the cat" - "the dog chases the cat and the cat chases the mouse"
    assert len(list(dmrs_exact_matching(examples.the_dog_chases_the_cat(), examples.the_dog_chases_the_cat_and_the_cat_chases_the_mouse()))) == 1

    # "the cat" - "the dog chases the cat and the cat chases the mouse"
    assert len(list(dmrs_exact_matching(examples.the_cat(), examples.the_dog_chases_the_cat_and_the_cat_chases_the_mouse()))) == 2

    # "dog cat" - "the dog chases the cat and the cat chases the mouse"
    assert len(list(dmrs_exact_matching(examples.dog_cat(), examples.the_dog_chases_the_cat_and_the_cat_chases_the_mouse()))) == 2

    # predsort - "the dog chases the cat"
    assert len(list(dmrs_exact_matching(examples.predsort(), examples.the_dog_chases_the_cat()))) == 5

    # noun - "the dog chases the cat"
    assert len(list(dmrs_exact_matching(examples.noun(), examples.the_dog_chases_the_cat()))) == 2
