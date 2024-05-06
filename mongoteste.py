import pymongo
from pymongo.errors import OperationFailure
from bson import ObjectId
from bson import errors
import paho.mqtt.client as mqtt
import json
from datetime import datetime

myclient = pymongo.MongoClient("mongodb+srv://igorvieira:vitalguard@cluster0.w3yfk85.mongodb.net/")
mydb = myclient["teste"]
mycol = mydb["infos"]

payload = {
      "nome": "asd",
      "senha": "qwe",
      "cpf": "123123",
      "email": "asd@qwe.br"
    }

nome = payload["nome"]
senha = payload["senha"]
cpf = payload["cpf"]
email = payload["email"]

conta_check = mycol.find_one({"cpf": str(cpf)}, {"cpf": True, "_id": False})

if conta_check:
    print(conta_check["cpf"])
else:
    print("User not found")