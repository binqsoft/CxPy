# coding=utf-8
import json
import logging
import os
import ast

from suds.client import Client
from suds.cache import NoCache
from suds.sudsobject import asdict

logger = logging.getLogger(__name__)


def get_config(config_path):
    try:
        with open(config_path + "/config.json", "r") as outfile:
            tmp_json = json.load(outfile)["checkmarx"]
            username = str(tmp_json["username"])
            password = str(tmp_json["password"])
            url = str(tmp_json["url"])
            api_type = tmp_json["APIType"]
            is_user_admin = ast.literal_eval(str(tmp_json["IsUserAdmin"]))
            team = str(tmp_json["team"])
            return username, password, url, api_type, is_user_admin, team
    except Exception as e:
        logger.error("Unable to get configuration from etc/config.json: {} ".format(e.message))
        raise Exception("Unable to get configuration from etc/config.json: {} ".format(e.message))


def open_connection(url):
    try:
        tmp_client = Client(url)
        return tmp_client
    except Exception as e:
        logger.error("Unable to establish connection "
                     "with WSDL [{}]: {} ".format(url, e.message))
        raise Exception("Unable to establish connection "
                        "with WSDL [{}]: {} ".format(url, e.message))


def get_service_url(client, api_type):
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
    :param api_type:
    :return: Checkmarx web service url
    """
    try:
        cx_client = client.factory.create('CxClientType')
        response = client.service.GetWebServiceUrl(cx_client.SDK, api_type)

        if response.IsSuccesfull:
            service_url = response.ServiceURL
        else:
            logger.error("Error establishing connection:"
                         "{}".format(response.ErrorMessage))
            raise Exception("Error establishing connection:"
                            " {}".format(response.ErrorMessage))

        service_url = service_url or None
        return service_url
    except Exception as e:
        logger.error("GetWebServiceUrl, "
                     "Unable to get Service URL: {} ".format(e.message))
        raise Exception("GetWebServiceUrl, "
                        "Unable to get Service URL: {} ".format(e.message))


def get_session_id(service_url, user_name, password, lcid=2052):
    """

    Login in Checkmarx and retrieve the Session ID

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

    :param service_url:
    :param user_name:
    :param password:
    :param lcid:
    :return:
    """
    try:
        client_sdk = Client(service_url + "?wsdl", cache=NoCache(), prettyxml=True)

        cx_login = client_sdk.factory.create("Credentials")
        cx_login.User = user_name
        cx_login.Pass = password

        cx_sdk = client_sdk.service.Login(cx_login, lcid)

        if not cx_sdk.IsSuccesfull:
            logger.error("Unable to Login > "
                         "{}".format(cx_sdk.ErrorMessage))
            raise Exception("Unable to Login > "
                            "{}".format(cx_sdk.ErrorMessage))

        return cx_sdk.SessionId, client_sdk
    except Exception as e:
        logger.error("Unable to get SessionId from "
                     "[{}] : {} ".format(service_url, e.message))
        raise Exception("Unable to get SessionId from "
                        "[{}] : {} ".format(service_url, e.message))


class Common(object):

    DEBUG = False

    dir_path = os.path.dirname(os.path.realpath(__file__))
    # Get Configuration
    user_name, password, url, api_type, is_user_admin, team = get_config(config_path=dir_path + "/etc")
    # Open Connection With Checkmarx
    init_client = open_connection(url)
    # Get the Service URL
    service_url = get_service_url(init_client, api_type)
    # Get the Session Id and Client Object
    session_id, client = get_session_id(service_url, user_name, password)

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
            preset_id = 1
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

    def get_user_id_by_name(self, user_name):
        """

        get user id by name.

        :param user_name:
        :return: user id
        """
        user_id = None

        users = self.client.service.GetAllUsers(self.session_id)
        for user in users.UserDataList.UserData:
            if user.UserName == user_name:
                user_id = user.ID
                break

        if not user_id:
            logger.error("user {} does not exist in Checkmarx server".format(user_name))
            raise Exception("user {} does not exist in Checkmarx server".format(user_name))

        logger.info('user {} has id {}'.format(user_name, user_id))

        return user_id

    def get_first_associated_group_id(self):
        """
        :return:
        :rtype: string
        """
        first_associated_group_id = '0'
        group_list = self.convert_to_json(self.client.service.GetAssociatedGroupsList(self.session_id))
        groups = group_list.get("GroupList").get("Group")
        first_associated_group = next(iter(groups), None)

        if first_associated_group:
            first_associated_group_id = first_associated_group.get("ID")

        return str(first_associated_group_id)

    def recursive_asdict(self, d):
        """

        Convert Suds object into serializable format.

        :param d:
        :return:
        """
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

    def convert_to_json(self, data):
        """

        Return Subs Object into Serializable format Handler

        :param data:
        :return:
        """
        try:
            tmp = self.recursive_asdict(data)
            # return json.dumps(tmp)
            return tmp
        except Exception as e:
            logger.error("Unable to convert to JSON: {} ".format(e.message))
            raise Exception("Unable to convert to JSON: {} ".format(e.message))

