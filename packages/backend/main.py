from fastapi import FastAPI

from packages.backend.api.routers import auth, courses, users

app = FastAPI()

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(courses.router, prefix="/api/courses", tags=["courses"])
app.include_router(users.router, prefix="/api/users", tags=["users"])


@app.get("/")
async def root():
    return {"message": "Hello World"}
