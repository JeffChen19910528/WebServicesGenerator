import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from models import ServiceDefinition
from generators.base import BaseGenerator, PRIMITIVE_TYPES
from typing import Dict


XSD_TYPE_MAP = {
    "string": "xs:string",
    "int": "xs:int",
    "float": "xs:float",
    "boolean": "xs:boolean",
    "date": "xs:date",
    "datetime": "xs:dateTime",
    "void": None,
}


def to_xsd_type(t: str) -> str:
    lower = t.lower()
    if lower in XSD_TYPE_MAP:
        return XSD_TYPE_MAP[lower]
    return f"tns:{t}"


class JavaSpringWSGenerator(BaseGenerator):
    def __init__(self, service: ServiceDefinition):
        super().__init__(service)

    def generate(self) -> Dict[str, str]:
        files = {}
        pkg = self.pkg
        cls = self.class_name
        namespace = self.service.namespace

        files["pom.xml"] = self._pom_xml(pkg)
        files[f"src/main/java/com/{pkg}/Application.java"] = self._application(pkg, cls)
        files[f"src/main/java/com/{pkg}/WebServiceConfig.java"] = self._ws_config(pkg, cls, namespace)
        files[f"src/main/java/com/{pkg}/endpoint/{cls}Endpoint.java"] = self._endpoint(pkg, cls, namespace)
        files[f"src/main/resources/{cls}.xsd"] = self._xsd(cls, namespace)
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
    <description>{self.service.description or self.service.service_name + ' SOAP Web Service'}</description>

    <properties>
        <java.version>17</java.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web-services</artifactId>
        </dependency>
        <dependency>
            <groupId>wsdl4j</groupId>
            <artifactId>wsdl4j</artifactId>
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

    def _application(self, pkg: str, cls: str) -> str:
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

    def _ws_config(self, pkg: str, cls: str, namespace: str) -> str:
        return f"""package com.{pkg};

import org.springframework.boot.web.servlet.ServletRegistrationBean;
import org.springframework.context.ApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.io.ClassPathResource;
import org.springframework.ws.config.annotation.EnableWs;
import org.springframework.ws.config.annotation.WsConfigurerAdapter;
import org.springframework.ws.transport.http.MessageDispatcherServlet;
import org.springframework.ws.wsdl.wsdl11.DefaultWsdl11Definition;
import org.springframework.xml.xsd.SimpleXsdSchema;
import org.springframework.xml.xsd.XsdSchema;

@EnableWs
@Configuration
public class WebServiceConfig extends WsConfigurerAdapter {{

    @Bean
    public ServletRegistrationBean<MessageDispatcherServlet> messageDispatcherServlet(
            ApplicationContext applicationContext) {{
        MessageDispatcherServlet servlet = new MessageDispatcherServlet();
        servlet.setApplicationContext(applicationContext);
        servlet.setTransformWsdlLocations(true);
        return new ServletRegistrationBean<>(servlet, "/ws/*");
    }}

    @Bean(name = "{cls.lower()}")
    public DefaultWsdl11Definition defaultWsdl11Definition(XsdSchema schema) {{
        DefaultWsdl11Definition wsdl = new DefaultWsdl11Definition();
        wsdl.setPortTypeName("{cls}Port");
        wsdl.setLocationUri("/ws");
        wsdl.setTargetNamespace("{namespace}");
        wsdl.setSchema(schema);
        return wsdl;
    }}

    @Bean
    public XsdSchema schema() {{
        return new SimpleXsdSchema(new ClassPathResource("{cls}.xsd"));
    }}
}}
"""

    def _endpoint(self, pkg: str, cls: str, namespace: str) -> str:
        lines = [
            f"package com.{pkg}.endpoint;",
            "",
            "import org.springframework.ws.server.endpoint.annotation.Endpoint;",
            "import org.springframework.ws.server.endpoint.annotation.PayloadRoot;",
            "import org.springframework.ws.server.endpoint.annotation.RequestPayload;",
            "import org.springframework.ws.server.endpoint.annotation.ResponsePayload;",
            "import javax.xml.bind.annotation.*;",
            "",
            f"@Endpoint",
            f"public class {cls}Endpoint {{",
            f'    private static final String NAMESPACE_URI = "{namespace}";',
            "",
        ]

        for method in self.service.methods:
            mname = method.name
            mname_cap = mname[0].upper() + mname[1:]
            req_class = f"{mname_cap}Request"
            resp_class = f"{mname_cap}Response"

            lines += [
                f"    @PayloadRoot(namespace = NAMESPACE_URI, localPart = \"{req_class}\")",
                f"    @ResponsePayload",
                f"    public {resp_class} {mname}(@RequestPayload {req_class} request) {{",
                f"        {resp_class} response = new {resp_class}();",
            ]

            if method.return_type.lower() != "void":
                rt = method.return_type
                if rt.lower() == "string":
                    lines.append(f'        response.setResult("");')
                elif rt.lower() in ("int",):
                    lines.append(f'        response.setResult(0);')
                elif rt.lower() in ("float",):
                    lines.append(f'        response.setResult(0.0f);')
                elif rt.lower() == "boolean":
                    lines.append(f'        response.setResult(false);')
                else:
                    lines.append(f'        response.setResult(null);')

            lines += [
                f"        return response;",
                f"    }}",
                "",
            ]

            # Inner request/response classes
            lines += [
                f"    @XmlRootElement(name = \"{req_class}\", namespace = NAMESPACE_URI)",
                f"    @XmlAccessorType(XmlAccessType.FIELD)",
                f"    public static class {req_class} {{",
            ]
            for param in method.parameters:
                java_type = _java_type(param.type)
                lines.append(f"        private {java_type} {param.name};")
            for param in method.parameters:
                java_type = _java_type(param.type)
                pname_cap = param.name[0].upper() + param.name[1:]
                lines += [
                    f"        public {java_type} get{pname_cap}() {{ return {param.name}; }}",
                    f"        public void set{pname_cap}({java_type} {param.name}) {{ this.{param.name} = {param.name}; }}",
                ]
            lines += ["    }", ""]

            lines += [
                f"    @XmlRootElement(name = \"{resp_class}\", namespace = NAMESPACE_URI)",
                f"    @XmlAccessorType(XmlAccessType.FIELD)",
                f"    public static class {resp_class} {{",
            ]
            if method.return_type.lower() != "void":
                java_type = _java_type(method.return_type)
                lines.append(f"        private {java_type} result;")
                lines += [
                    f"        public {java_type} getResult() {{ return result; }}",
                    f"        public void setResult({java_type} result) {{ this.result = result; }}",
                ]
            lines += ["    }", ""]

        lines.append("}")
        return "\n".join(lines)

    def _xsd(self, cls: str, namespace: str) -> str:
        lines = [
            f'<?xml version="1.0" encoding="UTF-8"?>',
            f'<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"',
            f'           xmlns:tns="{namespace}"',
            f'           targetNamespace="{namespace}"',
            f'           elementFormDefault="qualified">',
            "",
        ]

        # Model complex types
        for model in self.service.models:
            lines += [
                f'    <xs:complexType name="{model.name}">',
                f'        <xs:sequence>',
            ]
            for field in model.fields:
                xsd_t = to_xsd_type(field.type)
                min_occ = "1" if field.required else "0"
                nillable = "" if field.required else ' nillable="true"'
                lines.append(
                    f'            <xs:element name="{field.name}" type="{xsd_t}" minOccurs="{min_occ}" maxOccurs="1"{nillable}/>'
                )
            lines += [
                f'        </xs:sequence>',
                f'    </xs:complexType>',
                "",
            ]

        # Request/response elements per method
        for method in self.service.methods:
            mname_cap = method.name[0].upper() + method.name[1:]
            req = f"{mname_cap}Request"
            resp = f"{mname_cap}Response"

            lines += [
                f'    <xs:element name="{req}">',
                f'        <xs:complexType>',
                f'            <xs:sequence>',
            ]
            for param in method.parameters:
                xsd_t = to_xsd_type(param.type)
                min_occ = "1" if param.required else "0"
                lines.append(
                    f'                <xs:element name="{param.name}" type="{xsd_t}" minOccurs="{min_occ}" maxOccurs="1"/>'
                )
            lines += [
                f'            </xs:sequence>',
                f'        </xs:complexType>',
                f'    </xs:element>',
                "",
                f'    <xs:element name="{resp}">',
                f'        <xs:complexType>',
                f'            <xs:sequence>',
            ]
            if method.return_type.lower() != "void":
                xsd_t = to_xsd_type(method.return_type)
                lines.append(
                    f'                <xs:element name="result" type="{xsd_t}" minOccurs="0" maxOccurs="1"/>'
                )
            lines += [
                f'            </xs:sequence>',
                f'        </xs:complexType>',
                f'    </xs:element>',
                "",
            ]

        lines.append("</xs:schema>")
        return "\n".join(lines)


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
