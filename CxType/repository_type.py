# coding=utf-8

from common import Common


class RepositoryType(Common):

    def __init__(self, repository_type="GIT"):
        """
        :param repository_type: TFS, SVN, GIT, Perforce
        """
        self.repository_type = repository_type

    def get_repository_type(self):
        re_type = self.client.factory.create('RepositoryType')
        return re_type.__getitem__(self.repository_type)
