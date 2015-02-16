NATURAL LANGUAGE PATTERN MATCHER

The program implements a regex-like pattern matcher which operates on words rather than characters, and thus is convenient for working with natural language. It supports named groups, subpatterns, and custom predicates.

'nlre' stands for Natural Language Regular Expressions. The syntax is meant
to resemble standard regular expressions, except that it uses words as units,
instead of characters.

To get a grasp of how the module works, read
    http://www.cs.berkeley.edu/~bh/v2ch7/match.html
But note that the version described there is slightly different – and written
in Logo, a different programming language!
An acquintance with standard regex can also be helpful.

IMPORTANT INFORMATION
If you use only the end-user interface and you don't need to understand
precisely how the module works, you should remember that there are certain
limitations as to what is a 'regular word' in a pattern. Due to the nlre
syntax, regular words (by 'words' we mean sequences of non-whitespace
characters) can't begin with any of the metacharacters: . ? + * { 
You also can't use square brackets except as part of the nlre syntax.
An accidental use of any of those may result in an error.


Below certain technical issues are discussed.

1. How many words?

A pattern is defined by a string containing both regular words and `special
elements` which are words beginning with so-called metacharacters, whose
meaning is borrowed from standard regex. `Special elements` may represent an
arbitrary number of elements in the compared sentence. Unlike in standard
regex, where characters to be repeated by metacharacters must be specified,
nlre symbols always operate on words. For example:

'. said in a ? voice: +'

matches: one word, then 'said in a', then zero or one word, then 'voice:',
then one or more words.

Similarly, * matches any number of words, {m,n} matches from m to n words,
and {n} matches n words.

Note that each symbol can be replaced by the curly braces notation.

The symbols . ? + * {m,n} {n} are called 'greedy' — they match as many words
as possible. There are also 'non-greedy' versions which do the opposite — they
match as few words as possible: ?? +? *? {m,n}?

2. Using the module

Before a pattern is actually compared against a string, it is parsed so that
it can be easily handled by the nlre engine. You can save a parsed pattern as
a 'pattern object' which can afterwards be used for performing comparisons.
Thus parsing is done only once even if you use the pattern several times.
Here's what a sample statement looks like:

p = nlre.parse('pattern sentence')

p is now a pattern object, which has several methods:

p.match('some sentence') will compare the pattern against the argument
string, starting from the beginning of that string.

p.search('some sentence') will do a similar thing, but if the pattern
doesn't match at the very beginning of the argument string, then another
attempt will be made, this time starting from the second word of the argument
string, and so on.

In either case, if a match has been found, a 'match object' is returned;
otherwise, the return value is None. The following scenorio is therefore
common:

p = nlre.parse(...)
m = p.match('string goes here')
if m:
    print('Match found: ', m)
else:
    print('No match')

The 'match' attribute of a match object stores the fragment of the compared
string that matched the pattern.

Pattern objects have two more methods:

p.finditer(sentence) will return a generator object containing all matches
of the pattern within the sentence.

p.findall(sentence) works as p.finditer, except it returns a list of matches.

Nonetheless, you don’t have to create a pattern object and call its methods;
the nlre module also provides top-level functions called match(), search(),
finditer(), and findall().

>>>
>>> m = nlre.match('.', 'one two')
>>> m
'one'

3. Saving specific words

It is possible to save the words that correspond to a given metacharacter.
Let's consider an example:

>>>
>>> p = nlre.parse('one *middle four')
>>> m = p.match('one two three four')
>>> m.middle
'two three'

In the pattern * is immediately followed by a name, which becomes
an attribute of the match object and allows to access the words
represented by * easily.

This applies to all repeating symbols.

4. Patterns and sentences as structured lists.

Although patterns, sentences and matches are read and presented to the user as
strings, the actual computation is performed on structured lists created from
those strings. In the simpliest case, a string is split with whitespace as
separator to form a list of words. In addition, left square bracket marks the
beginning of a sublist, and the corresponding right square bracket marks its
end. Any level of nesting is allowed. For example, the string

'[three two one] go'

is transformed into

[['three', 'two', 'one'], 'go']

When a match object returns a text extract, a reverse proccess is done and
the elements are again joined into

'[three two one] go'

Sublists may serve as regular elements of patterns and sentences or as part of
nlre syntax: they are used as arguments to :in and :notin special functions,
which are desribed in further sections. The use of the phrase 'pattern
element' in the previous sentence was important. It is not always true to say
that patterns and sentences are made out of words; they are made out of
elements, which can be either words or sublists.

5. Testing words

Sometimes we want to match only words that meet a certain condition. There are
two kinds of tests which can be performed on potentially matching words.

If we want to test consequtive single words, we can use *:fun notation, where
* could be any other metacharacter and fun is the name of a function which
takes one word as its argument and returns either True or False. The
metacharacter will match consecutive words only as long as fun(word) returns
True. Any number of functions can be specified: *fun1:fun2:…

However, if we need to test a whole slice of sentence which can potentially
be matched by a given metacharacter, we should use the *@fun1@fun2@… notation,
where fun1, fun2, … are functions which take a list as its argument and return
True or False.

The two kinds of test can be combined. Let's consider an example of comparing

'*:islower@headtail'

against the sentence

'a b a c D'

where islower accepts only lowercase words and headtail only returns True
when the first member of the slice is equal to its last member.

At first, the : functions — islower — is taken into account, and at this stage
the 'a b a c' slice is matched. Then the slice is tested with headtail
(remember that the program sees the slice as a list of words). The first
attempt results in headtail returning False, so the last member of the slice
is popped. headtail accepts the 'a b a' slice and that's what is matched
by the *.

In order to use functions in nlre special elements, you need to update
the 'functions' dictionary existing in the module namespace. Note that
what is referred to as functions in the nlre syntax are in fact mere strings
delimited by colons or at-signs; therefore, you need to map those strings
to actual functions, which is done by the 'functions' dictionary. For example:

nlre.functions['fun'] = fun

If a string is not mapped, KeyError is raised.

A metacharacter expression can also have : as its last character. An example:

'?: dog'

Such pattern creates a so-called `special function` which is equivalent to 
	'?:fun', where
	fun = lambda elem: _compare(elem, 'dog')
In other words, potentially matching elements are compared against the next
element of the pattern. Note that technically 'dog' in the above example
is not a regular member of the pattern; instead, it is the argument
of the previous expression.

The ending semicolon is typically used with ? to indicate that the next
element is optional, as in the example above.

There are two more functions which require an argument: :in and :notin. They
check if there is a pattern that matches a given element in the argument
sublist, or if there is not one, respectively. For example

'.:in [blue yellow] flower'

matches sentences 'blue flower' and 'yellow flower'.

Naming and testing can be freely combined, like in

'*name:fun1@fun2:fun3: […]'

Note that as the
*: element
*:in [list] or *:notin [list]
*@in [list] or *@notin [list]
notations all require an argument and therefore cannot be used together
as such. You can, however, write functions whose meaning is analogous
to that of the above notations and apply them using the *:fun notation.

5. Case-sensitivity.

Comparisons are case-insensitive. However, when retrieving matches,
the original case is always preserved. For example, if we compare the pattern

'John .second Paul'

against the sentence

'John George Paul'

then the 'second' entry of the match dict has value 'George', not 'george'.

10. Error handling

If pattern elements which appear to have special meaning turn out to have
illegal syntax, ValueError is raised.
