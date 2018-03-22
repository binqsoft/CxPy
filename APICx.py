#!usr/bin/python
# coding=utf-8

# Python Dependencies
import CxPy
import logging
import base64
import os
import time

dir_path = os.path.dirname(os.path.realpath(__file__))

logging.basicConfig(filename=dir_path + '/checkmarx_soap_api.log',
                    format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

report_types = {
    "PDF": ".pdf",
    "RTF": ".rtf",
    "CSV": ".csv",
    "XML": ".xml",
}


def check_scanning_status(run_id_i):
    while True:
        current_status, scan_id_i = pyC.get_status_of_single_scan(run_id_i)
        logger.info('The engine is scanning, the runId is {}, '
                    'scanId is {}, and status is {} '.format(run_id_i, scan_id_i, current_status))

        if current_status == 'Finished':
            logger.info('The scanning is Finished, run id is {}, scan id is {}, '
                        'and the status is Finished. <-><-><-><->'.format(run_id_i, scan_id_i))
            return scan_id_i
        time.sleep(0.01)


def generate_report(scan_id_i, report_type):
    report_id = pyC.create_scan_report(scan_id_i, report_type=report_type.upper())
    logger.info('The project scan id {} generate report id {}'.format(scan_id_i, report_id))
    while True:
        is_ready, is_failed = pyC.get_scan_report_status(report_id)
        if is_ready:
            break
        time.sleep(0.01)

    scan_results, contain_all_results = pyC.get_scan_report(report_id)

    report_name = dir_path + '/reports/' + project_name.split('\\')[-1] + report_types.get(report_type.upper())
    if not os.path.isfile(report_name):
        with open(os.path.expanduser(report_name), 'wb') as f:
            f.write(base64.decodestring(scan_results))


if __name__ == '__main__':
    print ("[SYS]\tLoading...")
    pyC = CxPy.CxPy()

    # the project name is set to follow name just in case you use a non admin user to call Checkmarx SOAP API
    project_name = "CxServer\SP\Company\Users\BookStoreJava"
    scan_id = None

    # start scanning
    project_id, run_id = pyC.scan(project_name=project_name,
                                  preset_name='All',
                                  scan_configuration_id=1,
                                  source_location_type="Local",
                                  file_name=dir_path + "/BookStoreJava_21403_lines.zip",
                                  is_public=True,
                                  is_private_scan=False,
                                  is_incremental=False,
                                  comment='Empty comment.',
                                  ignore_scan_with_unchanged_code=True,
                                  exclude_files=None,
                                  exclude_folders=None)

    # check scanning status
    scan_id = check_scanning_status(run_id)

    # generate reports
    generate_report(scan_id, report_type="PDF")
    generate_report(scan_id, report_type="XML")
    print ("[SYS]\tFinished...")
    pass
