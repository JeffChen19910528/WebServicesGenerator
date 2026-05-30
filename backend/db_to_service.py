import re
from typing import Dict, List, Any
from models import (
    ServiceDefinition, ServiceType, Method, Parameter,
    ParameterLocation, ModelDef, Field
)


def to_pascal_case(name: str) -> str:
    name = name.split('.')[-1] if '.' in name else name
    return ''.join(w.capitalize() for w in re.split(r'[_\s]+', name))


def to_camel_case(name: str) -> str:
    p = to_pascal_case(name)
    return p[0].lower() + p[1:] if p else p


def find_pk(columns: List[Dict]) -> Dict:
    for col in columns:
        if col.get('is_primary_key'):
            return col
    for col in columns:
        if col['name'].lower() in ('id',):
            return col
    return columns[0] if columns else {"name": "id", "service_type": "integer"}


def build_service_from_schema(
    schema: Dict[str, List[Dict]],
    operations: Dict[str, List[str]],
    service_name: str,
    service_type: str,
    namespace: str = "http://example.com/service",
) -> ServiceDefinition:
    methods: List[Method] = []
    models: List[ModelDef] = []

    for full_table_name, columns in schema.items():
        display = full_table_name.split('.')[-1] if '.' in full_table_name else full_table_name
        model_name = to_pascal_case(display)
        ops = operations.get(full_table_name, ["getAll", "getById", "create", "update", "delete"])

        pk = find_pk(columns)
        pk_name = pk['name']
        pk_type = pk['service_type']
        path_base = f"/{display.lower()}"

        fields = [
            Field(
                name=col['name'],
                type=col['service_type'],
                required=not col['is_nullable'],
            )
            for col in columns
        ]
        models.append(ModelDef(name=model_name, fields=fields))

        if "getAll" in ops:
            methods.append(Method(
                name=f"getAll{model_name}",
                description=f"取得所有 {display} 資料",
                parameters=[],
                return_type=f"List[{model_name}]",
                http_method="GET",
                path=path_base,
            ))

        if "getById" in ops:
            methods.append(Method(
                name=f"get{model_name}ById",
                description=f"依 {pk_name} 取得單筆 {display}",
                parameters=[Parameter(
                    name=pk_name, type=pk_type,
                    required=True, location=ParameterLocation.PATH,
                )],
                return_type=model_name,
                http_method="GET",
                path=f"{path_base}/{{{pk_name}}}",
            ))

        if "create" in ops:
            methods.append(Method(
                name=f"create{model_name}",
                description=f"新增 {display} 資料",
                parameters=[Parameter(
                    name=to_camel_case(display), type=model_name,
                    required=True, location=ParameterLocation.BODY,
                )],
                return_type=model_name,
                http_method="POST",
                path=path_base,
            ))

        if "update" in ops:
            methods.append(Method(
                name=f"update{model_name}",
                description=f"更新 {display} 資料",
                parameters=[
                    Parameter(name=pk_name, type=pk_type,
                              required=True, location=ParameterLocation.PATH),
                    Parameter(name=to_camel_case(display), type=model_name,
                              required=True, location=ParameterLocation.BODY),
                ],
                return_type=model_name,
                http_method="PUT",
                path=f"{path_base}/{{{pk_name}}}",
            ))

        if "delete" in ops:
            methods.append(Method(
                name=f"delete{model_name}",
                description=f"刪除 {display} 資料",
                parameters=[Parameter(
                    name=pk_name, type=pk_type,
                    required=True, location=ParameterLocation.PATH,
                )],
                return_type="boolean",
                http_method="DELETE",
                path=f"{path_base}/{{{pk_name}}}",
            ))

    return ServiceDefinition(
        service_name=service_name,
        service_type=ServiceType(service_type),
        namespace=namespace,
        description="由資料庫自動產生的服務",
        version="1.0",
        methods=methods,
        models=models,
    )
