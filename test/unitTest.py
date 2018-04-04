# encoding=utf-8

import unittest
import CxPy
import logging
import os
import json
import ast
import datetime


dir_path = os.path.dirname(os.path.realpath(__file__))

logging.basicConfig(filename=dir_path + '/checkmarx_soap_api.log',
                    format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
pyC = CxPy.CxPy()
DATE = datetime.datetime.min


class MyTest(unittest.TestCase):

    @staticmethod
    def time_calculation(date_1, date_2=DATE):
        time_data = date_1 - date_2
        return (time_data.days * 24 * 3600 + time_data.seconds) * 10000000

    def create_scan(self, json_path="local_zip_file.json"):
        try:
            with open(dir_path + "/scan_params_json/" + json_path, "r") as f:
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
        project_id, run_id = pyC.scan(**d)
        return project_id, run_id

    def start_scan(self, json_path):
        try:
            with open(dir_path + "/scan_params_json/" + json_path, "r") as f:
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

        # get ssh private key
        ssh_private_key_path = d.get("ssh_private_key", None)
        if ssh_private_key_path:
            try:
                with open(ssh_private_key_path, "r") as f:
                    ssh_private_key = f.read()
            except Exception as e:
                raise Exception(" Fail to open id_rsa")

            d["ssh_private_key"] = ssh_private_key

        # create scan
        project_id, run_id = pyC.scan(**d)

        # check scanning status
        scan_id = pyC.check_scanning_status(run_id)

        # generate reports
        pyC.generate_report(project_name, scan_id, report_type="PDF")
        pyC.generate_report(project_name, scan_id, report_type="CSV")
        pyC.generate_report(project_name, scan_id, report_type="XML")

        # delete the project
        pyC.delete_projects(["BookStoreJava"])
        return project_id, run_id

    def test_local_zip_file(self, zip_json_file="local_zip_file.json"):
        project_id, run_id = self.start_scan(zip_json_file)
        self.assertEqual((project_id > 0, run_id > 0), (True, True))

    def test_svn(self, svn_json_file="svn.json"):
        project_id, run_id = self.start_scan(svn_json_file)
        self.assertEqual((project_id > 0, run_id > 0), (True, True))

    def test_windows_shared_folder(self, win_shared_folder_json_file="windows_shared_folder.json"):
        project_id, run_id = self.start_scan(win_shared_folder_json_file)
        self.assertEqual((project_id > 0, run_id > 0), (True, True))

    def test_git_http_repo(self, git_http_json_file="git_http_repo.json"):
        project_id, run_id = self.start_scan(git_http_json_file)
        self.assertEqual((project_id > 0, run_id > 0), (True, True))

    def test_ssh_repo(self, git_ssh_json_file="git_ssh_repo.json"):
        project_id, run_id = self.start_scan(git_ssh_json_file)
        self.assertEqual((project_id > 0, run_id > 0), (True, True))

    def test_branch_project_by_id(self):
        project_id = pyC.branch_project_by_id("demo", "demo_01") > 0
        self.assertEqual(project_id > 0, True)

    def test_cancel_scan(self):
        project_id, run_id = self.test_create_scan()
        result = pyC.cancel_scan(run_id)
        self.assertEqual(result.get("success"), True)

    def test_create_scan_report(self):
        project_id, run_id = self.create_scan()
        scan_id = pyC.check_scanning_status(run_id)
        result = pyC.create_scan_report(scan_id, report_type="PDF")
        print("pdf_id:", result)
        self.assertEqual(result > 0, True)
        result = pyC.create_scan_report(scan_id, report_type="RTF")
        print("rtf_id:", result)
        self.assertEqual(result > 0, True)
        result = pyC.create_scan_report(scan_id, report_type="CSV")
        print("scv_id:", result)
        self.assertEqual(result > 0, True)
        result = pyC.create_scan_report(scan_id, report_type="XML")
        print("xml_id:", result)
        self.assertEqual(result > 0, True)

    def test_delete_projects(self):
        delete_state = pyC.delete_projects(["BookStoreJava"])
        self.assertEqual(delete_state.get("success"), True)
        delete_state2 = pyC.delete_projects(["TestCxPy", "TestPy"])
        self.assertEqual(delete_state2.get("success"), True)

    def test_delete_user(self):
        result = pyC.delete_user(user_name="chen072262@gmail.com")
        self.assertEqual(result.get("success"), True)

    def test_delete_scan(self):
        project_id, run_id = self.create_scan()
        scan_id = pyC.check_scanning_status(run_id)
        result = pyC.delete_scans([scan_id])
        self.assertEqual(result.get("success"), True)
    #
    def test_execute_data_retention(self):
        startDate = datetime.datetime(2018, 1, 1, 0, 0, 0)
        endDate = datetime.datetime(2018, 4, 2, 0, 0, 0)

        start_date = self.time_calculation(startDate)
        end_date = self.time_calculation(endDate)

        result = pyC.execute_data_retention(data_retention_type="DatesRange",
                                            num_of_scans_to_preserve=0,
                                            start_date=start_date,
                                            end_date=end_date,
                                            duration_limit_in_hours=1L)
        self.assertEqual(result, "ExecuteDataRetention called successfully")

    def test_get_all_users(self):
        user_list = pyC.get_all_users()
        self.assertNotEqual(user_list, None)

    def test_get_associated_groups_list(self):
        group_list = pyC.get_associated_groups_list()
        self.assertNotEqual(type(group_list), None)

    def test_get_configuration_set_list(self):
        config= pyC.get_configuration_set_list()
        self.assertNotEqual(config, None)

    def test_get_preset_list(self):
        preset_list = pyC.get_preset_list()
        self.assertNotEqual(preset_list, None)

    def test_get_project_configuration(self):
        config, permission = pyC.get_project_configuration("demo")
        self.assertNotEqual(config, None)
        self.assertNotEqual(permission, None)

    def test_get_project_scanned_display_data(self):
        data = pyC.get_project_scanned_display_data()
        self.assertNotEqual(data, None)

    def test_get_projects_display_data(self):
        data = pyC.get_projects_display_data()
        self.assertNotEqual(data, None)

    def test_get_scan_report(self):
        project_id, run_id = self.create_scan()
        scan_id = pyC.check_scanning_status(run_id=run_id)
        report_id = pyC.create_scan_report(scan_id=scan_id, report_type="PDF")
        is_ready, is_failed = pyC.get_scan_report_status(report_id=report_id)
        while is_ready:
            report = pyC.get_scan_report(report_id)
            self.assertNotEqual(report, None)

    def test_get_scan_report_status(self):
        project_id, run_id = self.create_scan()
        scan_id = pyC.check_scanning_status(run_id=run_id)
        report_id = pyC.create_scan_report(scan_id=scan_id, report_type="PDF")
        is_ready, is_failed = pyC.get_scan_report_status(report_id=report_id)
        while is_ready:
            self.assertTrue("ok")

    def test_get_scan_summary(self):
        project_id, run_id = self.create_scan()
        scan_id = pyC.check_scanning_status(run_id=run_id)
        result = pyC.get_scan_summary(scan_id=scan_id)
        self.assertNotEqual(result, None)

    def test_get_scans_display_data_for_all_projects(self):
        result = pyC.get_scans_display_data_for_all_projects()
        self.assertNotEqual(result, None)

    def test_get_status_of_single_scan(self):
        project_id, run_id = self.create_scan()
        while True:
            current_status, scan_id = pyC.get_status_of_single_scan(run_id=run_id)
            if scan_id > 0:
                break
        self.assertEqual(scan_id > 0, True)
        self.assertEqual(current_status, "Finished")

    def test_is_valid_project_name(self):
        first = pyC.is_valid_project_name("BookStoreJava")
        second = pyC.is_valid_project_name("HelloWorld")
        self.assertNotEqual(first, True)
        self.assertEqual(second, True)

    def test_logout(self):
        pyC.logout()

    def test_stop_data_retention(self):
        result = pyC.stop_data_retention()
        self.assertEqual(result, "StopDataRetention called successfully.")

    def test_update_project_configuration(self):
        result = pyC.update_project_configuration("BookStoreJava")
        print(result)
        self.assertEqual(result, "ok")

    def test_update_scan_comment(self):
        project_id, run_id = self.create_scan()
        scan_id = pyC.check_scanning_status(run_id=run_id)
        result = pyC.update_scan_comment(scan_id=scan_id, comment="HelloWorld")
        self.assertEqual(result, "ok")


if __name__ == '__main__':
    unittest.main()
