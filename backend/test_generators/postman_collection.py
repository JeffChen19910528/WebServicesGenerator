import sys, os, uuid, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models import ServiceDefinition, ServiceType, ParameterLocation
from typing import Dict, Any, List


SAMPLE_VALUES = {
    "string": "example_string",
    "int": 1,
    "float": 1.0,
    "boolean": True,
    "date": "2024-01-01",
    "datetime": "2024-01-01T00:00:00",
}

SAMPLE_VALUES_STR = {
    "string": "example_string",
    "int": "1",
    "float": "1.0",
    "boolean": "true",
    "date": "2024-01-01",
    "datetime": "2024-01-01T00:00:00",
}


def _sample_value(param_type: str):
    return SAMPLE_VALUES.get(param_type.lower(), "example_value")


def _sample_value_str(param_type: str) -> str:
    return SAMPLE_VALUES_STR.get(param_type.lower(), "example_value")


def _soap11_envelope(method, namespace: str) -> str:
    param_lines = []
    for param in method.parameters:
        value = _sample_value_str(param.type)
        param_lines.append(f"            <tns:{param.name}>{value}</tns:{param.name}>")
    params = "\n".join(param_lines)
    body_inner = (
        f"        <tns:{method.name}>\n{params}\n        </tns:{method.name}>"
        if params
        else f"        <tns:{method.name}/>"
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"\n'
        f'                  xmlns:tns="{namespace}">\n'
        "    <soapenv:Header/>\n"
        "    <soapenv:Body>\n"
        f"{body_inner}\n"
        "    </soapenv:Body>\n"
        "</soapenv:Envelope>"
    )


def _path_segments(path: str) -> List[str]:
    """Split a URL path string into non-empty segments."""
    return [seg for seg in path.strip("/").split("/") if seg]


def _build_rest_item(method, namespace: str) -> Dict[str, Any]:
    """Build a Postman collection item for a REST method."""
    http_method = method.http_method.upper()

    # Separate parameters by location
    query_params = [p for p in method.parameters if p.location == ParameterLocation.QUERY]
    path_params = [p for p in method.parameters if p.location == ParameterLocation.PATH]
    body_params = [p for p in method.parameters if p.location == ParameterLocation.BODY]
    header_params = [p for p in method.parameters if p.location == ParameterLocation.HEADER]

    # Resolve path: replace :param or {param} placeholders with sample values
    resolved_path = method.path
    for param in path_params:
        resolved_path = resolved_path.replace(f"{{{param.name}}}", f":{param.name}")

    raw_url = f"{{{{base_url}}}}{method.path}"

    query_array = [
        {
            "key": p.name,
            "value": _sample_value_str(p.type),
            "description": p.description or "",
        }
        for p in query_params
    ]

    url_obj: Dict[str, Any] = {
        "raw": raw_url,
        "host": ["{{base_url}}"],
        "path": _path_segments(method.path),
    }
    if query_array:
        url_obj["query"] = query_array

    # Build headers
    headers = [{"key": "Content-Type", "value": "application/json"}]
    for p in header_params:
        headers.append({"key": p.name, "value": _sample_value_str(p.type), "description": p.description or ""})

    # Build body
    body_obj: Dict[str, Any] = {"mode": "raw", "raw": "", "options": {"raw": {"language": "json"}}}
    if http_method in ("POST", "PUT", "PATCH") and body_params:
        body_dict = {p.name: _sample_value(p.type) for p in body_params}
        body_obj["raw"] = json.dumps(body_dict, indent=2)
    elif http_method in ("POST", "PUT", "PATCH"):
        body_obj["raw"] = "{}"

    item: Dict[str, Any] = {
        "name": method.name,
        "request": {
            "method": http_method,
            "header": headers,
            "url": url_obj,
        },
        "response": [],
    }
    if http_method in ("POST", "PUT", "PATCH", "DELETE"):
        item["request"]["body"] = body_obj

    return item


def _build_soap_item(method, namespace: str) -> Dict[str, Any]:
    """Build a Postman collection item for a SOAP method (POST with XML body)."""
    envelope = _soap11_envelope(method, namespace)
    action = f"{namespace}/{method.name}"
    raw_url = "{{base_url}}"

    return {
        "name": f"{method.name} (SOAP)",
        "request": {
            "method": "POST",
            "header": [
                {"key": "Content-Type", "value": "text/xml; charset=utf-8"},
                {"key": "SOAPAction", "value": f'"{action}"'},
            ],
            "url": {
                "raw": raw_url,
                "host": ["{{base_url}}"],
                "path": [],
            },
            "body": {
                "mode": "raw",
                "raw": envelope,
                "options": {"raw": {"language": "xml"}},
            },
        },
        "response": [],
    }


def _collection_skeleton(service: ServiceDefinition, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "info": {
            "_postman_id": str(uuid.uuid4()),
            "name": service.service_name,
            "description": service.description or "",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "item": items,
        "variable": [
            {"key": "base_url", "value": "http://localhost:8080"},
        ],
    }


def _environment_doc(service: ServiceDefinition) -> Dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "name": f"{service.service_name} Environment",
        "values": [
            {"key": "base_url", "value": "http://localhost:8080", "enabled": True},
        ],
    }


def generate_postman_collection(service: ServiceDefinition) -> Dict[str, str]:
    """
    Generate a Postman Collection v2.1 JSON and a companion environment JSON
    for the given service definition.

    - SOAP services: each method becomes a SOAP POST item.
    - REST services: each method becomes a REST item with correct HTTP verb,
      path/query/body parameters.
    - BOTH services: items are grouped into "SOAP Requests" and "REST Requests"
      folders.

    Returns a dict mapping relative file paths to their JSON content.
    """
    files: Dict[str, str] = {}

    collection_path = f"postman/{service.service_name}.postman_collection.json"
    environment_path = f"postman/{service.service_name}.postman_environment.json"

    if service.service_type == ServiceType.SOAP:
        items = [_build_soap_item(m, service.namespace) for m in service.methods]
        collection = _collection_skeleton(service, items)

    elif service.service_type == ServiceType.REST:
        items = [_build_rest_item(m, service.namespace) for m in service.methods]
        collection = _collection_skeleton(service, items)

    else:  # BOTH
        soap_folder: Dict[str, Any] = {
            "name": "SOAP Requests",
            "item": [_build_soap_item(m, service.namespace) for m in service.methods],
        }
        rest_folder: Dict[str, Any] = {
            "name": "REST Requests",
            "item": [_build_rest_item(m, service.namespace) for m in service.methods],
        }
        collection = _collection_skeleton(service, [soap_folder, rest_folder])

    files[collection_path] = json.dumps(collection, indent=2)
    files[environment_path] = json.dumps(_environment_doc(service), indent=2)

    return files
