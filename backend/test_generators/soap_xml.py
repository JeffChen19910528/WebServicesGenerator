import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models import ServiceDefinition
from typing import Dict


SAMPLE_VALUES = {
    "string": "example_string",
    "int": "1",
    "float": "1.0",
    "boolean": "true",
    "date": "2024-01-01",
    "datetime": "2024-01-01T00:00:00",
}


def _sample_value(param_type: str) -> str:
    return SAMPLE_VALUES.get(param_type.lower(), "example_value")


def _build_param_elements(method, namespace: str, indent: str = "            ") -> str:
    lines = []
    for param in method.parameters:
        value = _sample_value(param.type)
        lines.append(f"{indent}<tns:{param.name}>{value}</tns:{param.name}>")
    return "\n".join(lines) if lines else ""


def generate_soap_xml(service: ServiceDefinition) -> Dict[str, str]:
    """
    Generate SOAP 1.1 and SOAP 1.2 XML envelope files for each method
    in the service definition.

    Returns a dict mapping relative file paths to their XML content.
    """
    files: Dict[str, str] = {}

    for method in service.methods:
        param_block = _build_param_elements(method, service.namespace)

        # --- SOAP 1.1 ---
        soap11_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"',
            f'                  xmlns:tns="{service.namespace}">',
            "    <soapenv:Header/>",
            "    <soapenv:Body>",
            f"        <tns:{method.name}>",
        ]
        if param_block:
            soap11_lines.append(param_block)
        soap11_lines += [
            f"        </tns:{method.name}>",
            "    </soapenv:Body>",
            "</soapenv:Envelope>",
        ]
        soap11_content = "\n".join(soap11_lines)
        soap11_path = f"soap_xml/{method.name}Request.xml"
        files[soap11_path] = soap11_content

        # --- SOAP 1.2 ---
        soap12_ns = "http://www.w3.org/2003/05/soap-envelope"
        action = f"{service.namespace}/{method.name}"

        # Re-build param block with same indentation; namespace prefix stays tns
        param_block_12 = _build_param_elements(method, service.namespace)

        soap12_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<soap:Envelope xmlns:soap="{soap12_ns}"',
            f'               xmlns:tns="{service.namespace}">',
            "    <soap:Header>",
            f'        <soap:Action>{action}</soap:Action>',
            "    </soap:Header>",
            "    <soap:Body>",
            f"        <tns:{method.name}>",
        ]
        if param_block_12:
            soap12_lines.append(param_block_12)
        soap12_lines += [
            f"        </tns:{method.name}>",
            "    </soap:Body>",
            "</soap:Envelope>",
        ]
        soap12_content = "\n".join(soap12_lines)
        soap12_path = f"soap_xml/{method.name}Request_SOAP12.xml"
        files[soap12_path] = soap12_content

    return files
