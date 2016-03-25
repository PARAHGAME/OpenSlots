#!/usr/bin/env python3

import os
import sys
print(os.path.abspath('./'))
sys.path.append(os.path.abspath('./'))

from openslots.core import Symbol, Reel, LeftPay


# This test is derived from the mathematical model of the Atkins Diet slot
# machine game, designed by Wizard of Odds Consulting, Inc. in 2008 as an
# example of how slot machine probabilities and paybacks work.
# See http://wizardofodds.com/games/slots/atkins-diet/ for details


# define test Symbols

atkins = Symbol('Atkins', True, ['Scale'])
steak = Symbol('Steak')
ham = Symbol('Ham')
wings = Symbol('Wings')
sausage = Symbol('Sausage')
eggs = Symbol('Eggs')
butter = Symbol('Butter')
cheese = Symbol('Cheese')
bacon = Symbol('Bacon')
mayo = Symbol('Mayo')
scale = Symbol('Scale')

reel1 = Reel([scale, mayo, ham, sausage, bacon, eggs, cheese, mayo, sausage, butter,
         wings, bacon, eggs, mayo, steak, wings, butter, cheese, eggs, atkins,
         bacon, mayo, ham, cheese, eggs, scale, butter, bacon, sausage, wings,
         steak, butter])
reel2 = Reel([mayo, wings, steak, sausage, cheese, mayo, ham, butter, bacon, steak,
         sausage, mayo, ham, atkins, butter, eggs, cheese, bacon, sausage, wings,
         scale, mayo, butter, cheese, bacon, eggs, wings, mayo, steak, ham,
         cheese, bacon])
reel3 = Reel([ham, butter, eggs, scale, cheese, mayo, butter, ham, sausage, bacon,
         steak, wings, butter, mayo, cheese, sausage, eggs, bacon, mayo, wings,
         ham, sausage, bacon, cheese, eggs, atkins, wings, bacon, butter, cheese,
         mayo, steak])
reel4 = Reel([ham, cheese, atkins, scale, butter, bacon, cheese, sausage, steak, eggs,
         bacon, mayo, sausage, cheese, butter, ham, mayo, bacon, wings, sausage,
         cheese, eggs, butter, wings, bacon, mayo, eggs, ham, sausage, steak,
         mayo, bacon])
reel5 = Reel([bacon, scale, steak, ham, cheese, sausage, butter, bacon, wings, cheese,
         sausage, ham, butter, steak, mayo, eggs, sausage, ham, atkins, butter,
         wings, mayo, eggs, ham, bacon, butter, steak, mayo, sausage, eggs,
         cheese, wings])

reels = reel1, reel2, reel3, reel4, reel5
rules = []

# atkins linepays
for i, p in enumerate((0, 5, 50, 500, 5000)):
    if p:
        rules.append(LeftPay(atkins, i+1, p))

# steak linepays
for i, p in enumerate((0, 3, 40, 200, 1000)):
    if p:
        rules.append(LeftPay(steak, i+1, p))

# ham linepays
for i, p in enumerate((0, 2, 30, 150, 500)):
    if p:
        rules.append(LeftPay(ham, i+1, p))

# buffalo wings linepays
for i, p in enumerate((0, 2, 25, 100, 300)):
    if p:
        rules.append(LeftPay(wings, i+1, p))

# sausage and eggs linepays
for i, p in enumerate((0, 0, 20, 75, 200)):
    if p:
        rules.append(LeftPay(sausage, i+1, p))
        rules.append(LeftPay(eggs, i+1, p))

# butter and cheese linepays
for i, p in enumerate((0, 0, 15, 50, 100)):
    if p:
        rules.append(LeftPay(butter, i+1, p))
        rules.append(LeftPay(cheese, i+1, p))

# bacon and mayonnaise linepays
for i, p in enumerate((0, 0, 10, 25, 50)):
    if p:
        rules.append(LeftPay(bacon, i+1, p))
        rules.append(LeftPay(mayo, i+1, p))


def test_LeftPay_payback():
    payback_contrib = 0.0
    for rule in rules:
        if rule.mode == 'line':
            s = rule.symbol
            payback = rule.payback(reels)
            print("{}x {}: {}".format(rule.n, s, payback))
            payback_contrib += payback[1]
    print("Total linepay payback contribution: {}".format(payback_contrib))


if __name__ == '__main__':
    test_LeftPay_payback()
