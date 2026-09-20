import os
import sys
import time
import glob

backend_dir = os.path.abspath("backend")
sys.path.insert(0, backend_dir)

from app.services.database import init_db, list_exams
from app.services.omr_engine import grade_submission

init_db()
exams = list_exams()
exam = exams[0]

scans = glob.glob("backend/storage/scans/*.jpg")[:5]
print(f"Testing {len(scans)} real scan photos from storage/scans:")

for sc in scans:
    with open(sc, "rb") as f:
        img_bytes = f.read()
    size_kb = len(img_bytes) / 1024
    t0 = time.perf_counter()
    try:
        res = grade_submission(img_bytes, exam, student_name="Teste")
        t1 = time.perf_counter()
        print(f"[{os.path.basename(sc)}] Size: {size_kb:.0f}KB | Time: {t1 - t0:.3f}s | Score: {res.get('score')} | QR: {res.get('qr_pos')}")
    except Exception as e:
        t1 = time.perf_counter()
        print(f"[{os.path.basename(sc)}] Size: {size_kb:.0f}KB | Time: {t1 - t0:.3f}s | ERROR: {e}")
