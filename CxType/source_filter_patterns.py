# coding=utf-8

from common import Common


class SourceFilterPatterns(Common):

    def __init__(self, exclude_files_patterns=None, exclude_folders_patterns=None):
        self.ExcludeFilesPatterns = exclude_files_patterns
        self.ExcludeFoldersPatterns = exclude_folders_patterns

    def get_source_filter_patterns(self):
        source_filter_lists = self.client.factory.create('SourceFilterPatterns')
        source_filter_lists.ExcludeFilesPatterns = self.ExcludeFilesPatterns
        source_filter_lists.ExcludeFoldersPatterns = self.ExcludeFoldersPatterns
        return source_filter_lists
