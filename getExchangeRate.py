def getExchangeRateDict():
    return dict(line.strip().split() for line in open('currencyList'))


def getExchangeRate(dictionary, currency):
    if currency == 'USD':
        return 1
    elif currency in dictionary:
        return float(dictionary[currency])
    else:
        raise Exception("no currency found")
