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


def _ruby_type(t: str) -> str:
    return RUBY_TYPE_MAP.get(t.lower(), t)


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
        return "Date.today"
    elif lower == "datetime":
        return "DateTime.now"
    else:
        return "nil"


def _rails_action_name(method_name: str) -> str:
    # Convert camelCase to snake_case
    import re
    s = re.sub(r'(?<!^)(?=[A-Z])', '_', method_name).lower()
    return s


def _http_verb_to_rails(http_method: str) -> str:
    return http_method.lower()


def _route_path_to_rails(path: str) -> str:
    # Convert {param} to :param for Rails
    import re
    return re.sub(r"\{(\w+)\}", r":\1", path)


class RubyRailsGenerator(BaseGenerator):
    def __init__(self, service: ServiceDefinition):
        super().__init__(service)

    def generate(self) -> Dict[str, str]:
        files: Dict[str, str] = {}
        files["Gemfile"] = self._gemfile()
        files["config/routes.rb"] = self._routes_rb()
        files[f"app/controllers/api/{self.pkg}_controller.rb"] = self._controller_rb()
        for model in self.service.models:
            model_filename = self._model_filename(model.name)
            files[f"app/models/{model_filename}.rb"] = self._model_rb(model)
        files["README.md"] = self._readme()
        return files

    def _model_filename(self, model_name: str) -> str:
        import re
        s = re.sub(r'(?<!^)(?=[A-Z])', '_', model_name).lower()
        return s

    def _gemfile(self) -> str:
        return f"""# frozen_string_literal: true

source "https://rubygems.org"

ruby "3.2.0"

gem "rails", "~> 7.1"
gem "puma", ">= 5.0"
gem "tzinfo-data", platforms: %i[ windows jruby ]

group :development, :test do
  gem "debug", platforms: %i[ mri windows ]
end
"""

    def _routes_rb(self) -> str:
        lines = [
            'Rails.application.routes.draw do',
            '  namespace :api do',
        ]

        for method in self.service.methods:
            action = _rails_action_name(method.name)
            verb = _http_verb_to_rails(method.http_method)
            route_path = _route_path_to_rails(method.path)
            # Strip leading slash for Rails routes
            route_path = route_path.lstrip('/')
            if not route_path:
                route_path = action
            lines.append(
                f'    {verb} "/{route_path}", to: "{self.pkg}#{action}"'
            )

        lines += [
            '  end',
            'end',
        ]
        return '\n'.join(lines) + '\n'

    def _controller_rb(self) -> str:
        class_name = f'{self.class_name}Controller'
        lines = [
            '# frozen_string_literal: true',
            '',
            'module Api',
            f'  class {class_name} < ApplicationController',
            '',
        ]

        for method in self.service.methods:
            action = _rails_action_name(method.name)
            lines.append(f'    # {method.description or method.name}')
            lines.append(f'    def {action}')

            # Read parameters
            for param in method.parameters:
                if param.location == ParameterLocation.PATH:
                    lines.append(f'      {param.name} = params[:{param.name}]')
                elif param.location == ParameterLocation.QUERY:
                    lines.append(f'      {param.name} = params[:{param.name}]')
                elif param.location == ParameterLocation.BODY:
                    lines.append(f'      {param.name} = request.body.read')
                elif param.location == ParameterLocation.HEADER:
                    header_key = param.name.upper().replace('-', '_')
                    lines.append(f'      {param.name} = request.headers["HTTP_{header_key}"]')

            # Suppress unused variable warnings (Ruby style)
            for param in method.parameters:
                lines.append(f'      _ = {param.name}')

            if method.return_type.lower() == 'void':
                lines.append(f'      render json: {{ message: "success", method: "{method.name}" }}')
            else:
                default_val = _ruby_default_value(method.return_type)
                lines.append(f'      result = {default_val}')
                lines.append(f'      render json: {{ result: result }}')

            lines += ['    end', '']

        lines += ['  end', 'end', '']
        return '\n'.join(lines)

    def _model_rb(self, model) -> str:
        lines = [
            '# frozen_string_literal: true',
            '',
            f'class {model.name}',
            f'  attr_accessor {", ".join(":" + f.name for f in model.fields)}',
            '',
            '  def initialize(attrs = {})',
        ]
        for field in model.fields:
            lines.append(f'    @{field.name} = attrs[:{field.name}]')
        lines += [
            '  end',
            '',
            '  def to_h',
            '    {',
        ]
        for i, field in enumerate(model.fields):
            comma = ',' if i < len(model.fields) - 1 else ''
            lines.append(f'      {field.name}: @{field.name}{comma}')
        lines += [
            '    }',
            '  end',
            'end',
            '',
        ]
        return '\n'.join(lines)

    def _readme(self) -> str:
        method_docs = []
        for m in self.service.methods:
            action = _rails_action_name(m.name)
            method_docs.append(
                f'- `{m.http_method} /api{m.path}` — `api/{self.pkg}#{action}`' +
                (f': {m.description}' if m.description else '')
            )
        routes_section = '\n'.join(method_docs) if method_docs else '- No routes defined.'

        model_names = ', '.join(m.name for m in self.service.models) if self.service.models else 'None'

        return f"""# {self.service.service_name}

{self.service.description or 'A REST API built with Ruby on Rails (API mode).'}

**Version:** {self.service.version}

## Requirements

- Ruby 3.2.0
- Bundler

## Getting Started

```bash
rails new {self.pkg} --api -T
bundle install
rails server
```

The server will start on port **3000**.

## Routes

{routes_section}

## Models

{model_names}

## Project Structure

```
.
├── Gemfile
├── config/
│   └── routes.rb
├── app/
│   ├── controllers/
│   │   └── api/
│   │       └── {self.pkg}_controller.rb
│   └── models/
```
"""
