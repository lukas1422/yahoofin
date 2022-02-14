def getExchangeRateDict():
    return dict(line.strip().split() for line in open('list_currency'))


def getExchangeRate(dictionary, listingCurr, bsCurr):
    currency = listingCurr + bsCurr
    if listingCurr == bsCurr:
        return 1
    elif currency in dictionary:
        return float(dictionary[currency])
    else:
        raise Exception("getExchangeRate, no currency found", listingCurr, bsCurr)
