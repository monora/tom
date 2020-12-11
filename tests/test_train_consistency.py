import pytest
import copy

from tom.tom import Train, TomError, RouteSection


def test_train_section_ids_not_unique(ac_to_emm: RouteSection):
    s1 = ac_to_emm
    s2 = copy.copy(s1)
    with pytest.raises(TomError, match=r"Section IDs.*not unique: .0, 0.*"):
        Train('12AB', sections=[s1, s2])

    # Fix errors
    s2.section_id = 1
    s2.origin = s2.origin + "_"
    t = Train('12AB', sections=[s1, s2])
    assert [s.section_id for s in t.sections] == [0, 1]


def test_train_section_keys_not_unique(ac_to_emm: RouteSection):
    s1 = ac_to_emm
    s2 = copy.copy(s1)
    # Avoid id check failing
    s2.section_id = 1
    with pytest.raises(TomError, match=r"Section keys.*not unique:.*"):
        Train('12AB', sections=[s1, s2])

    # Fix error
    s2.origin = s2.origin + "_"
    t = Train('12AB', sections=[s1, s2])
    assert s1.section_key()[0][0] == 'AC'
    assert s2.section_key()[0][0] == 'AC_'
