"""
Handling string representations of structured lists.

The string representations of structured lists are modelled upon Logo lists,
which facilitate computing lists of words. For example, the string
representation of
    ['one', ['two', ['three', 'four']], 'five']
is
    'one [two [three four]] five'

This module provides the SList (which stands for structured list) class, which
has two methods for conversion between the string form and the SList object
form:
    __init__    Construct a SList object from the argument.
    __str__     Return a string representing the SList.
"""


class SList(list):
    def __init__(self, arg=None):
        """Construct a structured list object from the argument.

        If the argument is a list, then its members will be converted using
        their '__str__' method if they are not 'list' instances; if they are,
        they will be converted to structured lists recursively.

        >>> SList(['one', ['two', ['three', 'four']], 5])
        ['one', ['two', ['three', 'four']], '5']

        If the argument is a string, conversion works as in the following
        example:

        >>> SList('one [two [three four]] five')
        ['one', ['two', ['three', 'four']], 'five']

        If unbalanced brackets are detected, ValueError is raised.
        For example,

        >>> SList('aaa [bbb [ccc]')
        Traceback (most recent call last):
            ...
        ValueError: brackets not balanced
        """
        if arg is None:
            super().__init__()

        elif isinstance(arg, list):
            super().__init__(SList(elem) if isinstance(elem, list)
                             else str(elem) for elem in arg)

        elif isinstance(arg, str):
            opened = 0  # counts opened square brackets
            for (i, char) in enumerate(arg):
                if char == "[":
                    opened += 1
                    if opened == 1:  # the first bracket
                        left = i
                elif char == "]":
                    opened -= 1
                    if opened == 0:  # brackets closed
                        right = i
                        break
                    elif opened == -1:
                        # the first found bracket is a right bracket
                        raise ValueError("brackets not balanced")
            else:
                if opened > 0:
                    # an opening bracket was found it was not balanced
                    raise ValueError("brackets not balanced")
                else:
                    # no brackets were found
                    super().__init__(arg.split())
                    return
                    
            before = arg[:left]
            sublist = arg[left+1:right]
            after = arg[right+1:]
            super().__init__(before.split() + [SList(sublist)] + SList(after))

        else:
            raise TypeError("the argument to SList must be either a list "
                            "or a string")

    def __str__(self):
        """Return a string representing the structured list.

        >>> str(SList('one [two [three four]] five'))
        'one [two [three four]] five'
        """
        return ' '.join('[{0}]'.format(str(elem)) if isinstance(elem, list)
                        else elem for elem in self)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
