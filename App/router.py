from fastapi import FastAPI, APIRouter
from App.api.agent_schedule import agent_schedule_router

app = FastAPI()

api_router = APIRouter(prefix="/api/v1")
@app.get("/")   
async def root():
    return {"message": "Welcome to the API"}

# Include agent schedule routes
api_router.include_router(agent_schedule_router)
app.include_router(api_router)
# For debugging - print all registered routes
for route in app.routes:
    print(f"Route: {route.path}, Methods: {route.methods}")
