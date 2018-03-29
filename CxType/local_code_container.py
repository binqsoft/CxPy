# coding=utf-8
import logging
import os

from common import Common

logger = logging.getLogger(__name__)


class LocalCodeContainer(Common):

    def __init__(self, file_path=None):
        self.FilePath = file_path

    def get_local_code_container(self):
        container = self.client.factory.create('LocalCodeContainer')

        try:
            with open(self.FilePath, 'rb') as f:
                file_content = f.read().encode('base64')
                container.ZippedFile = file_content
        except Exception as e:
            logger.error('Fail to open file : {}'.format(e.message))
            raise Exception('Fail to open file : {}'.format(e.message))

        file_name = os.path.basename(self.FilePath)
        if not isinstance(self.FilePath, unicode):
            file_name = unicode(file_name, "utf-8")
        container.FileName = file_name
        return container
