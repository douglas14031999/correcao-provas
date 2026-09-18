import os
import sys
import json
import uuid
import urllib.request
import numpy as np
import cv2

# Ensure backend root is in sys.path
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(TEST_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.services.pdf_generator import generate_aruco_marker_image

def test_api_upload():
    # 1. Fetch created exams from running API
    res = urllib.request.urlopen("http://localhost:8080/api/exams")
    exams = json.loads(res.read().decode("utf-8"))
    assert len(exams) > 0, "No exams found on API"
    target_exam = exams[0]
    exam_id = target_exam["id"]
    template = target_exam["sheet_template"]
    
    print(f"Target Exam: {target_exam['title']} (ID: {exam_id})")
    
    # 2. Synthesize a filled sheet for this exam
    h, w = template["canonical_height"], template["canonical_width"]
    sheet = np.ones((h, w, 3), dtype=np.uint8) * 255
    
    # Draw ArUco markers
    marker_centers = template["marker_centers"]
    marker_size = 120
    half_m = marker_size // 2
    for mid in [0, 1, 2, 3]:
        cx, cy = marker_centers.get(str(mid)) or marker_centers.get(mid)
        pil_marker = generate_aruco_marker_image(mid, size=marker_size)
        m_arr = cv2.cvtColor(np.array(pil_marker), cv2.COLOR_GRAY2BGR)
        sheet[cy - half_m:cy + half_m, cx - half_m:cx + half_m] = m_arr
        
    # Fill bubbles to score on all questions
    bubbles = template["bubbles"]
    for q_str, options in bubbles.items():
        # Fill the first alternative (e.g. 'A')
        first_opt = list(options.keys())[0]
        coords = options[first_opt]
        bx, by, br = coords["x"], coords["y"], coords["radius"]
        # Draw bubble outline and fill inner circle
        cv2.circle(sheet, (bx, by), br, (140, 140, 140), 2)
        cv2.circle(sheet, (bx, by), br - 1, (10, 10, 10), -1)
        
    # Simulate camera skew
    pts1 = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    skew = 120
    pts2 = np.float32([
        [skew + 40, skew + 20],
        [w - skew - 30, skew + 60],
        [w - skew + 20, h - skew - 40],
        [skew - 30, h - skew + 30]
    ])
    warp_mat = cv2.getPerspectiveTransform(pts1, pts2)
    camera_photo = np.ones((h, w, 3), dtype=np.uint8) * 90
    cv2.warpPerspective(sheet, warp_mat, (w, h), dst=camera_photo, borderMode=cv2.BORDER_TRANSPARENT)
    
    _, jpg_data = cv2.imencode(".jpg", camera_photo, [cv2.IMWRITE_JPEG_QUALITY, 90])
    img_bytes = jpg_data.tobytes()
    
    # 3. Perform multipart/form-data upload to POST /api/grade
    boundary = "----WebKitFormBoundary" + uuid.uuid4().hex
    body = bytearray()
    
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(b'Content-Disposition: form-data; name="file"; filename="camera_sheet.jpg"\r\n')
    body.extend(b"Content-Type: image/jpeg\r\n\r\n")
    body.extend(img_bytes)
    body.extend(b"\r\n")
    
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(b'Content-Disposition: form-data; name="exam_id"\r\n\r\n')
    body.extend(exam_id.encode("utf-8"))
    body.extend(b"\r\n")
    
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(b'Content-Disposition: form-data; name="student_name"\r\n\r\n')
    body.extend("Lucas Santos Oliveira".encode("utf-8"))
    body.extend(b"\r\n")
    
    body.extend(f"--{boundary}--\r\n".encode("utf-8"))
    
    req = urllib.request.Request(
        "http://localhost:8080/api/grade",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    res = urllib.request.urlopen(req)
    result = json.loads(res.read().decode("utf-8"))
    
    print("\n--- RESULTADO DA CORREÇÃO VIA API REST ---")
    print(f"Aluno: {result['student_name']}")
    print(f"Nota: {result['score']} / {result['max_score']} ({result['percentage']}%)")
    print(f"Acertos: {result['correct_count']} | Erros: {result['wrong_count']}")
    print(f"Raio-X (Overlay): http://localhost:8080{result['overlay_image_url']}")
    print("Status: [PASSOU COM SUCESSO]")

if __name__ == "__main__":
    test_api_upload()
