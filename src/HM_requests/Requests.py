from urllib.parse import urlparse
import requests
from aiocoap import *
import paho.mqtt.client as mqtt
import json
import asyncio

class MyResponse:
    def __init__(self, status_code, content, text = "", headers=None, protocol=None):
        self.status_code = status_code  # Codice di stato (es. HTTP/CoAP)
        self.content = content          # Contenuto della risposta
        self.headers = headers or {}   # Intestazioni (se applicabili)
        self.protocol = protocol       # Protocollo usato (es. "http", "coap", "mqtt")
        self.text = text or str(content)

    def json(self):
        try:
            return json.loads(self.content)
        except json.JSONDecodeError:
            return None


class Request:
    @staticmethod
    def post(url, payload=None, **kwargs):
        method = "POST"
        protocol = urlparse(url).scheme
        if  protocol == "http":
            return Request._http_request(method, url, json=payload, **kwargs)
        elif protocol == "coap":
            return asyncio.run(Request._coap_request(method, url, payload))
        elif protocol == "mqtt":
            topic = kwargs.get("topic", "default/request")
            return Request._mqtt_request(method,url,topic, payload)
        else:
            raise ValueError(f"Protocol {protocol} not supported.")

    @staticmethod
    def get(url, **kwargs):
        method = "GET"
        protocol = urlparse(url).scheme
        if  protocol == "http":
            return Request._http_request(method, url, **kwargs)
        elif protocol == "coap":
            import asyncio
            return asyncio.run(Request._coap_request(method, url))
        else:
            raise ValueError(f"Protocol {protocol} not supported.")

    @staticmethod
    def delete(url, **kwargs):
        method = "DELETE"
        protocol = urlparse(url).scheme
        if  protocol == "http":
            return Request._http_request(method, url,  **kwargs)
        elif protocol == "coap":
            import asyncio
            return asyncio.run(Request._coap_request(method, url))
        else:
            raise ValueError(f"Protocol {protocol} not supported.")

    @staticmethod
    def put(url, payload=None, **kwargs):
        method = "PUT"
        protocol = urlparse(url).scheme
        if protocol == "http":
            return Request._http_request(method, url, json=payload, **kwargs)
        elif protocol == "coap":
            import asyncio
            return asyncio.run(Request._coap_request(method, url, payload))
        else:
            raise ValueError(f"Protocol {protocol} not supported.")

    @staticmethod
    def _http_request(method, url, **kwargs):
        response = requests.request(method, url, **kwargs)
        return MyResponse(
            status_code=response.status_code,
            content=response.content,
            text = response.text,
            headers=response.headers,
            protocol="http"
        )

    @staticmethod
    async def _coap_request(method, url, payload=""):
        code_map = {
            "GET": GET,
            "POST": POST,
            "PUT": PUT,
            "DELETE": DELETE
        }
        protocol = await Context.create_client_context()

        # Costruisci il messaggio CoAP
        request = Message(code=code_map[method], uri=url, payload=payload.encode() if payload else "")

        # Invia e ricevi risposta
        response = await protocol.request(request).response

        # Converte lo status CoAP in HTTP (approssimativamente)
        coap_to_http_status = {
            # Successi (2.xx)
            "2.01": 201,  # Created
            "2.02": 204,  # Deleted
            "2.03": 304,  # Valid -> HTTP 304 Not Modified per risposte di validazione
            "2.04": 200,  # Changed
            "2.05": 200,  # Content
            # Errori client (4.xx)
            "4.00": 400,  # Bad Request
            "4.01": 401,  # Unauthorized
            "4.02": 403,  # Forbidden -> HTTP 403 Forbidden
            "4.03": 403,  # Forbidden
            "4.04": 404,  # Not Found
            "4.05": 405,  # Method Not Allowed
            "4.06": 406,  # Not Acceptable
            "4.12": 428,  # Precondition Failed -> HTTP 428 Precondition Required
            "4.13": 413,  # Request Entity Too Large
            "4.15": 415,  # Unsupported Media Type
            # Errori server (5.xx)
            "5.00": 500,  # Internal Server Error
            "5.01": 501,  # Not Implemented
            "5.02": 503,  # Bad Gateway -> HTTP 503 Service Unavailable
            "5.03": 503,  # Service Unavailable
            "5.04": 504,  # Gateway Timeout
            "5.05": 505,  # Proxying Not Supported -> HTTP 505 HTTP Version Not Supported
        }
        status_code = coap_to_http_status.get(str(response.code).split(' ')[0], 500)  # Default: Internal Server Error
        return MyResponse(
            status_code=status_code,
            content=response.payload.decode("utf-8"),
            text = response.payload.decode("utf-8"),
            headers={},  # CoAP ha meno supporto per le intestazioni
            protocol="coap"
        )

    @staticmethod
    def _mqtt_request(method, url,topic, payload):
        # Pubblicazione del messaggio MQTT
        response = {}
        try:
            if method == "POST":
                client = mqtt.Client()
                client.connect(urlparse(url).hostname, urlparse(url).port)
                client.loop_start()
                # Pubblica il JSON come stringa
                result, mid = client.publish(topic, payload, 2)
                if result == mqtt.MQTT_ERR_SUCCESS:
                    response["status_code"] = 200
                    response["content"] = {"status": "ok", "response": "sent"}
                elif result == mqtt.MQTT_ERR_NO_CONN:
                    response["status_code"] = 503
                    response["content"] = {"status": "ko", "response": "error"}
                else:
                    response["status_code"] = 500
                    response["content"] = {"status": "ko", "response": "error"}
                client.loop_stop()
                client.disconnect()
        except Exception as e:
            response["status_code"] = 500
            response["content"] = {"status": "ko", "response": "error"}
        return MyResponse(
            status_code=response.get("status_code", 500),  # Default: timeout o errore
            content=response.get("content", {"status": "ko", "response": "error"}),
            text = str(response.get("content", {"status": "ko", "response": "error"})),
            protocol="mqtt"
        )
