from fastapi import FastAPI
from routers import auth, users

app = FastAPI(title="RAG Backend")

app.include_router(auth.router, prefix="/auth")
app.include_router(users.router, prefix="/users")
