# coding=utf-8

from common import Common


class ProjectOrigin(Common):

    def get_project_origin(self):
        project_origin = self.client.factory.create('ProjectOrigin')
        return project_origin.LocalPath
