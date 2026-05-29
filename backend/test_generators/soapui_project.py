import sys, os, uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models import ServiceDefinition, ServiceType
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


def _soap11_envelope(method, namespace: str) -> str:
    """Build a minimal SOAP 1.1 envelope for embedding inside XML CDATA."""
    param_lines = []
    for param in method.parameters:
        value = _sample_value(param.type)
        param_lines.append(f"            <tns:{param.name}>{value}</tns:{param.name}>")
    params = "\n".join(param_lines)
    body_inner = f"        <tns:{method.name}>\n{params}\n        </tns:{method.name}>" if params else f"        <tns:{method.name}/>"
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


def _xml_escape(text: str) -> str:
    """Escape special XML characters for attribute/text embedding."""
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _generate_soap_project(service: ServiceDefinition) -> str:
    """Build a SoapUI 5.x WSDL/SOAP project XML string."""
    project_id = str(uuid.uuid4())

    # Build interface operations
    operations_xml_parts = []
    for method in service.methods:
        op_id = str(uuid.uuid4())
        req_id = str(uuid.uuid4())
        envelope = _soap11_envelope(method, service.namespace)
        escaped_envelope = _xml_escape(envelope)
        action = f"{service.namespace}/{method.name}"
        operations_xml_parts.append(
            f'        <con:operation isOneWay="false" name="{method.name}" sendSchemaAsBody="false" action="{action}">\n'
            f'            <con:request name="Request 1" id="{req_id}">\n'
            f"                <con:request>{escaped_envelope}</con:request>\n"
            f"            </con:request>\n"
            f"        </con:operation>"
        )
    operations_xml = "\n".join(operations_xml_parts)

    # Build test suites
    suite_id = str(uuid.uuid4())
    test_cases_parts = []
    for method in service.methods:
        case_id = str(uuid.uuid4())
        step_id = str(uuid.uuid4())
        envelope = _soap11_envelope(method, service.namespace)
        escaped_envelope = _xml_escape(envelope)
        test_cases_parts.append(
            f'        <con:testCase name="{method.name} Test" id="{case_id}">\n'
            f'            <con:testStep type="request" name="{method.name} Request" id="{step_id}">\n'
            f"                <con:config>\n"
            f"                    <con:request>{escaped_envelope}</con:request>\n"
            f"                </con:config>\n"
            f"            </con:testStep>\n"
            f"        </con:testCase>"
        )
    test_cases_xml = "\n".join(test_cases_parts)

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<con:soapui-project xmlns:con="http://eviware.com/soapui/config"\n'
        f'    id="{project_id}" name="{service.service_name}" resourceRoot=""\n'
        f'    soapui-version="5.7.0" abortOnError="false">\n'
        f'    <con:interface type="wsdl"\n'
        f'        name="{service.service_name}Service"\n'
        f'        xmlns:con="http://eviware.com/soapui/config"\n'
        f'        bindingName="tns:{service.service_name}SoapBinding"\n'
        f'        definition="{service.namespace}?wsdl"\n'
        f'        wsaVersion="NONE">\n'
        f"{operations_xml}\n"
        f"    </con:interface>\n"
        f'    <con:testSuite name="{service.service_name} Test Suite" id="{suite_id}">\n'
        f"{test_cases_xml}\n"
        f"    </con:testSuite>\n"
        f"</con:soapui-project>"
    )


def _generate_rest_project(service: ServiceDefinition) -> str:
    """Build a SoapUI 5.x REST project XML string."""
    project_id = str(uuid.uuid4())
    suite_id = str(uuid.uuid4())

    # Build REST interface resources
    resources_parts = []
    for method in service.methods:
        res_id = str(uuid.uuid4())
        req_id = str(uuid.uuid4())

        # Build query-param elements
        query_params_xml = ""
        for param in method.parameters:
            value = _sample_value(param.type)
            query_params_xml += (
                f'                    <con:parameter name="{param.name}" '
                f'style="QUERY" default="{value}"/>\n'
            )

        resources_parts.append(
            f'        <con:resource name="{method.name}" path="{method.path}" id="{res_id}">\n'
            f'            <con:method name="{method.name}" method="{method.http_method}" id="{req_id}">\n'
            f"                <con:parameters>\n"
            f"{query_params_xml}"
            f"                </con:parameters>\n"
            f"                <con:request name=\"Request 1\">\n"
            f"                    <con:settings/>\n"
            f"                </con:request>\n"
            f"            </con:method>\n"
            f"        </con:resource>"
        )
    resources_xml = "\n".join(resources_parts)

    # Build REST test cases
    test_cases_parts = []
    for method in service.methods:
        case_id = str(uuid.uuid4())
        step_id = str(uuid.uuid4())
        test_cases_parts.append(
            f'        <con:testCase name="{method.name} Test" id="{case_id}">\n'
            f'            <con:testStep type="restrequest" name="{method.name} Request" id="{step_id}">\n'
            f"                <con:config>\n"
            f'                    <con:method>{method.http_method}</con:method>\n'
            f'                    <con:path>{method.path}</con:path>\n'
            f"                </con:config>\n"
            f"            </con:testStep>\n"
            f"        </con:testCase>"
        )
    test_cases_xml = "\n".join(test_cases_parts)

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<con:soapui-project xmlns:con="http://eviware.com/soapui/config"\n'
        f'    id="{project_id}" name="{service.service_name}" resourceRoot=""\n'
        f'    soapui-version="5.7.0" abortOnError="false">\n'
        f'    <con:interface type="rest"\n'
        f'        name="{service.service_name}REST"\n'
        f'        xmlns:con="http://eviware.com/soapui/config"\n'
        f'        basePath="{service.namespace}">\n'
        f"{resources_xml}\n"
        f"    </con:interface>\n"
        f'    <con:testSuite name="{service.service_name} Test Suite" id="{suite_id}">\n'
        f"{test_cases_xml}\n"
        f"    </con:testSuite>\n"
        f"</con:soapui-project>"
    )


def generate_soapui_project(service: ServiceDefinition) -> Dict[str, str]:
    """
    Generate a SoapUI 5.x project XML file for the given service definition.

    For SOAP or BOTH service types a WSDL/SOAP project is produced.
    For REST-only services a REST project is produced.

    Returns a dict mapping relative file paths to their XML content.
    """
    files: Dict[str, str] = {}
    filename = f"soapui/{service.service_name}-soapui-project.xml"

    if service.service_type in (ServiceType.SOAP, ServiceType.BOTH):
        files[filename] = _generate_soap_project(service)
    else:
        # REST only
        files[filename] = _generate_rest_project(service)

    return files
