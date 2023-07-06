ielove
==========

![Python 3](https://img.shields.io/badge/python-3-blue?logo=python)
[![License](https://img.shields.io/badge/license-MIT-green)](https://choosealicense.com/licenses/mit/)
[![Code style](https://img.shields.io/badge/style-black-black)](https://pypi.org/project/black)

ielove.co.jp scraper

# Howto

## Scrape a property page

```sh
python3 -m ielove get-property https://www.ielove.co.jp/chintai/c1-397758400
```
If commiting to database:
```sh
. ./secret.env
python3 -m ielove get-property --commit -u $MONGO_INITDB_ROOT_USERNAME -p $MONGO_INITDB_ROOT_PASSWORD https://www.ielove.co.jp/chintai/c1-397758400
```

# Contributing

## Dependencies

* `python3.10` or newer;
* `requirements.txt` for runtime dependencies;
* `requirements.dev.txt` for development dependencies.
* `make` (optional);

Simply run
```sh
virtualenv venv -p python3.10
. ./venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements.dev.txt
```

## Documentation

Simply run
```sh
make docs
```
This will generate the HTML doc of the project, and the index file should be at
`docs/index.html`. To have it directly in your browser, run
```sh
make docs-browser
```

## Code quality

Don't forget to run
```sh
make
```
to format the code following [black](https://pypi.org/project/black/),
typecheck it using [mypy](http://mypy-lang.org/), and check it against coding
standards using [pylint](https://pylint.org/).
