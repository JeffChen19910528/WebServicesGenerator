import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from models import ServiceDefinition, ParameterLocation
from generators.base import BaseGenerator
from typing import Dict


class JavaSpringBootGenerator(BaseGenerator):
    """Generates a Spring Boot 3.x Maven REST API project."""

    # ------------------------------------------------------------------ #
    #  Java type mapping
    # ------------------------------------------------------------------ #
    JAVA_TYPES: Dict[str, str] = {
        "string":   "String",
        "int":      "Integer",
        "float":    "Double",
        "boolean":  "Boolean",
        "date":     "LocalDate",
        "datetime": "LocalDateTime",
        "void":     "void",
    }

    # Imports needed per type
    TYPE_IMPORTS: Dict[str, str] = {
        "date":     "import java.time.LocalDate;",
        "datetime": "import java.time.LocalDateTime;",
    }

    def _java_type(self, t: str) -> str:
        return self.JAVA_TYPES.get(t.lower(), t)  # fall back to the model name

    def _collect_type_imports(self, types) -> list:
        imports = []
        for t in types:
            imp = self.TYPE_IMPORTS.get(t.lower())
            if imp and imp not in imports:
                imports.append(imp)
        return imports

    # ------------------------------------------------------------------ #
    #  generate()
    # ------------------------------------------------------------------ #
    def generate(self) -> Dict[str, str]:
        files: Dict[str, str] = {}
        pkg = self.pkg
        cls = self.class_name

        files["pom.xml"] = self._pom_xml()
        files[f"src/main/java/com/{pkg}/Application.java"] = self._application_java()
        files[f"src/main/resources/application.properties"] = self._application_properties()

        for model in self.service.models:
            path = f"src/main/java/com/{pkg}/model/{model.name}.java"
            files[path] = self._model_java(model)

        files[f"src/main/java/com/{pkg}/controller/{cls}Controller.java"] = self._controller_java()
        files[f"src/main/java/com/{pkg}/service/{cls}Service.java"] = self._service_java()

        return files

    # ------------------------------------------------------------------ #
    #  pom.xml
    # ------------------------------------------------------------------ #
    def _pom_xml(self) -> str:
        pkg = self.pkg
        cls = self.class_name
        ver = self.service.version
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
        <relativePath/>
    </parent>

    <groupId>com.{pkg}</groupId>
    <artifactId>{pkg}</artifactId>
    <version>{ver}</version>
    <name>{cls}</name>
    <description>{self.service.description or cls + " REST API"}</description>

    <properties>
        <java.version>17</java.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
        </dependency>
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
            <optional>true</optional>
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
                <configuration>
                    <excludes>
                        <exclude>
                            <groupId>org.projectlombok</groupId>
                            <artifactId>lombok</artifactId>
                        </exclude>
                    </excludes>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
"""

    # ------------------------------------------------------------------ #
    #  Application.java
    # ------------------------------------------------------------------ #
    def _application_java(self) -> str:
        pkg = self.pkg
        cls = self.class_name
        return f"""package com.{pkg};

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class {cls}Application {{

    public static void main(String[] args) {{
        SpringApplication.run({cls}Application.class, args);
    }}
}}
"""

    # ------------------------------------------------------------------ #
    #  application.properties
    # ------------------------------------------------------------------ #
    def _application_properties(self) -> str:
        cls = self.class_name
        return f"""server.port=8080
spring.application.name={cls}
"""

    # ------------------------------------------------------------------ #
    #  Model Java (Lombok)
    # ------------------------------------------------------------------ #
    def _model_java(self, model) -> str:
        pkg = self.pkg
        all_types = [f.type for f in model.fields]
        type_imports = self._collect_type_imports(all_types)
        imports_block = "\n".join(type_imports)
        if imports_block:
            imports_block = "\n" + imports_block

        fields_block = ""
        for field in model.fields:
            java_type = self._java_type(field.type)
            fields_block += f"    private {java_type} {field.name};\n"

        return f"""package com.{pkg}.model;

import lombok.Data;
import lombok.AllArgsConstructor;
import lombok.NoArgsConstructor;{imports_block}

@Data
@AllArgsConstructor
@NoArgsConstructor
public class {model.name} {{
{fields_block}}}
"""

    # ------------------------------------------------------------------ #
    #  Controller
    # ------------------------------------------------------------------ #
    def _controller_java(self) -> str:
        pkg = self.pkg
        cls = self.class_name
        svc_var = cls[0].lower() + cls[1:] + "Service"

        # Collect imports
        mapping_imports = set()
        param_imports = set()
        type_imports = set()

        for method in self.service.methods:
            http = method.http_method.upper()
            mapping_imports.add(f"import org.springframework.web.bind.annotation.{http.capitalize()}Mapping;")
            for p in method.parameters:
                if p.location == ParameterLocation.PATH:
                    param_imports.add("import org.springframework.web.bind.annotation.PathVariable;")
                elif p.location == ParameterLocation.QUERY:
                    param_imports.add("import org.springframework.web.bind.annotation.RequestParam;")
                elif p.location == ParameterLocation.BODY:
                    param_imports.add("import org.springframework.web.bind.annotation.RequestBody;")
                elif p.location == ParameterLocation.HEADER:
                    param_imports.add("import org.springframework.web.bind.annotation.RequestHeader;")
                ti = self.TYPE_IMPORTS.get(p.type.lower())
                if ti:
                    type_imports.add(ti)
            rt = method.return_type.lower()
            ti = self.TYPE_IMPORTS.get(rt)
            if ti:
                type_imports.add(ti)

        # Model imports
        model_names = {m.name for m in self.service.models}
        used_models = set()
        for method in self.service.methods:
            for p in method.parameters:
                if not self._is_primitive(p.type) and p.type in model_names:
                    used_models.add(p.type)
            if not self._is_primitive(method.return_type) and method.return_type in model_names:
                used_models.add(method.return_type)

        model_imports = "\n".join(
            f"import com.{pkg}.model.{m};" for m in sorted(used_models)
        )

        all_imports = sorted(mapping_imports | param_imports | type_imports)
        imports_block = "\n".join(all_imports)
        if model_imports:
            imports_block += "\n" + model_imports

        # Build methods
        methods_block = ""
        for method in self.service.methods:
            http = method.http_method.upper()
            mapping_ann = f'@{http.capitalize()}Mapping("{method.path}")'
            ret_type = self._java_type(method.return_type)
            if ret_type == "void":
                ret_type = "ResponseEntity<Void>"
                ret_stmt = f"return {svc_var}.{method.name}({{args}});\n        return ResponseEntity.ok().build();"
            else:
                ret_stmt = f"return ResponseEntity.ok({svc_var}.{method.name}({{args}}));"

            params = []
            call_args = []
            for p in method.parameters:
                jtype = self._java_type(p.type)
                if p.location == ParameterLocation.PATH:
                    ann = "@PathVariable"
                elif p.location == ParameterLocation.QUERY:
                    req = str(p.required).lower()
                    ann = f'@RequestParam(required = {req})'
                elif p.location == ParameterLocation.BODY:
                    ann = "@RequestBody"
                elif p.location == ParameterLocation.HEADER:
                    ann = f'@RequestHeader("{p.name}")'
                else:
                    ann = "@RequestParam"
                params.append(f"{ann} {jtype} {p.name}")
                call_args.append(p.name)

            args_str = ", ".join(call_args)
            ret_full = ret_stmt.replace("{args}", args_str)

            # Handle void service call differently
            if method.return_type.lower() == "void":
                ret_type = "ResponseEntity<Void>"
                ret_full = f"{svc_var}.{method.name}({args_str});\n        return ResponseEntity.noContent().build();"
            else:
                ret_type = f"ResponseEntity<{self._java_type(method.return_type)}>"
                ret_full = f"return ResponseEntity.ok({svc_var}.{method.name}({args_str}));"

            desc = f"// {method.description}" if method.description else ""
            param_str = ", ".join(params)
            methods_block += f"""
    {mapping_ann}
    public {ret_type} {method.name}({param_str}) {{
        {desc}
        {ret_full}
    }}
"""

        return f"""package com.{pkg}.controller;

import com.{pkg}.service.{cls}Service;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
{imports_block}

@RestController
@RequestMapping("/api/v{self.service.version.replace('.', '_')}")
public class {cls}Controller {{

    private final {cls}Service {svc_var};

    public {cls}Controller({cls}Service {svc_var}) {{
        this.{svc_var} = {svc_var};
    }}
{methods_block}}}
"""

    # ------------------------------------------------------------------ #
    #  Service
    # ------------------------------------------------------------------ #
    def _service_java(self) -> str:
        pkg = self.pkg
        cls = self.class_name

        type_imports = set()
        model_names = {m.name for m in self.service.models}
        used_models = set()

        for method in self.service.methods:
            for p in method.parameters:
                ti = self.TYPE_IMPORTS.get(p.type.lower())
                if ti:
                    type_imports.add(ti)
                if not self._is_primitive(p.type) and p.type in model_names:
                    used_models.add(p.type)
            rt = method.return_type.lower()
            ti = self.TYPE_IMPORTS.get(rt)
            if ti:
                type_imports.add(ti)
            if not self._is_primitive(method.return_type) and method.return_type in model_names:
                used_models.add(method.return_type)

        model_imports = "\n".join(
            f"import com.{pkg}.model.{m};" for m in sorted(used_models)
        )
        imports_block = "\n".join(sorted(type_imports))
        if model_imports:
            imports_block = (imports_block + "\n" + model_imports).strip()

        methods_block = ""
        for method in self.service.methods:
            params = []
            for p in method.parameters:
                params.append(f"{self._java_type(p.type)} {p.name}")
            param_str = ", ".join(params)
            ret_java = self._java_type(method.return_type)

            if ret_java == "void":
                body = "// stub implementation"
            elif ret_java in ("String",):
                body = 'return "";'
            elif ret_java in ("Integer",):
                body = "return 0;"
            elif ret_java in ("Double",):
                body = "return 0.0;"
            elif ret_java in ("Boolean",):
                body = "return false;"
            elif ret_java in ("LocalDate",):
                body = "return LocalDate.now();"
            elif ret_java in ("LocalDateTime",):
                body = "return LocalDateTime.now();"
            else:
                body = "return null;"

            desc = f"// {method.description}" if method.description else ""
            methods_block += f"""
    public {ret_java} {method.name}({param_str}) {{
        {desc}
        {body}
    }}
"""

        return f"""package com.{pkg}.service;

import org.springframework.stereotype.Service;
import java.time.LocalDate;
import java.time.LocalDateTime;
{imports_block}

@Service
public class {cls}Service {{
{methods_block}}}
"""
