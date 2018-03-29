# coding=utf-8

from common import Common


class Credentials(Common):

    def __init__(self, username=None, password=None):
        self.User = username
        self.Pass = password

    def get_credential(self):
        credential = self.client.factory.create("Credentials")
        credential.User = self.User
        credential.Pass = self.Pass
        return credential
