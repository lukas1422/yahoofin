


def main():
    with open("tickerList", "r") as grilled_cheese:
        lines = grilled_cheese.read().splitlines()
        print(lines)


if __name__ == "__main__":
    main()
