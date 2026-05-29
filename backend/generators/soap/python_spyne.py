import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from models import ServiceDefinition
from generators.base import BaseGenerator, PRIMITIVE_TYPES
from typing import Dict


SPYNE_TYPE_MAP = {
    "string": "Unicode",
    "int": "Integer",
    "float": "Float",
    "boolean": "Boolean",
    "date": "Date",
    "datetime": "DateTime",
}

PYTHON_DEFAULT = {
    "string": '""',
    "int": "0",
    "float": "0.0",
    "boolean": "False",
    "date": "None",
    "datetime": "None",
    "void": "None",
}


def _spyne_type(t: str) -> str:
    lower = t.lower()
    return SPYNE_TYPE_MAP.get(lower, t)


def _python_default(t: str) -> str:
    return PYTHON_DEFAULT.get(t.lower(), "None")


class PythonSpyneGenerator(BaseGenerator):
    def __init__(self, service: ServiceDefinition):
        super().__init__(service)

    def generate(self) -> Dict[str, str]:
        files = {}
        files["requirements.txt"] = self._requirements()
        files["service.py"] = self._service()
        files["app.py"] = self._app()
        files["README.md"] = self._readme()
        return files

    def _requirements(self) -> str:
        return """spyne>=2.14.0
lxml>=4.9.0
werkzeug>=2.3.0
flask>=3.0.0
"""

    def _service(self) -> str:
        svc = self.service
        cls = self.class_name
        namespace = svc.namespace

        # Collect all spyne types needed
        spyne_types = set()
        for method in svc.methods:
            for param in method.parameters:
                spyne_types.add(_spyne_type(param.type))
            if method.return_type.lower() != "void":
                spyne_types.add(_spyne_type(method.return_type))
        for model in svc.models:
            for field in model.fields:
                spyne_types.add(_spyne_type(field.type))

        # Remove model names (not spyne primitives)
        primitive_spyne = {"Unicode", "Integer", "Float", "Boolean", "Date", "DateTime"}
        spyne_types = spyne_types & primitive_spyne

        lines = [
            "from spyne import Application, ComplexModel, rpc, ServiceBase",
            f"from spyne.model import {', '.join(sorted(spyne_types)) if spyne_types else 'Unicode'}",
            "from spyne.protocol.soap import Soap11",
            "from spyne.server.wsgi import WsgiApplication",
            "",
        ]

        # Generate ComplexModel classes for each ModelDef
        for model in svc.models:
            lines += [
                f"class {model.name}(ComplexModel):",
            ]
            if not model.fields:
                lines.append("    pass")
            else:
                for field in model.fields:
                    spyne_t = _spyne_type(field.type)
                    lines.append(f"    {field.name} = {spyne_t}")
            lines.append("")

        # Generate the ServiceBase class
        lines += [
            f"class {cls}Service(ServiceBase):",
            "",
        ]

        for method in svc.methods:
            params_in = []
            for param in method.parameters:
                spyne_t = _spyne_type(param.type)
                params_in.append(f"_in_{param.name}={spyne_t}")

            if method.return_type.lower() == "void":
                ret_spec = "_returns=None"
            else:
                ret_t = _spyne_type(method.return_type)
                ret_spec = f"_returns={ret_t}"

            decorator_args = ", ".join(params_in + [ret_spec])
            lines += [
                f"    @rpc({decorator_args})",
                f"    def {method.name}(ctx, {', '.join(p.name for p in method.parameters)}):",
            ]
            if method.description:
                lines.append(f'        """{method.description}"""')

            if method.return_type.lower() == "void":
                lines.append("        pass")
            else:
                default = _python_default(method.return_type)
                lines.append(f"        return {default}")
            lines.append("")

        lines += [
            "",
            f"application = Application(",
            f"    [{cls}Service],",
            f"    tns='{namespace}',",
            f"    in_protocol=Soap11(validator='lxml'),",
            f"    out_protocol=Soap11(),",
            f")",
            "",
            "wsgi_application = WsgiApplication(application)",
        ]

        return "\n".join(lines)

    def _app(self) -> str:
        cls = self.class_name
        return f"""from flask import Flask, request, Response
from service import wsgi_application
import io

flask_app = Flask(__name__)


@flask_app.route('/ws', methods=['GET', 'POST'])
@flask_app.route('/ws/', methods=['GET', 'POST'])
def soap_service():
    environ = request.environ.copy()
    responses = []

    def start_response(status, headers, exc_info=None):
        responses.append((status, headers))

    body = wsgi_application(environ, start_response)

    if responses:
        status_line = responses[0][0]
        status_code = int(status_line.split(' ', 1)[0])
        headers = dict(responses[0][1])
        content = b''.join(body)
        return Response(content, status=status_code, headers=headers)

    return Response(b''.join(body), status=200)


if __name__ == '__main__':
    flask_app.run(host='0.0.0.0', port=8000, debug=True)
"""

    def _readme(self) -> str:
        svc = self.service
        cls = self.class_name
        return f"""# {svc.service_name} — Spyne SOAP Service

## Description
{svc.description or svc.service_name + ' SOAP web service built with Python Spyne.'}

## Version
{svc.version}

## Requirements
- Python 3.9+
- Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Service

```bash
python app.py
```

The service will be available at:
- SOAP endpoint: http://localhost:8000/ws
- WSDL: http://localhost:8000/ws?wsdl

## Methods

{chr(10).join(f'- **{m.name}**: {m.description or "No description"}' for m in svc.methods)}

## Namespace
`{svc.namespace}`
"""
