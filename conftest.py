import pytest

def pytest_addoption(parser):
    parser.addoption("--yaml", default="machine.yaml",
        help="machine yaml file")


@pytest.fixture(scope="session", autouse=True)
def machine_yaml(request):
    if not request.config.getoption('--yaml'):
        yield "machine.yaml"
    else:
        yield request.config.getoption('--yaml')
