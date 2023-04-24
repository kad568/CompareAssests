from price_history import crypto

def main():
    crypto_index_file_path = "top_5_crypto.csv"

    crypto.crypto_by_rank([1, 100], crypto_index_file_path)
    crypto_index_df = crypto.get_price_history(crypto_index_file_path)
    print(crypto_index_df["ticker"].to_list())

if __name__ == "__main__":
    main()
