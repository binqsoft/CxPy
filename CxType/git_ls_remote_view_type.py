# coding=utf-8

from common import Common


class GitLsRemoteViewType(Common):

    def __init__(self, git_ls_view_type):
        """

        :param git_ls_view_type:  TAGS, HEADS, TAGS_AND_HEADS, ALL
        """
        self.GitLsRemoteViewType = git_ls_view_type

    def get_git_ls_remote_view_type(self):
        git_ls_view_type = self.client.factory.create('GitLsRemoteViewType')
        return git_ls_view_type.__getitem__(self.GitLsRemoteViewType)
