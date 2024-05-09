const { MongoClient } = require("mongodb");
const mqtt = require("mqtt");
const uuid = require("uuid");

const mongoClient = new MongoClient(
  "mongodb+srv://igorvieira:vitalguard@cluster0.w3yfk85.mongodb.net/"
);
const client = mqtt.connect("mqtt://192.168.0.108");

class MongoCall {
  constructor(payload_data) {
    this.payload = payload_data;
  }

  async login() {
    const mydb = mongoClient.db("Users");
    const mycol = mydb.collection("infos");

    try {
      const { email, senha } = this.payload;
      const loginCheck = await mycol.findOne(
        { email, senha },
        { projection: { id_paho_mqtt: 1 } }
      );
      if (loginCheck) {
        const id_paho_mqtt = loginCheck.id_paho_mqtt.toString();
        client.publish(
          `VitalGuard/${id_paho_mqtt}/login/status`,
          JSON.stringify({ aprovado: true, id_paho_mqtt })
        );
      } else {
        console.log("Usuário não encontrado");
        client.publish(
          "VitalGuard/**id_da_sessão_app**/login/status",
          JSON.stringify({ aprovado: false })
        );
      }
    } catch (error) {
      console.error("Login error:", error);
    }
  }

  async cadastro() {
    const mydb = mongoClient.db("Users");
    const mycol = mydb.collection("infos");

    try {
      const { nome, senha, cpf, email } = this.payload;
      const cpf_check = await mycol.findOne({ cpf });
      const email_check = await mycol.findOne({ email });
      if (cpf_check || email_check) {
        console.log("CPF ou email já cadastrado!");
        client.publish(
          "VitalGuard/**id_sessão**/cadastro/cadastroFalhou",
          "cpf&emailDuplicado"
        );
        return;
      }
      const client_id = uuid.v4();
      const myobj = { nome, email, senha, cpf, id_paho_mqtt: client_id };
      await mycol.insertOne(myobj);
      console.log("Documento inserido!");
    } catch (error) {
      console.error("Cadastro error:", error);
    }
  }

  cadastroPaciente() {
    // To be implemented
  }

  async update() {
    const mydb = mongoClient.db("Paciente");
    const mycol = mydb.collection("infos");

    try {
      const { cpf, BPM } = this.payload;
      const update_query = {
        $push: {
          "ocorrenciasAmbulancia.0.streamAmbulancia.BPM": BPM,
          "ocorrenciasAmbulancia.0.streamAmbulancia.data": new Date(),
        },
      };
      await mycol.updateOne({ cpf }, update_query);
      console.log("Documento atualizado!");
    } catch (error) {
      console.error("Update error:", error);
    }
  }
}

const on_connect = () => {
  console.log("Conectado");
  client.subscribe("VitalGuard/#");
};

const on_message = (topic, message) => {
  try {
    const payload_str = message.toString();
    if (payload_str) {
      const payload_data = JSON.parse(payload_str);
      const mongoDB = new MongoCall(payload_data);
      if (topic === "VitalGuard/cadastro/dados") {
        mongoDB.cadastro();
      } else if (topic === "VitalGuard/sensor/dados") {
        mongoDB.update();
      } else if (topic === "VitalGuard/login") {
        mongoDB.login();
      }
    } else {
      console.log("Payload vazio.");
    }
  } catch (error) {
    console.error("on_message error:", error);
  }
};

client.on("connect", on_connect);
client.on("message", on_message);

try {
  client.options.username = "Igor";
  client.options.password = "abc";
  client.reconnect();
} catch (error) {
  console.error("MQTT connection error:", error);
}
