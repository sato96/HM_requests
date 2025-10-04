HM_requests

A Python library that provides a unified interface for sending requests across different protocols.
Currently supports HTTP, CoAP, and MQTT, with an API similar to the popular requests library.

The goal is to let microservices interact with heterogeneous systems without worrying about protocol-specific details.

✨ Features

Familiar API (get, post, put, delete)

Supported protocols:

HTTP (via requests)

CoAP (via aiocoap)

MQTT (via paho-mqtt)

Unified response object (MyResponse) with:

status_code

content

text

headers (when applicable)

protocol

📦 Installation

Clone the repository and install directly from GitHub:

pip install git+https://github.com/your-user/HM_requests.git


Required dependencies:

requests

aiocoap

paho-mqtt

🚀 Usage Examples
HTTP
from HM_requests import Request

resp = Request.post("http://localhost:5000/api", payload={"id": 123, "status": "ok"})
print(resp.status_code, resp.text)

CoAP
from HM_requests import Request

resp = Request.get("coap://localhost/resource")
print(resp.status_code, resp.text)

MQTT
from HM_requests import Request

resp = Request.post("mqtt://localhost:1883", payload={"id": 123, "status": "ok"}, topic="alerts")
print(resp.status_code, resp.json())

📖 API
Request.get(url, **kwargs)

Send a GET request using the selected protocol.

Request.post(url, payload=None, **kwargs)

Send a POST request (HTTP/CoAP/MQTT).
For MQTT, the topic parameter must be provided in kwargs.

Request.put(url, payload=None, **kwargs)

Send a PUT request.

Request.delete(url, **kwargs)

Send a DELETE request.

📋 Roadmap

WebSocket support

Retry and advanced error handling

Asynchronous handling for MQTT

Built-in logging integration