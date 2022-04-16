# Divinity introduction

Divinity is a trading algorithm I developed from scratch to improve my software engineering skills. A more in-depth explanation can be found on my website, [here](https://kentkr.github.io/Divinity-introduction/). 

# Quick start guide

## Basic install 

### Clone repository

To install divinity on an OS or linux device then switch into the directory you'd like divinity to be in. Clone the repo then move into the `divinity` directory.

```
https://github.com/kentkr/divinity
cd divinity
```

### Install modules

If you have python version 3.8 already on your device, then use `pip` to install required modules. 

```
pip install -r requirements.txt
```
Most of the modules are easy to install, but I had trouble getting `prophet` to work properly with python 3.7. If you have trouble then consult stack overflow, install with `conda-forge`, try using python 3.8, or create an issue and I can try and help.  

### Run the algorithm locally

The script is now able to be run with the `--test` flag and allow you to `--plot` the algorithm over the last year. Simply call `python3 scripts/final_scripts/divinity.py --ticker TSLA --plot --test` from the divinity directory. You can replace `TSLA` with any ticker available on yahoo finance.

# Run the algorithm live

To run the algorithm in a paper or live account you first need to sign up for [alpaca](https://alpaca.markets/). It is a free brokerage with zero trading fees.

Next create a file in the root directory called `.env.ini` and add the following to it.

```
# keys for alpaca

# paper keys
[alpaca_paper]
alpaca_paper_key=
alpaca_paper_secret_key=

# real keys
[alpaca_real]
alpaca_real_key=
alpaca_real_secret_key=

```

Then go to your alpaca account get the key and secret key for either your paper or live account. Fill in the keys in the specified places above without quotes or spaces (eg `alpaca_paper_key=ABC123`).

To run the algorithm with a paper account *do not* use the `--test` flag. If you want to use your real account with real money *specify* the `--live` flag.

# Legal disclaimer

I do not claim to be a financial advisor and investing carries inherent risks, so please use your own discretion. I claim no liability over financial losses made using divinity or iterations there of. 

