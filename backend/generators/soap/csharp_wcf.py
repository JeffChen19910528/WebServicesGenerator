import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from models import ServiceDefinition
from generators.base import BaseGenerator, PRIMITIVE_TYPES
from typing import Dict


CS_TYPE_MAP = {
    "string": "string",
    "int": "int",
    "float": "double",
    "boolean": "bool",
    "date": "DateTime",
    "datetime": "DateTime",
    "void": "void",
}

CS_DEFAULT = {
    "string": '""',
    "int": "0",
    "float": "0.0",
    "boolean": "false",
    "date": "DateTime.Today",
    "datetime": "DateTime.Now",
}


def _cs_type(t: str) -> str:
    return CS_TYPE_MAP.get(t.lower(), t)


def _cs_default(t: str) -> str:
    return CS_DEFAULT.get(t.lower(), "null")


class CSharpWCFGenerator(BaseGenerator):
    def __init__(self, service: ServiceDefinition):
        super().__init__(service)

    def generate(self) -> Dict[str, str]:
        files = {}
        cls = self.class_name

        files[f"{cls}Service.csproj"] = self._csproj(cls)
        files["Program.cs"] = self._program(cls)
        files[f"I{cls}Service.cs"] = self._interface(cls)
        files[f"{cls}Service.cs"] = self._implementation(cls)

        for model in self.service.models:
            files[f"Models/{model.name}.cs"] = self._model_class(model)

        return files

    def _csproj(self, cls: str) -> str:
        return f"""<Project Sdk="Microsoft.NET.Sdk.Web">

  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <AssemblyName>{cls}Service</AssemblyName>
    <RootNamespace>{cls}Service</RootNamespace>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="CoreWCF.Http" Version="1.5.1" />
    <PackageReference Include="CoreWCF.Primitives" Version="1.5.1" />
  </ItemGroup>

</Project>
"""

    def _program(self, cls: str) -> str:
        return f"""using CoreWCF;
using CoreWCF.Configuration;
using CoreWCF.Description;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddServiceModelServices();
builder.Services.AddServiceModelMetadata();
builder.Services.AddSingleton<IServiceBehavior, UseRequestHeadersForMetadataAddressBehavior>();

var app = builder.Build();

app.UseServiceModel(serviceBuilder =>
{{
    serviceBuilder.AddService<{cls}Service.{cls}Service>(serviceOptions =>
    {{
        serviceOptions.DebugBehavior.IncludeExceptionDetailInFaults = true;
    }});

    serviceBuilder.AddServiceEndpoint<{cls}Service.{cls}Service, {cls}Service.I{cls}Service>(
        new BasicHttpBinding(),
        "/ws/{cls.lower()}");
}});

var serviceMetadataBehavior = app.Services.GetRequiredService<ServiceMetadataBehavior>();
serviceMetadataBehavior.HttpGetEnabled = true;

app.Run();
"""

    def _interface(self, cls: str) -> str:
        svc = self.service
        lines = [
            f"using CoreWCF;",
            f"using System.Runtime.Serialization;",
            f"using {cls}Service.Models;",
            "",
            f"namespace {cls}Service;",
            "",
            f'[ServiceContract(Namespace = "{svc.namespace}")]',
            f"public interface I{cls}Service",
            "{",
        ]
        for method in svc.methods:
            ret = _cs_type(method.return_type)
            params = ", ".join(f"{_cs_type(p.type)} {p.name}" for p in method.parameters)
            if method.description:
                lines.append(f"    // {method.description}")
            lines += [
                f"    [OperationContract]",
                f"    {ret} {method.name[0].upper() + method.name[1:]}({params});",
                "",
            ]
        lines.append("}")
        return "\n".join(lines)

    def _implementation(self, cls: str) -> str:
        svc = self.service
        lines = [
            f"using CoreWCF;",
            f"using {cls}Service.Models;",
            "",
            f"namespace {cls}Service;",
            "",
            f"public class {cls}Service : I{cls}Service",
            "{",
        ]
        for method in svc.methods:
            ret = _cs_type(method.return_type)
            params = ", ".join(f"{_cs_type(p.type)} {p.name}" for p in method.parameters)
            mname_cap = method.name[0].upper() + method.name[1:]
            lines += [
                f"    public {ret} {mname_cap}({params})",
                "    {",
            ]
            if ret != "void":
                default = _cs_default(method.return_type)
                lines.append(f"        return {default};")
            lines += [
                "    }",
                "",
            ]
        lines.append("}")
        return "\n".join(lines)

    def _model_class(self, model) -> str:
        cls = self.class_name
        lines = [
            "using System.Runtime.Serialization;",
            "",
            f"namespace {cls}Service.Models;",
            "",
            "[DataContract]",
            f"public class {model.name}",
            "{",
        ]
        for field in model.fields:
            cs_t = _cs_type(field.type)
            nullable = "" if field.required else "?"
            lines += [
                "    [DataMember]",
                f"    public {cs_t}{nullable} {field.name[0].upper() + field.name[1:]} {{ get; set; }}",
                "",
            ]
        lines.append("}")
        return "\n".join(lines)
