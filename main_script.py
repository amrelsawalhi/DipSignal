from etl.fetch_binance import main as fetch_binance_main
from etl.fetch_fgi import main as fetch_fgi_main
from etl.fetch_macro import main as fetch_macro_main
from etl.news import main as news_main
from llama.llama_prediction import main as llama_prediction_main
from llama.llama_news import process_batches as llama_news_main
import sys


sys.stdout.reconfigure(encoding='utf-8')

if __name__ == "__main__":
    # fetch data from various sources
    fetch_binance_main()
    fetch_fgi_main()
    fetch_macro_main()
    news_main()


    # Run Llama predictions
    llama_prediction_main() 
    llama_news_main()
    

  
    

    print("All tasks completed successfully.")