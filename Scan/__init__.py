import logging

import azure.functions as func
# from Utils import ReadTagContainer,UpdateTagContainer, DeleteTagContainer, CreateTagContainer
# from EncryptionDecryption import encrypt_message,decrypt_message
import json
import time
from geopy.distance import geodesic
import os, sys

from os.path import dirname, join, abspath
sys.path.insert(0, abspath(join(dirname(__file__), '..')))

from Utils import ReadTagContainer,UpdateTagContainer, DeleteTagContainer, CreateTagContainer





def main(req: func.HttpRequest) -> func.HttpResponse:
    response_message = "Nothing happened."
    try:
        try:
            req_body = req.get_json()
        except Exception:
            req_body = req.form
        # response_message = EncryptValuesOfDictionary(req_body)
        # print("thi is obj" + str(response_message))
        # response_message = DecryptValuesOfDictionary(response_message)
        # print("thi is obj" + str(response_message))
        # return func.HttpResponse(body=str(response_message))
        submittedid = str(req_body.get('uidtid')) if 'uidtid' in req_body else ""
        submittedcode = str(req_body.get('code')) if 'code' in req_body else ""
        # ip = str(req_body.get('ip')) if 'ip' in req_body else ""
        ip = req.headers['x-forwarded-for'] if 'x-forwarded-for' in req.headers else "" 

        
        logging.info("--------------- IP is: " + ip + "---------------")
        action = str(req_body.get('action')).lower() if 'action' in req_body else ""
        scannedby = str(req_body.get('user')) if 'user' in req_body else ""
        LatLocation = req_body.get('Lat') if 'Lat' in req_body else ""
        LonLocation = req_body.get('Lon') if 'Lon' in req_body else ""
        distance = req_body.get('distance') if 'distance' in req_body else ""
        description = req_body.get('description') if 'description' in req_body else ""


        
        if submittedid and submittedcode:
            id = "--RFID:" + submittedid + "--CODE:" + submittedcode + "--"
        elif submittedid == "" and submittedcode:
            id = "--CODE:" + submittedcode + "--"
        elif submittedcode == "" and submittedid:
            id = "--RFID:" + submittedid
        else:
            id = ""
            
        #filter junk out
        id = id.replace("\t","")
        id = id.replace("\n","")
        id = id.replace("\"","")
        ip = ip.replace("\t","")
        ip = ip.replace("\n","")
        ip = ip.replace("\"","")
        action = action.replace("\t","")
        action = action.replace("\n","")
        action = action.replace("\"","")
        scannedby = scannedby.replace("\t","")
        scannedby = scannedby.replace("\n","")
        scannedby = scannedby.replace("\"","")
        LatLocation = LatLocation.replace("\t","")
        LatLocation = LatLocation.replace("\n","")
        LatLocation = LatLocation.replace("\"","")
        LonLocation = LonLocation.replace("\t","")
        LonLocation = LonLocation.replace("\n","")
        LonLocation = LonLocation.replace("\"","")
        description = description.replace("\t","")
        description = description.replace("\n","")
        description = description.replace("\"","")

        # if action is enroll new record
        if action and action == "enroll":
            tag_obj = {}
            tag_obj['id'] = id
            tag_obj['status'] = 'enrolled'
            tag_obj['clientid'] = scannedby
            tag_obj['isDeleted'] = 0
            tag_obj['description'] = description
            scan = {}
            scan["id"] = 0
            scan['scannedby'] = scannedby
            scan['datetime'] = str(int(round(time.time() * 1000)))
            scan['ip'] = ip
            scan['LatLocation'] = LatLocation
            scan['LonLocation'] = LonLocation
            scan['distance'] = distance
            scan['mph'] = 0
            scans_array = list()
            scans_array.append(scan)
            tag_obj["scans"] = scans_array
            already_obj = ReadTagContainer(id)
            if already_obj and "status" in already_obj and already_obj["status"] == "assigned":
                response_message = "Enrollment error as object has already assigned status"
            elif already_obj:
                tag_obj["id"] = already_obj["id"]
                response = UpdateTagContainer(tag_obj)
                if response:
                    response_message = "Enrolled "+ id 
                else:
                    response_message = "Enrollment error"
            else:
                response = CreateTagContainer(tag_obj)
                if response:
                    response_message = "Enrolled "+ id 
                else:
                    response_message = "Enrollment error"



        # if action is void delete db record
        elif action and action == "void":
            response = DeleteTagContainer(id)
            if response:
                response_message = "deleted "+ id 
            else:
                response_message = "Error, can't delete the record."



        # read record and add scan
        elif action and action == "checkinverify":
            tag_obj = ReadTagContainer(id)
            if tag_obj and "status" in tag_obj and tag_obj["status"] == "assigned":
                response_message = "Enrollment error as object has already assigned status"
            elif not tag_obj:
                response_message = "No Record"
            else:
                already_scans = list(tag_obj["scans"])
                last_scans = already_scans[len(tag_obj["scans"])-1]
                scan = {}
                scan["id"] = len(already_scans)
                scan['scannedby'] = scannedby
                scan['datetime'] = str(int(round(time.time() * 1000)))
                scan['ip'] = ip
                scan['LatLocation'] = LatLocation
                scan['LonLocation'] = LonLocation
                scan['distance'] = distance
                scan['mph'] = 0
                #compute distance from last scan
                speed = 0
                scan['distance'] = geodesic((last_scans['LatLocation'],last_scans['LonLocation']), (scan['LatLocation'],scan['LonLocation'])).miles
                if scan['distance'] <= 0:
                    scan['distance'] = 0.001
                #compute time from last scan
                timeinhours = round(((int(scan['datetime']) - int(last_scans['datetime']))/1000)/3600,32)
                if timeinhours <= 0:
                    timeinhours = 0.001
                #compute speed one must travel to get between both points in the given time
                speedmph = round(int(scan['distance'])/timeinhours,32)
                #speed = (int(scan['distance'])/((int(scan['datetime']) - int(last_scans['datetime']))/1000)/3600)
                # if speed is greater than 90 it is considered counterfiet
                if speedmph >= 90:
                    response_message = "counterfeit " + str(speedmph) + " mph"
                        #response_message = response_message + " \ndistance from last scan is " + str(scan['distance']) + " miles, which would need to travel at " + str(speedmph) + " mph.\n>90mph, so failed"
                        # update db record by new scand adding data
                elif speedmph < 90:
                    response_message = "Verified OK if product scanned matches the registered description, which is: \n\n" + tag_obj['description'] + "\n\nOpportunity to put photo of item here?"
                    response_message = response_message + " \ntime from last scan is " + str(timeinhours) + " (hrs)\ndistance from last scan is " + str(scan['distance']) + " miles, which would need to travel at " + str(speedmph) + " mph.\n<90mph, so approved"
                    #response_message = response_message + "<BR /><BR /><img src=\"fail.png\" />"
                scan['mph'] = speedmph
                already_scans.append(scan)
                tag_obj["scans"] = already_scans
                UpdateTagContainer(tag_obj)
    except Exception as ex:
        response_message = "An unhandled error occured: " + str(ex)

    #response_message = response_message + "<br /><br /><a href=\"javascript:history.back()\">Go Back</a>"
    #response_message = "<html><head></head><body>"+response_message+"</body></html>"
    return func.HttpResponse(body=response_message)
