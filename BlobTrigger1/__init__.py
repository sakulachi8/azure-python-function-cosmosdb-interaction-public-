import logging

import azure.functions as func
from datetime import timedelta, datetime
import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.errors as errors
import azure.cosmos.http_constants as http_constants
import os
import json

import os, sys
from os.path import dirname, join, abspath
sys.path.insert(0, abspath(join(dirname(__file__), '..')))

from Utils import CreateTagContainer, DeleteTagContainer, ReadTagContainerForBulk, UpdateTagContainer




def main(myblob: func.InputStream):
    logging.info(f"Python blob trigger function processed blob \n"
                 f"Name: {myblob.name}\n"
                 f"Blob Size: {myblob.length} bytes")
    # data = str(myblob.read(size=-1))
    #logging.info(data)
    delete_record = False
    if "-delete" in myblob.name:
        delete_record = True
        logging.info("----------------Delete Operations-----------------------")
    else:
        logging.info("----------------Assigned Operations-----------------------")

    lines_data = myblob.readlines()
    total_operations = len(lines_data)
    logging.info("---------------Total Records are: " + str(len(lines_data)) + "---------------")
    completed_operation = 0
    for obj in lines_data:
        try:
            obj = obj.decode().replace("\\n","").replace("\\r","")
            attributes = obj.split(",")
            attributes_len = len(attributes)
            if attributes_len >= 7:
                submittedcode = attributes[0]
                submittedid = attributes[1]
                clientid = 1
                date = attributes[6]
                date_time_obj = datetime.strptime(date, "%m/%d/%Y") - datetime(1900, 1, 1)
                time = attributes[7]
                (h, m, s) = time.split(':')
                seconds = int(h) * 3600 + int(m) * 60 + int(s)
                date_time_sec =  date_time_obj.total_seconds() + seconds

                

                if submittedid and submittedcode:
                    id = "--RFID:" + submittedid + "--CODE:" + submittedcode + "--"
                elif submittedid == "" and submittedcode:
                    id = "--CODE:" + submittedcode + "--"
                elif submittedcode == "" and submittedid:
                    id = "--RFID:" + submittedid
                else:
                    id = ""


                tag_obj = {}
                tag_obj['id'] = id
                tag_obj['status'] = 'assigned'
                tag_obj['clientid'] = clientid
                tag_obj['isDeleted'] = 0
                tag_obj['description'] = ""
                tag_obj['datetime'] = str(int(date_time_sec))
                # scan = {}
                # scan["id"] = 0
                # scan['scannedby'] = scannedby
                # scan['datetime'] = str(int(round(time.time() * 1000)))
                # scan['ip'] = ip
                # scan['LatLocation'] = LatLocation
                # scan['LonLocation'] = LonLocation
                # scan['distance'] = distance
                # scan['mph'] = 0
                # scans_array = list()
                # scans_array.append(scan)
                tag_obj["scans"] = []
                already_obj = ReadTagContainerForBulk(id)
                if delete_record:
                    response = DeleteTagContainer(tag_obj["id"])
                    if not already_obj:
                        logging.info("Object not exist " + id)
                    elif response:
                        completed_operation = completed_operation + 1
                    else:
                        logging.info("Delete error with id: " + id)
                else:
                    # response = CreateTagContainer(tag_obj)
                    if (already_obj and "status" in already_obj and already_obj["status"] == "enroll"):
                        logging.info("Assignment error with id: " + id + " record already exist with enrolled status.")
                    elif already_obj and "isDeleted" in already_obj and already_obj["isDeleted"] == 0:
                        logging.info("Assignment error with id: " + id + " record already exist")
                    elif already_obj and "isDeleted" in already_obj and already_obj["isDeleted"] == 1:
                        response = UpdateTagContainer(tag_obj)
                        if response:
                            completed_operation = completed_operation + 1
                        else:
                            logging.info("Assignment error with id: " + id)
                    else:
                        response = CreateTagContainer(tag_obj)
                        if response:
                            completed_operation = completed_operation + 1
                        else:
                            logging.info("Assignment error with id: " + id)
        except Exception as ex:
            pass

    logging.info("Failed operations: " + str(total_operations - completed_operation))
    # logging.info(lines_data)
    # data1 = myblob.readline(1)
    # logging.info(data1)
