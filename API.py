import pymongo
import paho.mqtt.client as mqtt
import json
from datetime import datetime
import uuid

myclient = pymongo.MongoClient("mongodb+srv://igorvieira:vitalguard@cluster0.w3yfk85.mongodb.net/")
client = mqtt.Client()
"""

Qual DB e qual collection usar?

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
  
  def Login(self): #Login do profissional da saúde (app=>API)
    mydb = myclient["Users"]
    mycol = mydb["infos"]
    
    try:
        email = self.payload["email"]
        senha = self.payload["senha"]
    except Exception as e:
        print("Login: " + str(e))
    
    #match do email e senha + retorna o campo "id_paho_mqtt"
    #id_paho_mqtt é a id única de um usuário
    login_check = mycol.find_one({"email": str(email), "senha": str(senha)}, {"id_paho_mqtt": True})
    
    if login_check:
      id_paho_mqtt = str(login_check["id_paho_mqtt"])
    else:
      print("Usuário não encontrado")
      #**id_da_sessão_app** deve ser uma id única que é utilizada somente
      #para diferenciar um aparelho do outro no broker para que não haja 
      #conflito na comunicação entre 2 aparelhos não logados em uma conta.
      #Deve ser gerado no app.
      client.publish("VitalGuard/**id_da_sessão_app**/login/status", {"aprovado": False})
      return
    
    client.publish(f"VitalGuard/{id_paho_mqtt}/login/status", {"aprovado": True, "id_paho_mqtt": id_paho_mqtt})

  def Cadastro(self):   #Cadastro do profissional da saúde
    mydb = myclient["Users"]
    mycol = mydb["infos"]
    
    #payload exemplo (app=>API)
    """
    {
      "nome": "Igor",
      "senha": "abc",
      "cpf": "48858859812",
      "email": "vitalguard@gmail.com"
    }
    """
    
    try:
      nome = str(self.payload["nome"])
      senha = str(self.payload["senha"])
      cpf = str(self.payload["cpf"])
      email = str(self.payload["email"])
    except Exception as e:
      print("Cadastro: " + str(e))
    
    cpf_check = mycol.find_one({"cpf": cpf})
    email_check = mycol.find_one({"email": email})
    
    #check se email ou senha já foram tomados, retorna caso os campos sejam (!= None)
    if (cpf_check and email_check) != None:
      print("CPF e email já cadastrado!")
      client.publish("VitalGuard/**id_sessão**/cadastro/cadastroFalhou", "cpf&emailDuplicado")
      return
    elif email_check != None:
      print("Email já cadastrado!")
      client.publish("VitalGuard/**id_sessão**/cadastro/cadastroFalhou", "emailDuplicado")
      return
    elif cpf_check != None:
      print("CPF já cadastrado!")
      client.publish("VitalGuard/**id_sessão**/cadastro/cadastroFalhou", "cpfDuplicado")
      return
    else:
      pass
    
    #criação de id mqtt para o novo user
    client_id = str(uuid.uuid4())
    
    myobj = {
      "nome": nome,
      "email": email,
      "senha": senha,
      "cpf": cpf,
      "id_paho_mqtt": client_id
    }

    mycol.insert_one(myobj)
    
    print("Documento inserido!")
  
  def CadastroPaciente(self): #cadastro de um paciente
    pass
      
  def Update(self): #update das infos do paciente
      
    mydb = myclient["Paciente"]
    mycol = mydb["infos"]
    
    try:
      cpf = self.payload["cpf"]
      BPM = self.payload["BPM"]
      
      update_query = {
          "$push": {
              "ocorrenciasAmbulancia.0.streamAmbulancia.BPM": BPM,
              "ocorrenciasAmbulancia.0.streamAmbulancia.data": datetime.now()
          }
      }
      
      mycol.update_one({"cpf": cpf}, update_query)
    except Exception as e:
      print("MongoCall.update: " + str(e))
    else:
      print("Documento atualizado!")
    

def on_connect(client, userdata, flags, rc):
  print("Conectado - Codigo de resultado: "+str(rc))
  client.subscribe("VitalGuard/#")

def on_message(client, userdata, msg):
  try:
    payload_str = str(msg.payload.decode())
    if payload_str:  # Verifica se o payload não está vazio
      payload_data = json.loads(payload_str)
      # Instância que interage com o banco de dados
      mongoDB = MongoCall(payload_data)
    else:
      print("Payload vazio.")
      return
  except Exception as e:
      print("on_message: " + str(e))
  
  if(msg.topic == "VitalGuard/cadastro/dados"):
    mongoDB.Cadastro()
  
  if(msg.topic == "VitalGuard/sensor/dados"):
    mongoDB.Update()

  if msg.topic == "VitalGuard/login":
    mongoDB.Login()
    

client.on_connect = on_connect
client.on_message = on_message
		
try:
  client.username_pw_set("Igor", "abc")    
  client.connect("192.168.0.108", 1883, 60)
except:
  print("Não foi possivel conectar ao MQTT...")
  print("Encerrando...")

try:
  client.loop_forever()
except KeyboardInterrupt:
  print("Encerrando...")