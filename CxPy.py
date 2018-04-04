# coding=utf-8
# Python Dependencies
import base64
import re
import time
import logging
import os

from common import Common
from CxType.cli_scan_args import CliScanArgs

dir_path = os.path.dirname(os.path.realpath(__file__))

logging.basicConfig(filename=dir_path + '/checkmarx_soap_api.log',
                    format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

report_types = {
    "PDF": ".pdf",
    "RTF": ".rtf",
    "CSV": ".csv",
    "XML": ".xml",
}


class CxPy(Common):
    # Internal Variables for the Class
    errorLog = []
    ttlReport = 6
    timeWaitReport = 3

    ##########################################
    #
    # Functions Related to the functionality of the WSDL
    #
    ##########################################

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
        :rtype: Integer
        """

        try:
            origin_project_id = self.get_project_id_by_name(project_name)

            if not origin_project_id:
                logger.error("branch_project_by_id, Project does not exist.")
                raise Exception("branch_project_by_id, Project does not exist.")

            tmp = self.client.service.BranchProjectById(self.session_id,
                                                        origin_project_id,
                                                        new_branch_project_name)
            if not tmp.IsSuccesfull:
                logger.error("Error establishing connection: "
                             "{} ".format(tmp.ErrorMessage))
                raise Exception("Error establishing connection: "
                                "{} ".format(tmp.ErrorMessage))

            project_id = tmp.ProjectID
            logger.info('branch_project_by_id, project {} '
                        'has project id {}'.format(project_name, project_id))
            return project_id

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
        :rtype: dictionary
        """
        try:
            logger.warning("cancel_scan, scan run id {}".format(scan_run_id))
            response = self.client.service.CancelScan(self.session_id,
                                                      scan_run_id)

            if not response.IsSuccesfull:
                logger.error(" Fail to CancelScan: {} ".format(response.ErrorMessage))
                raise Exception(" Fail to CancelScan: "
                                "{} ".format(response.ErrorMessage))

            return {"success": True, "runId": scan_run_id}

        except Exception as e:
            logger.error("Unable to CancelScan: {} ".format(e.message))
            raise Exception("Unable to CancelScan: "
                            "{} ".format(e.message))

    def create_scan_report(self, scan_id, report_type="PDF"):
        """

        The API client can generate a result report for a scan, by Scan ID.

        :param scan_id:
        :type scan_id: Integer
        :param report_type: report_type should be member of the list: ["PDF", "RTF", "CSV", "XML"]
        :type report_type: String
        :return: report_id
        :rtype: Integer
        """
        report_request = self.client.factory.create('CxWSReportRequest')
        ws_report_type = self.client.factory.create('CxWSReportType')
        report_request.ScanID = scan_id
        if report_type not in ["PDF", "RTF", "CSV", "XML"]:
            logger.error(' Report type not supported, report_type should be '
                         'member of the list: ["PDF", "RTF", "CSV", "XML"] ')
            raise Exception(' Report type not supported, report_type should be'
                            ' member of the list: ["PDF", "RTF", "CSV", "XML"] ')

        report_request.Type = ws_report_type.__getitem__(report_type)

        try:
            tmp = self.client.service.CreateScanReport(self.session_id, report_request)

            if not tmp.IsSuccesfull:
                raise Exception(' Fail to CreateScanReport %s'.format(tmp.ErrorMessage))

            report_id = tmp.ID
            logger.info("begin to create report, "
                        "scan_id {} has report_id {}".format(scan_id, report_id))
            return report_id

        except Exception as e:
            raise Exception("Unable to CreateScanReport: {} ".format(e.message))

    # def delete_projects(self, project_names):
    #     """
    #
    #     delete projects by project names
    #
    #     :param project_names:
    #     :type project_names: list
    #     :return: dictionary
    #     """
    #     project_ids_number = []
    #     project_names_exist = []
    #     project_names_not_exist = []
    #
    #     for projectName in project_names:
    #         project_id = self.get_project_id_by_name(projectName)
    #         if project_id:
    #             project_names_exist.append(projectName)
    #             project_ids_number.append(project_id)
    #         else:
    #             project_names_not_exist.append(projectName)
    #
    #     logger.warning(" deleting_projects >>> project names {} : "
    #                    "project ids {} ".format(', '.join(project_names), project_ids_number))
    #     project_ids = self.client.factory.create('ArrayOfLong')
    #     project_ids.long.extend(project_ids_number)
    #
    #     try:
    #         tmp = self.client.service.DeleteProjects(self.session_id, project_ids)
    #
    #         if not tmp.IsSuccesfull:
    #             logger.error(' Fail to delete projects: '
    #                          '{} '.format(tmp.ErrorMessage))
    #             raise Exception(' Fail to delete projects: '
    #                             '{} '.format(tmp.ErrorMessage))
    #
    #         return {"success": True,
    #                 "deleted_projects": project_names_exist,
    #                 "projects_not_exit": project_names_not_exist}
    #
    #     except Exception as e:
    #         logger.error("Unable to DeleteProjects: "
    #                      "{} ".format(e.message))
    #         raise Exception("Unable to DeleteProjects: "
    #                         "{} ".format(e.message))

    def delete_scans(self, scan_ids_number):
        """

        The API client can delete requested scans.
        Scans that are currently running won't be deleted.
        If there's even a single scan that the user can't delete (due to security reasons)
        the operation will fail and an error message is returned.

        :param scan_ids_number:
        :type scan_ids_number: list
        :return:
        :rtype: dictionary
        """
        scan_ids_number = scan_ids_number or []
        scan_ids = self.client.factory.create('ArrayOfLong')
        scan_ids.long.extend(scan_ids_number)
        try:
            logger.warning('delete_scans, scan_ids {}'.format(scan_ids_number))
            tmp = self.client.service.DeleteScans(self.session_id, scan_ids)

            if not tmp.IsSuccesfull:
                logger.error(' Fail to DeleteScans {} '.format(tmp.ErrorMessage))
                raise Exception(' Fail to DeleteScans {} '.format(tmp.ErrorMessage))

            return {"success": True,
                    'scanIds': scan_ids_number}

        except Exception as e:
            logger.error("Unable to DeleteScans: {} ".format(e.message))
            raise Exception("Unable to DeleteScans: {} ".format(e.message))

    # def delete_user(self, user_name):
    #     """
    #
    #     delete user from Checkmarx server.
    #
    #     :param user_name:
    #     :type user_name: string
    #     :return:
    #     :rtype: dictionary
    #     """
    #     user_id = self.get_user_id_by_name(user_name)
    #
    #     try:
    #         logger.warning("deleting user {}".format(user_name))
    #         tmp = self.client.service.DeleteUser(self.session_id, user_id)
    #
    #         if not tmp.IsSuccesfull:
    #             logger.error(' Fail to DeleteUser {} '.format(tmp.ErrorMessage))
    #             raise Exception(' Fail to DeleteUser {} '.format(tmp.ErrorMessage))
    #
    #         return {"success": True,
    #                 "deleted_user": user_name}
    #
    #     except Exception as e:
    #         logger.error("Unable to DeleteUser: {} ".format(e.message))
    #         raise Exception("Unable to DeleteUser: {} ".format(e.message))

    def execute_data_retention(self, data_retention_type, num_of_scans_to_preserve,
                               start_date, end_date, duration_limit_in_hours):
        """
        :param data_retention_type:  [NumOfScansToPreserve,  DatesRange]
        :type data_retention_type: string
        :param num_of_scans_to_preserve:
        :type num_of_scans_to_preserve: integer
        :param start_date:
        :type start_date: long
        :param end_date:
        :type end_date: long
        :param duration_limit_in_hours:
        :type duration_limit_in_hours: long
        :return:
        """
        try:
            drt = self.client.factory.create("CxDataRetentionType")
            data_retention_configuration = self.client.factory.create("CxDataRetentionConfiguration")
            data_retention_configuration.DataRetentionType = drt.__getitem__(data_retention_type)
            data_retention_configuration.NumOfScansToPreserve = num_of_scans_to_preserve
            data_retention_configuration.StartDate = start_date
            data_retention_configuration.EndDate = end_date
            data_retention_configuration.DurationLimitInHours = duration_limit_in_hours
            tmp = self.client.service.ExecuteDataRetention(self.session_id, data_retention_configuration)

            if not tmp.IsSuccesfull:
                logger.error(' Fail to execute_data_retention {} '.format(tmp.ErrorMessage))
                raise Exception(' Fail to execute_data_retention {} '.format(tmp.ErrorMessage))

            return "ExecuteDataRetention called successfully"

        except Exception as e:
            logger.error("Unable to execute_data_retention: {} ".format(e.message))
            raise Exception("Unable to execute_data_retention: {} ".format(e.message))

    def get_all_users(self):
        """
        get all users from the Checkmarx server.

        :return: user list
        :rtype: list
        """
        try:
            tmp = self.client.service.GetAllUsers(self.session_id)
            if not tmp.IsSuccesfull:
                logger.error('Fail to GetAllUsers: {}'.format(tmp.ErrorMessage))
                raise Exception('Fail to GetAllUsers: '
                                '{}'.format(tmp.ErrorMessage))
            user_data_list = tmp.UserDataList.UserData
            return user_data_list

        except Exception as e:
            logger.error("Unable to GetAllUsers: {} ".format(e.message))
            raise Exception("Unable to GetAllUsers: {} ".format(e.message))

    def get_associated_groups_list(self):
        """

        The API client can get information on all groups related to the current user.

        :return: CxWSResponseGroupList.GroupList contains an array of group data.

        """
        try:
            tmp = self.client.service.GetAssociatedGroupsList(self.session_id)

            if not tmp.IsSuccesfull:
                logger.error("get_associated_groups, Unable to get data from the server.")
                raise Exception("get_associated_groups, Unable to get data from the server.")

            return self.convert_to_json(tmp)
        except Exception as e:
            logger.error("get_associated_groups, Unable to GetAssociatedGroupsList: {} ".format(e.message))
            raise Exception("get_associated_groups, Unable to GetAssociatedGroupsList: {} ".format(e.message))

    def get_configuration_set_list(self):
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

            return self.convert_to_json(tmp)
        except Exception as e:
            logger.error("Unable to get_configuration_list: {} ".format(e.message))
            raise Exception("Unable to get_configuration_list: {} ".format(e.message))

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

            return self.convert_to_json(tmp)
        except Exception as e:
            logger.error("Unable to GetPresetList: {} ".format(e.message))
            raise Exception("Unable to GetPresetList: {} ".format(e.message))

    def get_project_configuration(self, project_name):
        """

        get project configuration

        :param project_name:
        :return:
        """
        try:
            project_id = self.get_project_id_by_name(project_name)

            if not project_id:
                logger.error(' project not exists: {}'.format(project_name))
                raise Exception(' project not exists: {}'.format(project_name))

            tmp = self.client.service.GetProjectConfiguration(self.session_id,
                                                              project_id)
            if not tmp.IsSuccesfull:
                logger.error(' unable to GetProjectConfiguration : '
                             '{}'.format(tmp.ErrorMessage))
                raise Exception(' unable to GetProjectConfiguration :'
                                ' {}'.format(tmp.ErrorMessage))
            project_config = tmp.ProjectConfig
            permission = tmp.Permission

            return project_config, permission

        except Exception as e:
            logger.error("Unable to GetProjectConfiguration: {} ".format(e.message))
            raise Exception("Unable to GetProjectConfiguration: "
                            "{} ".format(e.message))

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

            if not filter_on:
                return self.convert_to_json(tmp)
            else:
                return tmp.ProjectScannedList[0]
        except Exception as e:
            logger.error("Unable to GetProjectScannedDisplayData: "
                         "{} ".format(e.message))
            raise Exception("Unable to GetProjectScannedDisplayData: "
                            "{} ".format(e.message))

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

            if not filter_on:
                return self.convert_to_json(tmp)
            else:
                return tmp.projectList[0]
        except Exception as e:
            logger.error("Unable to GetProjectsDisplayData: "
                         "{} ".format(e.message))
            raise Exception("Unable to GetProjectsDisplayData: "
                            "{} ".format(e.message))

    def get_scan_report(self, report_id):
        """

        Once a scan result report has been generated and the report is ready,
        the API client can retrieve the report's content.

        :param report_id:
        :type report_id: integer
        :return: (scan_results, contain_all_results)
        :rtype: tuple
        """
        try:
            tmp = self.client.service.GetScanReport(self.session_id, report_id)

            if not tmp.IsSuccesfull:
                logger.error(" unable to GetScanReport: {} ".format(tmp.ErrorMessage))
                raise Exception(" unable to GetScanReport: {} ".format(tmp.ErrorMessage))

            scan_results = tmp.ScanResults
            contain_all_results = tmp.containsAllResults
            logger.info("getting report {} data, containsAllResults: "
                        "{}".format(report_id, contain_all_results))
            return scan_results, contain_all_results

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

            if not tmp.IsSuccesfull:
                logger.error(" unable to GetScanReportStatus: {} ".format(tmp.ErrorMessage))
                raise Exception(" unable to GetScanReportStatus: {} ".format(tmp.ErrorMessage))

            is_ready = tmp.IsReady
            is_failed = tmp.IsFailed
            logger.info("report {} status, IsReady: {}, "
                        "IsFailed: {}".format(report_id, is_ready, is_failed))

            return is_ready, is_failed

        except Exception as e:
            raise Exception("Unable to GetScanReport: {} ".format(e.message))

    def get_scan_summary(self, scan_id):
        """

        get scan summary

        :param scan_id:
        :return:
        """
        try:
            tmp = self.client.service.GetScanSummary(self.session_id, scan_id)

            if not tmp.IsSuccesfull:
                logger.error('Fail to GetScanSummaryResult:'
                             '{} '.format(tmp.ErrorMessage))
                raise Exception('Fail to GetScanSummaryResult: '
                                '{} '.format(tmp.ErrorMessage))
            return tmp

        except Exception as e:
            logger.error("Unable to GetScanSummaryResult:"
                         "{} ".format(e.message))
            raise Exception("Unable to GetScanSummaryResult: "
                            "{} ".format(e.message))

    def get_scans_display_data_for_all_projects(self, filter_on=False):
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

            if not filter_on:
                return self.convert_to_json(tmp)
            else:
                return tmp
        except Exception as e:
            logger.error("Unable to GetScansDisplayDataForAllProjects: "
                         "{} ".format(e.message))
            raise Exception("Unable to GetScansDisplayDataForAllProjects: "
                            "{} ".format(e.message))

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

            if not tmp.IsSuccesfull:
                logger.error(" unable to GetStatusOfSingleScan: {} ".format(tmp.ErrorMessage))
                raise Exception(" unable to GetStatusOfSingleScan: {} ".format(tmp.ErrorMessage))

            current_status = tmp.CurrentStatus
            scan_id = tmp.ScanId
            return current_status, scan_id

        except Exception as e:
            logger.error("Unable to GetScanReport: {} ".format(e.message))
            raise Exception("Unable to GetScanReport: {} ".format(e.message))

    def get_team_ldap_groups_mapping(self, team_id):
        """
        get team LDAP groups mapping
        :param team_id:
        :return:
        """
        try:
            tmp = self.client.service.GetTeamLdapGroupsMapping(self.session_id,
                                                               team_id)
            if not tmp.IsSuccesfull:
                logger.error(" unable to GetTeamLdapGroupsMapping: {} ".format(tmp.ErrorMessage))
                raise Exception(" unable to GetTeamLdapGroupsMapping: {} ".format(tmp.ErrorMessage))

            return tmp.LdapGroups

        except Exception as e:
            logger.error("Unable to GetTeamLdapGroupsMapping: "
                         "{} ".format(e.message))
            raise Exception("Unable to GetTeamLdapGroupsMapping: "
                            "{} ".format(e.message))

    def is_valid_project_name(self, project_name, group_id=None):
        """
         is valid project name or not
        """
        try:
            tmp = self.client.service.IsValidProjectName(self.session_id, project_name, group_id)

            return tmp.IsSuccesfull

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

    def scan(self, project_name, preset_name="All", description="No description", is_public=True,
             source_location_type="Local", windows_shared_user_name=None, windows_shared_password=None,
             path=None, include_subtree=True,
             port=3690, use_ssl=False, use_ssh=False, server_name=None, repository_type="GIT",
             srctl_username=None, srctl_password=None, source_control_protocol_type="PasswordServer",
             repository_name=None, protocol_parameters=None, git_branch="refs\\heads\\master",
             git_ls_view_type="TAGS_AND_HEADS",
             ssh_private_key=None, perforce_browsing_mode="None",
             file_path=None,
             exclude_files_patterns=None, exclude_folders_patterns=None,
             is_private_scan=False, is_incremental=False, comment="Empty comment",
             ignore_scan_with_unchanged_code=False):
        """

        The API client can call an immediate scan. Depending on whether the submitted
        project name (CliScanArgs.PrjSettings.ProjectName) already exists,
        the scan is called for the existing CxSAST project or a new project is created.

        example 1: scan, Local Zip source code file.
        scan(project_name=project_name,
             preset_name='All',
             source_location_type="Local",
             file_path=dir_path + "/BookStoreJava_21403_lines.zip",
             is_public=True,
             is_private_scan=False,
             is_incremental=False,
             comment='Empty comment.',
             ignore_scan_with_unchanged_code=True,
             exclude_files_patterns=None,
             exclude_folders_patterns=None)

        example 2: scan, Shared
        scan(project_name=project_name,
             preset_name='All',
             source_location_type="Shared",
             windows_shared_user_name="172.16.29.116\Administrator",
             windows_shared_password="Password01!",
             is_public=True,
             is_private_scan=False,
             is_incremental=False,
             comment='Empty comment.',
             ignore_scan_with_unchanged_code=True,
             exclude_files_patterns=None,
             exclude_folders_patterns=None,
             path="\\\\172.16.29.116\\checkmarx-share\\BookStoreJava_21403_lines",
             include_subtree=True,
             git_ls_view_type="TAGS_AND_HEADS")

       example : scan, SVN
       scan(project_name=project_name,
            preset_name='All',
            source_location_type="SourceControl",
            is_public=True,
            is_private_scan=False,
            is_incremental=False,
            comment='Empty comment.',
            ignore_scan_with_unchanged_code=False,
            exclude_files_patterns=None,
            exclude_folders_patterns=None,
            path="/",
            include_subtree=True,
            port=3690,
            repository_type="SVN",
            srctl_username="admin",
            srctl_password="admin",
            use_ssl=False,
            use_ssh=False,
            server_name="svn://192.168.0.105/test-repo",
            source_control_protocol_type="PasswordServer",
            repository_name="svn://192.168.0.105/test-repo",
            protocol_parameters=None,
            git_ls_view_type="TAGS_AND_HEADS")



        example 3: scan, GIT repository with http protocol
        Gitlab repository url: http://username:Password@192.168.31.204:10080/happy/checkmarx-java.git
            scan(project_name=project_name,
                 preset_name='All',
                 source_location_type="SourceControl",
                 is_public=True,
                 is_private_scan=False,
                 is_incremental=False,
                 comment='Empty comment.',
                 ignore_scan_with_unchanged_code=False,
                 exclude_files_patterns=None,
                 exclude_folders_patterns=None,
                 use_ssl=False,
                 use_ssh=False,
                 server_name="http://yhl:Password01!@www.zuluoji.cn/gitlab/yhl/CxPy.git",
                 source_control_protocol_type="PasswordServer",
                 repository_name="http://yhl:Password01!@www.zuluoji.cn/gitlab/yhl/CxPy.git",
                 protocol_parameters="happy/checkmarx-java.git",
                 git_branch="refs/heads/master",
                 git_ls_view_type="TAGS_AND_HEADS")

        example 2: scan, GIT repository with SSH protocol
        Gitlab repository url: ssh://git@192.168.31.204:10022/happy/checkmarx-java.git

        scan(project_name='project_name',
             preset_name='All',
             source_location_type="SourceControl",
             is_public=True,
             is_private_scan=False,
             is_incremental=False,
             comment='Empty comment.',
             ignore_scan_with_unchanged_code=False,
             exclude_files_patterns=None,
             exclude_folders_patterns=None,
             use_ssl=False,
             use_ssh=True,
             server_name="ssh://git@www.zuluoji.cn:10022/yhl/CxPy.git",
             source_control_protocol_type="SSH",
             repository_name="ssh://git@www.zuluoji.cn:10022/yhl/CxPy.git",
             protocol_parameters="happy/checkmarx-java.git",
             git_branch="refs/heads/master",
             git_ls_view_type="TAGS_AND_HEADS",
             ssh_private_key=ssh_private_key)



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
        :param description:
        :param source_location_type: String
                'Local', 'Shared', 'SourceControl'

        :param file_path: String
                please give the full path of the file name

        :param windows_shared_user_name: String
        :param windows_shared_password: String
        :param path: String
        :param include_subtree: Boolean
        :param port: Integer
        :param repository_type: String
            "TFS", "SVN", "GIT", "Perforce"
        :param srctl_username: String
        :param srctl_password: String
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

        :param source_control_protocol_type: [WindowsAuthentication, SSL, SSH, PasswordServer]
        :param repository_name: repository name
        :param protocol_parameters:
        :param git_branch:  "refs/heads/master"
        :param git_ls_view_type: [TAGS, HEADS, TAGS_AND_HEADS, ALL]
        :param ssh_private_key: string
        :param perforce_browsing_mode
        :param is_public: Boolean
        :param is_private_scan: Boolean
        :param is_incremental: Boolean
        :param comment: String
        :param ignore_scan_with_unchanged_code: Boolean
        :param exclude_folders_patterns: String
                folders to be excluded, a comma-separated list of folders,
                including wildcards to exclude. example: docs, test
        :param exclude_files_patterns: String
                files to be excluded, a comma-separated list of files,
                including wildcards to exclude. example: *.txt, *.doc
        :return:
        """
        scan_args = CliScanArgs(project_name=project_name,
                                preset_name=preset_name,
                                description=description,
                                is_public=is_public,
                                source_location_type=source_location_type,
                                windows_shared_user_name=windows_shared_user_name,
                                windows_shared_password=windows_shared_password,
                                path=path, include_subtree=include_subtree,
                                port=port, use_ssl=use_ssl, use_ssh=use_ssh,
                                server_name=server_name, repository_type=repository_type,
                                srctl_username=srctl_username, srctl_password=srctl_password,
                                source_control_protocol_type=source_control_protocol_type,
                                repository_name=repository_name, protocol_parameters=protocol_parameters,
                                git_branch=git_branch, git_ls_view_type=git_ls_view_type,
                                ssh_private_key=ssh_private_key, perforce_browsing_mode=perforce_browsing_mode,
                                file_path=file_path, exclude_files_patterns=exclude_files_patterns,
                                exclude_folders_patterns=exclude_folders_patterns,
                                is_private_scan=is_private_scan, is_incremental=is_incremental,
                                comment=comment,
                                ignore_scan_with_unchanged_code=ignore_scan_with_unchanged_code).get_cli_scan_args()
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
            if not tmp.IsSuccesfull:
                logger.error("Fail to SetTeamLdapGroupsMapping: "
                             "{} ".format(tmp.ErrorMessage))
                raise Exception("Fail to SetTeamLdapGroupsMapping: "
                                "{} ".format(tmp.ErrorMessage))

            project_id = tmp.ProjectID
            run_id = tmp.RunId
            return project_id, run_id

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

            return "StopDataRetention called successfully."

        except Exception as e:
            logger.error("Unable to StopDataRetention: {} ".format(e.message))
            raise Exception("Unable to StopDataRetention: "
                            "{} ".format(e.message))

    def update_project_configuration(self, project_name, project_configuration=None):
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
            return "ok"
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
            else:
                return "ok"

        except Exception as e:
            logger.error("Unable to UpdateProjectIncrementalConfiguration: "
                         "{} ".format(e.message))
            raise Exception("Unable to UpdateProjectIncrementalConfiguration: "
                            "{} ".format(e.message))

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

    def check_scanning_status(self, run_id):
        """
        :param run_id:
        :return:
        """
        while True:
            current_status, scan_id = self.get_status_of_single_scan(run_id)
            logger.info('The engine is scanning, runId is {}, '
                        'scanId is {}, and status is {} '.format(run_id, scan_id, current_status))

            if current_status == 'Finished':
                logger.info('The scanning is Finished, run id is {}, scan id is {}, '
                            'and the status is Finished. <-><-><-><->'.format(run_id, scan_id))
                return scan_id
            time.sleep(1)

    def generate_report(self, project_name, scan_id, report_type="PDF"):
        report_id = self.create_scan_report(scan_id, report_type=report_type.upper())
        logger.info('The project scan id {} generate report id {}'.format(scan_id, report_id))
        while True:
            is_ready, is_failed = self.get_scan_report_status(report_id)
            if is_ready:
                break
            time.sleep(1)

        scan_results, contain_all_results = self.get_scan_report(report_id)

        report_name = dir_path + '/reports/' + project_name.split('\\')[-1] + report_types.get(report_type.upper())
        if not os.path.isfile(report_name):
            with open(os.path.expanduser(report_name), 'wb') as f:
                f.write(base64.decodestring(scan_results))

