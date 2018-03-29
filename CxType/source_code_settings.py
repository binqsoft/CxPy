# coding=utf-8

from common import Common
from source_location_type import SourceLocationType
from credentials import Credentials
from array_of_scan_path import ArrayOfScanPath
from source_control_settings import SourceControlSettings
from local_code_container import LocalCodeContainer
from source_filter_patterns import SourceFilterPatterns


class SourceCodeSettings(Common):

    def __init__(self, source_location_type, windows_shared_user_name, windows_shared_password,
                 path, include_subtree,
                 port, use_ssl, use_ssh, server_name, repository_type,
                 srctl_username, srctl_password, source_control_protocol_type,
                 repository_name, protocol_parameters, git_branch, git_ls_view_type,
                 ssh_public_key, ssh_private_key, perforce_browsing_mode,
                 file_path,
                 exclude_files_patterns, exclude_folders_patterns
                 ):
        self.source_location_type = source_location_type
        self.windows_shared_user_name = windows_shared_user_name
        self.windows_shared_password = windows_shared_password
        self.path = path
        self.include_subtree = include_subtree
        self.port = port
        self.use_ssl = use_ssl
        self.use_ssh = use_ssh
        self.server_name = server_name
        self.repository_type = repository_type
        self.srctl_username = srctl_username
        self.srctl_password = srctl_password
        self.source_control_protocol_type = source_control_protocol_type
        self.repository_name = repository_name
        self.protocol_parameters = protocol_parameters
        self.git_branch = git_branch
        self.git_ls_view_type = git_ls_view_type
        self.ssh_public_key = ssh_public_key
        self.ssh_private_key = ssh_private_key
        self.perforce_browsing_mode = perforce_browsing_mode
        self.file_path = file_path
        self.exclude_files_patterns = exclude_files_patterns
        self.exclude_folders_patterns = exclude_folders_patterns

    def get_source_code_settings(self):
        source_code_settings = self.client.factory.create('SourceCodeSettings')
        if self.source_location_type not in ["Local", "Shared", "SourceControl"]:
            raise Exception("illegal source_location_type, it can only be Local, Shared, SourceControl. ")
        source_code_settings.SourceOrigin = SourceLocationType(self.source_location_type).get_source_location_type()
        if self.source_location_type == "Local":
            source_code_settings.PackagedCode = LocalCodeContainer(self.file_path).get_local_code_container()
        else:
            source_code_settings.PathList = ArrayOfScanPath(self.path, self.include_subtree).get_array_of_scan_path()
            if self.source_location_type == "Shared":
                source_code_settings.UserCredentials = Credentials(self.windows_shared_user_name,
                                                                   self.windows_shared_password).get_credential()
            else:
                source_code_settings.SourceControlSetting = \
                    SourceControlSettings(self.port, self.use_ssl, self.use_ssh, self.server_name, self.repository_type,
                                          self.srctl_username, self.srctl_password, self.source_control_protocol_type,
                                          self.repository_name, self.protocol_parameters, self.git_branch,
                                          self.git_ls_view_type, self.ssh_public_key,
                                          self.ssh_private_key, self.perforce_browsing_mode).get_source_control_settings()
        source_code_settings.SourceFilterLists = \
            SourceFilterPatterns(self.exclude_files_patterns,
                                 self.exclude_folders_patterns).get_source_filter_patterns()
        return source_code_settings
