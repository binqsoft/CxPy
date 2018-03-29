# coding=utf-8

import ast

from common import Common
from scan_path import ScanPath


class ArrayOfScanPath(Common):

    def __init__(self, path=None, include_subtree=True):
        self.path = path
        self.include_subtree = include_subtree

    def get_array_of_scan_path(self):
        array_of_scan_path = self.client.factory.create("ArrayOfScanPath")
        array_of_scan_path.ScanPath.append(ScanPath(self.path, self.include_subtree).get_scan_path())
        return array_of_scan_path
