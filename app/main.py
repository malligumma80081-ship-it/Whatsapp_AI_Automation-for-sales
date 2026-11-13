from fastapi import FastAPI

from app.core.config import settings
from app.database.connection import ensure_database_ready

from app.api.routes import router as business_router
from app.api.customers import router as customer_router
from app.api.orders import router as order_router
from app.api.inventory import router as inventory_router
from app.api.products import router as product_router
from app.api.analytics import router as analytics_router
from app.whatsapp.webhook import router as whatsapp_router
from app.api.messages import router as messages_router
from app.api.conversations import (
    router as conversations_router
)
from app.api.ai import router as ai_router
from app.api.knowledge import (
    router as knowledge_router
)
from app.api.rag import router as rag_router
from app.api.llm_gateway import (
    router as llm_gateway_router
)
from app.api.tools import router as tools_router
from app.api.cache import router as cache_router
from app.api.evaluation import router as evaluation_router
from app.api.auth import router as auth_router


ensure_database_ready()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered Millet Milk Sales Management",
)


@app.get("/")
def root():

    return {
        "message": "Welcome to Millet Milk Sales AI",
        "status": "running",
    }


@app.get("/health")
def health_check():

    return {
        "status": "healthy",
    }


app.include_router(
    business_router,
    prefix=settings.API_PREFIX,
    tags=["Business"],
)

app.include_router(
    customer_router,
    prefix=f"{settings.API_PREFIX}/customers",
    tags=["Customers"],
)

app.include_router(
    order_router,
    prefix=f"{settings.API_PREFIX}/orders",
    tags=["Orders"],
)

app.include_router(
    inventory_router,
    prefix=f"{settings.API_PREFIX}/inventory",
    tags=["Inventory"],
)
app.include_router(
    product_router,
    prefix=f"{settings.API_PREFIX}/products",
    tags=["Products"],
)

app.include_router(
    analytics_router,
    prefix=f"{settings.API_PREFIX}/analytics",
    tags=["Analytics"],
)

app.include_router(
    whatsapp_router,
    prefix="/webhook/whatsapp",
    tags=["WhatsApp"],
)

app.include_router(
    messages_router,
    prefix="/api/v1/messages",
    tags=["Messages"]
)

app.include_router(
    conversations_router,
    prefix="/api/v1/conversations",
    tags=["Conversations"]
)

app.include_router(
    ai_router,
    prefix="/api/v1/ai",
    tags=["AI Assistant"]
)

app.include_router(
    knowledge_router,
    prefix="/api/v1/knowledge",
    tags=["Knowledge Base"]
)

app.include_router(
    rag_router,
    prefix="/api/v1/rag",
    tags=["RAG"]
)

app.include_router(
    llm_gateway_router,
    prefix="/api/v1/llm",
    tags=["LLM Gateway"]
)

app.include_router(
    tools_router,
    prefix="/api/v1",
)

app.include_router(
    cache_router,
    prefix="/api/v1",
)

app.include_router(
    evaluation_router,
    prefix="/api/v1",
)

app.include_router(
    auth_router,
    prefix="/api/v1",
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
    ],
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
    ],
    allow_headers=[
        "Authorization",
        "Content-Type",
    ],
)