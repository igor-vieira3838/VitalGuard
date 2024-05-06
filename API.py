import pymongo
from pymongo.errors import OperationFailure
from bson import ObjectId
from bson import errors
import paho.mqtt.client as mqtt
import json
from datetime import datetime

myclient = pymongo.MongoClient("mongodb+srv://igorvieira:vitalguard@cluster0.w3yfk85.mongodb.net/")
client = mqtt.Client()
"""
mydoc = {
  "cpf": "123123",
  "nome": "Ana Silva",
  "data_de_nascimento": "1985-03-20T00:00:00Z",
  "genero": "Feminino",
  "endereco": "Rua das Flores, 123",
  "telefone": "+55 987654321",
  "historico_medico": [
    {
      "data_da_visita": "2023-05-10T00:00:00Z",
      "diagnostico": "Gripe",
      "tratamento": "Repouso, hidratação e medicamentos sintomáticos",
      "descricao": "Paciente apresentando febre e dor de cabeça"
    },
    {
      "data_da_visita": "2023-07-15T00:00:00Z",
      "diagnostico": "Fratura no braço direito",
      "tratamento": "Imobilização e fisioterapia",
      "descricao": "Acidente de bicicleta resultando em queda"
    }
  ],
  "exames_laboratoriais": [
    {
      "tipo_de_exame": "Hemograma completo",
      "data_do_exame": "2023-05-12T00:00:00Z",
      "resultado": "Normal"
    },
    {
      "tipo_de_exame": "Raio-X do braço",
      "data_do_exame": "2023-07-16T00:00:00Z",
      "resultado": "Fratura no rádio distal"
    }
  ],
  "prescricoes_medicas": [
    {
      "medicamento": "Paracetamol",
      "dosagem": "500mg, 1 comprimido a cada 6 horas",
      "instrucoes": "Tomar após as refeições"
    },
    {
      "medicamento": "Dipirona",
      "dosagem": "1g, 1 comprimido a cada 8 horas",
      "instrucoes": "Tomar apenas em caso de febre acima de 38°C"
    },
    {
      "medicamento": "Diclofenaco",
      "dosagem": "50mg, 1 comprimido a cada 12 horas",
      "instrucoes": "Tomar junto com as refeições"
    }
  ],
  "visitas_agendadas": [
    {
      "data_da_visita": "2023-08-01T00:00:00Z",
      "tipo_de_visita": "Retorno para avaliação da fratura",
      "id_medico": "Dr. José da Silva"
    },
    {
      "data_da_visita": "2023-09-05T00:00:00Z",
      "tipo_de_visita": "Acompanhamento clínico",
      "id_medico": "Dra. Maria Oliveira"
    }
  ],
  "streamAmbulancia": {
    "BPM": [
      42,
      55
    ]
  }
}

self.mydb = myclient["teste"]
self.mycol = self.mydb["infos"]

mycol.insert_one(mydoc)
"""

class MongoCall:
  def __init__(self, payload_data):
    self.payload = payload_data
    self.mydb = myclient["teste"]
    self.mycol = self.mydb["infos"]
  
  #Cadastro do profissional da saúde
  def Cadastro(self):
    #payload exemplo (app=>API)
    """
    {
      "nome": "asd",
      "senha": "qwe",
      "cpf": "123123",
      "email": "asd@qwe.br"
    }
    """
    try:
      nome = self.payload["nome"]
      senha = self.payload["senha"]
      cpf = self.payload["cpf"]
      email = self.payload["email"]
      
      conta_check = self.mycol.find_one({"cpf": cpf}, {"cpf": True})
      
      if conta_check != None:
        print("CPF já cadastrado!")
        return
      
      if(conta_check["cpf"] == cpf):
        print("CPF já cadastrado!")
        client.publish("Vitalguard/cadastro/**id_mqtt**/cadastroFalhou", {})
        return
      
      """
      if(conta_check["email"] == email):
        print("Email já cadastrado!")
        client.publish("Vitalguard/cadastro/**id_mqtt**/cadastroFalhou", {})
        return
      """
      
      myobj = {
        "nome": str(nome),
        "email": str(email),
        "senha": str(senha),
        "cpf": str(cpf)
      }
      
      self.mycol.insert_one(myobj)
    except OperationFailure as e:
      print("Cadastro: " + str(e))
  
  def CadastroPaciente(self):
    pass
      
  def Update(self):
    try:
      cpf = self.payload["cpf"]
      BPM = self.payload["BPM"]
      
      update_query = {
          "$push": {
              "ocorrenciasAmbulancia.0.streamAmbulancia.BPM": BPM,
              "ocorrenciasAmbulancia.0.streamAmbulancia.data": datetime.now()
          }
      }
      
      self.mycol.update_one({"cpf": cpf}, update_query)
    except OperationFailure as e:
      print("MongoCall.update: " + str(e))
    else:
      print("Documento atualizado!")
    

def on_connect(client, userdata, flags, rc):
  print("Conectado - Codigo de resultado: "+str(rc))
  client.subscribe("VitalGuard/#")

def on_message(client, userdata, msg):
  try:
    payload_data = json.loads(str(msg.payload.decode()))
    
    # Instância que interage com o banco de dados
    mongoDB = MongoCall(payload_data)
    
    if(msg.topic == "VitalGuard/cadastro/dados"):
      mongoDB.Cadastro()
    
    if(msg.topic == "VitalGuard/sensor/dados"):
      mongoDB.Update()
            
  except Exception as e:
    print("on_message: "+str(e))

client.on_connect = on_connect
client.on_message = on_message
		
try:
  client.username_pw_set("Igor", "abc")    
  client.connect("localhost", 1883, 60)
except:
  print("Não foi possivel conectar ao MQTT...")
  print("Encerrando...")

try:
  client.loop_forever()
except KeyboardInterrupt:
  print("Encerrando...")