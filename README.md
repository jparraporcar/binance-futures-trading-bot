# Project ongoing to create a trading BOT for working with OHLC data from Binance API. Folder structure as follows:

**/macd_long_backtester/**: here can be found the class `Macd_long_backtester`, which is used to carry out analysis and optimization of OHLC data type.

**/optimization/"symbol_name"/results/**: each subfolder contains data related to an optimization for a certain coin. - symbol_name: any of the symbols from Binance API

The structure of optimization results storing is the following, using BTCUSDT Binance API symbol as an example:

**/optimization/"symbol_name"/results/"trend_type"/"trendletter_date_start&date_end"/"interval"/**"filename"
- trend_type: Up Trend, Down Trend, Sideways, If adding the sufix "_TA" it means that the trend have been assigned by doing technical analysis (TA). All trends in intervals different to daily have to be done by TA.
- trendletter: this is a letter assigned by the function assign_trends, from A to Z. In the case of sideways trends, the letters are from AA to ZZ.
- date_start: start time for the optimization
- date_end: end time for the optimization

## Example of folder structure:

**/optimization/"symbol_name"/results/BTCUSDT/uptrend/A_start=2021-09-01-00:00:00&end=2022-09-10-00:00:00/daily/**

## Structure of optimization results filename

"RES_filecreationtime_symbolname_trendtype_trendletter_date_start&date_end_interval

Note: data format for 'start' and 'end' --> %Y-%m-%d-%H:%M:%S

**/optimization/"symbol_name"/calculations/**

### Structure of file for calculations

"CALC_filecreationtime_symbolname"

This file is used to do all the necessary calculations to extract then the filtered results by trend, interval, period

**/testing/**: this folder is intended to be used for doing any kind of test that does not need to be registered in results files

### Structure of filename:

filecreationtime_descriptionoftest

# Notes regarding backtesting in intervals different than daily

Till there is not other package for analizing trends available, the way to use the current package would be: to analyze
the trend in the daily following the package guidelines, and adopt those parameters for another type of trend in a different interval sampling **according to a technical analysis of structures in tradingview**