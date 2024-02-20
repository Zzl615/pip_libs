from typing import Optional

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse

__all__ = ['setup']


def get_rapi_html(
        *,
        openapi_url: str,
        title: str,
):
    html = f"""
    <!doctype html> <!-- Important: must specify -->
    <html>
    <head>
        <meta charset="utf-8"> <!-- Important: rapi-doc uses utf8 characters -->
        <script type="module" src="https://unpkg.com/rapidoc/dist/rapidoc-min.js"></script>
        <title>{title}</title>
    </head>
    <body>
    <rapi-doc
            spec-url="{openapi_url}"
            theme="dark"
            show-method-in-nav-bar="as-colored-block"
            update-route="true"
            show-header="false"
    ></rapi-doc>
    </body>
    </html>
    """
    return HTMLResponse(html)


def get_stoplight_html(
        *,
        openapi_url: str,
        title: str,
):
    html = f"""
    <!doctype html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
        <title>{title}</title>

        <script src="https://unpkg.com/@stoplight/elements/web-components.min.js"></script>
        <link rel="stylesheet" href="https://unpkg.com/@stoplight/elements/styles.min.css">
    </head>
    <body>

        <elements-api
            apiDescriptionUrl="{openapi_url}"
            router="hash"
        />

    </body>
    </html>
    """
    return HTMLResponse(html)


def setup_rapi_doc(
        fastapi_app: FastAPI,
        rapi_url: str,
):
    if not fastapi_app.openapi_url:
        return

    async def rapi_html(req: Request) -> HTMLResponse:
        root_path = req.scope.get("root_path", "").rstrip("/")
        openapi_url = root_path + fastapi_app.openapi_url
        return get_rapi_html(
            openapi_url=openapi_url,
            title=fastapi_app.title,
        )

    fastapi_app.add_route(rapi_url, rapi_html)


def setup_stoplight_doc(
        fastapi_app: FastAPI,
        stoplight_url: str,
) -> None:
    if not fastapi_app.openapi_url:
        return

    async def stoplight_html(req: Request) -> HTMLResponse:
        root_path = req.scope.get("root_path", "").rstrip("/")
        openapi_url = root_path + fastapi_app.openapi_url
        return get_stoplight_html(
            openapi_url=openapi_url,
            title=fastapi_app.title,
        )

    fastapi_app.add_route(stoplight_url, stoplight_html)


def get_docs_html(docs_ui: dict) -> HTMLResponse:
    html = """
    <!doctype html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
        <title>选择文档UI</title>
    </head>
     <body>
     <h1>选择文档UI</h1>

    """
    for k, v in docs_ui.items():
        html += f"""
        <a href="{v}">{k}</a> <br>
        """
    html += "</body>"
    return HTMLResponse(html)


def setup(
        *,
        fastapi_app: FastAPI,
        doc_ui_url: Optional[str] = '/docs-ui',
        stoplight_url: Optional[str] = '/stoplight',
        rapi_url: Optional[str] = '/rapi',
):
    if not fastapi_app.openapi_url:
        return
    docs = {}
    if stoplight_url:
        setup_stoplight_doc(fastapi_app, stoplight_url)
        docs['stoplight'] = stoplight_url
    if rapi_url:
        setup_rapi_doc(fastapi_app, rapi_url)
        docs['rapi'] = rapi_url
    if fastapi_app.docs_url:
        docs['swagger'] = fastapi_app.docs_url
    if fastapi_app.redoc_url:
        docs['redoc'] = fastapi_app.redoc_url

    if doc_ui_url:
        async def get_docs(req: Request) -> HTMLResponse:
            root_path = req.scope.get("root_path", "").rstrip("/")
            this_docs = {}
            for k, v in docs.items():
                this_docs[k] = root_path + v
            return get_docs_html(this_docs)

        fastapi_app.add_route(doc_ui_url, get_docs)
