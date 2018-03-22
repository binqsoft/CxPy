# CxPy
This is a Checkmarx SOAP API SDK implemented by Python 2.7.

## Getting Started
If you want to know more about Checkmarx SOAP API, please check Checkmarx Knowledge Center: https://checkmarx.atlassian.net/wiki/spaces/KC/pages/33980521/SOAP+API 

### Prerequisites
Python package requirements:
    suds==0.4
    
### file structure of this project

```
.
|-- etc
|   |-- config.json                    configuration demo, please edit this file to set your username, password, Checkmarx server ip   
|   `-- config.json_template           configuration template
|-- reports                            This is the directory where the generated reports will be.
|   `-- reports.txt
|-- BookStoreJava_21403_lines.zip      sample source code provied by Checkmarx
|-- CxPy.py                            The python SOAP API SDK file
|-- CxSDKWebService.xml                The CxSAST SOAP API WSDL file      
|-- LICENSE                            license
|-- README.md                          readme
|-- checkmarx_soap_api.log             output log
|-- requirements.txt                   the file that describes which python packages you need to install
`-- test_Checkmarx_SOAP_API.py         An demo script to call the SDK "CxPy.py"
```


## How to use this project
 1. We suggest using virtualenv to setup an independent running environment for your project
     * pip install virtualenv
 2. create a virtual environment for your project
     * virtualenv CxPy-env
 3. activate your environment
     * source CxPy-env/bin/activate
 4. clone the repository from github
     * git clone  https://github.com/binqsoft/CxPy.git
 5. change working directory to CxPy directory
     * cd CxPy
 6. install Python packages
     * pip install -r requirement.txt
 7. set proper configuration in etc/config.json 
     * Please modify etc/config.json to set your Checkmarx server ip, username, password
 8. run the demo script 'test_Checkmarx_SOAP_API.py' to scan source code 'BookStoreJava_21403_lines.zip' and generate PDF and XML reports
     * python test_Checkmarx_SOAP_API.py
 9. check reports from the CxPy/reports folder, BookStoreJava.pdf, BookStoreJava.xml will be generated.
     




