# coding=utf-8
# Python Dependencies
import base64
import re
import json
import time
import logging
import os
from suds.client import Client
from suds.sudsobject import asdict
from suds.cache import NoCache

dir_path = os.path.dirname(os.path.realpath(__file__))

logging.basicConfig(filename=dir_path + '/checkmarx_soap_api.log',
                    format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class CxPy(object):
    # Internal Variables for the Class
    DEBUG = False
    configPath = dir_path + "/etc/"
    errorLog = []
    ttlReport = 6
    timeWaitReport = 3

    #
    # Init Function
    #
    def __init__(self):
        # Get Configuration
        self.user_name, self.password, self.url, self.api_type = self.get_config()
        # Open Connection With Checkmarx
        self.init_client = self.open_connection()
        # Get the Service URL
        self.service_url = self.get_service_url(self.init_client)
        # Get the Session Id and Client Object
        self.session_id, self.client = self.get_session_id(self.init_client, self.service_url)
        pass

    ##########################################
    #
    # Functions Related to Opening session with Checkmarx
    #
    ##########################################

    #
    # Get Configuration
    #
    def get_config(self):
        try:
            with open(self.configPath + "config.json", "r") as outfile:
                tmp_json = json.load(outfile)["checkmarx"]
                username = str(tmp_json["username"])
                password = str(tmp_json["password"])
                url = str(tmp_json["url"])
                api_type = tmp_json["APIType"]
                return username, password, url, api_type
        except Exception as e:
            logger.error("Unable to get configuration: {} ".format(e.message))
            raise Exception("Unable to get configuration: {} ".format(e.message))

    #
    # Open Connection
    #
    def open_connection(self):
        try:
            tmp_client = Client(self.url)
            if self.DEBUG:
                print(dir(tmp_client))
            return tmp_client
        except Exception as e:
            logger.error("Unable to establish connection "
                         "with WSDL [{}]: {} ".format(self.url, e.message))
            raise Exception("Unable to establish connection "
                            "with WSDL [{}]: {} ".format(self.url, e.message))

    #
    # Get Service URL
    #
    def get_service_url(self, client):
        """

        https://checkmarx.atlassian.net/wiki/display/KC/Getting+the+SDK+Web+Service+URL

        Create an instance of the Resolver generated proxy client,
        and set its URL to: http://<server>/Cxwebinterface/CxWsResolver.asmx
        where <server> is the IP address or resolvable name of the CxSAST server
        (in a distributed architecture: the CxManager server).

        Call the Resolver's single available method (GetWebServiceUrl) as below.
        The returned CxWSResponseDiscovery object's .ServiceURL field will
        contain the SDK web service URL.

        The service url example: http://192.168.31.121/cxwebinterface/SDK/CxSDKWebService.asmx

        :param client:
        :return: Checkmarx web service url
        """
        try:
            cx_client = client.factory.create('CxClientType')
            response = client.service.GetWebServiceUrl(cx_client.SDK, self.api_type)

            if response.IsSuccesfull:
                service_url = response.ServiceURL
            else:
                logger.error("Error establishing connection:"
                             "{}".format(response.ErrorMessage))
                raise Exception("Error establishing connection:"
                                " {}".format(response.ErrorMessage))

            if self.DEBUG:
                print("Response Discovery Object:", dir(response))
                print("Service Url:", service_url)
            service_url = service_url or None
            return service_url
        except Exception as e:
            logger.error("GetWebServiceUrl, "
                         "Unable to get Service URL: {} ".format(e.message))
            raise Exception("GetWebServiceUrl, "
                            "Unable to get Service URL: {} ".format(e.message))

    #
    # Login in Checkmarx and retrieve the Session ID
    #
    def get_session_id(self, client, service_url, lcid=2052):
        """

        https://checkmarx.atlassian.net/wiki/display/KC/Initiating+a+Session

        The login web service parameters are as follows:
        public CxWSResponseLoginData Login(
                   Credentials applicationCredentials,
                   int lcid
                );

        applicationCredentials: A Credentials object, with fields:
        User: The username for login
        Pass: The password for login

        lcid: ID# of the language for web service responses.
        The current API version supports the following values:
        1033: English
        1028: Chinese Taiwan
        1041: Japanese
        2052: Chinese

        Log in Checkmarx and retrieve the session id.
        The Checkmarx server session timeout is 24 hours.

        :param client:
        :param service_url:
        :param lcid:
        :return:
        """
        try:
            client_sdk = Client(service_url + "?wsdl", cache=NoCache(), prettyxml=True)

            cx_login = client_sdk.factory.create("Credentials")
            cx_login.User = self.user_name
            cx_login.Pass = self.password

            cx_sdk = client_sdk.service.Login(cx_login, lcid)

            if not cx_sdk.IsSuccesfull:
                logger.error("Unable to Login > "
                             "{}".format(cx_sdk.ErrorMessage))
                raise Exception("Unable to Login > "
                                "{}".format(cx_sdk.ErrorMessage))

            if self.DEBUG:
                print("Service Object:", dir(client))
                print("Login Object:", dir(cx_sdk))
                print("Session ID:", cx_sdk.SessionId)

            return cx_sdk.SessionId, client_sdk
        except Exception as e:
            logger.error("Unable to get SessionId from "
                         "[{}] : {} ".format(service_url, e.message))
            raise Exception("Unable to get SessionId from "
                            "[{}] : {} ".format(service_url, e.message))

    ##########################################
    #
    # Functions Related to the functionality of the WSDL
    #
    ##########################################

    #
    # Get data from the Projects
    #
    def get_project_scanned_display_data(self, filter_on=False):
        """

        The API client can get a list of all public projects in the system with
        a risk level and summary of results by severity (high, medium, low).

        :param filter_on:
        :return: CxWSResponseProjectScannedDisplayData
        """
        try:
            tmp = self.client.service.GetProjectScannedDisplayData(self.session_id)

            if not tmp.IsSuccesfull:
                logger.error("GetProjectScannedDisplayData, "
                             "Unable to get data from the server.")
                raise Exception("GetProjectScannedDisplayData, "
                                "Unable to get data from the server.")

            if self.DEBUG:
                print dir(tmp)

            if not filter_on:
                return self.convert_to_json(tmp)
            else:
                return tmp.ProjectScannedList[0]
        except Exception as e:
            logger.error("Unable to GetProjectScannedDisplayData: "
                         "{} ".format(e.message))
            raise Exception("Unable to GetProjectScannedDisplayData: "
                            "{} ".format(e.message))

    #
    # Get Project Display Data
    #
    def get_projects_display_data(self, filter_on=False):
        """

        The API client can get a list of CxSAST projects available to the current user.
        This is used primarily for display purposes.

        :param filter_on:
        :return: Array of projects. Each project contains data for display.
        """
        try:
            tmp = self.client.service.GetProjectsDisplayData(self.session_id)

            if not tmp.IsSuccesfull:
                logger.error("GetProjectsDisplayData, "
                             "Unable to get data from the server.")
                raise Exception("GetProjectsDisplayData, "
                                "Unable to get data from the server.")

            if self.DEBUG:
                print dir(tmp)

            if not filter_on:
                return self.convert_to_json(tmp)
            else:
                return tmp.projectList[0]
        except Exception as e:
            logger.error("Unable to GetProjectsDisplayData: "
                         "{} ".format(e.message))
            raise Exception("Unable to GetProjectsDisplayData: "
                            "{} ".format(e.message))

    #
    # Get Scan Info For All Projects
    #
    def get_scan_info_for_all_projects(self, filter_on=False):
        """

        get scan info for all projects

        :param filter_on:
        :return:
        """
        try:
            tmp = self.client.service.GetScansDisplayDataForAllProjects(self.session_id)
            if not tmp.IsSuccesfull:
                logger.error("GetScansDisplayDataForAllProjects,"
                             " Unable to get data from the server.")
                raise Exception("GetScansDisplayDataForAllProjects, "
                                "Unable to get data from the server.")

            if self.DEBUG:
                print dir(tmp)

            if not filter_on:
                return self.convert_to_json(tmp)
            else:
                return tmp
        except Exception as e:
            logger.error("Unable to GetScansDisplayDataForAllProjects: "
                         "{} ".format(e.message))
            raise Exception("Unable to GetScansDisplayDataForAllProjects: "
                            "{} ".format(e.message))

    #
    # Get Preset List
    #
    def get_preset_list(self):
        """

        get preset list from server

        :return:
        """
        try:
            tmp = self.client.service.GetPresetList(self.session_id)

            if not tmp.IsSuccesfull:
                logger.error("GetPresetList, Unable to get data from the server.")
                raise Exception("GetPresetList, Unable to get data from the server.")

            if self.DEBUG:
                print dir(tmp)

            return self.convert_to_json(tmp)
        except Exception as e:
            logger.error("Unable to GetPresetList: {} ".format(e.message))
            raise Exception("Unable to GetPresetList: {} ".format(e.message))

    def get_preset_id_by_name(self, preset_name):
        """
        get preset list from server, and search it in the preset list.

        Checkmarx default preset list:

        preset name : preset id

        "Checkmarx Default": 36,
        "All": 1,
        "Android": 9,
        "Apple Secure Coding Guide": 19,
        "Default": 7,
        "Default 2014": 17,
        "Empty preset": 6,
        "Error handling": 2,
        "High and Medium": 3,
        "High and Medium and Low": 13,
        "HIPAA": 12,
        "JSSEC": 20,
        "MISRA_C": 10,
        "MISRA_CPP": 11,
        "Mobile": 14,
        "OWASP Mobile TOP 10 - 2016": 37,
        "OWASP TOP 10 - 2010": 4,
        "OWASP TOP 10 - 2013": 15,
        "PCI": 5,
        "SANS top 25": 8,
        "WordPress": 16,
        "XS": 35

        :param preset_name:
        :return: preset id
        """
        try:
            preset_id = None
            tmp = self.client.service.GetPresetList(self.session_id)

            if not tmp.IsSuccesfull:
                logger.error("In get_preset_id_by_name unable to getPresetList:"
                             "{}".format(tmp.ErrorMessage))
                raise Exception("In get_preset_id_by_name unable to getPresetList:"
                                " {}".format(tmp.ErrorMessage))

            preset_list = tmp.PresetList.Preset
            for preset in preset_list:
                if preset.PresetName == preset_name:
                    preset_id = preset.ID
                    break

            if not preset_id:
                logger.error(" get_preset_id_by_name >>> "
                             "please check your preset name again, "
                             "the following preset does not exist: "
                             "{}".format(preset_name))
                raise Exception(' get_preset_id_by_name >>>'
                                ' please check your preset name again,'
                                'the following preset does not exist: '
                                '{}'.format(preset_name))

            return preset_id
        except Exception as e:
            logger.error("Unable to GetPresetList: {} ".format(e.message))
            raise Exception("Unable to GetPresetList: {} ".format(e.message))

    #
    # Get Configuration List
    #
    def get_configuration_list(self):
        """

        The API client can get the list of available encoding options
        (for scan configuration).

        :return: Available encoding options.
        """
        try:
            tmp = self.client.service.GetConfigurationSetList(self.session_id)

            if not tmp.IsSuccesfull:
                logger.error("get_configuration_list, Unable to get data from the server.")
                raise Exception("get_configuration_list, Unable to get data from the server.")

            if self.DEBUG:
                print dir(tmp)

            return self.convert_to_json(tmp)
        except Exception as e:
            logger.error("Unable to get_configuration_list: {} ".format(e.message))
            raise Exception("Unable to get_configuration_list: {} ".format(e.message))

    #
    # Get Associated Groups List
    #
    def get_associated_groups(self):
        """

        The API client can get information on all groups related to the current user.

        :return: CxWSResponseGroupList.GroupList contains an array of group data.

        """
        try:
            tmp = self.client.service.GetAssociatedGroupsList(self.session_id)

            if not tmp.IsSuccesfull:
                logger.error("get_associated_groups, Unable to get data from the server.")
                raise Exception("get_associated_groups, Unable to get data from the server.")

            if self.DEBUG:
                print dir(tmp)

            return self.convert_to_json(tmp)
        except Exception as e:
            logger.error("get_associated_groups, Unable to GetAssociatedGroupsList: {} ".format(e.message))
            raise Exception("get_associated_groups, Unable to GetAssociatedGroupsList: {} ".format(e.message))

    #
    # get first associated group id
    #
    def get_first_associated_group_id(self):
        first_associated_group_id = '0'
        group_list = self.get_associated_groups()
        groups = group_list.get("GroupList").get("Group")
        first_associated_group = next(iter(groups), None)
        if first_associated_group:
            first_associated_group_id = first_associated_group.get("ID")
        return str(first_associated_group_id)

    #
    # Filter For get_project_scanned_display_data
    #
    def filter_project_scanned_display_data(self, project_id):
        """

        filter for get_project_scanned_display_data

        :param project_id:
        :return:
        """
        tmp_projects = self.get_project_scanned_display_data(True)
        for project in tmp_projects:
            if project.ProjectID == project_id:
                return self.convert_to_json(project)

        logger.error("filter_project_scanned_display_data, "
                     "Could not find ProjectID: {} ".format(project_id))
        raise Exception("filter_project_scanned_display_data ,"
                        "Could not find ProjectID: {} ".format(project_id))

    #
    # Filter for get_projects_display_data
    #
    def filter_projects_display_data(self, project_id):
        """

        filter for get_projects_display_data

        :param project_id:
        :return:
        """
        tmp_projects = self.get_projects_display_data(True)
        for project in tmp_projects:
            if project.projectID == project_id:
                return self.convert_to_json(project)

        logger.error("filter_projects_display_data, "
                     "Could not find ProjectID: {} ".format(project_id))
        raise Exception("filter_projects_display_data,"
                        "Could not find ProjectID: {} ".format(project_id))

    #
    # Filter for get_scan_info_for_all_projects
    #
    def filter_scan_info_for_all_projects(self, project_id):
        """

        filter for get_scan_info_for_all_projects

        :param project_id:
        :return:
        """
        tmp_projects = self.get_scan_info_for_all_projects(True).ScanList[0]
        for project in tmp_projects:
            if project.ProjectId == project_id:
                return self.convert_to_json(project)

        logger.error("filter_scan_info_for_all_projects, "
                     "Could not find ProjectID: {} ".format(project_id))
        raise Exception("filter_scan_info_for_all_projects, "
                        "Could not find ProjectID: {} ".format(project_id))

    #
    # Get Suppressed Issues
    #
    def get_suppressed_issues(self, scan_id):
        cx_ws_report_type = self.client.factory.create("CxWSReportType")
        cx_report_request = self.client.factory.create("CxWSReportRequest")
        cx_report_request.ScanID = scan_id
        cx_report_request.Type = cx_ws_report_type.XML
        create_report_response = self.client.service.CreateScanReport(self.session_id,
                                                                      cx_report_request)
        if create_report_response.IsSuccesfull:

            if self.DEBUG:
                print create_report_response
                print "Success. Creating Get Scan Report Status"

            inc = 0
            while inc < self.ttlReport:
                inc += 1
                r_status = self.client.service.GetScanReportStatus(self.session_id,
                                                                   create_report_response.ID)
                if r_status.IsSuccesfull and r_status.IsReady:
                    break

                if self.DEBUG:
                    print "fail"
                time.sleep(self.timeWaitReport)

            if self.DEBUG:
                print "Success. Creating Get Scan Report"
            r_scan_results = self.client.service.GetScanReport(self.session_id,
                                                               create_report_response.ID)

            if r_scan_results.IsSuccesfull and r_scan_results.ScanResults:

                xml_data = base64.b64decode(r_scan_results.ScanResults)

                issues = re.findall('FalsePositive="([a-zA-Z]+)" Severity="([a-zA-Z]+)"',
                                    xml_data)

                if self.DEBUG:
                    print r_scan_results
                    print issues

                medium_suppress_issues = 0
                low_suppress_issues = 0
                high_suppress_issues = 0
                other_suppress_issues = 0

                for a, b in issues:
                    if a == "True":
                        if b == "Medium":
                            medium_suppress_issues += 1
                        elif b == "High":
                            high_suppress_issues += 1
                        elif b == "Low":
                            low_suppress_issues += 1
                        else:
                            other_suppress_issues += 1
                if self.DEBUG:
                    print high_suppress_issues
                    print medium_suppress_issues
                    print low_suppress_issues
                return {"highSuppressIssues": high_suppress_issues,
                        "mediumSuppressIssues": medium_suppress_issues,
                        "lowSuppressIssues": low_suppress_issues}
            else:
                raise Exception("Unable to Get Report")

        else:
            raise Exception("Unable to get Suppressed")

            #

    # Convert Suds object into serializable format.
    #
    def recursive_asdict(self, d):
        out = {}
        for k, v in asdict(d).iteritems():
            if hasattr(v, '__keylist__'):
                out[k] = self.recursive_asdict(v)
            elif isinstance(v, list):
                out[k] = []
                for item in v:
                    if hasattr(item, '__keylist__'):
                        out[k].append(self.recursive_asdict(item))
                    else:
                        out[k].append(item)
            else:
                out[k] = v
        return out

    #
    # Return Subs Object into Serializable format Handler
    #
    def convert_to_json(self, data):
        try:
            tmp = self.recursive_asdict(data)
            # return json.dumps(tmp)
            return tmp
        except Exception as e:
            logger.error("Unable to convert to JSON: {} ".format(e.message))
            raise Exception("Unable to convert to JSON: {} ".format(e.message))

    def get_project_id_by_name(self, project_name):
        """

        get project id by name

        :param project_name:
        :type project_name:  string
        :return: project_id
        """
        try:
            tmp = self.client.service.GetProjectsDisplayData(self.session_id)

            if tmp.IsSuccesfull:
                project_id = None
                project_data_list = tmp.projectList.ProjectDisplayData
                for projectData in project_data_list:
                    if projectData.ProjectName == project_name:
                        project_id = projectData.projectID
                        break

                if not project_id:
                    logger.error(' get_project_id_by_name >>> '
                                 'please check your projectName again,'
                                 'the following project does not exist: '
                                 '{}'.format(project_name))
                    raise Exception(' get_project_id_by_name >>> '
                                    'please check your projectName again,'
                                    'the following project does not exist: '
                                    '{}'.format(project_name))
                logger.info(" project {} has project id {}".format(project_name, project_id))
                return project_id

            else:
                logger.error(' Fail to GetProjectsDisplayData: '
                             '{} '.format(tmp.ErrorMessage))
                raise Exception(' Fail to GetProjectsDisplayData: '
                                '{} '.format(tmp.ErrorMessage))

        except Exception as e:
            logger.error("Unable to GetProjectsDisplayData: "
                         "{} ".format(e.message))
            raise Exception("Unable to GetProjectsDisplayData: "
                            "{} ".format(e.message))

    def delete_projects(self, project_names):
        """

        delete projects by project names

        :param project_names:
        :return:
        """
        project_ids_number = []

        for projectName in project_names:
            project_id = self.get_project_id_by_name(projectName)
            if project_id:
                project_ids_number.append(project_id)

        logger.warning(" deleting_projects >>> project names {} : "
                       "project ids {} ".format(', '.join(project_names), project_ids_number))
        project_ids = self.client.factory.create('ArrayOfLong')
        project_ids.long = project_ids_number

        try:
            tmp = self.client.service.DeleteProjects(self.session_id, project_ids)

            if not tmp.IsSuccesfull:
                logger.error(' Fail to delete projects: '
                             '{} '.format(tmp.ErrorMessage))
                raise Exception(' Fail to delete projects: '
                                '{} '.format(tmp.ErrorMessage))

        except Exception as e:
            logger.error("Unable to DeleteProjects: "
                         "{} ".format(e.message))
            raise Exception("Unable to DeleteProjects: "
                            "{} ".format(e.message))

    def branch_project_by_id(self, project_name, new_branch_project_name):
        """

        This API client can create a branch for an existing project.

        To create a new project, first run a scan with a new project name,
        and then branch the existing project as described here.

        :param project_name: The name of the project that will be branched.
        :type project_name: String
        :param new_branch_project_name: The new project name of the branched project.
        :type new_branch_project_name: String
        :return: project_id
        """

        try:
            origin_project_id = self.get_project_id_by_name(project_name)

            if origin_project_id:
                tmp = self.client.service.BranchProjectById(self.session_id,
                                                            origin_project_id,
                                                            new_branch_project_name)
                if tmp.IsSuccesfull:
                    project_id = tmp.ProjectID
                    logger.info('branch_project_by_id, project {} '
                                'has project id {}'.format(project_name, project_id))
                    return project_id
                else:
                    logger.error("Error establishing connection: "
                                 "{} ".format(tmp.ErrorMessage))
                    raise Exception("Error establishing connection: "
                                    "{} ".format(tmp.ErrorMessage))

            else:
                logger.error("branch_project_by_id, Project does not exist.")
                raise Exception("branch_project_by_id, Project does not exist.")

        except Exception as e:
            logger.error("Unable to BranchProjectById: "
                         "{} ".format(e.message))
            raise Exception("Unable to BranchProjectById: "
                            "{} ".format(e.message))

    def cancel_scan(self, scan_run_id):
        """

        The API client can cancel a scan in progress.
        The scan can be canceled while waiting in the queue or during a scan.

        :param scan_run_id:
        :type scan_run_id: string
        :return:
        """
        try:
            logger.warning("cancel_scan, scan run id {}".format(scan_run_id))
            response = self.client.service.CancelScan(self.session_id,
                                                      scan_run_id)

            if not response.IsSuccesfull:
                logger.error(" Fail to CancelScan: {} ".format(response.ErrorMessage))
                raise Exception(" Fail to CancelScan: "
                                "{} ".format(response.ErrorMessage))

        except Exception as e:
            logger.error("Unable to CancelScan: {} ".format(e.message))
            raise Exception("Unable to CancelScan: "
                            "{} ".format(e.message))

    def create_scan_report(self, scan_id, report_type="PDF"):
        """

        The API client can generate a result report for a scan, by Scan ID.

        :param scan_id:
        :param report_type: report_type should be member of the list: ["PDF", "RTF", "CSV", "XML"]
        :return: report_id
        """
        report_request = self.client.factory.create('CxWSReportRequest')
        ws_report_type = self.client.factory.create('CxWSReportType')
        report_request.ScanID = scan_id

        if report_type == "PDF":
            report_request.Type = ws_report_type.PDF
        elif report_type == "RTF":
            report_request.Type = ws_report_type.RTF
        elif report_type == "CSV":
            report_request.Type = ws_report_type.CSV
        elif report_type == "XML":
            report_request.Type = ws_report_type.XML
        else:
            logger.error(' Report type not supported, report_type should be '
                         'member of the list: ["PDF", "RTF", "CSV", "XML"] ')
            raise Exception(' Report type not supported, report_type should be'
                            ' member of the list: ["PDF", "RTF", "CSV", "XML"] ')

        try:
            tmp = self.client.service.CreateScanReport(self.session_id, report_request)

            if tmp.IsSuccesfull:
                report_id = tmp.ID
                logger.info("begin to create report, "
                            "scan_id {} has report_id {}".format(scan_id, report_id))
                return report_id

            else:
                raise Exception(' Fail to CreateScanReport %s'.format(tmp.ErrorMessage))

        except Exception as e:
            raise Exception("Unable to CreateScanReport: {} ".format(e.message))

    def delete_scans(self, scan_ids_number):
        """

        The API client can delete requested scans.
        Scans that are currently running won't be deleted.
        If there's even a single scan that the user can't delete (due to security reasons)
        the operation will fail and an error message is returned.

        :return:
        """
        scan_ids_number = scan_ids_number or []
        scan_ids = self.client.factory.create('ArrayOfLong')
        scan_ids.long = scan_ids_number
        try:
            logger.warning('delete_scans, scan_ids {}'.format(scan_ids_number))
            tmp = self.client.service.DeleteScans(self.session_id, scan_ids)

            if not tmp.IsSuccesfull:
                logger.error(' Fail to DeleteScans {} '.format(tmp.ErrorMessage))
                raise Exception(' Fail to DeleteScans {} '.format(tmp.ErrorMessage))

        except Exception as e:
            logger.error("Unable to DeleteScans: {} ".format(e.message))
            raise Exception("Unable to DeleteScans: {} ".format(e.message))

    def get_user_id_by_name(self, user_name):
        """

        get user id by name.

        :param user_name:
        :return: user id
        """
        user_id = None

        users = self.get_all_users()
        for user in users:
            if user.UserName == user_name:
                user_id = user.ID
                break

        if not user_id:
            logger.error("user {} does not exist in Checkmarx server".format(user_name))
            raise Exception("user {} does not exist in Checkmarx server".format(user_name))

        logger.info('user {} has id {}'.format(user_name, user_id))
        return user_id

    def delete_user(self, user_name):
        """

        delete user from Checkmarx server.

        :param user_name:
        :return:
        """
        user_id = self.get_user_id_by_name(user_name)

        try:
            logger.warning("deleting user {}".format(user_name))
            tmp = self.client.service.DeleteUser(self.session_id, user_id)

            if not tmp.IsSuccesfull:
                logger.error(' Fail to DeleteUser {} '.format(tmp.ErrorMessage))
                raise Exception(' Fail to DeleteUser {} '.format(tmp.ErrorMessage))

        except Exception as e:
            logger.error("Unable to DeleteUser: {} ".format(e.message))
            raise Exception("Unable to DeleteUser: {} ".format(e.message))

    def get_scan_report(self, report_id):
        """

        Once a scan result report has been generated and the report is ready,
        the API client can retrieve the report's content.

        :param report_id:
        :return:
        """
        try:
            tmp = self.client.service.GetScanReport(self.session_id, report_id)

            if tmp.IsSuccesfull:
                scan_results = tmp.ScanResults
                contain_all_results = tmp.containsAllResults
                logger.info("getting report {} data, containsAllResults: {}".format(report_id, contain_all_results))
                return scan_results, contain_all_results
            else:
                logger.error(" unable to GetScanReport: {} ".format(tmp.ErrorMessage))
                raise Exception(" unable to GetScanReport: {} ".format(tmp.ErrorMessage))

        except Exception as e:
            logger.error("Unable to GetScanReport: {} ".format(e.message))
            raise Exception("Unable to GetScanReport: {} ".format(e.message))

    def get_status_of_single_scan(self, run_id):
        """

        After running a scan, The API client can get the scan status and its details.
        To do this, the API will first need the scan's Run ID.
        The obtained details include the scan's Scan ID, which can be subsequently
        used for commenting and reports.

        :param run_id:
        :return:
        """
        try:
            tmp = self.client.service.GetStatusOfSingleScan(self.session_id, run_id)

            if tmp.IsSuccesfull:
                current_status = tmp.CurrentStatus
                scan_id = tmp.ScanId
                return current_status, scan_id
            else:
                logger.error(" unable to GetStatusOfSingleScan: {} ".format(tmp.ErrorMessage))
                raise Exception(" unable to GetStatusOfSingleScan: {} ".format(tmp.ErrorMessage))

        except Exception as e:
            logger.error("Unable to GetScanReport: {} ".format(e.message))
            raise Exception("Unable to GetScanReport: {} ".format(e.message))

    def get_scan_report_status(self, report_id):
        """

        The API client can track the status of a report generation request.

        :param report_id:
        :return:
        """
        try:
            tmp = self.client.service.GetScanReportStatus(self.session_id, report_id)

            if tmp.IsSuccesfull:
                is_ready = tmp.IsReady
                is_failed = tmp.IsFailed
                logger.info("report {} status, IsReady: {}, IsFailed: {}".format(report_id, is_ready, is_failed))
                return is_ready, is_failed
            else:
                logger.error(" unable to GetScanReportStatus: {} ".format(tmp.ErrorMessage))
                raise Exception(" unable to GetScanReportStatus: {} ".format(tmp.ErrorMessage))

        except Exception as e:
            raise Exception("Unable to GetScanReport: {} ".format(e.message))

    def get_all_users(self):
        """
        get all users from the Checkmarx server.

        :return: user list
        """
        try:
            tmp = self.client.service.GetAllUsers(self.session_id)
            if tmp.IsSuccesfull:
                user_data_list = tmp.UserDataList.UserData
                return user_data_list
            else:
                logger.error('Fail to GetAllUsers: {}'.format(tmp.ErrorMessage))
                raise Exception('Fail to GetAllUsers: '
                                '{}'.format(tmp.ErrorMessage))
        except Exception as e:
            logger.error("Unable to GetAllUsers: {} ".format(e.message))
            raise Exception("Unable to GetAllUsers: {} ".format(e.message))

    def get_project_configuration(self, project_name):
        """

        get project configuration

        :param project_name:
        :return:
        """
        try:
            project_id = self.get_project_id_by_name(project_name)
            if project_id:
                tmp = self.client.service.GetProjectConfiguration(self.session_id,
                                                                  project_id)
                if tmp.IsSuccesfull:
                    project_config = tmp.ProjectConfig
                    permission = tmp.Permission
                    return project_config, permission
                else:
                    logger.error(' unable to GetProjectConfiguration : '
                                 '{}'.format(tmp.ErrorMessage))
                    raise Exception(' unable to GetProjectConfiguration :'
                                    ' {}'.format(tmp.ErrorMessage))
            else:
                logger.error(' project not exists: {}'.format(project_name))
                raise Exception(' project not exists: {}'.format(project_name))

        except Exception as e:
            logger.error("Unable to GetProjectConfiguration: {} ".format(e.message))
            raise Exception("Unable to GetProjectConfiguration: "
                            "{} ".format(e.message))

    def get_scan_summary(self, scan_id):
        """

        get scan summary

        :param scan_id:
        :return:
        """
        try:
            tmp = self.client.service.GetScanSummary(self.session_id, scan_id)

            if tmp.IsSuccesfull:
                scan_summary_result = tmp
                return scan_summary_result
            else:
                logger.error('Fail to GetScanSummaryResult:'
                             '{} '.format(tmp.ErrorMessage))
                raise Exception('Fail to GetScanSummaryResult: '
                                '{} '.format(tmp.ErrorMessage))

        except Exception as e:
            logger.error("Unable to GetScanSummaryResult:"
                         "{} ".format(e.message))
            raise Exception("Unable to GetScanSummaryResult: "
                            "{} ".format(e.message))

    def get_team_ldap_groups_mapping(self, team_id):
        """
        get team LDAP groups mapping
        :param team_id:
        :return:
        """
        try:
            tmp = self.client.service.GetTeamLdapGroupsMapping(self.session_id,
                                                               team_id)
            if tmp.IsSuccesfull:
                team_ldap_groups_mapping = tmp.LdapGroups
                return team_ldap_groups_mapping
        except Exception as e:
            logger.error("Unable to GetTeamLdapGroupsMapping: "
                         "{} ".format(e.message))
            raise Exception("Unable to GetTeamLdapGroupsMapping: "
                            "{} ".format(e.message))

    def logout(self):
        try:
            response = self.client.service.Logout(self.session_id)
            if not response.IsSuccesfull:
                logger.error('Fail to Logout: {}'.format(response.ErrorMessage))
                raise Exception('Fail to Logout:'
                                ' {}'.format(response.ErrorMessage))

        except Exception as e:
            logger.error("Unable to Logout: {} ".format(e.message))
            raise Exception("Unable to Logout: "
                            "{} ".format(e.message))

    def set_team_ldap_groups_mapping(self, team_id):
        """

        set team LDAP groups mapping

        :param team_id:
        :return:
        """

        ldap_groups = self.client.factory.create('ArrayOfCxWSLdapGroupMapping')
        ldap_group = self.client.factory.create('CxWSLdapGroupMapping')
        ldap_groups.CxWSLdapGroupMapping = ldap_group
        ldap_groups.CxWSLdapGroupMapping.LdapServerId = None
        cx_ws_ldap_group = self.client.factory.create('CxWSLdapGroup')
        ldap_groups.CxWSLdapGroupMapping.LdapGroup = cx_ws_ldap_group
        ldap_groups.CxWSLdapGroupMapping.LdapGroup.DN = None
        ldap_groups.CxWSLdapGroupMapping.LdapGroup.Name = None

        try:
            tmp = self.client.service.SetTeamLdapGroupsMapping(self.session_id,
                                                               team_id,
                                                               ldap_groups)
            if tmp.IsSuccesfull:
                project_id = tmp.ProjectID
                run_id = tmp.RunId
                return project_id, run_id
            else:
                logger.error("Fail to SetTeamLdapGroupsMapping: "
                             "{} ".format(tmp.ErrorMessage))
                raise Exception("Fail to SetTeamLdapGroupsMapping: "
                                "{} ".format(tmp.ErrorMessage))
        except Exception as e:
            logger.error("Unable to SetTeamLdapGroupsMapping: {} ".format(e.message))
            raise Exception("Unable to SetTeamLdapGroupsMapping: "
                            "{} ".format(e.message))

    def stop_data_retention(self):
        """

        stop data retention

        :return:
        """
        try:
            tmp = self.client.service.StopDataRetention(self.session_id)
            if not tmp.IsSuccesfull:
                logger.error("Fail to StopDataRetention: {} ".format(tmp.ErrorMessage))
                raise Exception("Fail to StopDataRetention: "
                                "{} ".format(tmp.ErrorMessage))

        except Exception as e:
            logger.error("Unable to StopDataRetention: {} ".format(e.message))
            raise Exception("Unable to StopDataRetention: "
                            "{} ".format(e.message))

    def update_project_configuration(self, project_name):
        """

        update project configuration

        :param project_name:
        :return:
        """
        project_id = self.get_project_id_by_name(project_name)
        project_configuration = self.get_project_configuration(project_name)
        schedule_type = self.client.factory.create('ScheduleType')
        project_configuration.ScheduleSettings.Schedule = schedule_type.Now

        try:
            tmp = self.client.service.UpdateProjectConfiguration(self.session_id,
                                                                 project_id,
                                                                 project_configuration)
            if not tmp.IsSuccesfull:
                logger.error("Fail to update_project_configuration: "
                             "{} ".format(tmp.ErrorMessage))
                raise Exception("Fail to update_project_configuration: "
                                "{} ".format(tmp.ErrorMessage))
        except Exception as e:
            logger.error("Unable to update_project_configuration: {} ".format(e.message))
            raise Exception("Unable to update_project_configuration: "
                            "{} ".format(e.message))

    def update_project_incremental_configuration(self, project_name):
        """

        update project incremental configuration.

        The API client can change the configuration of an existing project.
        To create a new project, first run a scan with a new project name,
        and then configure the project as described here.

        :param project_name:
        :return:
        """
        project_id = self.get_project_id_by_name(project_name)
        project_configuration = self.get_project_configuration(project_name)
        schedule_type = self.client.factory.create('ScheduleType')
        project_configuration.ScheduleSettings.Schedule = schedule_type.Now

        try:
            tmp = self.client.service.UpdateProjectIncrementalConfiguration(self.session_id,
                                                                            project_id)
            if not tmp.IsSuccesfull:
                logger.error("Fail to UpdateProjectIncrementalConfiguration: "
                             "{} ".format(tmp.ErrorMessage))
                raise Exception(
                    "Fail to UpdateProjectIncrementalConfiguration: "
                    "{} ".format(tmp.ErrorMessage))

        except Exception as e:
            logger.error("Unable to UpdateProjectIncrementalConfiguration:"
                         "{} ".format(e.message))
            raise Exception(
                "Unable to UpdateProjectIncrementalConfiguration: "
                "{} ".format(e.message))

    def update_scan_comment(self, scan_id, comment):
        """

        update scan comment

        :param scan_id:
        :param comment:
        :return:
        """
        try:
            tmp = self.client.service.UpdateScanComment(self.session_id,
                                                        scan_id, comment)
            if not tmp.IsSuccesfull:
                logger.error("Fail to UpdateProjectIncrementalConfiguration: "
                             "{} ".format(tmp.ErrorMessage))
                raise Exception(
                    "Fail to UpdateProjectIncrementalConfiguration: "
                    "{} ".format(tmp.ErrorMessage))

        except Exception as e:
            logger.error("Unable to UpdateProjectIncrementalConfiguration: "
                         "{} ".format(e.message))
            raise Exception("Unable to UpdateProjectIncrementalConfiguration: "
                            "{} ".format(e.message))

    def scan(self, project_name, preset_name, scan_configuration_id=1,
             source_location_type='Local', file_name="",
             shared_user_name="", shared_password="",
             shared_path="", shared_include_sub_tree=True,
             source_control_port=8080,
             repository_type="GIT", use_ssl=False, use_ssh=True, server_name="",
             protocol="SSH", repository_name="repo.git", protocol_parameters="",
             git_branch="refs/heads/master", git_view_type="TAGS_AND_HEADS",
             ssl_private_key_file_path="", perforce_browsing_mode="None",
             is_public=True, is_private_scan=False, is_incremental=False,
             comment='Empty comment.', ignore_scan_with_unchanged_code=False,
             exclude_files=None, exclude_folders=None):
        """

        The API client can call an immediate scan. Depending on whether the submitted
        project name (CliScanArgs.PrjSettings.ProjectName) already exists,
        the scan is called for the existing CxSAST project or a new project is created.

        example 1: scan, Local Zip source code file.
        scan(project_name='dtest', preset_name='All', scan_configuration_id=1,
             source_location_type="Local", file_name="/home/alex/Downloads/bodgeit-1.4.0.zip",
             is_public=True, is_private_scan=False, is_incremental=False, comment='Empty comment.',
             ignore_scan_with_unchanged_code=False, exclude_files=None, exclude_folders=None)

        example 2: scan, GIT repository with SSH protocol
        Gitlab repository url: ssh://git@192.168.31.204:10022/happy/checkmarx-java.git
        scan(project_name='dtest', preset_name='All', scan_configuration_id=1,
             source_location_type="SourceControl", is_public=True, is_private_scan=False,
             is_incremental=False, comment='Empty comment.', ignore_scan_with_unchanged_code=False,
             exclude_files=None, exclude_folders=None, use_ssl=False, use_ssh=True,
             server_name="ssh://git@192.168.31.204:10022/happy/checkmarx-java.git",
             protocol="SSH", repository_name="checkmarx-java",
             protocol_parameters="happy/checkmarx-java.git", git_branch="refs/heads/master",
             git_view_type="TAGS_AND_HEADS", ssl_private_key_file_path="/home/alex/Downloads/id_rsa")

        example 3: scan, GIT repository with http protocol
        Gitlab repository url: http://192.168.31.204:10080/happy/checkmarx-java.git
        scan(project_name='dtest', preset_name='All', scan_configuration_id=1,
             source_location_type="SourceControl",is_public=True, is_private_scan=False,
             is_incremental=False, comment='Empty comment.', ignore_scan_with_unchanged_code=False,
             exclude_files=None, exclude_folders=None, use_ssl=False, use_ssh=False,
             server_name="http://happy:Password01@192.168.31.204:10080/happy/checkmarx-java.git",
             protocol="PasswordServer", repository_name="checkmarx-java",
             protocol_parameters="happy/checkmarx-java.git", git_branch="refs/heads/master",
             git_view_type="TAGS_AND_HEADS", ssl_private_key_file_path="/home/alex/Downloads/id_rsa")


        :param project_name:

        :param preset_name:
                Checkmarx default preset list:

                preset name : preset id

                "Checkmarx Default": 36,
                "All": 1,
                "Android": 9,
                "Apple Secure Coding Guide": 19,
                "Default": 7,
                "Default 2014": 17,
                "Empty preset": 6,
                "Error handling": 2,
                "High and Medium": 3,
                "High and Medium and Low": 13,
                "HIPAA": 12,
                "JSSEC": 20,
                "MISRA_C": 10,
                "MISRA_CPP": 11,
                "Mobile": 14,
                "OWASP Mobile TOP 10 - 2016": 37,
                "OWASP TOP 10 - 2010": 4,
                "OWASP TOP 10 - 2013": 15,
                "PCI": 5,
                "SANS top 25": 8,
                "WordPress": 16,
                "XS": 35

        :param scan_configuration_id: Integer
                1 English (Default Configuration), 100002 Japanese (Shift-JIS), 100003 Korea

        :param source_location_type: String
                'Local', 'Shared', 'SourceControl'

        :param file_name: String
                please give the full path of the file name

        :param shared_user_name: String
        :param shared_password: String
        :param shared_path: String
        :param shared_include_sub_tree: Boolean
        :param source_control_port: Integer
        :param repository_type: String
            "TFS", "SVN", "GIT", "Perforce"
        :param use_ssl: Boolean
            True, False
        :param use_ssh: Boolean
            True, False
        :param server_name: GIT repository url,
            ssh protocol:
                example: ssh://git@localhost:10022/happy/checkmarx-java.git
            HTTP, HTTPS protocol:
                format: <protocol>://<user>:<password>@<server>/<repository_name>.git
                example: http://happy:Password01@172.16.28.166:10080/happy/checkmarx-java.git
                note: password should not contain special characters, eg: !

        :param protocol: [WindowsAuthentication, SSL, SSH, PasswordServer]
        :param repository_name: repository name
        :param protocol_parameters:
        :param git_branch:  "refs/heads/master"
        :param git_view_type: [TAGS, HEADS, TAGS_AND_HEADS, ALL]
        :param ssl_private_key_file_path: string
        :param perforce_browsing_mode: String

        :param is_public: Boolean
        :param is_private_scan: Boolean
        :param is_incremental: Boolean
        :param comment: String
        :param ignore_scan_with_unchanged_code: Boolean
        :param exclude_folders: String
                folders to be excluded, a comma-separated list of folders,
                including wildcards to exclude. example: docs, test
        :param exclude_files: String
                files to be excluded, a comma-separated list of files,
                including wildcards to exclude. example: *.txt, *.doc
        :return:
        """

        scan_args = self.client.factory.create('CliScanArgs')

        project_settings = self.client.factory.create('ProjectSettings')
        scan_args.PrjSettings = project_settings
        scan_args.PrjSettings.projectID = 0
        # CxSAST 8.6.0 requires PrjSettings.TaskId, just set it to 0
        scan_args.PrjSettings.TaskId = 0
        # Set project name from parameter
        if project_name:
            scan_args.PrjSettings.ProjectName = project_name
        else:
            raise Exception('Project name is missing!')
        # Set preset name from parameter
        if preset_name:
            preset_id = self.get_preset_id_by_name(preset_name)
            # Set preset, "Checkmarx Default" has id 36
            scan_args.PrjSettings.PresetID = preset_id or 36
        else:
            raise Exception('Preset name is missing!')
        scan_args.PrjSettings.AssociatedGroupID = self.get_first_associated_group_id()
        # Set the source files encoding, English = 1
        if scan_configuration_id in [1, 100002, 100003]:
            scan_args.PrjSettings.ScanConfigurationID = scan_configuration_id
        else:
            raise Exception('scan configuration id is invalid!')
        scan_args.PrjSettings.IsPublic = is_public
        project_origin = self.client.factory.create('ProjectOrigin')
        scan_args.PrjSettings.OpenSourceAnalysisOrigin = project_origin.LocalPath

        source_code_settings = self.client.factory.create('SourceCodeSettings')
        scan_args.SrcCodeSettings = source_code_settings

        slt = self.client.factory.create('SourceLocationType')
        if source_location_type == 'Local':
            scan_args.SrcCodeSettings.SourceOrigin = slt.Local

            container = self.client.factory.create('LocalCodeContainer')
            scan_args.SrcCodeSettings.PackagedCode = container
            # scan_args.SrcCodeSettings.PackagedCode.FileName
            scan_args.SrcCodeSettings.PackagedCode.FileName = 'test'

            try:
                with open(file_name, 'rb') as f:
                    file_content = f.read().encode('base64')
                    scan_args.SrcCodeSettings.PackagedCode.ZippedFile = file_content
            except Exception as e:
                logger.error('Fail to open file : {}'.format(e.message))
                raise Exception('Fail to open file : {}'.format(e.message))

        elif source_location_type == 'Shared':
            scan_args.SrcCodeSettings.SourceOrigin = slt.Shared
            credential = self.client.factory.create('Credentials')
            scan_args.SrcCodeSettings.UserCredentials = credential
            scan_args.SrcCodeSettings.UserCredentials.User = shared_user_name
            scan_args.SrcCodeSettings.UserCredentials.Pass = shared_password
            scan_path_list = self.client.factory.create('ArrayOfScanPath')
            scan_args.SrcCodeSettings.PathList = scan_path_list
            scan_path = self.client.factory.create('ScanPath')
            scan_args.SrcCodeSettings.PathList.ScanPath = scan_path
            scan_args.SrcCodeSettings.PathList.ScanPath.Path = shared_path
            scan_args.SrcCodeSettings.PathList.ScanPath.IncludeSubTree = shared_include_sub_tree

        elif source_location_type == 'SourceControl':
            scan_args.SrcCodeSettings.SourceOrigin = slt.SourceControl

            scan_args.SrcCodeSettings.SourceControlSetting.Port = source_control_port or 8080
            scan_args.SrcCodeSettings.SourceControlSetting.UseSSL = use_ssl
            scan_args.SrcCodeSettings.SourceControlSetting.UseSSH = use_ssh
            scan_args.SrcCodeSettings.SourceControlSetting.ServerName = server_name
            re_type = self.client.factory.create('RepositoryType')
            scan_args.SrcCodeSettings.SourceControlSetting.RepositoryName = repository_name

            protocol_type = self.client.factory.create('SourceControlProtocolType')
            if protocol == "WindowsAuthentication":
                scan_args.SrcCodeSettings.SourceControlSetting.Protocol = protocol_type.WindowsAuthentication
            elif protocol == "SSL":
                scan_args.SrcCodeSettings.SourceControlSetting.Protocol = protocol_type.SSL
            elif protocol == "SSH" and use_ssh:
                scan_args.SrcCodeSettings.SourceControlSetting.Protocol = protocol_type.SSH
            elif protocol == "PasswordServer":
                scan_args.SrcCodeSettings.SourceControlSetting.Protocol = protocol_type.PasswordServer
            else:
                raise Exception(" Source control protocols only support "
                                "[WindowsAuthentication, SSL, SSH, PasswordServer]")
            scan_args.SrcCodeSettings.SourceControlSetting.ProtocolParameters = protocol_parameters

            if repository_type == "TFS":
                # TODO
                scan_args.SrcCodeSettings.SourceControlSetting.Repository = re_type.TFS
                credential = self.client.factory.create('Credentials')
                scan_args.SrcCodeSettings.SourceControlSetting.UserCredentials = credential
                scan_args.SrcCodeSettings.SourceControlSetting.UserCredentials.User = ""
                scan_args.SrcCodeSettings.SourceControlSetting.UserCredentials.Pass = ""
                pass
            elif repository_type == "SVN":
                # TODO
                scan_args.SrcCodeSettings.SourceControlSetting.Repository = re_type.SVN
                credential = self.client.factory.create('Credentials')
                scan_args.SrcCodeSettings.SourceControlSetting.UserCredentials = credential
                scan_args.SrcCodeSettings.SourceControlSetting.UserCredentials.User = ""
                scan_args.SrcCodeSettings.SourceControlSetting.UserCredentials.Pass = ""

                if use_ssh:
                    if ssl_private_key_file_path:
                        with open(ssl_private_key_file_path, 'r') as f:
                            ssl_private_key = f.read()
                            scan_args.SrcCodeSettings.SourceControlSetting.SSHPrivateKey = ssl_private_key
                    else:
                        logger.error(' you must define the full path of the private key.')
                        raise Exception(' you must define the full path of the private key.')
                pass
            elif repository_type == "GIT":
                scan_args.SrcCodeSettings.SourceControlSetting.Repository = re_type.GIT
                scan_args.SrcCodeSettings.SourceControlSetting.GITBranch = git_branch
                git_ls_view_type = self.client.factory.create('GitLsRemoteViewType')
                if git_view_type == "TAGS":
                    scan_args.SrcCodeSettings.SourceControlSetting.GitLsViewType = git_ls_view_type.TAGS
                elif git_view_type == "HEADS":
                    scan_args.SrcCodeSettings.SourceControlSetting.GitLsViewType = git_ls_view_type.HEADS
                elif git_view_type == "TAGS_AND_HEADS":
                    scan_args.SrcCodeSettings.SourceControlSetting.GitLsViewType = git_ls_view_type.TAGS_AND_HEADS
                elif git_view_type == "ALL":
                    scan_args.SrcCodeSettings.SourceControlSetting.GitLsViewType = git_ls_view_type.ALL
                else:
                    logger.error(' git ls view type not supported, only support '
                                 '[TAGS, HEADS, TAGS_AND_HEADS, ALL]')
                    raise Exception(' git ls view type not supported, only support '
                                    '[TAGS, HEADS, TAGS_AND_HEADS, ALL]')

                if ssl_private_key_file_path:
                    with open(ssl_private_key_file_path, 'r') as f:
                        ssl_private_key = f.read()
                        scan_args.SrcCodeSettings.SourceControlSetting.SSHPrivateKey = ssl_private_key
                else:
                    logger.error(' you must define the full path of the private key.')
                    raise Exception(' you must define the full path of the private key.')

                perforce_browsing_mode = self.client.factory.create('CxWSPerforceBrowsingMode')
                scan_args.SrcCodeSettings.SourceControlSetting.PerforceBrowsingMode = perforce_browsing_mode.None
            elif repository_type == "Perforce":
                # TODO
                scan_args.SrcCodeSettings.SourceControlSetting.Repository = re_type.Perforce
                credential = self.client.factory.create('Credentials')
                scan_args.SrcCodeSettings.SourceControlSetting.UserCredentials = credential
                scan_args.SrcCodeSettings.SourceControlSetting.UserCredentials.User = ""
                scan_args.SrcCodeSettings.SourceControlSetting.UserCredentials.Pass = ""

                pbm = self.client.factory.create('CxWSPerforceBrowsingMode')
                if perforce_browsing_mode == 'Depot':
                    scan_args.SrcCodeSettings.SourceControlSetting.PerforceBrowsingMode = pbm.Depot
                elif perforce_browsing_mode == 'Workspace':
                    scan_args.SrcCodeSettings.SourceControlSetting.PerforceBrowsingMode = pbm.Workspace
                else:
                    scan_args.SrcCodeSettings.SourceControlSetting.PerforceBrowsingMode = pbm.None
                pass
            else:
                raise Exception("source control system only support"
                                " ['TFS', 'SVN', 'GIT', 'Perforce'] ")

        else:
            raise Exception("source location type only support"
                            " ['Local', 'Shared', 'SourceControl'] ")

        source_filter_lists = self.client.factory.create('SourceFilterPatterns')
        scan_args.SrcCodeSettings.SourceFilterLists = source_filter_lists
        scan_args.SrcCodeSettings.SourceFilterLists.ExcludeFilesPatterns = exclude_files
        scan_args.SrcCodeSettings.SourceFilterLists.ExcludeFoldersPatterns = exclude_folders

        scan_args.IsPrivateScan = is_private_scan
        scan_args.IsIncremental = is_incremental
        scan_args.Comment = comment
        scan_args.IgnoreScanWithUnchangedCode = ignore_scan_with_unchanged_code

        cx_client_type = self.client.factory.create('CxClientType')
        scan_args.ClientOrigin = cx_client_type.SDK

        try:
            response = self.client.service.Scan(self.session_id, scan_args)

            if response.IsSuccesfull:
                project_id = response.ProjectID
                run_id = response.RunId
                logger.info("project {} has been created "
                            "with project id {} and run id {} ".format(project_name,
                                                                       project_id,
                                                                       run_id))
                return project_id, run_id
            else:
                logger.error("Error establishing connection: "
                             "{} ".format(response.ErrorMessage))
                raise Exception("Error establishing connection: "
                                "{} ".format(response.ErrorMessage))

        except Exception as e:
            raise Exception("Unable to scan: {} ".format(e.message))
