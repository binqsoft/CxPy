# coding=utf-8

from common import Common


class SourceLocationType(Common):

    def __init__(self, source_location_type="Local"):
        self.SourceLocationType = source_location_type

    def get_source_location_type(self):
        slt = self.client.factory.create('SourceLocationType')
        return slt.__getitem__(self.SourceLocationType)
