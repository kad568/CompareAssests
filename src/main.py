from price_history.crypto import (crypto_by_rank,
                                  get_price_history,
                                  read_price_history)

def main():
    # price_history = get_price_history(crypto_by_rank, [1, 100])
    read_price_history("test.db")

if __name__ == "__main__":
    main()