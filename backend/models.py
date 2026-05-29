from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class ServiceType(str, Enum):
    SOAP = "SOAP"
    REST = "REST"
    BOTH = "BOTH"


class ParameterLocation(str, Enum):
    QUERY = "query"
    PATH = "path"
    BODY = "body"
    HEADER = "header"


class Parameter(BaseModel):
    name: str
    type: str  # string, int, float, boolean, date, datetime, or model name
    required: bool = True
    description: Optional[str] = None
    location: ParameterLocation = ParameterLocation.QUERY


class Method(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: List[Parameter] = []
    return_type: str = "void"
    http_method: str = "GET"
    path: str = "/"


class Field(BaseModel):
    name: str
    type: str
    required: bool = True
    description: Optional[str] = None


class ModelDef(BaseModel):
    name: str
    fields: List[Field] = []


class ServiceDefinition(BaseModel):
    service_name: str
    service_type: ServiceType
    namespace: str = "http://example.com/service"
    description: Optional[str] = None
    version: str = "1.0"
    methods: List[Method] = []
    models: List[ModelDef] = []


class GenerateRequest(BaseModel):
    service: ServiceDefinition
    framework: str


class GenerateTestsRequest(BaseModel):
    service: ServiceDefinition
    test_types: List[str]  # "soap-xml", "soapui", "postman"
