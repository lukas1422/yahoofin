import math


def passLambda(num, func):
    return func(num)


def getNumberFunction(num):
    return lambda x: x + num


print(getNumberFunction(3)(3))

# print(passLambda(2, lambda x: x ** 4))
