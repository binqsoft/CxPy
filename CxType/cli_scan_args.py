# coding=utf-8

from common import Common
from project_settings import ProjectSettings
from source_code_settings import SourceCodeSettings
from cx_client_type import CxClientType


class CliScanArgs(Common):

    def __init__(self,
                 project_name, preset_name="All", description="No description", is_public=True,
                 source_location_type="Local", windows_shared_user_name=None, windows_shared_password=None,
                 path=None, include_subtree=True,
                 port=3690, use_ssl=False, use_ssh=False, server_name=None, repository_type="GIT",
                 srctl_username=None, srctl_password=None, source_control_protocol_type="PasswordServer",
                 repository_name=None, protocol_parameters=None, git_branch="refs/heads/master",
                 git_ls_view_type="TAGS_AND_HEADS",
                 ssh_public_key=None, ssh_private_key=None, perforce_browsing_mode="None",
                 file_path=None,
                 exclude_files_patterns=None, exclude_folders_patterns=None,
                 is_private_scan=False, is_incremental=False, comment="Empty comment",
                 ignore_scan_with_unchanged_code=False):
        self.project_name = project_name
        self.preset_name = preset_name
        self.description = description
        self.is_public = is_public
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
        self.IsPrivateScan = is_private_scan
        self.IsIncremental = is_incremental
        self.Comment = comment
        self.IgnoreScanWithUnchangedCode = ignore_scan_with_unchanged_code

    def get_cli_scan_args(self):
        scan_args = self.client.factory.create('CliScanArgs')
        scan_args.PrjSettings = ProjectSettings(self.project_name,
                                                self.preset_name,
                                                self.description,
                                                self.is_public).get_project_settings()
        scan_args.SrcCodeSettings = SourceCodeSettings(
            self.source_location_type, self.windows_shared_user_name, self.windows_shared_password,
            self.path, self.include_subtree,
            self.port, self.use_ssl, self.use_ssh, self.server_name, self.repository_type,
            self.srctl_username, self.srctl_password, self.source_control_protocol_type,
            self.repository_name, self.protocol_parameters, self.git_branch,
            self.git_ls_view_type, self.ssh_public_key,
            self.ssh_private_key, self.perforce_browsing_mode,
            self.file_path,
            self.exclude_files_patterns, self.exclude_folders_patterns
        ).get_source_code_settings()
        scan_args.IsPrivateScan = self.IsPrivateScan
        scan_args.IsIncremental = self.IsIncremental
        scan_args.Comment = self.Comment
        scan_args.IgnoreScanWithUnchangedCode = self.IgnoreScanWithUnchangedCode
        scan_args.ClientOrigin = CxClientType().get_cx_client_type()
        return scan_args
