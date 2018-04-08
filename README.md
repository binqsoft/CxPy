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
|-- CxType                                 Checkmarx CliScanArgs
|   |-- __init__.py
|   |-- array_of_scan_path.py
|   |-- cli_scan_args.py
|   |-- credentials.py
|   |-- cx_client_type.py
|   |-- cx_ws_perforce_browsing_mode.py
|   |-- git_ls_remote_view_type.py
|   |-- local_code_container.py
|   |-- project_origin.py
|   |-- project_settings.py
|   |-- repository_type.py
|   |-- scan_path.py
|   |-- source_code_settings.py
|   |-- source_control_protocol_type.py
|   |-- source_control_settings.py
|   |-- source_filter_patterns.py
|   `-- source_location_type.py
|-- etc
|   |-- config.json                        configuration demo, please edit this file to set your username, password, Checkmarx server ip
|   `-- config.json_template               configuration template
|-- reports                                This is the directory where the generated reports will be.
|   `-- reports.txt
|-- scan_params_json                       json files for the parameters of the scan method from CxPy.py
|   |-- git_http_repo.json                 get source code from git http repository url
|   |-- git_ssh_repo.json                  get source code from git ssh repository url
|   |-- local_zip_file.json                get source code from local zip file
|   |-- svn.json                           get source code from svn
|   `-- windows_shared_folder.json         get source code from windows shared folder
|-- test
|   `-- unitTest.py                        The API unittest file
|-- BookStoreJava_21403_lines.zip
|-- CxPy.py                                The python SOAP API SDK file
|-- CxSDKWebService.xml                    The CxSAST SOAP API WSDL file
|-- LICENSE
|-- README.md
|-- common.py                              common class that other class will inherit
|-- id_rsa
|-- requirements.txt
`-- scan_and_generate_reports.py            a demo script you can run to scan source code and generate reports
```

## A demo process to use CxPy
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
 7. set proper configuration in CxPy/etc/config.json
     * Please modify etc/config.json to set your Checkmarx server ip, username, password
 8. set proper values for json files in CxPy/scan_params_json
     * Please modify these json files to set proper values for the scan parameter of the scan method in CxPy.py
 9. change the 'scan_params_json_file' variable in 'scan_and_generate_reports.py'
     * Choose the json file you want to load
 9. run the demo script 'scan_and_generate_reports.py' to scan source code and generate PDF, CSV, XML reports
     * python scan_and_generate_reports.py
 10. check reports from the CxPy/reports folder, BookStoreJava.pdf, BookStoreJava.csv, BookStoreJava.xml will be generated.

 ## The API list provided in CxPy

| API |  UnitTest | |
| :---------- | :----------: | :---------- |
| 1. branch_project_by_id | ok | |
| 2. cancel_scan | ok | |
| 3.  create_scan_report | ok | |
| 4.  delete_projects | ok | |
| 5.  delete_scans | ok | |
|6.  execute_data_retention | ok | |
| 7.  get_all_users | ok | |
| 8.  get_associated_groups_list | ok | |
| 9.  get_configuration_set_list | ok | |
| 10. get_preset_list | ok | |
| 11. get_project_configuration | ok | |
| 12. get_project_scanned_display_data | ok | |
| 13. get_projects_display_data | ok | |
| 14. get_scan_report | ok | |
| 15. get_scan_report_status | ok | |
| 16. get_scan_summary | ok | |
| 17. get_scans_display_data_for_all_projects | ok | |
| 18. get_status_of_single_scan  | ok | |
| 19. logout | ok | |
| 20. scan | ok | |
| 21. stop_data_retention | ok | |
| 22. update_project_configuration | ok | |
| 23. update_project_incremental_configuration | ok | |
| 24. update_scan_comment | ok | |
| 25. filter_project_scanned_display_data | ok | |
| 26. filter_projects_display_data | ok | |
| 27. filter_scan_info_for_all_projects | ok | |
| 28. check_scanning_status | ok | |
| 29. generate_report | ok | |
| 30. get_team_ldap_groups_mapping  | `X` | The same as 31 |
| 31. set_team_ldap_groups_mapping | `X` | You need to configure your own ldap service |


## Upgrade Notice
* If you use Checkmarx v8.6.0 and up, you should use the "TaskID" field in "CxType/project_settings.py"