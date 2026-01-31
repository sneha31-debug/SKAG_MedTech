import uvicorn
from backend.api.main import app
from backend.core import settings


def main():
    uvicorn.run(
        "backend.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
