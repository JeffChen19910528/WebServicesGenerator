import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from models import ServiceDefinition
from generators.base import BaseGenerator
from typing import Dict


TS_TYPE_MAP = {
    "string": "string",
    "int": "number",
    "float": "number",
    "boolean": "boolean",
    "date": "string",
    "datetime": "string",
}

TS_DEFAULT_MAP = {
    "string": "''",
    "int": "0",
    "float": "0.0",
    "boolean": "false",
    "date": "new Date().toISOString().split('T')[0]",
    "datetime": "new Date().toISOString()",
}

HTTP_TO_NEST_DECORATOR = {
    "GET": "Get",
    "POST": "Post",
    "PUT": "Put",
    "DELETE": "Delete",
    "PATCH": "Patch",
}

LOCATION_TO_DECORATOR = {
    "path": "Param",
    "query": "Query",
    "body": "Body",
    "header": "Headers",
}


def _ts_type(t: str) -> str:
    return TS_TYPE_MAP.get(t.lower(), t)


def _ts_default(t: str) -> str:
    return TS_DEFAULT_MAP.get(t.lower(), "null")


def _nest_path(path: str) -> str:
    """NestJS uses :param style already (same as Express)."""
    return path


class NodeJSNestJSGenerator(BaseGenerator):
    def __init__(self, service: ServiceDefinition):
        super().__init__(service)

    def generate(self) -> Dict[str, str]:
        files = {}
        files["package.json"] = self._gen_package_json()
        files["tsconfig.json"] = self._gen_tsconfig()
        files["src/main.ts"] = self._gen_main()
        files["src/app.module.ts"] = self._gen_app_module()
        files[f"src/{self.pkg}/{self.pkg}.module.ts"] = self._gen_module()
        files[f"src/{self.pkg}/{self.pkg}.controller.ts"] = self._gen_controller()
        files[f"src/{self.pkg}/{self.pkg}.service.ts"] = self._gen_service()
        for model in self.service.models:
            files[f"src/{self.pkg}/dto/{model.name}.dto.ts"] = self._gen_dto(model)
        files["README.md"] = self._gen_readme()
        return files

    def _gen_package_json(self) -> str:
        return f"""\
{{
  "name": "{self.pkg}",
  "version": "{self.service.version}",
  "description": "{self.service.description or self.service.service_name + ' NestJS REST API'}",
  "scripts": {{
    "build": "nest build",
    "start": "nest start",
    "start:dev": "nest start --watch",
    "start:prod": "node dist/main"
  }},
  "dependencies": {{
    "@nestjs/common": "^10.0.0",
    "@nestjs/core": "^10.0.0",
    "@nestjs/platform-express": "^10.0.0",
    "class-transformer": "^0.5.1",
    "class-validator": "^0.14.0",
    "reflect-metadata": "^0.1.13",
    "rxjs": "^7.8.1"
  }},
  "devDependencies": {{
    "@nestjs/cli": "^10.0.0",
    "@nestjs/schematics": "^10.0.0",
    "@nestjs/testing": "^10.0.0",
    "@types/express": "^4.17.17",
    "@types/node": "^20.3.1",
    "ts-node": "^10.9.1",
    "typescript": "^5.1.3"
  }}
}}
"""

    def _gen_tsconfig(self) -> str:
        return """\
{
  "compilerOptions": {
    "module": "commonjs",
    "declaration": true,
    "removeComments": true,
    "emitDecoratorMetadata": true,
    "experimentalDecorators": true,
    "allowSyntheticDefaultImports": true,
    "target": "ES2017",
    "sourceMap": true,
    "outDir": "./dist",
    "baseUrl": "./",
    "incremental": true,
    "skipLibCheck": true,
    "strictNullChecks": false,
    "noImplicitAny": false,
    "strictBindCallApply": false,
    "forceConsistentCasingInFileNames": false,
    "noFallthroughCasesInSwitch": false
  }
}
"""

    def _gen_main(self) -> str:
        return f"""\
import {{ NestFactory }} from '@nestjs/core';
import {{ AppModule }} from './app.module';
import {{ ValidationPipe }} from '@nestjs/common';

async function bootstrap() {{
  const app = await NestFactory.create(AppModule);
  app.useGlobalPipes(new ValidationPipe());
  app.enableCors();
  app.setGlobalPrefix('api');
  await app.listen(3000);
  console.log(`{self.service.service_name} API running on http://localhost:3000`);
}}
bootstrap();
"""

    def _gen_app_module(self) -> str:
        module_class = f"{self.class_name}Module"
        return f"""\
import {{ Module }} from '@nestjs/common';
import {{ {module_class} }} from './{self.pkg}/{self.pkg}.module';

@Module({{
  imports: [{module_class}],
}})
export class AppModule {{}}
"""

    def _gen_module(self) -> str:
        controller_class = f"{self.class_name}Controller"
        service_class = f"{self.class_name}Service"
        module_class = f"{self.class_name}Module"
        return f"""\
import {{ Module }} from '@nestjs/common';
import {{ {controller_class} }} from './{self.pkg}.controller';
import {{ {service_class} }} from './{self.pkg}.service';

@Module({{
  controllers: [{controller_class}],
  providers: [{service_class}],
}})
export class {module_class} {{}}
"""

    def _gen_controller(self) -> str:
        controller_class = f"{self.class_name}Controller"
        service_class = f"{self.class_name}Service"

        # Collect all necessary NestJS decorators
        http_decorators = set()
        param_decorators = set()
        for method in self.service.methods:
            http_decorators.add(HTTP_TO_NEST_DECORATOR.get(method.http_method.upper(), "Get"))
            for p in method.parameters:
                dec = LOCATION_TO_DECORATOR.get(p.location.value)
                if dec:
                    param_decorators.add(dec)

        all_decorators = sorted(http_decorators | param_decorators)
        decorator_imports = ", ".join(["Controller"] + all_decorators)

        lines = [
            f"import {{ {decorator_imports} }} from '@nestjs/common';",
            f"import {{ {service_class} }} from './{self.pkg}.service';",
        ]

        # Import DTOs
        for model in self.service.models:
            lines.append(f"import {{ {model.name}Dto }} from './dto/{model.name}.dto';")

        lines.append("")
        lines.append(f"@Controller('{self.pkg.replace('_', '-')}')")
        lines.append(f"export class {controller_class} {{")
        lines.append(f"  constructor(private readonly {self.pkg}Service: {service_class}) {{}}")
        lines.append("")

        for method in self.service.methods:
            verb_dec = HTTP_TO_NEST_DECORATOR.get(method.http_method.upper(), "Get")
            # Convert {param} path style
            nest_path = method.path
            if method.description:
                lines.append(f"  // {method.description}")

            lines.append(f"  @{verb_dec}('{nest_path}')")

            # Build parameter decorators
            param_parts = []
            for p in method.parameters:
                dec = LOCATION_TO_DECORATOR.get(p.location.value, "Query")
                ts_t = _ts_type(p.type)
                if p.location.value == "path":
                    param_parts.append(f"@{dec}('{p.name}') {p.name}: {ts_t}")
                elif p.location.value == "body":
                    # Use DTO if type matches a model
                    if not self._is_primitive(p.type):
                        param_parts.append(f"@{dec}() {p.name}: {p.type}Dto")
                    else:
                        param_parts.append(f"@{dec}('{p.name}') {p.name}: {ts_t}")
                elif p.location.value == "header":
                    param_parts.append(f"@{dec}() headers: Record<string, string>")
                else:
                    param_parts.append(f"@{dec}('{p.name}') {p.name}: {ts_t}")

            params_str = ", ".join(param_parts)
            camel = method.name[0].lower() + method.name[1:]
            svc_args = ", ".join(p.name if p.location.value != "header" else "headers"
                                  for p in method.parameters)

            # Return type
            rt = method.return_type
            if rt == "void":
                ts_rt = "void"
            elif self._is_primitive(rt):
                ts_rt = _ts_type(rt)
            else:
                ts_rt = rt

            lines.append(f"  {camel}({params_str}): Promise<{ts_rt}> {{")
            lines.append(f"    return this.{self.pkg}Service.{camel}({svc_args});")
            lines.append("  }")
            lines.append("")

        lines.append("}")
        return "\n".join(lines) + "\n"

    def _gen_service(self) -> str:
        service_class = f"{self.class_name}Service"
        lines = [
            "import { Injectable } from '@nestjs/common';",
            "",
            "@Injectable()",
            f"export class {service_class} {{",
        ]

        for method in self.service.methods:
            camel = method.name[0].lower() + method.name[1:]
            # Build param list
            params = []
            for p in method.parameters:
                ts_t = _ts_type(p.type)
                if p.location.value == "header":
                    params.append("headers: Record<string, string>")
                elif p.location.value == "body" and not self._is_primitive(p.type):
                    params.append(f"{p.name}: {p.type}Dto")
                else:
                    opt = "" if p.required else "?"
                    params.append(f"{p.name}{opt}: {ts_t}")

            params_str = ", ".join(params)

            rt = method.return_type
            if rt == "void":
                ts_rt = "void"
                return_val = ""
            elif self._is_primitive(rt):
                ts_rt = _ts_type(rt)
                return_val = f"return {_ts_default(rt)};"
            else:
                model_match = next((m for m in self.service.models if m.name == rt), None)
                ts_rt = rt
                if model_match:
                    fields_str = ", ".join(
                        f"{f.name}: {_ts_default(f.type)}" for f in model_match.fields
                    )
                    return_val = f"return {{ {fields_str} }} as any;"
                else:
                    return_val = "return {} as any;"

            if method.description:
                lines.append(f"  // {method.description}")
            lines.append(f"  async {camel}({params_str}): Promise<{ts_rt}> {{")
            if return_val:
                lines.append(f"    {return_val}")
            lines.append("  }")
            lines.append("")

        lines.append("}")
        return "\n".join(lines) + "\n"

    def _gen_dto(self, model) -> str:
        lines = [
            "import { IsString, IsNumber, IsBoolean, IsOptional, IsDate } from 'class-validator';",
            "import { Type } from 'class-transformer';",
            "",
            f"export class {model.name}Dto {{",
        ]
        for f in model.fields:
            t_lower = f.type.lower()
            if not f.required:
                lines.append("  @IsOptional()")
            if t_lower == "string":
                lines.append("  @IsString()")
                lines.append(f"  {f.name}: string;")
            elif t_lower in ("int", "float"):
                lines.append("  @IsNumber()")
                lines.append(f"  {f.name}: number;")
            elif t_lower == "boolean":
                lines.append("  @IsBoolean()")
                lines.append(f"  {f.name}: boolean;")
            elif t_lower in ("date", "datetime"):
                lines.append("  @IsDate()")
                lines.append("  @Type(() => Date)")
                lines.append(f"  {f.name}: Date;")
            else:
                lines.append(f"  {f.name}: {f.type};")
            lines.append("")
        lines.append("}")
        return "\n".join(lines) + "\n"

    def _gen_readme(self) -> str:
        return f"""\
# {self.service.service_name} — NestJS REST API

{self.service.description or ''}

## Requirements

- Node.js >= 18
- npm

## Setup

```bash
npm install
```

## Running

```bash
# Development (watch mode)
npm run start:dev

# Production build
npm run build
npm run start:prod
```

The server starts on **http://localhost:3000**

## API Base URL

`http://localhost:3000/api/{self.pkg.replace('_', '-')}`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
{"".join(f"| {m.http_method} | {m.path} | {m.description or m.name} |" + chr(10) for m in self.service.methods)}\

## DTOs / Models

{"".join(f"- `{model.name}Dto`: " + ", ".join(f.name for f in model.fields) + chr(10) for model in self.service.models)}\
"""
