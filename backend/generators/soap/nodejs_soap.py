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


def _xsd_type(t: str) -> str:
    return XSD_TYPE_MAP.get(t.lower(), f"tns:{t}")


def _js_default(t: str) -> str:
    mapping = {
        "string": '""',
        "int": "0",
        "float": "0.0",
        "boolean": "false",
        "date": 'new Date().toISOString().split("T")[0]',
        "datetime": "new Date().toISOString()",
    }
    return mapping.get(t.lower(), "null")


class NodeJSSoapGenerator(BaseGenerator):
    def __init__(self, service: ServiceDefinition):
        super().__init__(service)

    def generate(self) -> Dict[str, str]:
        files = {}
        cls = self.class_name

        files["package.json"] = self._package_json()
        files["server.js"] = self._server_js()
        files[f"wsdl/{cls}.wsdl"] = self._wsdl()
        files["README.md"] = self._readme()
        return files

    def _package_json(self) -> str:
        pkg_name = self.pkg.replace("_", "-")
        return f"""{{
  "name": "{pkg_name}",
  "version": "{self.service.version}",
  "description": "{self.service.description or self.service.service_name + ' SOAP Service'}",
  "main": "server.js",
  "scripts": {{
    "start": "node server.js",
    "dev": "nodemon server.js"
  }},
  "dependencies": {{
    "soap": "^1.0.0",
    "express": "^4.18.2"
  }},
  "devDependencies": {{
    "nodemon": "^3.0.0"
  }}
}}
"""

    def _server_js(self) -> str:
        cls = self.class_name
        svc = self.service
        pkg_name = self.pkg.replace("_", "-")

        lines = [
            "'use strict';",
            "",
            "const express = require('express');",
            "const soap = require('soap');",
            "const fs = require('fs');",
            "const path = require('path');",
            "",
            "const app = express();",
            "const PORT = process.env.PORT || 8000;",
            "",
            f"// Service implementation for {cls}",
            f"const {cls}Service = {{",
            f"  {cls}Service: {{",
            f"    {cls}Port: {{",
        ]

        for method in svc.methods:
            lines.append(f"      {method.name}: function(args, callback) {{")
            lines.append(f"        // args contains the request parameters")
            result_obj = "{}"
            if method.return_type.lower() != "void":
                default = _js_default(method.return_type)
                result_obj = f"{{ result: {default} }}"
            lines.append(f"        callback(null, {result_obj});")
            lines.append("      },")

        lines += [
            "    }",
            "  }",
            "};",
            "",
            "// Start HTTP server, then add SOAP service",
            "const server = app.listen(PORT, function() {",
            f"  console.log(`{svc.service_name} SOAP server listening on port ${{PORT}}`);",
            "",
            f"  const wsdlPath = path.join(__dirname, 'wsdl', '{cls}.wsdl');",
            "  const wsdl = fs.readFileSync(wsdlPath, 'utf8');",
            "",
            f"  soap.listen(server, '/ws', {cls}Service, wsdl, function() {{",
            f"    console.log('SOAP service published at http://localhost:' + PORT + '/ws?wsdl');",
            "  });",
            "});",
            "",
            "module.exports = { app, server };",
        ]
        return "\n".join(lines)

    def _wsdl(self) -> str:
        cls = self.class_name
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
            f'    <xsd:schema targetNamespace="{ns}" xmlns:xsd="http://www.w3.org/2001/XMLSchema">',
        ]

        # Complex types for models
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

        # Request/response elements
        for method in svc.methods:
            mname_cap = method.name[0].upper() + method.name[1:]
            req = f"{mname_cap}Request"
            resp = f"{mname_cap}Response"

            lines += [
                f'      <xsd:element name="{req}">',
                f'        <xsd:complexType>',
                f'          <xsd:sequence>',
            ]
            for param in method.parameters:
                xsd_t = _xsd_type(param.type)
                min_o = "1" if param.required else "0"
                lines.append(f'            <xsd:element name="{param.name}" type="{xsd_t}" minOccurs="{min_o}" maxOccurs="1"/>')
            lines += [
                f'          </xsd:sequence>',
                f'        </xsd:complexType>',
                f'      </xsd:element>',
                f'      <xsd:element name="{resp}">',
                f'        <xsd:complexType>',
                f'          <xsd:sequence>',
            ]
            if method.return_type.lower() != "void":
                xsd_t = _xsd_type(method.return_type)
                lines.append(f'            <xsd:element name="result" type="{xsd_t}" minOccurs="0" maxOccurs="1"/>')
            lines += [
                f'          </xsd:sequence>',
                f'        </xsd:complexType>',
                f'      </xsd:element>',
            ]

        lines += [
            '    </xsd:schema>',
            '  </types>',
            '',
        ]

        # Messages
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

        # PortType
        lines += [
            f'  <portType name="{cls}Port">',
        ]
        for method in svc.methods:
            mname_cap = method.name[0].upper() + method.name[1:]
            desc = f' name="{method.name}"'
            if method.description:
                lines.append(f'    <operation{desc}>')
                lines.append(f'      <documentation>{method.description}</documentation>')
            else:
                lines.append(f'    <operation{desc}>')
            lines += [
                f'      <input message="tns:{mname_cap}Request"/>',
                f'      <output message="tns:{mname_cap}Response"/>',
                f'    </operation>',
            ]
        lines += [
            f'  </portType>',
            '',
        ]

        # Binding
        lines += [
            f'  <binding name="{cls}Binding" type="tns:{cls}Port">',
            f'    <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>',
        ]
        for method in svc.methods:
            mname_cap = method.name[0].upper() + method.name[1:]
            lines += [
                f'    <operation name="{method.name}">',
                f'      <soap:operation soapAction="{ns}/{method.name}"/>',
                f'      <input>',
                f'        <soap:body use="literal"/>',
                f'      </input>',
                f'      <output>',
                f'        <soap:body use="literal"/>',
                f'      </output>',
                f'    </operation>',
            ]
        lines += [
            f'  </binding>',
            '',
        ]

        # Service
        lines += [
            f'  <service name="{cls}Service">',
            f'    <port name="{cls}Port" binding="tns:{cls}Binding">',
            f'      <soap:address location="http://localhost:8000/ws"/>',
            f'    </port>',
            f'  </service>',
            '',
            '</definitions>',
        ]
        return "\n".join(lines)

    def _readme(self) -> str:
        svc = self.service
        cls = self.class_name
        return f"""# {svc.service_name} — Node.js SOAP Service

## Description
{svc.description or svc.service_name + ' SOAP web service built with Node.js and the soap library.'}

## Version
{svc.version}

## Requirements
- Node.js 18+
- npm

## Installation

```bash
npm install
```

## Running the Service

```bash
npm start
```

Or for development with auto-reload:

```bash
npm run dev
```

The service will be available at:
- SOAP endpoint: http://localhost:8000/ws
- WSDL: http://localhost:8000/ws?wsdl

## Methods

{chr(10).join(f'- **{m.name}**: {m.description or "No description"}' for m in svc.methods)}

## Namespace
`{svc.namespace}`
"""
