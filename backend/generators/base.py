from abc import ABC, abstractmethod
from typing import Dict
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from models import ServiceDefinition


PRIMITIVE_TYPES = {"string", "int", "float", "boolean", "date", "datetime", "void"}


class BaseGenerator(ABC):
    def __init__(self, service: ServiceDefinition):
        self.service = service
        self.pkg = service.service_name.lower().replace(" ", "_").replace("-", "_")
        self.class_name = "".join(w.capitalize() for w in service.service_name.split())

    @abstractmethod
    def generate(self) -> Dict[str, str]:
        """Returns {file_path: content}"""
        pass

    def _is_primitive(self, t: str) -> bool:
        return t.lower() in PRIMITIVE_TYPES
