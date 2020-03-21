# Overview

this is a small script to inspect various aspects of one or more gw2 accounts. I use it to track birthdays and determine which character to make next.

# Getting started

Clone the repo, install the dependencies, and use.

``` bash
# clone the repository
git clone git@github.com:ccoakley/gw2inspect.git
cd gw2inspect
# create a virtual env (assumes python 3)
python -m venv venv
source venv bin activate
# install the requirements
pip install -r requirements.txt
# edit the configuration file
cp config.yml.example config.yml
vi config.yml
# verify the setup (this prints a small usage message)
python gw2inspect.py
```

# Usage

``` bash
python gw2inspect.py birthdays
```

lists all characters in all accounts, sorted by birthdate (ignores year).

``` bash
python gw2inspect.py find-all
```

Lists all profession, race, gender combinations an account is missing.

``` bash
python gw2inspect.py represent
```

Groups character by race and gender, lists the profession and the character name.