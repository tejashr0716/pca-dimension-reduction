import io

import pytest

from app import create_app

VALID_CSV = b"a,b,c\n1,3,7\n2,1,4\n3,6,9\n4,2,6\n5,5,8\n"


@pytest.fixture
def app():
    return create_app({"TESTING": True})


@pytest.fixture
def client(app):
    return app.test_client()


def upload(client, payload=VALID_CSV, components="2", filename="data.csv"):
    return client.post(
        "/api/analyze",
        data={"file": (io.BytesIO(payload), filename), "components": components},
        content_type="multipart/form-data",
    )
