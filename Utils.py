
import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.errors as errors
import azure.cosmos.http_constants as http_constants
from EncryptionDecryption import encrypt_message, decrypt_message
import os
import json

TAG_CONTAINER_NAME = "tags"
DATABASE_ID = "rfid"
PARTITION_KEY_NAME = "_partitionKey"


def CreateSQL(id):
    if id.find("--RFID:") != -1 and id.find("--CODE:") != -1:
        rfid=(id.split("--RFID:"))[1].split("--CODE:")[0]
        splitcode = id.split("--CODE:",1)
        code = splitcode[1]
        code = code.replace("-","")
    elif id.find("--RFID:") != -1:
        rfid = (id.split("--RFID:"))[1].split("--CODE:")[0]
        code = ""
    elif id.find("--CODE:") != -1:
        rfid = ""
        code = id.split("--CODE:")
        code = code[1].replace("-","")


    if rfid and code:
        query = "SELECT * FROM root r WHERE r.id=\'"+id+"\'"
    elif len(rfid) <2 and len(code)>2:
        query = "SELECT * FROM root r WHERE CONTAINS(r.id, '--CODE:"+code+"--')"
    else:
        query = "SELECT * FROM root r WHERE CONTAINS(r.id, '--RFID:"+rfid+"')"
    

    print("Query...................." + str(query))
    return query


def GetTagClient():
    client = cosmos_client.CosmosClient(os.environ.get('DATABASE_URL'), credential= os.environ.get('DATABASE_KEY'))
    client = client.get_database_client(DATABASE_ID)
    return client.get_container_client(TAG_CONTAINER_NAME)
    




def DeleteTagContainer(id):
    container_client = GetTagClient()
    try:
        
        data_obj = ReadTagContainer(id)
        data_obj["isDeleted"] = 1
        deleted_obj = {}
        deleted_obj["isDeleted"] = 1
        deleted_obj["id"] = data_obj["id"]
        deleted_obj["encrypted_data"] = EncryptDictionary(data_obj)
        data = container_client.replace_item(item=id,body=deleted_obj)


        # query = CreateSQL(id)
        # array_objs = container_client.query_items(
        #     query = query,
        #     enable_cross_partition_query = True)
        # for item in array_objs:
        #     item["isDeleted"] = 1
        #     container_client.replace_item(item=id,body=item)
        #     data = item
    except:
        data = ""
    
    return data



def ReadTagContainerForBulk(id):
    container_client = GetTagClient()
    data = ""
    try:
        discontinued_items = container_client.query_items(
            query = CreateSQL(id),
            enable_cross_partition_query = True)
        for item in discontinued_items:
            data = DecryptStringToDictionary(item["encrypted_data"])
    except Exception as ex:
        print("ReadTagContainer issue:" + str(ex))
    
    return data





def ReadTagContainer(id):
    container_client = GetTagClient()
    data = ""
    try:
        discontinued_items = container_client.query_items(
            #query = "SELECT * FROM root r WHERE r.id=\'"+id+"\' AND r.isDeleted = 0",
            query = CreateSQL(id) + " AND r.isDeleted = 0",
            enable_cross_partition_query = True)
        for item in discontinued_items:
            data = DecryptStringToDictionary(item["encrypted_data"])
    except Exception as ex:
        print("ReadTagContainer issue:" + str(ex))
    
    return data


def CreateTagContainer(obj):
    container_client = GetTagClient()
    try:
        new_obj = {}
        new_obj["id"] = obj["id"]
        new_obj["isDeleted"] = 0
        new_obj["encrypted_data"] = EncryptDictionary(obj)
        encrypted_data = container_client.upsert_item(new_obj)
    except Exception as ex:
        encrypted_data = ""
    return encrypted_data



def UpdateTagContainer(obj):
    container_client = GetTagClient()
    if not 'id' in obj: return ""
    try:
        new_obj = {}
        new_obj["id"] = obj["id"]
        new_obj["isDeleted"] = 0
        new_obj["encrypted_data"] = EncryptDictionary(obj)
        container_client.replace_item(item=new_obj['id'],body=new_obj)
    except Exception as ex:
        obj = ""
    return obj
            


def DecryptStringToDictionary(obj):
    try:
        obj = decrypt_message(obj)
        obj = json.loads(obj)
        # if isinstance(obj,dict):
        #     for key,value in obj.items():
        #         if isinstance(value,list) or isinstance(value,dict):
        #             obj[key] = DecryptValuesOfDictionary(value)
        #         elif key != "id" and key != "isDeleted":
        #             obj[key] = decrypt_message(value)
    except Exception as ex:
        print("DecryptValuesOfDictionary Issue: " + str(ex))
    return obj



def EncryptDictionary(obj):
    try:
        obj = encrypt_message(json.dumps(obj))
        # if isinstance(obj,dict):
        #     for key,value in obj.items():
        #         if isinstance(value,list) or isinstance(value,dict):
        #             obj[key] = EncryptValuesOfDictionary(value)
        #             pass
        #         elif key != "id" and key != "isDeleted":
        #             obj[key] = encrypt_message(value)
    except Exception as ex:
        print("EncryptValuesOfDictionary Issue: " + str(ex))

    return obj
    
        