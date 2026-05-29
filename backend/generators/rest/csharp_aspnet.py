import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from models import ServiceDefinition
from generators.base import BaseGenerator
from typing import Dict


CS_TYPE_MAP = {
    "string": "string",
    "int": "int",
    "float": "double",
    "boolean": "bool",
    "date": "DateTime",
    "datetime": "DateTime",
}

CS_DEFAULT_MAP = {
    "string": '"default"',
    "int": "0",
    "float": "0.0",
    "boolean": "false",
    "date": "DateTime.Today",
    "datetime": "DateTime.UtcNow",
}

HTTP_TO_CSHARP_ATTR = {
    "GET": "HttpGet",
    "POST": "HttpPost",
    "PUT": "HttpPut",
    "DELETE": "HttpDelete",
    "PATCH": "HttpPatch",
}

LOCATION_TO_ATTR = {
    "path": "FromRoute",
    "query": "FromQuery",
    "body": "FromBody",
    "header": "FromHeader",
}


def _cs_type(t: str) -> str:
    return CS_TYPE_MAP.get(t.lower(), t)


def _cs_default(t: str) -> str:
    return CS_DEFAULT_MAP.get(t.lower(), "null")


def _cs_nullable(t: str, required: bool) -> str:
    """Return nullable suffix for optional value types."""
    if not required and t.lower() in ("int", "float", "boolean", "date", "datetime"):
        return "?"
    return ""


class CSharpAspNetGenerator(BaseGenerator):
    def __init__(self, service: ServiceDefinition):
        super().__init__(service)

    def generate(self) -> Dict[str, str]:
        files = {}
        files[f"{self.class_name}Api.csproj"] = self._gen_csproj()
        files["Program.cs"] = self._gen_program()
        files[f"Controllers/{self.class_name}Controller.cs"] = self._gen_controller()
        for model in self.service.models:
            files[f"Models/{model.name}.cs"] = self._gen_model(model)
        files["appsettings.json"] = self._gen_appsettings()
        files["README.md"] = self._gen_readme()
        return files

    def _gen_csproj(self) -> str:
        return f"""\
<Project Sdk="Microsoft.NET.Sdk.Web">

  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <RootNamespace>{self.class_name}Api</RootNamespace>
    <AssemblyName>{self.class_name}Api</AssemblyName>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Microsoft.AspNetCore.OpenApi" Version="8.0.0" />
    <PackageReference Include="Swashbuckle.AspNetCore" Version="6.5.0" />
  </ItemGroup>

</Project>
"""

    def _gen_program(self) -> str:
        return f"""\
using {self.class_name}Api.Controllers;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{{
    c.SwaggerDoc("v{self.service.version}", new() {{
        Title = "{self.service.service_name} API",
        Version = "v{self.service.version}",
        Description = "{self.service.description or self.service.service_name + ' REST API'}"
    }});
}});

builder.Services.AddCors(options =>
{{
    options.AddDefaultPolicy(policy =>
    {{
        policy.AllowAnyOrigin()
              .AllowAnyMethod()
              .AllowAnyHeader();
    }});
}});

var app = builder.Build();

if (app.Environment.IsDevelopment())
{{
    app.UseSwagger();
    app.UseSwaggerUI(c => c.SwaggerEndpoint("/swagger/v{self.service.version}/swagger.json", "{self.service.service_name} v{self.service.version}"));
}}

app.UseCors();
app.UseHttpsRedirection();
app.UseAuthorization();
app.MapControllers();

app.Run();
"""

    def _gen_controller(self) -> str:
        # Collect model namespaces used
        model_names = {m.name for m in self.service.models}

        lines = [
            "using Microsoft.AspNetCore.Mvc;",
            f"using {self.class_name}Api.Models;",
            "",
            f"namespace {self.class_name}Api.Controllers;",
            "",
            "[ApiController]",
            '[Route("api/[controller]")]',
            f"public class {self.class_name}Controller : ControllerBase",
            "{",
        ]

        for method in self.service.methods:
            http_attr = HTTP_TO_CSHARP_ATTR.get(method.http_method.upper(), "HttpGet")

            # Build route — only include if path is not just "/"
            route_path = method.path
            if route_path and route_path != "/":
                # Remove leading slash for attribute route
                route_path_clean = route_path.lstrip("/")
                http_line = f'    [{http_attr}("{route_path_clean}")]'
            else:
                http_line = f"    [{http_attr}]"

            # Return type
            rt = method.return_type
            if rt == "void":
                cs_rt = "IActionResult"
            elif self._is_primitive(rt):
                cs_rt = f"ActionResult<{_cs_type(rt)}>"
            else:
                cs_rt = f"ActionResult<{rt}>"

            # Build params
            param_parts = []
            for p in method.parameters:
                loc_attr = LOCATION_TO_ATTR.get(p.location.value, "FromQuery")
                cs_t = _cs_type(p.type)
                nullable = _cs_nullable(p.type, p.required)
                param_parts.append(f"[{loc_attr}] {cs_t}{nullable} {p.name}")

            params_str = ", ".join(param_parts)
            method_name = method.name[0].upper() + method.name[1:]

            if method.description:
                lines.append(f"    /// <summary>{method.description}</summary>")
            lines.append(f"    [ProducesResponseType(StatusCodes.Status200OK)]")
            lines.append(http_line)
            lines.append(f"    public {cs_rt} {method_name}({params_str})")
            lines.append("    {")

            # Build return value
            if rt == "void":
                lines.append('        return Ok(new { success = true });')
            elif self._is_primitive(rt):
                lines.append(f"        var result = {_cs_default(rt)};")
                lines.append("        return Ok(result);")
            else:
                model_match = next((m for m in self.service.models if m.name == rt), None)
                if model_match:
                    lines.append(f"        var result = new {rt}")
                    lines.append("        {")
                    for f in model_match.fields:
                        lines.append(f"            {f.name[0].upper() + f.name[1:]} = {_cs_default(f.type)},")
                    lines.append("        };")
                    lines.append("        return Ok(result);")
                else:
                    lines.append(f"        var result = new {rt}();")
                    lines.append("        return Ok(result);")

            lines.append("    }")
            lines.append("")

        lines.append("}")
        return "\n".join(lines) + "\n"

    def _gen_model(self, model) -> str:
        lines = [
            f"namespace {self.class_name}Api.Models;",
            "",
            f"public class {model.name}",
            "{",
        ]
        for f in model.fields:
            cs_t = _cs_type(f.type)
            nullable = _cs_nullable(f.type, f.required)
            prop_name = f.name[0].upper() + f.name[1:]
            default = _cs_default(f.type)
            lines.append(f"    public {cs_t}{nullable} {prop_name} {{ get; set; }} = {default};")
        lines.append("}")
        return "\n".join(lines) + "\n"

    def _gen_appsettings(self) -> str:
        return """\
{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning"
    }
  },
  "AllowedHosts": "*"
}
"""

    def _gen_readme(self) -> str:
        return f"""\
# {self.service.service_name} — ASP.NET Core Web API

{self.service.description or ''}

## Requirements

- .NET 8 SDK

## Setup & Run

```bash
dotnet restore
dotnet run
```

The API starts on **https://localhost:5001** (or http://localhost:5000).

## Swagger UI

Open **https://localhost:5001/swagger** in your browser to explore and test the API.

## Endpoints

Base: `api/{self.class_name}`

| Method | Path | Description |
|--------|------|-------------|
{"".join(f"| {m.http_method} | {m.path} | {m.description or m.name} |" + chr(10) for m in self.service.methods)}\

## Models

{"".join(f"- `{model.name}`: " + ", ".join(f.name for f in model.fields) + chr(10) for model in self.service.models)}\

## Publishing

```bash
dotnet publish -c Release -o ./publish
```
"""
