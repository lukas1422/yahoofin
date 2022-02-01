import yahoo_fin.stock_info as si
import datetime
from prelimYahoo import processStock

fileOutput = open('reportList', 'w')
fileOutput.write("\n")

with open("tickerList", "r") as file:
    lines = file.read().rstrip().splitlines()

for comp in lines:
    try:
        info = si.get_company_info(comp)
        country = info.loc["country"][0]
        sector = info.loc['sector'][0]
        bs = si.get_balance_sheet(comp)
    except Exception as e:
        print(comp, "exception on info or BS")
    else:
        if (country.lower()) == "china":
            print(comp, "NO CHINA")
        else:
            try:
                totalCurrentAssets = bs.loc["totalCurrentAssets"][0]
                totalLiab = bs.loc["totalLiab"][0]
            except Exception as e:
                print("error when getting data ", comp, e)
            else:
                netnet = totalCurrentAssets - totalLiab
                try:
                    assert netnet > 0
                except AssertionError as ae:
                    print(datetime.datetime.now().time().strftime("%H:%M"), comp, "fails assertion", ae)
                else:

                    outputString = "Netnet" + comp + " " + country + " " + sector + " " + processStock(si, comp)

                    print(outputString)
                    fileOutput.write(outputString + '\n')
                    fileOutput.flush()
