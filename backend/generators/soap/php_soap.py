import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from models import ServiceDefinition
from generators.base import BaseGenerator, PRIMITIVE_TYPES
from typing import Dict


XSD_TYPE_MAP = {
    "string": "xsd:string",
    "int": "xsd:int",
    "float": "xsd:float",
    "boolean": "xsd:boolean",
    "date": "xsd:date",
    "datetime": "xsd:dateTime",
}

PHP_DEFAULT = {
    "string": "''",
    "int": "0",
    "float": "0.0",
    "boolean": "false",
    "date": "'2000-01-01'",
    "datetime": "'2000-01-01T00:00:00'",
}


def _xsd_type(t: str) -> str:
    return XSD_TYPE_MAP.get(t.lower(), f"tns:{t}")


def _php_default(t: str) -> str:
    return PHP_DEFAULT.get(t.lower(), "null")


class PHPSoapGenerator(BaseGenerator):
    def __init__(self, service: ServiceDefinition):
        super().__init__(service)

    def generate(self) -> Dict[str, str]:
        files = {}
        cls = self.class_name

        files["server.php"] = self._server_php(cls)
        files[f"{cls}Service.php"] = self._service_class(cls)
        files[f"wsdl/{cls}.wsdl"] = self._wsdl(cls)
        files["composer.json"] = self._composer_json()
        files["README.md"] = self._readme(cls)
        return files

    def _server_php(self, cls: str) -> str:
        return f"""<?php
require_once __DIR__ . '/vendor/autoload.php';
require_once __DIR__ . '/{cls}Service.php';

$wsdlPath = __DIR__ . '/wsdl/{cls}.wsdl';

if (!file_exists($wsdlPath)) {{
    http_response_code(500);
    echo 'WSDL file not found.';
    exit;
}}

$options = [
    'uri'      => '{self.service.namespace}',
    'location' => 'http://localhost:8080/server.php',
];

$server = new SoapServer($wsdlPath, $options);
$server->setClass('{cls}Service');
$server->handle();
"""

    def _service_class(self, cls: str) -> str:
        svc = self.service
        lines = [
            "<?php",
            "",
            f"class {cls}Service",
            "{",
        ]
        for method in svc.methods:
            params_str = ", ".join(f"${p.name}" for p in method.parameters)
            if method.description:
                lines += [
                    "    /**",
                    f"     * {method.description}",
                    "     */",
                ]
            lines += [
                f"    public function {method.name}({params_str})",
                "    {",
            ]
            if method.return_type.lower() != "void":
                default = _php_default(method.return_type)
                lines.append(f"        return {default};")
            lines += [
                "    }",
                "",
            ]
        lines.append("}")
        return "\n".join(lines)

    def _wsdl(self, cls: str) -> str:
        svc = self.service
        ns = svc.namespace

        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<definitions xmlns="http://schemas.xmlsoap.org/wsdl/"',
            f'             xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"',
            f'             xmlns:tns="{ns}"',
            f'             xmlns:xsd="http://www.w3.org/2001/XMLSchema"',
            f'             name="{cls}Service"',
            f'             targetNamespace="{ns}">',
            "",
            "  <types>",
            f'    <xsd:schema targetNamespace="{ns}">',
        ]

        for model in svc.models:
            lines += [
                f'      <xsd:complexType name="{model.name}">',
                f'        <xsd:sequence>',
            ]
            for field in model.fields:
                xsd_t = _xsd_type(field.type)
                min_o = "1" if field.required else "0"
                lines.append(f'          <xsd:element name="{field.name}" type="{xsd_t}" minOccurs="{min_o}" maxOccurs="1"/>')
            lines += [
                f'        </xsd:sequence>',
                f'      </xsd:complexType>',
            ]

        for method in svc.methods:
            mname_cap = method.name[0].upper() + method.name[1:]
            req = f"{mname_cap}Request"
            resp = f"{mname_cap}Response"

            lines += [
                f'      <xsd:element name="{req}">',
                f'        <xsd:complexType><xsd:sequence>',
            ]
            for param in method.parameters:
                xsd_t = _xsd_type(param.type)
                min_o = "1" if param.required else "0"
                lines.append(f'          <xsd:element name="{param.name}" type="{xsd_t}" minOccurs="{min_o}" maxOccurs="1"/>')
            lines += [
                f'        </xsd:sequence></xsd:complexType>',
                f'      </xsd:element>',
                f'      <xsd:element name="{resp}">',
                f'        <xsd:complexType><xsd:sequence>',
            ]
            if method.return_type.lower() != "void":
                xsd_t = _xsd_type(method.return_type)
                lines.append(f'          <xsd:element name="result" type="{xsd_t}" minOccurs="0" maxOccurs="1"/>')
            lines += [
                f'        </xsd:sequence></xsd:complexType>',
                f'      </xsd:element>',
            ]

        lines += [
            '    </xsd:schema>',
            '  </types>',
            '',
        ]

        for method in svc.methods:
            mname_cap = method.name[0].upper() + method.name[1:]
            lines += [
                f'  <message name="{mname_cap}Request">',
                f'    <part name="parameters" element="tns:{mname_cap}Request"/>',
                f'  </message>',
                f'  <message name="{mname_cap}Response">',
                f'    <part name="parameters" element="tns:{mname_cap}Response"/>',
                f'  </message>',
                '',
            ]

        lines += [
            f'  <portType name="{cls}Port">',
        ]
        for method in svc.methods:
            mname_cap = method.name[0].upper() + method.name[1:]
            lines += [
                f'    <operation name="{method.name}">',
                f'      <input message="tns:{mname_cap}Request"/>',
                f'      <output message="tns:{mname_cap}Response"/>',
                f'    </operation>',
            ]
        lines += [
            f'  </portType>',
            '',
            f'  <binding name="{cls}Binding" type="tns:{cls}Port">',
            f'    <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>',
        ]
        for method in svc.methods:
            mname_cap = method.name[0].upper() + method.name[1:]
            lines += [
                f'    <operation name="{method.name}">',
                f'      <soap:operation soapAction="{ns}/{method.name}"/>',
                f'      <input><soap:body use="literal"/></input>',
                f'      <output><soap:body use="literal"/></output>',
                f'    </operation>',
            ]
        lines += [
            f'  </binding>',
            '',
            f'  <service name="{cls}Service">',
            f'    <port name="{cls}Port" binding="tns:{cls}Binding">',
            f'      <soap:address location="http://localhost:8080/server.php"/>',
            f'    </port>',
            f'  </service>',
            '',
            '</definitions>',
        ]
        return "\n".join(lines)

    def _composer_json(self) -> str:
        pkg = self.pkg.replace("_", "-")
        return f"""{{
  "name": "example/{pkg}",
  "description": "{self.service.description or self.service.service_name + ' SOAP Service'}",
  "type": "project",
  "require": {{
    "php": ">=8.1"
  }},
  "autoload": {{
    "psr-4": {{
      "": "src/"
    }}
  }}
}}
"""

    def _readme(self, cls: str) -> str:
        svc = self.service
        return f"""# {svc.service_name} — PHP SOAP Service

## Description
{svc.description or svc.service_name + ' SOAP web service built with PHP SoapServer.'}

## Version
{svc.version}

## Requirements
- PHP 8.1+ with the `soap` extension enabled
- Composer (optional, for autoloading)

## Running the Service

Using PHP built-in server:

```bash
php -S localhost:8080
```

Then access:
- SOAP endpoint: http://localhost:8080/server.php
- WSDL: http://localhost:8080/wsdl/{cls}.wsdl

## Methods

{chr(10).join(f'- **{m.name}**: {m.description or "No description"}' for m in svc.methods)}

## Namespace
`{svc.namespace}`
"""
