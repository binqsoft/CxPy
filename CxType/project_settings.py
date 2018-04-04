# coding=utf-8

from common import Common
from project_origin import ProjectOrigin


class ProjectSettings(Common):

    def __init__(self, project_name, preset_name="All", description="Empty description", is_public=True):
        self.projectID = 0
        self.ProjectName = project_name
        self.presetName = preset_name
        # 8.5版本没有这个字段
        # self.TaskId = 0
        self.ScanConfigurationID = 1
        self.Description = description
        self.IsPublic = is_public

    def get_project_settings(self):
        project_settings = self.client.factory.create('ProjectSettings')
        project_settings.projectID = self.projectID
        project_settings.ProjectName = self.ProjectName
        project_settings.PresetID = self.get_preset_id_by_name(self.presetName)
        # project_settings.TaskId = self.TaskId
        project_settings.AssociatedGroupID = self.get_first_associated_group_id()
        project_settings.ScanConfigurationID = self.ScanConfigurationID
        project_settings.Description = self.Description
        project_settings.IsPublic = self.IsPublic
        project_settings.OpenSourceAnalysisOrigin = ProjectOrigin().get_project_origin()
        return project_settings
