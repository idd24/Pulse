from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, checkins, dashboard, screentime

app = FastAPI()

# Permissive CORS for dev (Expo web + LAN devices hit this from arbitrary origins).
# Tighten before shipping to production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(checkins.router)
app.include_router(screentime.router)
app.include_router(dashboard.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
