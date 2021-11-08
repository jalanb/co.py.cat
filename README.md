co.py.cat
=========

An implementation of [Douglas Hofstadter](http://prelectur.stanford.edu/lecturers/hofstadter/)'s copycat algorithm. The copycat algorithm is explained [on Wikipedia](https://en.wikipedia.org/wiki/Copycat_%28software%29), and is one of a group of algorithms including [metacat, musicat, seqsee, ...](https://github.com/Alex-Linhares/FARGonautica)

This implementation is a copycat of Scott Boland's [Java implementation](http://itee.uq.edu.au/~scottb/_Copycat/), but re-written into Python. It's not a direct translation, more "based on a true story". I did not carry over the GUI, as GUIs restrict the platform too much and this version can more usefully be imported for use by other Python scripts or run from command line.

In cases where I could not grok the Java implementation easily I took ideas from the [LISP implementation](http://web.cecs.pdx.edu/~mm/how-to-get-copycat.html), or directly from [Melanie Mitchell](https://en.wikipedia.org/wiki/Melanie_Mitchell)'s "[Analogy-Making as Perception](http://www.amazon.com/Analogy-Making-Perception-Computer-Melanie-Mitchell/dp/0262132893/ref=tmm_hrd_title_0?ie=UTF8&qid=1351269085&sr=1-3)"

I also tried to make the code "more pythonic".

Installation
------------

There are no particular installation instructions, just clone and run, e.g.

```sh
$ git clone https://github.com/jalanb/co.py.cat.git
$ cd co.py.cat
$ python3 -m copycat abc abd ijk
```

Running
-------

The script takes 3 or 4 arguments.

- The first two are a pair of strings with some change, for example "ABC" and "ABD".
- The third is a triplet which the script should try to change analogously
- The fourth is the number of iterations that will be attempted.
  - If left out then it defaults to `1`
  - A higher number of iterations will produce more answers
 

For example the following run uses a single iteration to give the answer `PQS`

```sh
$ python3 -m copycat ABC ABD PQR
PQS: 1 (average time 0.3 seconds, average temperature 14.43)
```

And an example of trying 10 iterations can produce output like

```sh
$ python3 -m copycat ABC ABD PQQRRR 10
PQQRRRR: 2 (average time 0.65 seconds, average temperature 17.1)
PQQRRS: 5 (average time 0.82 seconds, average temperature 17.38)
PQQSSS: 3 (average time 1.29 seconds, average temperature 24.83)
```
This shows that the program considered the solution as

- `PQQRRRR` 2 times
- `PQQRRS` 5 times
- `PQQSSS` 3 times 

Of these `PQQRRRR` might be considered the "best" answer because

1. The average temperature is lowest (i.e. this is the "most obvious" answer)
2. The average time is also lowest (i.e. needed the least amount of "extra work")

On the other hand `PQQRRS` might be considered "best" because it was the accepted solution most often.

For me: `PQQRRRR` is the "best" answer, because increasing the number of `Q`s from 3 to 4 is the "best" analogy to increasing the 3rd letter (`C`) to the 4th letter (`D`). However the other 2 answers also seem "quite good" because `PQQRRS` is the most direct (just increase the last letter), and `PQQSSS` is also fairly direct (increase letter in the last group).

This example output emphasizes that Copycat is not intended to produce a single definitive answer to an analogy problem, but to explore solutions, and try different strategies to find them. It also shows the different "levels" that Copycat considered in this problem: changing letters, or groups of letters, or both.

Note that there is no "correct" answer to an analogy problem - there are arguments to be made for each of `PQQRRRR`, `PQQRRS` and `PQQSSS` above, and only one's own preferences can decide that one of them is "best".

Importing
---------
The script can also be imported and run from within Python, e.g.

```python
>>> from copycat import copycat
>>> answers = copycat.run("abc", "abd", "pqqrrr", 10)
>>> print(answers)
{'pqqrrrr': {'avgtemp': 18.320790853668182, 'avgtime': 759.0, 'count': 1},
 'pqqrrs': {'avgtemp': 38.58653638621074, 'avgtime': 1294.1666666666667, 'count': 6},
 'pqqsss': {'avgtemp': 37.86964564086443, 'avgtime': 1642.6666666666667, 'count': 3}}
```

Thanks
======
A big "Thank You" for

Curation
--------
* @[Alex-Linhares](https://github.com/Alex-Linhares/FARGonautica#projects-to-join-here-desiderata)

Contributions
-------------
* @[Quuxplusone](https://github.com/Quuxplusone) for [reducing spew](https://github.com/jalanb/co.py.cat/pull/8)
* @[jtauber](https://github.com/jtauber) for [cleaning up](https://github.com/jalanb/co.py.cat/pull/3)

Forks
-----
* @[Alex-Linhares](https://github.com/Alex-Linhares/co.py.cat)
* @[ayberkt](https://github.com/ayberkt/co.py.cat)
* @[dproske](https://github.com/dproske/co.py.cat)
* @[erkapilmehta](https://github.com/erkapilmehta/co.py.cat)
* @[horacio](https://github.com/horacio/co.py.cat)
* @[josephfosco](https://github.com/josephfosco/co.py.cat)
* @[jtauber](https://github.com/jtauber/co.py.cat)
* @[OrmesKD](https://github.com/OrmesKD/co.py.cat)
* @[Quuxplusone](https://github.com/Quuxplusone/co.py.cat)
* @[qython](https://github.com/qython/co.py.cat)
* @[sjolicoeur](https://github.com/sjolicoeur/co.py.cat)
* @[skaslev](https://github.com/skaslev/co.py.cat)

You geeks make it all so worthwhile.

Links
=====

Readers who got this far will definitely enjoy analogising this project with @[Alex-Linhares](https://github.com/Alex-Linhares)'s [collection of FARGonautica](https://github.com/Alex-Linhares/FARGonautica#projects-to-join-here-desiderata), a collection of computational architectures that have been developed frm
Douglas Hofstadter's group's research in Fluid Concepts & Creative Analogies. 

They've got Lisp (lotsa (Lisp)), Python, C++, Java, even Perl. If you know one of those languages, then you too can be a FARGonaut. 

See Also
--------
1. "[The Copycat Project: An Experiment in Nondeterminism and Creative Analogies](http://dspace.mit.edu/handle/1721.1/5648)" by [Hofstadter, Douglas](https://en.wikipedia.org/wiki/Douglas_Hofstadter#Academic_career)
1. "[Analogy-Making as Perception](http://www.amazon.com/Analogy-Making-Perception-Computer-Melanie-Mitchell/dp/0262132893/ref=tmm_hrd_title_0?ie=UTF8&qid=1351269085&sr=1-3)" by [Mitchell, Melanie](https://en.wikipedia.org/wiki/Melanie_Mitchell)
1. Arthur O'Dwyer ([Quuxplusone on GitHub]()) has further cleaned and extended this code (including a GUI) in a fork available [here](https://github.com/Quuxplusone/co.py.cat).

Badges
======
[![Build Status](https://travis-ci.org/jalanb/co.py.cat.svg?branch=master)](https://travis-ci.org/jalanb/co.py.cat)

