from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.image import router as image_router
from routes.video import router as video_router

app = FastAPI(title="YOLO Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(image_router)
app.include_router(video_router)


@app.get("/")
async def root():
    return {"message": "YOLO Detection API", "status": "running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
