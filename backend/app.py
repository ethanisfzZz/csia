
from flask import Flask
import pandas as pd

app = Flask(__name__)
ending = False
df = pd.read_csv("./dataframe/order.csv")
print(df)


@app.route('/')
def hello_world():
    return 'Hello World'

@app.route('/end')
def signal_end():
    ending = True
    return "ended"

def main_loop():
    #threshold

    while (not ending):
        
        # fetch from Binance


        # write to pandas w/ csv

        # make your decision



        sleep(3600)

        break



if __name__ == '__main__':

    main_loop()

    # Start our API
    app.run(debug=True)

    # make synchronize
