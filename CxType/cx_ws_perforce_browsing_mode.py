# coding=utf-8

from common import Common


class CxWSPerforceBrowsingMode(Common):

    def __init__(self, perforce_browsing_mode):
        """

        :param perforce_browsing_mode: None, Depot, Workspace
        """
        self.PerforceBrowsingMode = perforce_browsing_mode

    def get_cx_ws_perforce_browsing_mode(self):
        cx_perforce_browsing_mode = self.client.factory.create('CxWSPerforceBrowsingMode')
        return cx_perforce_browsing_mode.__getitem__(self.PerforceBrowsingMode)
