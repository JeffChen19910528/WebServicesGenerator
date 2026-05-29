import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from models import ServiceDefinition
from generators.base import BaseGenerator

from generators.soap.java_spring import JavaSpringWSGenerator
from generators.soap.java_cxf import JavaCXFGenerator
from generators.soap.python_spyne import PythonSpyneGenerator
from generators.soap.nodejs_soap import NodeJSSoapGenerator
from generators.soap.csharp_wcf import CSharpWCFGenerator
from generators.soap.php_soap import PHPSoapGenerator
from generators.soap.go_soap import GoSoapGenerator

from generators.rest.java_spring_boot import JavaSpringBootGenerator
from generators.rest.python_fastapi import PythonFastAPIGenerator
from generators.rest.python_flask import PythonFlaskGenerator
from generators.rest.python_django import PythonDjangoGenerator
from generators.rest.nodejs_express import NodeJSExpressGenerator
from generators.rest.nodejs_nestjs import NodeJSNestJSGenerator
from generators.rest.nodejs_fastify import NodeJSFastifyGenerator
from generators.rest.csharp_aspnet import CSharpAspNetGenerator
from generators.rest.php_laravel import PHPLaravelGenerator
from generators.rest.php_slim import PHPSlimGenerator
from generators.rest.go_gin import GoGinGenerator
from generators.rest.go_echo import GoEchoGenerator
from generators.rest.ruby_rails import RubyRailsGenerator
from generators.rest.ruby_sinatra import RubySinatraGenerator

GENERATORS = {
    "soap-java-spring-ws": JavaSpringWSGenerator,
    "soap-java-cxf": JavaCXFGenerator,
    "soap-python-spyne": PythonSpyneGenerator,
    "soap-nodejs-soap": NodeJSSoapGenerator,
    "soap-csharp-wcf": CSharpWCFGenerator,
    "soap-php": PHPSoapGenerator,
    "soap-go": GoSoapGenerator,
    "rest-java-spring-boot": JavaSpringBootGenerator,
    "rest-python-fastapi": PythonFastAPIGenerator,
    "rest-python-flask": PythonFlaskGenerator,
    "rest-python-django": PythonDjangoGenerator,
    "rest-nodejs-express": NodeJSExpressGenerator,
    "rest-nodejs-nestjs": NodeJSNestJSGenerator,
    "rest-nodejs-fastify": NodeJSFastifyGenerator,
    "rest-csharp-aspnet": CSharpAspNetGenerator,
    "rest-php-laravel": PHPLaravelGenerator,
    "rest-php-slim": PHPSlimGenerator,
    "rest-go-gin": GoGinGenerator,
    "rest-go-echo": GoEchoGenerator,
    "rest-ruby-rails": RubyRailsGenerator,
    "rest-ruby-sinatra": RubySinatraGenerator,
}

def get_generator(framework: str, service: ServiceDefinition) -> BaseGenerator:
    cls = GENERATORS.get(framework)
    if not cls:
        raise ValueError(f"Unknown framework: {framework}")
    return cls(service)
