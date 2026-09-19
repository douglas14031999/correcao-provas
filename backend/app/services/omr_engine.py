import os
import uuid
import numpy as np
import cv2
from typing import Dict, Any, Tuple, Optional, List

CANONICAL_WIDTH = 1654
CANONICAL_HEIGHT = 2338
CANONICAL_HEIGHT_HALF = 1169

def get_aruco_detector():
    """Initializes ArUco detector compatible with OpenCV versions."""
    try:
        dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        parameters = cv2.aruco.DetectorParameters()
        detector = cv2.aruco.ArucoDetector(dictionary, parameters)
        return detector, "new"
    except AttributeError:
        dictionary = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)
        parameters = cv2.aruco.DetectorParameters_create()
        return (dictionary, parameters), "legacy"

def detect_aruco_markers(image: np.ndarray) -> Dict[int, np.ndarray]:
    """
    Detects ArUco markers 0, 1, 2, 3 in the image.
    Returns dict {marker_id: center_point_float32}
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    detector_obj, mode = get_aruco_detector()
    
    if mode == "new":
        corners, ids, _ = detector_obj.detectMarkers(gray)
    else:
        dictionary, parameters = detector_obj
        corners, ids, _ = cv2.aruco.detectMarkers(gray, dictionary, parameters=parameters)
        
    markers = {}
    if ids is not None and len(ids) > 0:
        ids = ids.flatten()
        for i, marker_id in enumerate(ids):
            if marker_id in [0, 1, 2, 3]:
                # Center of the marker is the mean of its 4 corners
                c = corners[i][0]
                center = np.mean(c, axis=0)
                markers[int(marker_id)] = center
                
    # If some markers were missed, try CLAHE contrast enhancement
    if len(markers) < 4:
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        if mode == "new":
            corners2, ids2, _ = detector_obj.detectMarkers(enhanced)
        else:
            corners2, ids2, _ = cv2.aruco.detectMarkers(enhanced, dictionary, parameters=parameters)
            
        if ids2 is not None and len(ids2) > 0:
            ids2 = ids2.flatten()
            for i, marker_id in enumerate(ids2):
                if marker_id in [0, 1, 2, 3] and marker_id not in markers:
                    c = corners2[i][0]
                    center = np.mean(c, axis=0)
                    markers[int(marker_id)] = center
                    
    return markers

def warp_sheet(image: np.ndarray, markers: Dict[int, np.ndarray], template: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Performs 4-point perspective warp aligning markers to canonical template coordinates.
    """
    # Source points from detected markers in order: 0 (TL), 1 (TR), 2 (BR), 3 (BL)
    src_pts = np.float32([
        markers[0],
        markers[1],
        markers[2],
        markers[3]
    ])
    
    # Destination points from template
    marker_centers = template["marker_centers"]
    def get_mc(mid):
        return marker_centers.get(str(mid)) if str(mid) in marker_centers else marker_centers[mid]

    dst_pts = np.float32([
        get_mc(0),
        get_mc(1),
        get_mc(2),
        get_mc(3)
    ])
    
    target_w = template.get("canonical_width", CANONICAL_WIDTH)
    target_h = template.get("canonical_height", CANONICAL_HEIGHT_HALF if template.get("is_compact") else CANONICAL_HEIGHT)
    
    matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped = cv2.warpPerspective(
        image, matrix, 
        (target_w, target_h),
        flags=cv2.INTER_LINEAR
    )
    return warped, matrix

def _parse_qr_payload(raw: str) -> Tuple[Optional[str], Optional[str]]:
    raw = raw.strip()
    exam_id = None
    student_id = None
    if "|" in raw:
        for part in raw.split("|"):
            part = part.strip()
            if part.startswith("EXAM:") or part.startswith("E:"):
                exam_id = part.split(":", 1)[1].strip()
            elif part.startswith("STUDENT:") or part.startswith("S:"):
                student_id = part.split(":", 1)[1].strip()
    elif raw.startswith("EXAM:") or raw.startswith("E:"):
        exam_id = raw.split(":", 1)[1].strip()
    elif len(raw) > 0:
        exam_id = raw
    return exam_id, student_id

def read_qr_metadata(image: np.ndarray) -> Tuple[Optional[str], Optional[str]]:
    """
    Attempts to decode QR code to identify exam_id and optional student_id.
    Uses ultra-fast staged detection optimized for both printed paper and mobile phone screen photos:
    1. Candidate ROIs:
       - Tight canonical QR card: x: 68%..98%, y: 1%..28% (fastest & highly isolated from header text)
       - Wide top-right quadrant: x: 48%..100%, y: 0%..45% (fallback for unwarped or non-standard angles)
    2. Per ROI strategies:
       - Strategy A: Direct Raw BGR & Gray with PyZBar (instant on paper, ~2ms)
       - Strategy B: Anti-Moiré Adaptive Filter (Gaussian C + MedianBlur 3px & 5px).
         Crucial for mobile phones photographing computer screens: eliminates LCD subpixel scanline stripes.
       - Strategy C: CLAHE contrast enhancement for shadowy paper scans
       - Strategy D: 2x Upscale with Anti-Moiré for small or low-res crops
       - Strategy E: OpenCV QRCodeDetector fallback
    """
    if image is None:
        return None, None

    h, w = image.shape[:2]
    # Candidate ROIs
    rois = [
        image[int(h * 0.01) : int(h * 0.28), int(w * 0.68) : int(w * 0.98)],
        image[0 : max(10, int(h * 0.45)), max(0, int(w * 0.48)) : w]
    ]

    try:
        from pyzbar.pyzbar import decode as pyzbar_decode, ZBarSymbol
    except ImportError:
        pyzbar_decode = None

    for roi in rois:
        if roi.size == 0:
            continue

        # Fast downscale if candidate ROI is excessively large (> 600px width or height)
        # Keeps QR resolution high (20+ px per module) but reduces decode work by 4x
        if max(roi.shape[:2]) > 600:
            scale_roi = 500.0 / max(roi.shape[:2])
            roi_proc = cv2.resize(roi, (0, 0), fx=scale_roi, fy=scale_roi, interpolation=cv2.INTER_AREA)
        else:
            roi_proc = roi

        gray_roi = cv2.cvtColor(roi_proc, cv2.COLOR_BGR2GRAY) if len(roi_proc.shape) == 3 else roi_proc

        if pyzbar_decode is not None:
            # Strategy A: Direct Raw BGR & Gray (instant on paper, ~2ms)
            for cand in (roi_proc, gray_roi):
                try:
                    for item in pyzbar_decode(cand, symbols=[ZBarSymbol.QRCODE]):
                        if item.data:
                            raw_str = item.data.decode("utf-8", errors="ignore").strip()
                            if raw_str:
                                eid, sid = _parse_qr_payload(raw_str)
                                if eid or sid:
                                    return eid, sid
                except Exception:
                    pass

            # Strategy B: Anti-Moiré Filter (Gaussian AdaptiveThreshold + MedianBlur)
            # Solves LCD monitor moiré/subpixel scanline interference (~6ms)
            for (bs, c_val, med_k) in [(19, 5, 5), (17, 4, 3)]:
                try:
                    adapt = cv2.adaptiveThreshold(gray_roi, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, bs, c_val)
                    med = cv2.medianBlur(adapt, med_k)
                    for item in pyzbar_decode(med, symbols=[ZBarSymbol.QRCODE]):
                        if item.data:
                            raw_str = item.data.decode("utf-8", errors="ignore").strip()
                            if raw_str:
                                eid, sid = _parse_qr_payload(raw_str)
                                if eid or sid:
                                    return eid, sid
                except Exception:
                    pass

            # Strategy C: CLAHE contrast enhancement (for shadowy paper scans)
            try:
                clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(gray_roi)
                for item in pyzbar_decode(clahe, symbols=[ZBarSymbol.QRCODE]):
                    if item.data:
                        raw_str = item.data.decode("utf-8", errors="ignore").strip()
                        if raw_str:
                            eid, sid = _parse_qr_payload(raw_str)
                            if eid or sid:
                                return eid, sid
            except Exception:
                pass

            # Strategy D: 2x Upscale only if ROI is very small (< 180px)
            if min(gray_roi.shape[:2]) < 180:
                try:
                    up2x = cv2.resize(gray_roi, (0, 0), fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
                    adapt_up = cv2.adaptiveThreshold(up2x, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 19, 5)
                    med_up = cv2.medianBlur(adapt_up, 5)
                    for item in pyzbar_decode(med_up, symbols=[ZBarSymbol.QRCODE]):
                        if item.data:
                            raw_str = item.data.decode("utf-8", errors="ignore").strip()
                            if raw_str:
                                eid, sid = _parse_qr_payload(raw_str)
                                if eid or sid:
                                    return eid, sid
                except Exception:
                    pass

        # Strategy E: OpenCV QRCodeDetector fallback
        try:
            det = cv2.QRCodeDetector()
            data, _, _ = det.detectAndDecode(roi_proc)
            if data and data.strip():
                eid, sid = _parse_qr_payload(data)
                if eid or sid:
                    return eid, sid
        except Exception:
            pass

    return None, None

def read_qr_exam_id(image: np.ndarray) -> Optional[str]:
    """Attempts to decode QR code to identify exam_id."""
    exam_id, _ = read_qr_metadata(image)
    return exam_id


def analyze_bubbles(warped_image: np.ndarray, template: Dict[str, Any]) -> Tuple[Dict[str, str], Dict[str, Dict[str, float]]]:
    """
    Analyzes fill ratio for every bubble and classifies responses:
    'A', 'B', 'C', ..., 'BLANK', or 'DOUBLE'.
    Uses local peak alignment search (+/- 4px) in sub-window to eliminate
    alignment errors from paper tilt, warping, and phone camera perspective.
    """
    gray = cv2.cvtColor(warped_image, cv2.COLOR_BGR2GRAY)
    
    # Combined Otsu + Adaptive thresholding:
    # Otsu separates ink (<80) from paper (>180), completely ignoring light gray internal letters.
    # Adaptive handles uneven camera lighting gradients.
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, binary_otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    binary_adapt = cv2.adaptiveThreshold(
        gray, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 
        blockSize=31, 
        C=16
    )
    binary = cv2.bitwise_and(binary_otsu, binary_adapt)
    
    detected_answers = {}
    fill_ratios_data = {}
    
    bubbles_map = template["bubbles"]
    img_h, img_w = binary.shape[:2]
    
    # Cache masks for common radii to maximize execution speed
    circle_masks_cache = {}
    def get_circular_mask(radius: int):
        if radius not in circle_masks_cache:
            y, x = np.ogrid[-radius:radius+1, -radius:radius+1]
            circle_masks_cache[radius] = (x**2 + y**2) <= (radius**2)
        return circle_masks_cache[radius]
    
    for q_str, options in bubbles_map.items():
        q_num = int(q_str)
        option_ratios = {}
        
        for opt_letter, coords in options.items():
            cx = int(coords["x"])
            cy = int(coords["y"])
            r = int(coords["radius"])
            
            # Safe inner radius: 56% of bubble radius guarantees mask never touches bubble border
            inner_r = max(3, int(r * 0.56))
            circ_mask = get_circular_mask(inner_r)
            mask_pixel_count = max(1, int(np.count_nonzero(circ_mask)))
            
            # Search window offsets strictly within safety margin so it cannot grab the outer circle border
            max_off = max(1, r - inner_r - 2)
            search_offsets = [-max_off, 0, max_off] if max_off >= 2 else [-1, 0, 1]
            
            best_ratio = 0.0
            for dx in search_offsets:
                for dy in search_offsets:
                    tx, ty = cx + dx, cy + dy
                    if tx - inner_r < 0 or tx + inner_r >= img_w or ty - inner_r < 0 or ty + inner_r >= img_h:
                        continue
                    
                    sub_patch = binary[ty - inner_r : ty + inner_r + 1, tx - inner_r : tx + inner_r + 1]
                    if sub_patch.shape != circ_mask.shape:
                        continue
                    
                    white_count = int(np.count_nonzero(sub_patch[circ_mask]))
                    ratio = white_count / mask_pixel_count
                    if ratio > best_ratio:
                        best_ratio = ratio
            
            option_ratios[opt_letter] = round(best_ratio, 4)
            
        fill_ratios_data[q_str] = option_ratios
        
        # Classification logic:
        sorted_opts = sorted(option_ratios.items(), key=lambda x: x[1], reverse=True)
        top_opt, top_ratio = sorted_opts[0]
        second_opt, second_ratio = sorted_opts[1] if len(sorted_opts) > 1 else ("", 0.0)
        
        # 1. Blank: Top bubble fill is below ink threshold
        if top_ratio < 0.35:
            detected_answers[q_str] = "BLANK"
        # 2. Genuine Double Mark: BOTH options are distinctly filled (> 0.45)
        # and the second mark is nearly as dark as the top
        elif second_ratio >= 0.45 and (second_ratio >= top_ratio * 0.78 or (top_ratio - second_ratio < 0.12)):
            detected_answers[q_str] = "DOUBLE"
        # 3. Confirmed Single Option: Top option is clearly dominant
        elif top_ratio >= 0.40 or (top_ratio >= 0.32 and top_ratio > second_ratio * 1.35):
            detected_answers[q_str] = top_opt
        else:
            detected_answers[q_str] = "BLANK"
            
    return detected_answers, fill_ratios_data

def cv2_safe_imwrite(path: str, img: np.ndarray, quality: int = 85) -> bool:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    ext = os.path.splitext(path)[1].lower() or ".jpg"
    is_success, buf = cv2.imencode(ext, img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if is_success:
        with open(path, "wb") as f:
            f.write(buf)
        return True
    return False

def generate_overlay_visualization(
    warped_image: np.ndarray,
    template: Dict[str, Any],
    detected_answers: Dict[str, str],
    answer_key: Dict[str, str],
    output_path: str
) -> str:
    """
    Draws visual X-Ray inspection overlay:
    - Green circle for correct answers
    - Red circle on wrong bubble with green circle on correct bubble
    - Yellow for blank or double marks
    """
    overlay = warped_image.copy()
    bubbles_map = template["bubbles"]
    
    for q_str, options in bubbles_map.items():
        detected = detected_answers.get(q_str, "BLANK")
        correct = answer_key.get(q_str, "").upper()
        
        is_correct = (detected == correct and correct != "")
        
        for opt_letter, coords in options.items():
            cx = int(coords["x"])
            cy = int(coords["y"])
            r = int(coords["radius"])
            
            # If student marked this option
            if detected == opt_letter:
                if is_correct:
                    # Correct -> Vibrant Green thick circle & fill
                    cv2.circle(overlay, (cx, cy), r + 4, (34, 197, 94), 4) # Green
                else:
                    # Wrong -> Crimson Red thick circle
                    cv2.circle(overlay, (cx, cy), r + 4, (30, 30, 220), 4) # Red
            
            # Show correct answer if student missed it or left blank
            if not is_correct and correct == opt_letter:
                # Dotted/thin green circle indicating the answer that should have been marked
                cv2.circle(overlay, (cx, cy), r + 6, (34, 197, 94), 2)
                
            # If double marked
            if detected == "DOUBLE" and opt_letter in options:
                # Mark potential options in Amber
                cv2.circle(overlay, (cx, cy), r + 3, (0, 190, 245), 2)

    # Blend overlay with original for a smooth aesthetic
    alpha = 0.85
    cv2.addWeighted(overlay, alpha, warped_image, 1 - alpha, 0, overlay)

    # Resize to web-friendly resolution (e.g. max width 900)
    h, w = overlay.shape[:2]
    web_w = 900
    web_h = int(h * (web_w / w))
    web_preview = cv2.resize(overlay, (web_w, web_h), interpolation=cv2.INTER_AREA)
    
    cv2_safe_imwrite(output_path, web_preview, 85)
    return output_path

def grade_submission(
    image_bytes: bytes,
    exam: Any,
    student_name: str = "Aluno",
    storage_dir: str = "storage"
) -> Dict[str, Any]:
    """
    Complete processing pipeline:
    1. Decode image
    2. Detect 4 ArUco markers
    3. Warp perspective to canonical sheet
    4. Analyze bubble fill ratios
    5. Grade against answer key
    6. Generate annotated overlay image
    """
    if isinstance(exam, str):
        from app.services.database import get_exam
        loaded_exam = get_exam(exam.strip())
        if loaded_exam:
            exam = loaded_exam
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if image is None:
        raise ValueError("Não foi possível decodificar a imagem enviada. Formato inválido.")
        
    markers = detect_aruco_markers(image)
    if len(markers) < 4:
        found_ids = list(markers.keys())
        raise ValueError(
            f"Não foi possível localizar os 4 marcadores ArUco da folha (encontrados: {found_ids}). "
            "Certifique-se de enquadrar toda a folha na câmera e evitar sombras extremas."
        )
        
    # Automatically identify if the photographed sheet is full A4 page (1 per page)
    # or half A4 page (2 per page / compact layout) based on marker aspect ratio
    w_top = np.linalg.norm(markers[1] - markers[0])
    w_bot = np.linalg.norm(markers[2] - markers[3])
    marker_w = (w_top + w_bot) / 2.0

    h_left = np.linalg.norm(markers[3] - markers[0])
    h_right = np.linalg.norm(markers[2] - markers[1])
    marker_h = (h_left + h_right) / 2.0

    aspect_ratio = marker_h / max(1.0, marker_w)
    is_compact = bool(aspect_ratio < 1.05)

    from app.services.pdf_generator import get_exam_template_for_layout
    template = get_exam_template_for_layout(exam, is_compact=is_compact)

    warped, _ = warp_sheet(image, markers, template)
    
    # Try reading QR: first on warped sheet (tight canonical ROI), then fallback to raw input image
    detected_qr_exam_id, detected_qr_student_id = read_qr_metadata(warped)
    if not detected_qr_exam_id and not detected_qr_student_id:
        # Fallback to raw image: downscale first if oversized (> 1280px) to prevent multi-second stalls
        raw_to_scan = image
        if max(image.shape[:2]) > 1280:
            scale_raw = 1280.0 / max(image.shape[:2])
            raw_to_scan = cv2.resize(image, (0, 0), fx=scale_raw, fy=scale_raw, interpolation=cv2.INTER_AREA)
        detected_qr_exam_id, detected_qr_student_id = read_qr_metadata(raw_to_scan)

    # If QR code identified an exam, dynamically switch to it in-place in a single pass
    if detected_qr_exam_id:
        try:
            from app.services.database import get_exam
            detected_exam = get_exam(detected_qr_exam_id)
            if detected_exam:
                exam = detected_exam
                template = get_exam_template_for_layout(exam, is_compact=is_compact)
        except Exception:
            pass
    
    student_id = detected_qr_student_id
    classroom_id = None
    school_id = None
    classroom_name = None
    school_name = None
    registration = None

    if detected_qr_student_id:
        try:
            from app.services.database import get_student_by_id
            st = get_student_by_id(detected_qr_student_id)
            if st:
                student_id = st.get("id") or student_id
                student_name = st.get("name") or student_name
                classroom_id = st.get("classroom_id")
                school_id = st.get("school_id")
                classroom_name = st.get("classroom_name")
                school_name = st.get("school_name")
                registration = st.get("registration")
        except Exception:
            pass

    # Ensure school and classroom fallback to exam if student has none
    if not school_name:
        school_name = exam.get("school_name") or ""
    if not classroom_name:
        classroom_name = exam.get("classroom") or ""
    if student_name in [None, "", "Aluno"] and exam.get("student_name"):
        student_name = exam.get("student_name")
    
    detected_answers, fill_ratios = analyze_bubbles(warped, template)
    
    answer_key = exam.get("answer_key", {})
    weights = exam.get("weights", {})
    default_weight = float(exam.get("points_per_question", 1.0))
    
    total_score = 0.0
    max_score = 0.0
    correct_count = 0
    wrong_count = 0
    blank_count = 0
    double_count = 0
    
    results_detail = []
    
    for q_idx in range(1, exam["num_questions"] + 1):
        q_str = str(q_idx)
        detected = detected_answers.get(q_str, "BLANK")
        correct = answer_key.get(q_str, "")
        q_weight = float(weights.get(q_str, default_weight))
        
        max_score += q_weight
        
        is_correct = (detected == correct and correct != "")
        if is_correct:
            points = q_weight
            correct_count += 1
        else:
            points = 0.0
            if detected == "BLANK":
                blank_count += 1
            elif detected == "DOUBLE":
                double_count += 1
            else:
                wrong_count += 1
                
        total_score += points
        
        results_detail.append({
            "question": q_idx,
            "chosen": detected,
            "correct": correct,
            "is_correct": is_correct,
            "points": round(points, 2),
            "weight": round(q_weight, 2),
            "ratios": fill_ratios.get(q_str, {})
        })
        
    submission_id = str(uuid.uuid4())
    
    # Save overlay image
    overlay_filename = f"overlay_{submission_id}.jpg"
    overlay_rel_url = f"/storage/overlays/{overlay_filename}"
    overlay_disk_path = os.path.join(storage_dir, "overlays", overlay_filename)
    generate_overlay_visualization(warped, template, detected_answers, answer_key, overlay_disk_path)
    
    # Save original warped scanned image
    scanned_filename = f"scanned_{submission_id}.jpg"
    scanned_rel_url = f"/storage/scans/{scanned_filename}"
    scanned_disk_path = os.path.join(storage_dir, "scans", scanned_filename)
    cv2_safe_imwrite(scanned_disk_path, warped, 80)
    
    return {
        "id": submission_id,
        "exam_id": exam["id"],
        "exam_title": exam.get("title", "Simulado"),
        "student_name": student_name,
        "student_id": student_id,
        "classroom_id": classroom_id,
        "classroom_name": classroom_name,
        "school_id": school_id,
        "school_name": school_name,
        "registration": registration,
        "score": round(total_score, 2),
        "max_score": round(max_score, 2),
        "percentage": round((total_score / max(1.0, max_score)) * 100, 1),
        "correct_count": correct_count,
        "wrong_count": wrong_count,
        "blank_count": blank_count,
        "double_count": double_count,
        "detected_answers": detected_answers,
        "results_detail": results_detail,
        "scanned_image_url": scanned_rel_url,
        "overlay_image_url": overlay_rel_url,
        "detected_qr_exam_id": detected_qr_exam_id,
        "detected_qr_student_id": detected_qr_student_id,
        "layout_detected": "2_por_folha" if is_compact else "pagina_inteira",
        "is_compact": is_compact
    }
