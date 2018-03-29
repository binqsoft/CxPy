# coding=utf-8

from common import Common


class CxClientType(Common):

    def get_cx_client_type(self):
        cx_client_type = self.client.factory.create('CxClientType')
        return cx_client_type.SDK
