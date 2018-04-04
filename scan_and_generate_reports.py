#!usr/bin/python
# coding=utf-8

# Python Dependencies
import CxPy
import logging
import os
import json
import ast

dir_path = os.path.dirname(os.path.realpath(__file__))

logging.basicConfig(filename=dir_path + '/checkmarx_soap_api.log',
                    format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


if __name__ == '__main__':
    print ("[SYS]\tLoading...")
    pyC = CxPy.CxPy()
    # scan_params_json_file = "local_zip_file.json"
    # scan_params_json_file = "svn.json"
    # scan_params_json_file = "windows_shared_folder.json"
    # scan_params_json_file = "git_http_repo.json"
    scan_params_json_file = "git_ssh_repo.json"

    try:
        with open(dir_path + "/scan_params_json/" + scan_params_json_file, "r") as f:
            data = json.loads(f.read())
    except Exception as e:
        raise Exception("unable to open file. ")

    d = {}

    for k, v in data.items():
        if v in ["True", "False", "None"]:
            v = ast.literal_eval(v)
        d[k] = v

    team = "" if pyC.is_user_admin else pyC.team

    if team:
        project_name = team + "\\" + "BookStoreJava"
    else:
        project_name = "BookStoreJava"

    d["project_name"] = project_name

    ssh_private_key_path = d.get("ssh_private_key", None)

    if ssh_private_key_path:
        try:
            with open(ssh_private_key_path, "r") as f:
                ssh_private_key = f.read()
        except Exception as e:
            raise Exception(" Fail to open id_rsa")

        d["ssh_private_key"] = ssh_private_key

    project_id, run_id = pyC.scan(**d)
    # check scanning status
    scan_id = pyC.check_scanning_status(run_id)

    # generate reports
    pyC.generate_report(project_name, scan_id, report_type="PDF")
    pyC.generate_report(project_name, scan_id, report_type="CSV")
    pyC.generate_report(project_name, scan_id, report_type="XML")

    pyC.delete_projects(["BookStoreJava"])
    print ("[SYS]\tFinished...")
