# coding=utf-8

from common import Common
from repository_type import RepositoryType
from credentials import Credentials
from source_control_protocol_type import SourceControlProtocolType
from git_ls_remote_view_type import GitLsRemoteViewType
from cx_ws_perforce_browsing_mode import CxWSPerforceBrowsingMode


class SourceControlSettings(Common):

    def __init__(self, port, use_ssl, use_ssh, server_name, repository_type,
                 srctl_username, srctl_password, source_control_protocol_type,
                 repository_name, protocol_parameters, git_branch="refs/heads/master",
                 git_ls_view_type="TAGS_AND_HEADS",
                 ssh_public_key=None, ssh_private_key=None, perforce_browsing_mode="None"):
        """

        :param port: [integer]
        :param use_ssl: [boolean]
        :param use_ssh: [boolean]
        :param server_name: [string]   repository url
        :param repository_type:
        :param srctl_username:
        :param srctl_password:
        :param source_control_protocol_type: [WindowsAuthentication, SSL, SSH, PasswordServer]
        :param repository_name:  [string] repository url
        :param protocol_parameters:
        :param git_branch:
        :param git_ls_view_type:  [TAGS, HEADS, TAGS_AND_HEADS, ALL]
        :param ssh_public_key:
        :param ssh_private_key:
        :param perforce_browsing_mode:
        """
        self.Port = port
        self.UseSSL = use_ssl
        self.UseSSH = use_ssh
        self.ServerName = server_name
        self.repository_type = repository_type
        self.srctl_username = srctl_username
        self.srctl_password = srctl_password
        self.source_control_protocol_type = source_control_protocol_type
        self.RepositoryName = repository_name
        self.ProtocolParameters = protocol_parameters
        self.GITBranch = git_branch
        self.git_ls_view_type = git_ls_view_type
        self.SSHPublicKey = ssh_public_key
        self.SSHPrivateKey = ssh_private_key
        self.perforce_browsing_mode = perforce_browsing_mode

    def get_source_control_settings(self):
        scs = self.client.factory.create('SourceControlSettings')
        scs.Port = self.Port
        scs.UseSSL = self.UseSSL
        scs.UseSSH = self.UseSSH
        scs.ServerName = self.ServerName
        scs.Repository = RepositoryType(self.repository_type).get_repository_type()
        scs.UserCredentials = Credentials(self.srctl_username, self.srctl_password).get_credential()
        scs.Protocol = SourceControlProtocolType(self.source_control_protocol_type).get_source_control_protocol_type()
        scs.RepositoryName = self.RepositoryName
        scs.ProtocolParameters = self.ProtocolParameters
        scs.GITBranch = self.GITBranch
        scs.GitLsViewType = GitLsRemoteViewType(self.git_ls_view_type).get_git_ls_remote_view_type()
        if self.UseSSH:
            scs.SSHPublicKey = self.SSHPublicKey
            scs.SSHPrivateKey = self.SSHPrivateKey
        scs.PerforceBrowsingMode = CxWSPerforceBrowsingMode(
            self.perforce_browsing_mode).get_cx_ws_perforce_browsing_mode()
        return scs
