# compare-cryptos

## Overview

A python package for investors and traders to compare assests against the overall asset class or group.
The comparisons are based on technical indicators derived from asset price and volume history.
Such as the relative strength index (RSI), an indicator commonly used to asses whether an asset is 
over or underbought. This package could be useful when doing technical analysis in the context of an asset class or group.

In some ways this is similar to popular portfolio optimisation methods that find a collection of assets 
with the highest historical returns but, the lowest historical volatility. Rather this method aims to use 
multiple types of technical indicators. Portfolio optimisation methods mostly ignore the following:

- volume indicators
- trend indicators
- momentum indicators

Using these additional indicators in isolation or together with volatility indicators may yeild an improved risk 
adjusted returns estimations. However, this may likely not be the case as fundamental analysis is not considered in these methods.
Something traditional investors may be in stern oppositon to. The validity of technical analysis and the indicators used will not 
be assesed here. During the development of this packege, this fact is acknowleged and development is agnostic to this.
This package soley served the purpose of offering traders and investors another research tool in their arsenal.

For more advanced users the package is general enough to add custom indicators. This may be user or 3rd party indicators.

## Software architecture

- main.py
- src
    - price history
    - comparisons
- docs
- tests

## Roadmap

### Stage 1
- cryptocurrencies will be used as the asset class
- RSI will be used as the technical 

**to do list**

- [ ] add crypto as a module within the price history package
- [ ] add RSI as a module within the comparisons package

## Further questions and notes

### How will the ranked assets be weighted?
- collection of assets with the highest historical returns but the most optimal indicator values
- this approach could be used accross asset groups and with multiple indicators to optimise

### Does more indicators equal a more accurate risk adjuested returns model?
- not exactly
- flaws in the use of specific indicators must be observed
- there are overall flaws with technical analysis. Lets if technical indicators are meaningless, using more 
of them should yield unpredictable outcomes

## Where is this method applicable?
- cryptocurrencies
    - a clear value model for cryptocurrencies is yet to be developed or may never be
    - so this addition, may help to mitigate the fundamental systematic risks of investing in this asset class
- for all asset classes in some way
    - adds some technical analysis on top of fundamental analysis that has already been done
        - better entry points on assets post fundamental analysis
        - slightly altered allocation of funds 

### is this not just a portfolio tool?
- yes in some ways, yet adds more options to identify risk rather than just volatility

how can this be used in a portfolio?
- typically, volatility is used as a benchmark for assesing risk. Hence, the outcomes from this analysis may
not be applicable
- due to the dynmic nature of these indicators, this strategy lends more to a swing traders apprach not to a long term investment
- regardless, how will funds be alllocated against different asset classes
    - use a generic risk profile. for example use the market cap weighted risk profile for crypto
    - backtest this dynamic approach and find the risk profile compared to the overall asset class. Adjuestments to the generic risk profile can then be made

