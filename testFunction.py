import math


def passLambda(num, func):
    return func(num)


print(passLambda(2, lambda x: x**4))