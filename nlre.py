"""
docstring
"""

import re
from collections import deque
from keyword import iskeyword
from slist import SList


# global dictionary functions
functions = {}


class Pattern(list):
    def __init__(self, arg):
        slist = SList(arg)
        super().__init__(pattern_init(slist))

    def match(self, sen):
        sen = SList(sen)
        m = compare(self, sen)
        if m is not None:
            return UserMatch(m)
        else:
            return None

    def search(self, sen):
        sen = SList(sen)

        # try to match the pattern against a slice of the sentence,
        # starting from the 0th element, then the 1st element, and so on,
        # until the slice sen[len(sen):] is a empty string;
        # if all attempts are unsuccessful, return None
        for i in range(len(sen)+1):
            m = compare(self, sen[i:])
            if m is not None:
                return UserMatch(m)
        else:
            return None

    def finditer(self, sen):
        sen = SList(sen)

        # try to match the pattern against a slice of the sentence,
        # starting from the 0th element, then the 1st element, and so on,
        # until the slice sen[len(sen):] is a empty string;
        # if all attempts are unsuccessful, return None
        for i in range(len(sen)+1):
            m = compare(self, sen[i:])
            if m is not None:
                yield UserMatch(m)

    def findall(self, sen):
        return list(self.finditer(sen))


def pattern_init(slist):
    slist.reverse()
    proccessed = []
    while slist:
        elem = slist.pop()
        if isinstance(elem, SList):
            proccessed.append(pattern_init(elem))
        else:  # elem is a string
            if elem[0] in "?!#&{":
                proccessed.append(Special(elem, slist))
            else:
                proccessed.append(elem)
    return proccessed


# Pattern mathods aliased as level-module functions

def match(pat, sen):
    return Pattern(pat).match(sen)

def search(pat, sen):
    return Pattern(pat).search(sen)

def finditer(pat, sen):
    return Pattern(pat).finditer(sen)

def findall(pat, sen):
    return Pattern(pat).findall(sen)


class Match(list):
    def __init__(self, arg=None, name=None):
        if isinstance(arg, list):
            super().__init__(arg)
        elif isinstance(arg, str):
            super().__init__([arg])
        elif arg is None:
            super().__init__()

        if name:
            if is_valid_name(name):
                self.name = name
                setattr(self, self.name, [])
                # this attribute will store the slice that matches the named
                # special element
            else:
                raise ValueError("'{0}' is not a valid match ".format(name) +
                                "name; presumably it is not alphanumerical"
                                "or it is a Python keyword")

    def __add__(self, obj):
        if isinstance(obj, Match):
            self.extend(obj)  # combine both matches
            self.update(obj)
            if hasattr(self, 'name'):
                del self.name
                # self.name won't be needed anymore
            return self
        elif obj is None:
            return None
        else:
            raise TypeError("the object added to a Match object must be "
                            "either another Match or None")

    def append(self, obj):
        # if the match object has the attribute "name", elements are appended
        # both to the object and to the attribute list of the name "self.name"
        super().append(obj)
        if hasattr(self, 'name'):
            getattr(self, self.name).append(obj)

    def pop(self):
        # if the match object has the attribute "name", elements are popped
        # from both the object and from the attribute list of the name
        # "self.name"
        if hasattr(self, 'name'):
            getattr(self, self.name).pop()
        return super().pop()

    def update(self, other):
        self.__dict__.update(other.__dict__)

    def as_sublist(self):
        # return a match similar to self, the only difference in that
        # the matched text becomes a sublist
        container = Match()
        container.update(self)
        container.append(list(self))
        return container


def is_valid_name(s):
    return s.isidentifier() and not iskeyword(s)


class UserMatch:
    def __init__(self, m):
        self._m = str(SList(m))
        for (attr, value) in m.__dict__.items():
            setattr(self, attr, str(SList(value)))

    def __call__(self):
        return self._m


class Special:
    from_to = {
        '?': (0, 1),
        '!': (1, 1),
        '#': (0, float('inf')),
        '&': (1, float('inf'))
    }

    # the from-to notation
    curly_mn = re.compile(r"""
        \{      # Opening curly brace
        (\d*)   # `from` value (possibly empty)
        :       # Semicolon
        (\d*)   # `to` value (possibly empty)
        \}      # Closing curly brace
        (.*)    # The rest of the special element: match name and functions
    """, re.VERBOSE)

    # the n-elements notation
    curly_n = re.compile(r"""
        \{      # Opening curly brace
        (\d+)   # `from` value
        \}      # Closing curly brace
        (.*)    # The rest of the special element: match name and functions
    """, re.VERBOSE)

    params = re.compile(r'([:@])')
    # used for splitting `params` at colons or at-signs

    def __init__(self, s, slist):
        self.slist = slist
        self.s = s

        for metachar in self.from_to:
            if self.s.startswith(metachar):
                from_, to = self.from_to[metachar]
                rest = self.s[1:]
                break
        else:
            # compare the element with the `from-to` notation pattern 
            m = self.curly_mn.match(self.s)
            if m:
                # the `from-to` notation was used
                # name groups
                from_ = m.group(1)
                to = m.group(2)
                rest = m.group(3)

                # convert `from_` and `to` to numbers (or infinity)
                if from_:
                    from_ = int(from_)
                else:
                    from_ = 0

                if to:
                    to = int(to)
                else:
                    to = float('inf')
            else:
                # compare the element with the `n elements` notation pattern
                m = self.curly_n.match(self.s)
                if m:
                    # the `n elements` notation was used
                    # name groups
                    n = m.group(1)
                    rest = m.group(2)
                    n = int(n)
                    from_, to = n, n
                else:
                    raise ValueError("The '{0}' element ".format(self.s) + 
                                     "of the pattern is a string which "
                                     "starts with a metacharacter -- "
                                     "? ! # & or { -- but is not "
                                     "a valid special element.")

        if rest.startswith('?'):
            self.greedy = False
            rest = rest[1:]
        else:
            self.greedy = True

        # Extract the match name and functions from the special element
        # string.

        # Create functions lists

        elem_funs = []
        slice_funs = []

        # Check for functions which require an argument
        if rest.endswith(':'):
            # Create a special function using the 'pat's first element
            arg = self.getarg()
            elem_funs.append(lambda elem:
                                compare(arg, elem, toplevel=False))
            rest = rest[:-1]  # Remove the trailing colon
        elif rest.endswith('@'):
            arg = self.getarg()
            slice_funs.append(lambda slice_:
                                compare(arg, slice_, toplevel=False))
            rest = rest[:-1]
        elif rest.endswith(':in'):
            elem_funs.append(self.make_in())
            rest = rest[:-3]
        elif rest.endswith(':notin'):
            elem_funs.append(self.make_notin())
            rest = rest[:-6]
        elif rest.endswith('@in'):
            slice_funs.append(self.make_in())
            rest = rest[:-3]
        elif rest.endswith('@notin'):
            slice_funs.append(self.make_notin())
            rest = rest[:-6]

        del self.slist
        # It won't be needed anymore.

        # Split `rest` at colons and at-signs, and preserve those colons
        # and at-signs as elements in the resulting list.
        # If `rest` are
        # 'name:fun1:fun2@fun3@fun4'
        # then `splitted` will be
        # ['name', ':', 'fun1', ':', 'fun2', '@', 'fun3', '@', 'fun4']
        splitted = self.params.split(rest)

        # We are going to pop elements from the start of the list
        splitted = deque(splitted)

        # Name of the match
        self.name = splitted.popleft()

        # Extracting functions
        if not all(splitted):
            # `splitted` has empty strings as its elements
            raise ValueError("two delimiters (colon or at-sign) "
                             "cannot be adjacent")

        while splitted:
            # At the start of each loop run the length of `splitted` is even
            symbol = splitted.popleft()
            fun = splitted.popleft()

            if fun in {'in', 'notin'}:
                raise ValueError("Functions 'in' and 'nnotin' can only occur "
                                 "at the end of the special element string "
                                 "in {0}".format(self.s))

            if fun not in functions:
                raise KeyError("the function name '{0}' is not ".format(fun) +
                               "in the 'functions' dictionary")

            if symbol == ":":
                elem_funs.append(functions[fun])
            elif symbol == "@":
                slice_funs.append(functions[fun])

        self.from_, self.to = from_, to
        self.elem_funs = elem_funs
        self.slice_funs = slice_funs

    # Higher order functions for creating :in and :notin instances
    def make_in(self):
        arg = self.getarg()
        if not isinstance(arg, list):
            raise TypeError("the argument to :in must be a list "
                            "in {0}".format(self.s))

        def in_(elem):
            for subpat in arg:
                m = compare(subpat, elem, toplevel=False)
                if m is not None:
                    return m
            else:
                return None
        return in_

    def make_notin(self):
        arg = self.getarg()
        if not isinstance(arg, list):
            raise TypeError("the argument to :notin must be a list "
                            "in {0}".format(self.s))

        def notin(elem):
            for subpat in arg:
                m = compare(subpat, elem, toplevel=False)
                if m is not None:
                    return False
            else:
                return True
        return notin

    def getarg(self):
        try:
            arg = self.slist.pop()
        except IndexError:
            raise ValueError("a function in a special element "
                             "{0} requires an argument".format(self.s))
        if isinstance(arg, list):
            return pattern_init(arg)
        else:  # "arg" is a string
            return arg

    def match(self, pat, sen, toplevel):
        return SpecialMatching(self, pat, sen, toplevel).go()


class SpecialMatching:
    def __init__(self, special, pat, sen, toplevel):
        self.__dict__.update(special.__dict__)
        if self.greedy:
            self.go = self.greedy1
        else:
            self.go = self.nongreedy
        self.pat = pat.copy()
        self.sen = deque(sen)
        self.match = Match(name=self.name)
        self.toplevel = toplevel

    def greedy1(self):
        if self.to == 0:
            # maximal number of elements have been matched, test slices
            return self.greedy2()
        if not self.sen:
            return self.greedy2()
        # test sen[0] against the functions in elem_funs
        for fun in self.elem_funs:
            if not fun(self.sen[0]):
                # one of the functions evaluated to False
                return self.greedy2()
        else:
            self.from_ -= 1
            self.to -= 1
            self.match.append(self.sen.popleft())
            return self.greedy1()    

    def greedy2(self):
        if self.from_ > 0:
            # not enough elements have been matched
            return None
        # test the match against the functions in elem_funs
        slice_rvs = [fun(self.match) for fun in self.slice_funs]
        if all(slice_rvs):
            # all functions evaluated to True
            # compare the remaining part of the pattern with the remaining part
            # of the sentence
            m = compare(self.pat, list(self.sen), self.toplevel)
            if m is not None:
                # matching successful
                for rv in slice_rvs:
                    if isinstance(rv, Match):
                        self.match.update(rv)
                return self.match + m
            else:
                # move the last element back from 'match' to 'sen'
                if self.match:
                    self.from_ += 1
                    self.sen.appendleft(self.match.pop())
                    return self.greedy2()
                else:
                    return None
        else:
            # some of the functions returned evaluated to False
            # move the last element back from 'match' to 'sen'
            if self.match:
                self.from_ += 1
                self.sen.appendleft(self.match.pop())
                return self.greedy2()
            else:
                return None

    def nongreedy(self):
        if self.to < 0:
            return None
        if not self.sen:
            return None
        for fun in self.elem_funs:
            if not fun(self.sen[0]):
                return None
        if self.from_ > 0:
            self.from_ -= 1
            self.to -= 1
            self.match.append(self.sen.popleft())
            return self.nongreedy()
        else:
            slice_rvs = [fun(self.match) for fun in self.slice_funs]
            if all(slice_rvs):
                m = compare(self.pat, list(self.sen), self.toplevel)
                if m is not None:
                    # matching successful
                    for rv in slice_rvs:
                        if isinstance(rv, Match):
                            self.match.update(rv)
                    return self.match + m
                else:
                    self.from_ -= 1
                    self.to -= 1
                    self.match.append(self.sen.popleft())
                    return self.nongreedy()
            else:
                self.from_ -= 1
                self.to -= 1
                self.match.append(self.sen.popleft())
                return self.nongreedy()


def compare(pat, sen, toplevel=True):
    if toplevel:
        if not pat:
            return Match()
        elif isinstance(pat[0], Special):
            special = pat[0]
            return special.match(pat[1:], sen, toplevel)
        elif not sen:
            return None
    else:
        if not pat and not sen:
            # comparing the pattern has finished successfully
            return Match()
        elif not pat:
            # the pattern and the sentence are of unequal lengths
            return None
        elif isinstance(pat[0], Special):
            special = pat[0]
            return special.match(pat[1:], sen, toplevel)
        elif not sen:
            return None

    # the pattern and the sentence are non-empty

    if isinstance(pat[0], str) and isinstance(sen[0], str):
    # pat[0] and sen[0] are regular words
        if pat[0].lower() == sen[0].lower():
            # pat[0] and sen[0] are equal, case-insentitive;
            # compare the remaining part of the pattern
            # and the sentence
            return Match(sen[0]) + compare(pat[1:], sen[1:], toplevel)
        else:
            return None
    elif isinstance(pat[0], list) and isinstance(sen[0], list):
        # pat[0] and sen[0] are sublists
        m = compare(pat[0], sen[0], toplevel=False)
        if m is not None:
            # pat[0] and sen[0] match each other;
            # compare the remaining part of the pattern
            # and the sentence
            return m.as_sublist() + \
                   compare(pat[1:], sen[1:], toplevel)
        else:
            return None
    else:
        # pat[0] and sen[0] are of different types
        return None
