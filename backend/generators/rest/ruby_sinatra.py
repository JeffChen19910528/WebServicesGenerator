import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from models import ServiceDefinition, ParameterLocation
from generators.base import BaseGenerator
from typing import Dict


RUBY_TYPE_MAP = {
    "string": "String",
    "int": "Integer",
    "float": "Float",
    "boolean": "Boolean",
    "date": "Date",
    "datetime": "DateTime",
    "void": "nil",
}


def _ruby_default_value(t: str) -> str:
    lower = t.lower()
    if lower == "string":
        return '"ok"'
    elif lower == "int":
        return "0"
    elif lower == "float":
        return "0.0"
    elif lower == "boolean":
        return "true"
    elif lower == "date":
        return "Date.today.to_s"
    elif lower == "datetime":
        return "Time.now.utc.iso8601"
    else:
        return "nil"


def _sinatra_http_method(http_method: str) -> str:
    return http_method.lower()


def _sinatra_route_path(path: str) -> str:
    # Convert {param} to :param for Sinatra
    import re
    return re.sub(r"\{(\w+)\}", r":\1", path)


def _model_filename(model_name: str) -> str:
    import re
    s = re.sub(r'(?<!^)(?=[A-Z])', '_', model_name).lower()
    return s


class RubySinatraGenerator(BaseGenerator):
    def __init__(self, service: ServiceDefinition):
        super().__init__(service)

    def generate(self) -> Dict[str, str]:
        files: Dict[str, str] = {}
        files["Gemfile"] = self._gemfile()
        files["app.rb"] = self._app_rb()
        for model in self.service.models:
            fname = _model_filename(model.name)
            files[f"models/{fname}.rb"] = self._model_rb(model)
        files["config.ru"] = self._config_ru()
        files["README.md"] = self._readme()
        return files

    def _gemfile(self) -> str:
        return f"""# frozen_string_literal: true

source "https://rubygems.org"

gem "sinatra", "~> 3.1"
gem "sinatra-contrib", "~> 3.1"
gem "json", "~> 2.6"
gem "puma", "~> 6.0"
"""

    def _app_rb(self) -> str:
        model_requires = []
        for model in self.service.models:
            fname = _model_filename(model.name)
            model_requires.append(f'require_relative "models/{fname}"')

        lines = [
            '# frozen_string_literal: true',
            '',
            'require "sinatra"',
            'require "sinatra/json"',
            'require "json"',
        ]
        lines.extend(model_requires)
        lines += [
            '',
            f'# {self.service.service_name}',
            f'# {self.service.description or "A REST API built with Sinatra."}',
            '',
            'configure do',
            '  set :port, 4567',
            '  set :bind, "0.0.0.0"',
            '  set :show_exceptions, false',
            'end',
            '',
            '# Health check',
            'get "/health" do',
            f'  json status: "ok", service: "{self.service.service_name}", version: "{self.service.version}"',
            'end',
            '',
        ]

        for method in self.service.methods:
            verb = _sinatra_http_method(method.http_method)
            route_path = _sinatra_route_path(method.path)

            lines.append(f'# {method.description or method.name}')
            lines.append(f'{verb} "{route_path}" do')
            lines.append('  content_type :json')
            lines.append('')

            # Parse parameters
            for param in method.parameters:
                if param.location == ParameterLocation.PATH:
                    lines.append(f'  {param.name} = params[:{param.name}]')
                elif param.location == ParameterLocation.QUERY:
                    lines.append(f'  {param.name} = params["{param.name}"]')
                elif param.location == ParameterLocation.BODY:
                    lines.append(f'  request.body.rewind')
                    lines.append(f'  body_data = JSON.parse(request.body.read, symbolize_names: true) rescue {{}}')
                    lines.append(f'  {param.name} = body_data[:{param.name}]')
                elif param.location == ParameterLocation.HEADER:
                    header_key = 'HTTP_' + param.name.upper().replace('-', '_')
                    lines.append(f'  {param.name} = request.env["{header_key}"]')

            # Suppress unused vars
            for param in method.parameters:
                lines.append(f'  _ = {param.name}')

            lines.append('')
            if method.return_type.lower() == 'void':
                lines.append(
                    f'  json message: "success", method: "{method.name}"'
                )
            else:
                default_val = _ruby_default_value(method.return_type)
                lines.append(f'  result = {default_val}')
                lines.append(f'  json result: result')

            lines += ['end', '']

        # Global error handlers
        lines += [
            'error 400 do',
            '  json error: "Bad Request", message: env["sinatra.error"]&.message',
            'end',
            '',
            'error 404 do',
            '  json error: "Not Found"',
            'end',
            '',
            'error 500 do',
            '  json error: "Internal Server Error", message: env["sinatra.error"]&.message',
            'end',
        ]

        return '\n'.join(lines) + '\n'

    def _model_rb(self, model) -> str:
        if model.fields:
            struct_members = ', '.join(':' + f.name for f in model.fields)
            lines = [
                '# frozen_string_literal: true',
                '',
                f'{model.name} = Struct.new({struct_members}, keyword_init: true) do',
                '  def to_h',
                '    super.transform_keys(&:to_s)',
                '  end',
                '',
                '  def to_json(*args)',
                '    to_h.to_json(*args)',
                '  end',
                'end',
                '',
            ]
        else:
            lines = [
                '# frozen_string_literal: true',
                '',
                f'class {model.name}',
                '  # No fields defined',
                '',
                '  def initialize(attrs = {})',
                '  end',
                '',
                '  def to_h',
                '    {}',
                '  end',
                '',
                '  def to_json(*args)',
                '    to_h.to_json(*args)',
                '  end',
                'end',
                '',
            ]
        return '\n'.join(lines)

    def _config_ru(self) -> str:
        return f"""# frozen_string_literal: true

require_relative "app"

run Sinatra::Application
"""

    def _readme(self) -> str:
        method_docs = []
        for m in self.service.methods:
            method_docs.append(
                f'- `{m.http_method} {m.path}` — {m.name}' +
                (f': {m.description}' if m.description else '')
            )
        routes_section = '\n'.join(method_docs) if method_docs else '- No routes defined.'

        model_files = []
        for model in self.service.models:
            fname = _model_filename(model.name)
            model_files.append(f'│   └── {fname}.rb')
        model_tree = '\n'.join(model_files) if model_files else '│   └── (none)'

        return f"""# {self.service.service_name}

{self.service.description or 'A REST API built with Ruby and Sinatra.'}

**Version:** {self.service.version}

## Requirements

- Ruby 3.x
- Bundler

## Getting Started

```bash
bundle install
bundle exec ruby app.rb
```

Or using Rack:

```bash
bundle exec rackup config.ru
```

The server will start on port **4567**.

## Routes

{routes_section}

## Project Structure

```
.
├── Gemfile
├── app.rb
├── config.ru
└── models/
{model_tree}
```
"""
