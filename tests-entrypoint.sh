#!/bin/sh

pip install -e .
python -m unittest discover -s tests
