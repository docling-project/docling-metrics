from typing import Optional


def precision(reference: set[str], test: set[str]) -> Optional[float]:
    """
    Given a set of reference values and a set of test values, return
    the fraction of test values that appear in the reference set.
    In particular, return card(``reference`` intersection ``test``)/card(``test``).
    If ``test`` is empty, then return None.

    :type reference: set
    :param reference: A set of reference values.
    :type test: set
    :param test: A set of values to compare against the reference set.
    :rtype: float or None
    """
    if not hasattr(reference, "intersection") or not hasattr(test, "intersection"):
        raise TypeError("reference and test should be sets")

    if len(test) == 0:
        return None
    else:
        return len(reference.intersection(test)) / len(test)


def recall(reference: set[str], test: set[str]) -> Optional[float]:
    """
    Given a set of reference values and a set of test values, return
    the fraction of reference values that appear in the test set.
    In particular, return card(``reference`` intersection ``test``)/card(``reference``).
    If ``reference`` is empty, then return None.

    :type reference: set
    :param reference: A set of reference values.
    :type test: set
    :param test: A set of values to compare against the reference set.
    :rtype: float or None
    """
    if not hasattr(reference, "intersection") or not hasattr(test, "intersection"):
        raise TypeError("reference and test should be sets")

    if len(reference) == 0:
        return None
    else:
        return len(reference.intersection(test)) / len(reference)


def f_measure(
    reference: set[str], test: set[str], alpha: float = 0.5
) -> Optional[float]:
    """
    Given a set of reference values and a set of test values, return
    the f-measure of the test values, when compared against the
    reference values.  The f-measure is the harmonic mean of the
    ``precision`` and ``recall``, weighted by ``alpha``.  In particular,
    given the precision *p* and recall *r* defined by:

    - *p* = card(``reference`` intersection ``test``)/card(``test``)
    - *r* = card(``reference`` intersection ``test``)/card(``reference``)

    The f-measure is:

    - *1/(alpha/p + (1-alpha)/r)*

    If either ``reference`` or ``test`` is empty, then ``f_measure``
    returns None.

    :type reference: set
    :param reference: A set of reference values.
    :type test: set
    :param test: A set of values to compare against the reference set.
    :rtype: float or None
    """
    p = precision(reference, test)
    r = recall(reference, test)
    if p is None or r is None:
        return None
    if p == 0 or r == 0:
        return 0
    return 1.0 / (alpha / p + (1 - alpha) / r)
