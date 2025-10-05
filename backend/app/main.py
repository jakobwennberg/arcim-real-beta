from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import tenants, webhooks, fivetran

app = FastAPI(title="Arcims API", version="1.0.0")

# CORS - allow Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(tenants.router, prefix="/api")
app.include_router(webhooks.router, prefix="/api")
app.include_router(fivetran.router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Arcims API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
