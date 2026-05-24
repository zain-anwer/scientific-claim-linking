#!/bin/bash

# creating virtual environment
python -m venv venv

# activating/setting virtual environment for package downloads
source venv/Scripts/activate

# upgrading the package manager pip
python -m pip install --upgrade pip

# downloading the packages mentioned in the requirements.txt
pip install -r requirements.txt

# downloading the spacy model
python -m spacy download en_core_web_sm

# downloading the scientific model for NER used in query expansion
pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.4/en_core_sci_sm-0.5.4.tar.gz


echo "Setup Complete..."
echo "Make sure to run 'source venv/Scripts/activate' for every session before trying to run anything"
