from price_history.crypto import (crypto_by_rank,
                                  get_price_history)

def main():
    price_history = get_price_history(crypto_by_rank, [1, 500])
    print(price_history)

if __name__ == "__main__":
    main()
