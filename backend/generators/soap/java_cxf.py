import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from models import ServiceDefinition
from generators.base import BaseGenerator, PRIMITIVE_TYPES
from typing import Dict


def _java_type(t: str) -> str:
    mapping = {
        "string": "String",
        "int": "Integer",
        "float": "Float",
        "boolean": "Boolean",
        "date": "java.time.LocalDate",
        "datetime": "java.time.LocalDateTime",
        "void": "void",
    }
    return mapping.get(t.lower(), t)


def _default_value(t: str) -> str:
    mapping = {
        "string": '""',
        "int": "0",
        "float": "0.0f",
        "boolean": "false",
        "date": "java.time.LocalDate.now()",
        "datetime": "java.time.LocalDateTime.now()",
    }
    lower = t.lower()
    if lower in mapping:
        return mapping[lower]
    return "null"


class JavaCXFGenerator(BaseGenerator):
    def __init__(self, service: ServiceDefinition):
        super().__init__(service)

    def generate(self) -> Dict[str, str]:
        files = {}
        pkg = self.pkg
        cls = self.class_name

        files["pom.xml"] = self._pom_xml(pkg)
        files[f"src/main/java/com/{pkg}/Application.java"] = self._application(pkg)
        files[f"src/main/java/com/{pkg}/{cls}Service.java"] = self._service_interface(pkg, cls)
        files[f"src/main/java/com/{pkg}/{cls}ServiceImpl.java"] = self._service_impl(pkg, cls)
        files[f"src/main/java/com/{pkg}/config/CxfConfig.java"] = self._cxf_config(pkg, cls)

        for model in self.service.models:
            files[f"src/main/java/com/{pkg}/model/{model.name}.java"] = self._model_class(pkg, model)

        return files

    def _pom_xml(self, pkg: str) -> str:
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
             https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
        <relativePath/>
    </parent>
    <groupId>com.{pkg}</groupId>
    <artifactId>{pkg}</artifactId>
    <version>{self.service.version}</version>
    <packaging>jar</packaging>
    <name>{self.service.service_name}</name>
    <description>{self.service.description or self.service.service_name + ' CXF SOAP Service'}</description>

    <properties>
        <java.version>17</java.version>
        <cxf.version>4.0.3</cxf.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.apache.cxf</groupId>
            <artifactId>cxf-spring-boot-starter-jaxws</artifactId>
            <version>${{cxf.version}}</version>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
"""

    def _application(self, pkg: str) -> str:
        return f"""package com.{pkg};

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class Application {{

    public static void main(String[] args) {{
        SpringApplication.run(Application.class, args);
    }}
}}
"""

    def _service_interface(self, pkg: str, cls: str) -> str:
        lines = [
            f"package com.{pkg};",
            "",
            "import javax.jws.WebMethod;",
            "import javax.jws.WebParam;",
            "import javax.jws.WebService;",
            "",
            f'@WebService(name = "{cls}Service", targetNamespace = "{self.service.namespace}")',
            f"public interface {cls}Service {{",
            "",
        ]
        for method in self.service.methods:
            ret = _java_type(method.return_type)
            params = ", ".join(
                f'@WebParam(name = "{p.name}") {_java_type(p.type)} {p.name}'
                for p in method.parameters
            )
            desc = f'    // {method.description}' if method.description else ""
            if desc:
                lines.append(desc)
            lines += [
                f"    @WebMethod",
                f"    {ret} {method.name}({params});",
                "",
            ]
        lines.append("}")
        return "\n".join(lines)

    def _service_impl(self, pkg: str, cls: str) -> str:
        lines = [
            f"package com.{pkg};",
            "",
            "import javax.jws.WebService;",
            "import org.springframework.stereotype.Service;",
            "",
            f'@Service',
            f'@WebService(endpointInterface = "com.{pkg}.{cls}Service",',
            f'            serviceName = "{cls}Service",',
            f'            targetNamespace = "{self.service.namespace}")',
            f"public class {cls}ServiceImpl implements {cls}Service {{",
            "",
        ]
        for method in self.service.methods:
            ret = _java_type(method.return_type)
            params = ", ".join(
                f"{_java_type(p.type)} {p.name}"
                for p in method.parameters
            )
            lines += [
                f"    @Override",
                f"    public {ret} {method.name}({params}) {{",
            ]
            if ret != "void":
                lines.append(f"        return {_default_value(method.return_type)};")
            lines += [
                f"    }}",
                "",
            ]
        lines.append("}")
        return "\n".join(lines)

    def _cxf_config(self, pkg: str, cls: str) -> str:
        return f"""package com.{pkg}.config;

import com.{pkg}.{cls}Service;
import com.{pkg}.{cls}ServiceImpl;
import org.apache.cxf.Bus;
import org.apache.cxf.jaxws.EndpointImpl;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import javax.xml.ws.Endpoint;

@Configuration
public class CxfConfig {{

    private final Bus bus;

    public CxfConfig(Bus bus) {{
        this.bus = bus;
    }}

    @Bean
    public Endpoint endpoint() {{
        EndpointImpl endpoint = new EndpointImpl(bus, new {cls}ServiceImpl());
        endpoint.publish("/{cls.lower()}");
        return endpoint;
    }}
}}
"""

    def _model_class(self, pkg: str, model) -> str:
        lines = [
            f"package com.{pkg}.model;",
            "",
            "import javax.xml.bind.annotation.XmlAccessType;",
            "import javax.xml.bind.annotation.XmlAccessorType;",
            "import javax.xml.bind.annotation.XmlRootElement;",
            "",
            "@XmlRootElement",
            "@XmlAccessorType(XmlAccessType.FIELD)",
            f"public class {model.name} {{",
            "",
        ]
        for field in model.fields:
            jt = _java_type(field.type)
            lines.append(f"    private {jt} {field.name};")
        lines.append("")
        for field in model.fields:
            jt = _java_type(field.type)
            fname_cap = field.name[0].upper() + field.name[1:]
            lines += [
                f"    public {jt} get{fname_cap}() {{ return {field.name}; }}",
                f"    public void set{fname_cap}({jt} {field.name}) {{ this.{field.name} = {field.name}; }}",
            ]
        lines += ["", "}"]
        return "\n".join(lines)
