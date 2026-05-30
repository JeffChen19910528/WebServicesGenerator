from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import zipfile
import io
from typing import Optional, List, Dict
from pydantic import BaseModel

from models import GenerateRequest, GenerateTestsRequest
from generators import get_generator
from test_generators.soap_xml import generate_soap_xml
from test_generators.soapui_project import generate_soapui_project
from test_generators.postman_collection import generate_postman_collection

app = FastAPI(title="Web Services Generator API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/frameworks")
def get_frameworks():
    return {
        "soap": [
            {"id": "soap-java-spring-ws", "label": "Java (Spring-WS)"},
            {"id": "soap-java-cxf", "label": "Java (Apache CXF)"},
            {"id": "soap-python-spyne", "label": "Python (spyne)"},
            {"id": "soap-nodejs-soap", "label": "Node.js (soap)"},
            {"id": "soap-csharp-wcf", "label": "C# (CoreWCF)"},
            {"id": "soap-php", "label": "PHP (SoapServer)"},
            {"id": "soap-go", "label": "Go (gowsdl)"},
        ],
        "rest": [
            {"id": "rest-java-spring-boot", "label": "Java (Spring Boot)"},
            {"id": "rest-python-fastapi", "label": "Python (FastAPI)"},
            {"id": "rest-python-flask", "label": "Python (Flask)"},
            {"id": "rest-python-django", "label": "Python (Django REST)"},
            {"id": "rest-nodejs-express", "label": "Node.js (Express)"},
            {"id": "rest-nodejs-nestjs", "label": "Node.js (NestJS)"},
            {"id": "rest-nodejs-fastify", "label": "Node.js (Fastify)"},
            {"id": "rest-csharp-aspnet", "label": "C# (ASP.NET Core)"},
            {"id": "rest-php-laravel", "label": "PHP (Laravel)"},
            {"id": "rest-php-slim", "label": "PHP (Slim)"},
            {"id": "rest-go-gin", "label": "Go (Gin)"},
            {"id": "rest-go-echo", "label": "Go (Echo)"},
            {"id": "rest-ruby-rails", "label": "Ruby (Rails API)"},
            {"id": "rest-ruby-sinatra", "label": "Ruby (Sinatra)"},
        ],
    }


@app.post("/api/generate")
def generate_project(request: GenerateRequest):
    try:
        generator = get_generator(request.framework, request.service)
        files = generator.generate()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path, content in files.items():
            zf.writestr(file_path, content)
    zip_buffer.seek(0)

    filename = f"{request.service.service_name}_{request.framework}.zip"
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


class DBConnectRequest(BaseModel):
    server: str
    port: Optional[int] = None
    database: str
    username: Optional[str] = None
    password: Optional[str] = None
    auth_type: str = "sql"


class DBSchemaRequest(DBConnectRequest):
    tables: List[str]


class DBGenerateServiceRequest(DBConnectRequest):
    tables: List[str]
    operations: Dict[str, List[str]]
    service_name: str
    service_type: str = "REST"
    namespace: str = "http://example.com/service"


def _get_db_conn(req: DBConnectRequest):
    from db_connector import get_connection
    try:
        return get_connection(req.server, req.port, req.database,
                              req.username, req.password, req.auth_type)
    except ImportError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/database/connect")
def database_connect(request: DBConnectRequest):
    conn = _get_db_conn(request)
    try:
        from db_connector import get_tables
        tables = get_tables(conn)
        return {"tables": tables}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.post("/api/database/schema")
def database_schema(request: DBSchemaRequest):
    conn = _get_db_conn(request)
    try:
        from db_connector import get_columns
        schema = {table: get_columns(conn, table) for table in request.tables}
        return {"schema": schema}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.post("/api/database/generate-service")
def database_generate_service(request: DBGenerateServiceRequest):
    conn = _get_db_conn(request)
    try:
        from db_connector import get_columns
        from db_to_service import build_service_from_schema
        schema = {table: get_columns(conn, table) for table in request.tables}
        service = build_service_from_schema(
            schema=schema,
            operations=request.operations,
            service_name=request.service_name,
            service_type=request.service_type,
            namespace=request.namespace,
        )
        return service.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.post("/api/generate-tests")
def generate_tests(request: GenerateTestsRequest):
    files = {}

    if "soap-xml" in request.test_types:
        files.update(generate_soap_xml(request.service))
    if "soapui" in request.test_types:
        files.update(generate_soapui_project(request.service))
    if "postman" in request.test_types:
        files.update(generate_postman_collection(request.service))

    if not files:
        raise HTTPException(status_code=400, detail="No test types selected")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path, content in files.items():
            zf.writestr(file_path, content)
    zip_buffer.seek(0)

    filename = f"{request.service.service_name}_tests.zip"
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
