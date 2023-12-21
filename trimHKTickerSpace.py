
# writing to file
#file1 = open('list_HK_Tickers.txt', 'w')
#file1.writelines(L)
#file1.close()

# Using readlines()
file1 = open('list_HK_Tickers', 'r', encoding='gbk')
Lines = file1.readlines()

count = 0
# Strips the newline character
for line in Lines:
    count += 1
    print("Line{}: {}".format(count, line.strip()))