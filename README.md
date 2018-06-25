# JASP - Just Another Shitty Lisp

This is a small toy LISP dialect I've written for purely (self) educational purposes. It's not meant to be a language used
in the wild--heck, it's written in Python! An interpreter inside an interpreter, performance must be pretty abysmal!

## The language

I'd lie if I claimed that I'm an expert at LISPS and its numerous dialects, so it's probably safest for me the say that
JASP is not a real LISP. It currently doesn't even support macros (and perhaps it never will as I never really
understood or used them (in that order)), tail call optimization, nor a whole host of builtin functions! But hey, it's
a work-in-progress.

## Whirlwind tour of the language

The basics are just as you'd expect:
```
(+ 1 (* 2 3))
```

Variable binding:
```
(let name (/ 8 2))
```

Lists (or vectors):
```
(let vec [1 23 (+ 2 34) (+ "hello" "world")])
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
```

You can also use multiple statements within if branches and function bodies with the `do` function, which evaluates all
its arguments and returns the last one:
```
(fn function-name (param1 param2)
    (do (let tmp param1)
        (+ tmp param1)))
```
