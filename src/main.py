import time
from typing import Literal

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from starlette.responses import FileResponse

from src.auth.auth import (
    auth_backend,
    fastapi_users,
    google_oauth_client,
    vk_oauth_client,
)
from src.auth.router import auth_router, users_router
from src.auth.schemas import UserCreateSchema, UserReadSchema
from src.sports.router import sports_router

from .s3_service import s3_bucket_service_factory
from .schemas import HealthcheckResponse

app = FastAPI(
    title="Atlecta API",
    swagger_ui_parameters={"displayRequestDuration": True},
    docs_url=None, redoc_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

favicon_url = "favicon-96x96.png"


@app.get("/healthcheck", response_model=HealthcheckResponse)
async def healthcheck():
    """
    Health check endpoint.

    Returns the current status of the API service. 
    Useful for monitoring and ensuring the server is running.

    Returns:
        dict: A simple dictionary with a "status" key indicating service health.
    """
    return HealthcheckResponse(status="healthy")


@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse(favicon_url)


@app.get("/docs", include_in_schema=False)
def overridden_swagger():
    return get_swagger_ui_html(openapi_url="/openapi.json", title=app.title + " - Swagger UI", swagger_favicon_url="favicon.ico", swagger_ui_parameters={"displayRequestDuration": True})


@app.get("/redoc", include_in_schema=False)
def overridden_redoc():
    return get_redoc_html(openapi_url="/openapi.json", title=app.title + " - ReDoc", redoc_favicon_url="favicon.ico")


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        s3_service = s3_bucket_service_factory()

        content = await file.read()
        await s3_service.upload_file_object(
            prefix="",
            source_file_name=file.filename,
            content=content,
            content_type=file.content_type
        )
        file_url = f"{s3_service.endpoint}/{s3_service.bucket_name}/{file.filename}"
        return {"url": file_url, "message": "Upload successful"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"File upload failed: {str(e)}")


@app.post("/upload_multiple")
async def upload_files(files: list[UploadFile]):
    try:
        s3_service = s3_bucket_service_factory()
        file_urls = ''

        for file in files:
            content = await file.read()
            await s3_service.upload_file_object(
                prefix="",
                source_file_name=file.filename,
                content=content,
                content_type=file.content_type
            )
            file_urls += f"{s3_service.endpoint}/{s3_service.bucket_name}/{file.filename}"

        return {"url": file_urls, "message": "Uploaded successful"}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"File upload failed: {str(e)}")


@app.delete("/delete/{file_name}/")
async def delete_file(file_name: str):
    try:
        s3_service = s3_bucket_service_factory()
        await s3_service.delete_file_object(
            prefix="test",
            source_file_name=file_name
        )
        return {"message": "Deleted!"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"File deletetion failed: {str(e)}")


app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserReadSchema, UserCreateSchema),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserReadSchema),
    prefix="/auth/verification",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_oauth_router(
        # WARNING: Change SECRET to something strong
        google_oauth_client, auth_backend, "SECRET",
        associate_by_email=True),
    prefix="/auth/google",
    tags=["auth"]
)
app.include_router(
    fastapi_users.get_oauth_router(
        # WARNING: Change SECRET to something strong
        vk_oauth_client, auth_backend, "SECRET", redirect_url="http://localhost/auth/vk/callback"),
    prefix="/auth/vk",
    tags=["auth"]
)
app.include_router(
    auth_router
)
app.include_router(
    users_router
)
app.include_router(
    sports_router
)

# Middleware


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Prints endpoint response time
    """
    start_time = time.time()
    response = await call_next(request)
    print("Time took to process the request and return response is {} sec".format(
        time.time() - start_time))
    return response
