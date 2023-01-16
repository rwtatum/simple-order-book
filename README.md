# simple-order-book
(Note: built using python 3.9)

Order book with no dependencies on third party packages.

# Setting up

* clone repo
```
git clone https://github.com/rwtatum/simple-order-book.git
```

## Run application

```
python src.main.py
```

## Run tests (pytest)

* create a virtual environment and pip install requirements-dev.txt
```
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements-dev.txt
pytest tests
```


## TODOs and further work

1. Exception handling and logging
2. Add ability to cancel orders
3. Improve data structures for better performance
