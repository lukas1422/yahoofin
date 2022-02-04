def getExchangeRateDict():
    return dict(line.strip().split() for line in open('list_currency'))


def getExchangeRate(dictionary, firstCurr, secondCurr):
    currency = firstCurr + secondCurr
    if currency == 'USDUSD':
        return 1
    elif currency in dictionary:
        return float(dictionary[currency])
    else:
        raise Exception("no currency found")
