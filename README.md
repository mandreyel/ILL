# ILL - I LIKE LISPS

This is a small toy LISP dialect I've written for purely (self) educational purposes. It's not meant to be a language used
in the wild--heck, it's written in Python! An interpreter inside an interpreter, performance must be pretty abysmal!

I'd lie if I claimed that I'm an expert at LISPS and its numerous dialects, so it's probably safest for me the say that
ILL is not a real LISP (hence the name). It currently doesn't even support macros (and perhaps it never will as I never really
understood or used them (in that order)), tail call optimization, nor a whole host of builtin functions! But hey, it's
a work-in-progress.

## Whirlwind tour of the language

The basics are just as you'd expect:
```
(+ 1 (* 2 3))
```

Types:
- bool: `true` or `false`
- number: `2` or `2.02`
- string: `"a utf8 string"`
- vector: `[1 2 3 "four"]`
- map: `{"key": "value"}`

Variable binding:
```
(let greeting "hello world")
(let name (/ 8 2))
(let vec [1 23 (+ 2 34) (+ "hello" "world")])
(let map {"key1":1 2:2 (+ 2 3):3})
```

Conditional branching:
```
(if (= 2 2 2)
    2
    "not 2")
```

Function definition:
```
(fn fib (n)
    (if (<= n 2)
        1
        (fib (- n 1) (- n 2))))

(fn greeter () "hello!")

(fn adder (a b) (+ a b))
```

You can loop with recursion, but since tail call optimization is not yet implemented (and I prefer explicit loop
constructs anyway), a while keyword is provided:
```
(let i 0)
(while (< i 10)
    (do (print i)
        (let i (+ i 1))))
```

Looping through collection elements is also supported:
```
(let list [1 2 3 4 5])
(each (list element)
    (print element))
```
or if the iterable is a map:
```
(let answers {
    "The Answer to the Ultimate Question of Life, the Universe, and Everything": 42})
(each (answers key val)
    (print key ": " val))
```


You can also use multiple statements within if branches and function bodies with the `do` function, which evaluates all
its arguments and returns the last one:
```
(fn function-name (param1 param2)
    (do (let tmp param1)
        (+ tmp param1)))
```

Since everything is an expression and thus evaluates to a value, you can use function definitions within expressions
as anonymus functions, like so:
```
((fn adder (a b) (+ a b)) 3 4)
```

## Running it

Just execute `./ill/repl.py` for the repl and `./ill/ill.py $filename` to run source code. Yes, it's not very
ergonomic. Yet.

## Useful things that have been built with ILL:
