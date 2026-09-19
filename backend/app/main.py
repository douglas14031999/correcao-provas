import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Ensure root backend dir is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from dotenv import load_dotenv
    # Load .env from project root or backend dir
    env_file = os.path.join(PROJECT_ROOT, ".env")
    if not os.path.exists(env_file):
        env_file = os.path.join(BASE_DIR, ".env")
    load_dotenv(env_file)
except Exception:
    pass

from app.api.exams import router as exams_router, submissions_router
from app.api.grade import router as grade_router
from app.api.schools import router as schools_router
from app.api.reports import router as reports_router
from app.api.settings import router as settings_router
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.backup import router as backup_router
from app.services.database import init_db

app = FastAPI(
    title="OMR Provas & Simulados API",
    description="Sistema Open-Source de Geração e Correção de Gabaritos via Câmera Mobile",
    version="1.0.0"
)

# Enable CORS for mobile browsers and PWA
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

# Initialize DB and directories
init_db()
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
os.makedirs(os.path.join(STORAGE_DIR, "overlays"), exist_ok=True)
os.makedirs(os.path.join(STORAGE_DIR, "scans"), exist_ok=True)
os.makedirs(os.path.join(STORAGE_DIR, "sheets"), exist_ok=True)

# Mount storage directory
app.mount("/storage", StaticFiles(directory=STORAGE_DIR), name="storage")

# Include API Routers
app.include_router(exams_router)
app.include_router(submissions_router)
app.include_router(grade_router)
app.include_router(schools_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(backup_router, prefix="/api")

# Mount frontend files if available
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
if os.path.exists(FRONTEND_DIR):
    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    @app.get("/manifest.json")
    async def serve_manifest():
        manifest_path = os.path.join(FRONTEND_DIR, "manifest.json")
        if os.path.exists(manifest_path):
            return FileResponse(manifest_path, media_type="application/manifest+json")
        raise HTTPException(status_code=404, detail="Manifest não encontrado")

    @app.get("/sw.js")
    async def serve_sw():
        sw_path = os.path.join(FRONTEND_DIR, "sw.js")
        if os.path.exists(sw_path):
            return FileResponse(
                sw_path,
                media_type="application/javascript",
                headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"}
            )
        raise HTTPException(status_code=404, detail="Service Worker não encontrado")

    @app.get("/pwa-icon-192.png")
    async def serve_pwa_icon_192():
        icon_path = os.path.join(FRONTEND_DIR, "pwa-icon-192.png")
        if os.path.exists(icon_path):
            return FileResponse(icon_path, media_type="image/png")
        raise HTTPException(status_code=404, detail="Ícone não encontrado")

    @app.get("/pwa-icon-512.png")
    async def serve_pwa_icon_512():
        icon_path = os.path.join(FRONTEND_DIR, "pwa-icon-512.png")
        if os.path.exists(icon_path):
            return FileResponse(icon_path, media_type="image/png")
        raise HTTPException(status_code=404, detail="Ícone não encontrado")

    @app.get("/prova-canoa-ca.crt")
    async def serve_ca_cert():
        ca_path = os.path.join(FRONTEND_DIR, "prova-canoa-ca.crt")
        if os.path.exists(ca_path):
            return FileResponse(
                ca_path,
                media_type="application/x-x509-ca-cert",
                filename="prova-canoa-ca.crt"
            )
        raise HTTPException(status_code=404, detail="Certificado CA não encontrado")
        
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="frontend_static")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "OMR Exam Grader Engine"}

if __name__ == "__main__":
    import uvicorn
    # Using port 8080 to avoid conflicts with other existing services on 8000
    port = int(os.getenv("PORT", 8080))
    print(f"Iniciando servidor OMR na porta {port} (Acesse http://localhost:{port})...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
