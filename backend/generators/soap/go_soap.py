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

GO_TYPE_MAP = {
    "string": "string",
    "int": "int",
    "float": "float64",
    "boolean": "bool",
    "date": "string",
    "datetime": "string",
    "void": "",
}

GO_DEFAULT = {
    "string": '""',
    "int": "0",
    "float": "0.0",
    "boolean": "false",
    "date": '"2000-01-01"',
    "datetime": '"2000-01-01T00:00:00Z"',
}


def _xsd_type(t: str) -> str:
    return XSD_TYPE_MAP.get(t.lower(), f"tns:{t}")


def _go_type(t: str) -> str:
    return GO_TYPE_MAP.get(t.lower(), t)


def _go_default(t: str) -> str:
    return GO_DEFAULT.get(t.lower(), "nil")


class GoSoapGenerator(BaseGenerator):
    def __init__(self, service: ServiceDefinition):
        super().__init__(service)

    def generate(self) -> Dict[str, str]:
        files = {}
        cls = self.class_name
        pkg = self.pkg

        files["go.mod"] = self._go_mod(pkg)
        files["main.go"] = self._main_go(pkg, cls)
        files["service.go"] = self._service_go(pkg, cls)
        files[f"wsdl/{cls}.wsdl"] = self._wsdl(cls)
        files["README.md"] = self._readme(cls)
        return files

    def _go_mod(self, pkg: str) -> str:
        return f"""module {pkg}

go 1.21

require (
    golang.org/x/net v0.20.0
)
"""

    def _main_go(self, pkg: str, cls: str) -> str:
        svc = self.service

        lines = [
            f"package main",
            "",
            "import (",
            '    "encoding/xml"',
            '    "fmt"',
            '    "io"',
            '    "log"',
            '    "net/http"',
            '    "os"',
            '    "strings"',
            ")",
            "",
            "// SOAPEnvelope represents a generic SOAP envelope",
            "type SOAPEnvelope struct {",
            '    XMLName xml.Name   `xml:"Envelope"`',
            '    Body    SOAPBody   `xml:"Body"`',
            "}",
            "",
            "type SOAPBody struct {",
            '    Content []byte `xml:",innerxml"`',
            "}",
            "",
            "// SOAPFault represents a SOAP fault response",
            "type SOAPFault struct {",
            '    XMLName xml.Name `xml:"Fault"`',
            '    Code    string   `xml:"faultcode"`',
            '    String  string   `xml:"faultstring"`',
            "}",
            "",
            f"var svc = &{cls}Service{{}}",
            "",
            "func soapHandler(w http.ResponseWriter, r *http.Request) {",
            '    w.Header().Set("Content-Type", "text/xml; charset=utf-8")',
            "",
            "    if r.Method == http.MethodGet {",
            '        if r.URL.Query().Get("wsdl") != "" {',
            '            wsdlPath := "wsdl/' + cls + '.wsdl"',
            "            data, err := os.ReadFile(wsdlPath)",
            "            if err != nil {",
            "                http.Error(w, err.Error(), http.StatusInternalServerError)",
            "                return",
            "            }",
            '            w.Header().Set("Content-Type", "text/xml; charset=utf-8")',
            "            w.Write(data)",
            "            return",
            "        }",
            "    }",
            "",
            "    body, err := io.ReadAll(r.Body)",
            "    if err != nil {",
            "        writeFault(w, err.Error())",
            "        return",
            "    }",
            "    defer r.Body.Close()",
            "",
            "    bodyStr := string(body)",
            "",
        ]

        for i, method in enumerate(svc.methods):
            mname_cap = method.name[0].upper() + method.name[1:]
            cond = "if" if i == 0 else "} else if"
            lines.append(f'    {cond} strings.Contains(bodyStr, "{mname_cap}Request") {{')
            lines.append(f"        handle{mname_cap}(w, body)")

        if svc.methods:
            lines += [
                "    } else {",
                '        writeFault(w, "Unknown SOAP action")',
                "    }",
            ]
        else:
            lines.append('    writeFault(w, "No methods defined")')

        lines += [
            "}",
            "",
            "func writeFault(w http.ResponseWriter, msg string) {",
            "    fault := SOAPFault{Code: \"soap:Server\", String: msg}",
            "    data, _ := xml.Marshal(fault)",
            '    envelope := fmt.Sprintf(`<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body>%s</soap:Body></soap:Envelope>`, string(data))',
            "    w.WriteHeader(http.StatusInternalServerError)",
            "    w.Write([]byte(envelope))",
            "}",
            "",
        ]

        # Per-method handlers
        for method in svc.methods:
            mname_cap = method.name[0].upper() + method.name[1:]
            req_type = f"{mname_cap}Request"
            resp_type = f"{mname_cap}Response"
            ns = svc.namespace

            lines += [
                f"type {req_type} struct {{",
                f'    XMLName xml.Name `xml:"{req_type}"`',
            ]
            for param in method.parameters:
                go_t = _go_type(param.type)
                pname_cap = param.name[0].upper() + param.name[1:]
                lines.append(f'    {pname_cap} {go_t} `xml:"{param.name}"`')
            lines += [
                "}",
                "",
                f"type {resp_type} struct {{",
                f'    XMLName xml.Name `xml:"{resp_type}"`',
            ]
            if method.return_type.lower() != "void":
                go_t = _go_type(method.return_type)
                lines.append(f'    Result {go_t} `xml:"result"`')
            lines += [
                "}",
                "",
                f"func handle{mname_cap}(w http.ResponseWriter, body []byte) {{",
                f"    var env struct {{",
                f'        XMLName xml.Name  `xml:"Envelope"`',
                f"        Body    struct {{",
                f"            Req {req_type} `xml:\"{req_type}\"`",
                f"        }} `xml:\"Body\"`",
                f"    }}",
                f"    if err := xml.Unmarshal(body, &env); err != nil {{",
                f"        writeFault(w, err.Error())",
                f"        return",
                f"    }}",
                f"    req := env.Body.Req",
                f"    _ = req",
            ]

            go_params = ", ".join(
                f"req.{p.name[0].upper() + p.name[1:]}"
                for p in method.parameters
            )

            if method.return_type.lower() != "void":
                lines.append(f"    result := svc.{method.name[0].upper() + method.name[1:]}({go_params})")
                lines.append(f"    resp := {resp_type}{{Result: result}}")
            else:
                lines.append(f"    svc.{method.name[0].upper() + method.name[1:]}({go_params})")
                lines.append(f"    resp := {resp_type}{{}}")

            lines += [
                "    data, _ := xml.Marshal(resp)",
                f'    envelope := fmt.Sprintf(`<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tns="{ns}"><soap:Body>%s</soap:Body></soap:Envelope>`, string(data))',
                "    w.Write([]byte(envelope))",
                "}",
                "",
            ]

        lines += [
            "func main() {",
            '    http.HandleFunc("/ws", soapHandler)',
            '    log.Println("' + svc.service_name + ' SOAP server starting on :8080...")',
            '    log.Println("WSDL available at http://localhost:8080/ws?wsdl")',
            '    if err := http.ListenAndServe(":8080", nil); err != nil {',
            "        log.Fatal(err)",
            "    }",
            "}",
        ]
        return "\n".join(lines)

    def _service_go(self, pkg: str, cls: str) -> str:
        svc = self.service

        lines = [
            "package main",
            "",
        ]

        # Struct types for models
        for model in svc.models:
            lines += [
                f"type {model.name} struct {{",
            ]
            for field in model.fields:
                go_t = _go_type(field.type)
                fname_cap = field.name[0].upper() + field.name[1:]
                lines.append(f"    {fname_cap} {go_t}")
            lines += ["}", ""]

        # Service struct
        lines += [
            f"type {cls}Service struct{{}}",
            "",
        ]

        for method in svc.methods:
            mname_cap = method.name[0].upper() + method.name[1:]
            params = ", ".join(f"{p.name} {_go_type(p.type)}" for p in method.parameters)
            ret = _go_type(method.return_type)

            if ret:
                lines += [
                    f"func (s *{cls}Service) {mname_cap}({params}) {ret} {{",
                    f"    return {_go_default(method.return_type)}",
                    "}",
                    "",
                ]
            else:
                lines += [
                    f"func (s *{cls}Service) {mname_cap}({params}) {{",
                    "}",
                    "",
                ]

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

        lines += [f'  <portType name="{cls}Port">']
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
            f'      <soap:address location="http://localhost:8080/ws"/>',
            f'    </port>',
            f'  </service>',
            '',
            '</definitions>',
        ]
        return "\n".join(lines)

    def _readme(self, cls: str) -> str:
        svc = self.service
        return f"""# {svc.service_name} — Go SOAP Service

## Description
{svc.description or svc.service_name + ' SOAP web service built with Go net/http.'}

## Version
{svc.version}

## Requirements
- Go 1.21+

## Running the Service

```bash
go mod tidy
go run .
```

The service will be available at:
- SOAP endpoint: http://localhost:8080/ws
- WSDL: http://localhost:8080/ws?wsdl

## Methods

{chr(10).join(f'- **{m.name}**: {m.description or "No description"}' for m in svc.methods)}

## Namespace
`{svc.namespace}`
"""
