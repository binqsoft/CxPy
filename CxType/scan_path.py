# coding=utf-8

from common import Common


class ScanPath(Common):

    def __init__(self, path, include_subtree=True):
        self.Path = path
        self.IncludeSubTree = include_subtree

    def get_scan_path(self):
        scan_path = self.client.factory.create("ScanPath")
        scan_path.Path = self.Path
        scan_path.IncludeSubTree = self.IncludeSubTree
        return scan_path
