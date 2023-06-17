# Crypto Trading Bot

## Description

This project is a cryptocurrency bot, developed in Python and run using a Jupyter Notebook. The bot operates on the Binance Futures API and utilizes two technical indicators to formulate trading signals:

- **MACD (Moving Average Convergence Divergence)**: This indicator identifies potential buy and sell signals. A bullish signal is identified when the MACD line crosses above the signal line, which the bot checks for confirmation.

- **Moving Averages (SMA & EMA)**: To confirm the signal from the MACD, the bot checks the position of the Exponential Moving Average (EMA) relative to the Simple Moving Average (SMA). For a buy signal to be confirmed, the EMA should be above the SMA.

Note: Conversely, the same applies for a sell signal

## Table of Contents

- [Installation](#installation)
- [Flowchart](#flowchart)
- [Technologies](#technologies)
- [Trading Indicators](#trading-indicators)
- [Screenshots](#screenshots)
- [Contact](#contact)

## Installation
Before you begin, ensure you have met the following requirements:

### Prerequisites

- You have installed [Jupyter Notebook](https://jupyter.org/install)

To install and use the Trading Bot, follow these steps:


1. Clone the repository
```
git clone https://github.com/jparraporcar/trading-bot.git
```

2. Navigate into the project directory
```
cd trading-bot
```

3. Launch Jupyter Notebook in this directory
```
jupyter notebook
```

4. Once Jupyter Notebook is open, navigate to the notebook file (`.ipynb` extension) and open it.
Run the cells to start the trading bot.

## Flowchart

<figure>
  <br />
  <br />
  <img src="./flowchart.jpg" alt="flowchart">
</figure>

Note:
- CamelCase: is used to describe processes between function invocations during the bot workflow.
- snake_case: is used to describe actual methods of the bot class.


## Technologies

This project is implemented with the following technologies and libraries:

1. Python
2. Jupyter Notebook
3. Binance Python SDK
4. Pandas
5. Numpy
6. Matplotlib
7. TA-Lib (Python wrapper)
8. smtplib

## Trading Indicators

The bot employs a blend of technical indicators for formulating robust trading signals, including:

1. MACD (Moving Average Convergence Divergence)
2. SMA (Simple Moving Average)
3. EMA (Exponential Moving Average)

## Screenshots

[...Add relevant screenshots of the project here...]

## Contact

If you want to contact me you can reach me at:

- **Name**: `Jordi Parra Porcar`
- **Email**: `jordiparraporcar@gmail.com`
- **LinkedIn**: [`Jordi Parra Porcar`](https://www.linkedin.com/in/jordiparraporcar/)

For any additional questions or comments, please feel free to reach out. Contributions, issues, and feature requests are welcome!

