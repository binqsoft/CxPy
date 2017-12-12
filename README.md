# CxPy
Python SOAP API for the Checkmarx WSDL

Please install virtualenv on your machine

# create a virtualenv
virtualenv CxPy
# activate
source CxPy/bin/activate
# clone the repository from github
git clone  https://github.com/binqsoft/CxPy.git
# change working directory to CxPy directory
cd CxPy
# install module dependencies
pip install -r requirement.txt
# run API to scan source code and generate PDF and XML reports
python APICx.py
# check reports from the CxPy/reports folder




