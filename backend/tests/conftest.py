import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models import (
    ServiceDefinition,
    ServiceType,
    Method,
    Parameter,
    ModelDef,
    Field,
    ParameterLocation,
)
import pytest


@pytest.fixture
def minimal_service():
    """Service with no methods or models."""
    return ServiceDefinition(
        service_name="EmptyService",
        service_type=ServiceType.BOTH,
        namespace="http://example.com/empty",
        version="1.0",
    )


@pytest.fixture
def soap_service():
    """SOAP-only service with two methods and one model."""
    return ServiceDefinition(
        service_name="OrderService",
        service_type=ServiceType.SOAP,
        namespace="http://example.com/orders",
        version="1.0",
        methods=[
            Method(
                name="getOrder",
                parameters=[
                    Parameter(
                        name="orderId",
                        type="int",
                        required=True,
                        location=ParameterLocation.PATH,
                    )
                ],
                return_type="Order",
                http_method="GET",
                path="/orders/{orderId}",
            ),
            Method(
                name="createOrder",
                parameters=[
                    Parameter(
                        name="order",
                        type="Order",
                        required=True,
                        location=ParameterLocation.BODY,
                    )
                ],
                return_type="Order",
                http_method="POST",
                path="/orders",
            ),
        ],
        models=[
            ModelDef(
                name="Order",
                fields=[
                    Field(name="id", type="int"),
                    Field(name="product", type="string"),
                    Field(name="quantity", type="int"),
                    Field(name="active", type="boolean"),
                ],
            )
        ],
    )


@pytest.fixture
def rest_service():
    """REST-only service with four CRUD methods and one model."""
    return ServiceDefinition(
        service_name="UserService",
        service_type=ServiceType.REST,
        namespace="http://example.com/users",
        version="2.0",
        methods=[
            Method(
                name="getUser",
                parameters=[
                    Parameter(
                        name="userId",
                        type="int",
                        required=True,
                        location=ParameterLocation.PATH,
                    ),
                    Parameter(
                        name="verbose",
                        type="boolean",
                        required=False,
                        location=ParameterLocation.QUERY,
                    ),
                ],
                return_type="User",
                http_method="GET",
                path="/users/{userId}",
            ),
            Method(
                name="createUser",
                parameters=[
                    Parameter(
                        name="user",
                        type="User",
                        required=True,
                        location=ParameterLocation.BODY,
                    )
                ],
                return_type="User",
                http_method="POST",
                path="/users",
            ),
            Method(
                name="updateUser",
                parameters=[
                    Parameter(
                        name="userId",
                        type="int",
                        required=True,
                        location=ParameterLocation.PATH,
                    ),
                    Parameter(
                        name="user",
                        type="User",
                        required=True,
                        location=ParameterLocation.BODY,
                    ),
                ],
                return_type="User",
                http_method="PUT",
                path="/users/{userId}",
            ),
            Method(
                name="deleteUser",
                parameters=[
                    Parameter(
                        name="userId",
                        type="int",
                        required=True,
                        location=ParameterLocation.PATH,
                    )
                ],
                return_type="void",
                http_method="DELETE",
                path="/users/{userId}",
            ),
        ],
        models=[
            ModelDef(
                name="User",
                fields=[
                    Field(name="id", type="int"),
                    Field(name="name", type="string"),
                    Field(name="email", type="string", required=False),
                    Field(name="active", type="boolean"),
                ],
            )
        ],
    )


@pytest.fixture
def both_service(soap_service):
    """Service that is both SOAP and REST."""
    import copy

    svc = copy.deepcopy(soap_service)
    svc.service_type = ServiceType.BOTH
    svc.service_name = "BothService"
    return svc
