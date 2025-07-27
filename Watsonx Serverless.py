import http.client
import urllib.parse
import json
from datetime import datetime

def main(params):
    # Step 1: Pega parametros
    mensagem = params.get("mensagem", "Perdi meu cartão, o que devo fazer?")
    
    # Step 2: Gerar o token IAM
    iam_url = "iam.cloud.ibm.com"
    iam_endpoint = "/identity/token"
    apikey = "zxRt6HxOkt-eSVrAl_fR3bMsACYQRZiwDk4R9dkPXk1F"

    # Preparar os dados e cabeçalhos
    iam_payload = urllib.parse.urlencode({
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": apikey
    })
    iam_headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }

    # Conexão com o endpoint IAM
    conn = http.client.HTTPSConnection(iam_url)
    conn.request("POST", iam_endpoint, body=iam_payload, headers=iam_headers)

    # Obter resposta
    iam_response = conn.getresponse()
    if iam_response.status != 200:
        raise ValueError(f"Falha ao obter token IAM: {iam_response.status} - {iam_response.reason}")

    iam_data = json.loads(iam_response.read().decode())
    token = iam_data.get("access_token")
    conn.close()

    
    # Step 3: Conecta WatsonX.ai Runtime
    watsonx_url = "https://us-south.ml.cloud.ibm.com/ml/v4/deployments/df652e81-332e-4d27-9c34-32d2cd100d64/ai_service?version=2021-05-01"
    watsonx_headers = {
        "Content-Type": "application/json", 
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    watsonx_payload = {"messages": [{"role": "user", "content": mensagem}]}

    try:
        conn = http.client.HTTPSConnection(watsonx_url.split('/')[2])
        path = '/' + '/'.join(watsonx_url.split('/')[3:])
        conn.request("POST", path, body=json.dumps(watsonx_payload), headers=watsonx_headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()

        if response.status >= 400:
            return {"statusCode": 200, "body": f"HTTP {response.status}: {data.decode('utf-8')}"}
            raise Exception(f"HTTP {response.status}: {data.decode('utf-8')}")
        # Validar se a resposta é um JSON válido
        try:
            watsonx_response = json.loads(data)
        except json.JSONDecodeError as e:
            raise Exception(f"Resposta não é um JSON válido: {data.decode('utf-8')} - Erro: {str(e)}")

        # Garantir que o JSON contém a estrutura esperada
        if not isinstance(watsonx_response, dict) or "choices" not in watsonx_response:
            raise Exception(f"Resposta JSON inesperada: {watsonx_response}")
        # Processar o conteúdo
        response_content = watsonx_response.get("choices", [{}])[0].get("message", {}).get("content", "")

    except Exception as e:
        return {
            "statusCode": 500,
            "body": {"error": "Failed to fetch response from WatsonX", "details": str(e)}
        }

    # 4 - Retorna resposta
    return {
        "statusCode": 200,
        "body": {
            "response": response_content
        }
    }
