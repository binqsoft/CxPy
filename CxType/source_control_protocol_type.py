# coding=utf-8

from common import Common


class SourceControlProtocolType(Common):

    def __init__(self, source_control_protocol_type="PasswordServer"):
        self.source_control_protocol_type = source_control_protocol_type

    def get_source_control_protocol_type(self):
        protocol_type = self.client.factory.create('SourceControlProtocolType')
        return protocol_type.__getitem__(self.source_control_protocol_type)
