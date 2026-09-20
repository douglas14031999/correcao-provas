import os
import uuid
import numpy as np
import cv2
from typing import Dict, Any, Tuple, Optional, List

CANONICAL_WIDTH = 1654
CANONICAL_HEIGHT = 2338
CANONICAL_HEIGHT_HALF = 1169

_CACHED_ARUCO_DETECTOR = None
_CACHED_ARUCO_MODE = None

def get_aruco_detector():
    """Initializes and caches ArUco detector singleton."""
    global _CACHED_ARUCO_DETECTOR, _CACHED_ARUCO_MODE
    if _CACHED_ARUCO_DETECTOR is not None:
        return _CACHED_ARUCO_DETECTOR, _CACHED_ARUCO_MODE
    try:
        dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        parameters = cv2.aruco.DetectorParameters()
        detector = cv2.aruco.ArucoDetector(dictionary, parameters)
        _CACHED_ARUCO_DETECTOR, _CACHED_ARUCO_MODE = detector, "new"
    except AttributeError:
        dictionary = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)
        parameters = cv2.aruco.DetectorParameters_create()
        _CACHED_ARUCO_DETECTOR, _CACHED_ARUCO_MODE = (dictionary, parameters), "legacy"
    return _CACHED_ARUCO_DETECTOR, _CACHED_ARUCO_MODE

def detect_aruco_markers(image: np.ndarray) -> Dict[int, np.ndarray]:
    """
    Detects ArUco markers 0, 1, 2, 3 in the image.
    Scales large photos to max 1200px for 5x faster processing,
    then re-maps center coordinates back with sub-pixel precision.
    Returns dict {marker_id: center_point_float32}
    """
    h, w = image.shape[:2]
    max_d = max(h, w)
    scale = 1200.0 / max_d if max_d > 1200 else 1.0
    if scale < 1.0:
        proc_img = cv2.resize(image, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    else:
        proc_img = image

    gray = cv2.cvtColor(proc_img, cv2.COLOR_BGR2GRAY) if len(proc_img.shape) == 3 else proc_img
    detector_obj, mode = get_aruco_detector()
    
    if mode == "new":
        corners, ids, _ = detector_obj.detectMarkers(gray)
    else:
        dictionary, parameters = detector_obj
        corners, ids, _ = cv2.aruco.detectMarkers(gray, dictionary, parameters=parameters)
        
    markers = {}
    inv_scale = 1.0 / scale
    if ids is not None and len(ids) > 0:
        ids = ids.flatten()
        for i, marker_id in enumerate(ids):
            if marker_id in [0, 1, 2, 3]:
                c = corners[i][0] * inv_scale
                markers[int(marker_id)] = np.mean(c, axis=0)
                
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
                    c = corners2[i][0] * inv_scale
                    markers[int(marker_id)] = np.mean(c, axis=0)
                    
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

def read_qr_metadata(image: np.ndarray, return_position: bool = False) -> Any:
    """
    Attempts to decode QR code to identify exam_id and optional student_id.
    Uses ultra-fast targeted scans on canonical positions (Top: Gabarito, Bottom: Capa)
    first in sub-5ms, with full fallbacks only if targeted search misses.
    """
    if image is None:
        return (None, None, None) if return_position else (None, None)

    h, w = image.shape[:2]

    try:
        from pyzbar.pyzbar import decode as pyzbar_decode, ZBarSymbol
    except ImportError:
        pyzbar_decode = None

    # Step 1: Ultra-fast targeted scans on known official positions
    if pyzbar_decode is not None:
        targeted_boxes = [
            ("top", 0, int(h * 0.25), int(w * 0.68), w),
            ("bottom", int(h * 0.75), h, int(w * 0.68), w)
        ]
        for tag, y1, y2, x1, x2 in targeted_boxes:
            patch = image[y1:y2, x1:x2]
            if patch.size == 0:
                continue
            gray_patch = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY) if len(patch.shape) == 3 else patch
            # Direct raw pyzbar
            try:
                for item in pyzbar_decode(gray_patch, symbols=[ZBarSymbol.QRCODE]):
                    if item.data:
                        raw_str = item.data.decode("utf-8", errors="ignore").strip()
                        eid, sid = _parse_qr_payload(raw_str)
                        if eid or sid:
                            return (eid, sid, tag) if return_position else (eid, sid)
            except Exception:
                pass
            # Fast Anti-Moiré on small targeted patch
            try:
                adapt_patch = cv2.adaptiveThreshold(gray_patch, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 19, 5)
                med_patch = cv2.medianBlur(adapt_patch, 5)
                for item in pyzbar_decode(med_patch, symbols=[ZBarSymbol.QRCODE]):
                    if item.data:
                        raw_str = item.data.decode("utf-8", errors="ignore").strip()
                        eid, sid = _parse_qr_payload(raw_str)
                        if eid or sid:
                            return (eid, sid, tag) if return_position else (eid, sid)
            except Exception:
                pass

    # Step 2: Fallback broader scans if sheet was rotated, skewed or non-canonical
    rois = [
        ("top", int(h * 0.01), int(h * 0.32), int(w * 0.60), w),
        ("bottom", int(h * 0.50), h, int(w * 0.50), w),
        ("top_wide", 0, max(10, int(h * 0.45)), max(0, int(w * 0.45)), w),
        ("bottom_wide", int(h * 0.45), h, max(0, int(w * 0.45)), w),
        ("full", 0, h, 0, w)
    ]

    def _determine_pos(tag_name: str, y_offset: int, item_top: float, s_roi: float) -> str:
        if "bottom" in tag_name:
            return "bottom"
        if "top" in tag_name:
            return "top"
        real_y = y_offset + (item_top / s_roi if s_roi > 0 else item_top)
        return "bottom" if real_y >= h * 0.45 else "top"

    for (tag, y1, y2, x1, x2) in rois:
        roi = image[y1:y2, x1:x2]
        if roi.size == 0:
            continue

        if max(roi.shape[:2]) > 600:
            scale_roi = 500.0 / max(roi.shape[:2])
            roi_proc = cv2.resize(roi, (0, 0), fx=scale_roi, fy=scale_roi, interpolation=cv2.INTER_AREA)
        else:
            scale_roi = 1.0
            roi_proc = roi

        gray_roi = cv2.cvtColor(roi_proc, cv2.COLOR_BGR2GRAY) if len(roi_proc.shape) == 3 else roi_proc

        if pyzbar_decode is not None:
            for cand in (roi_proc, gray_roi):
                try:
                    for item in pyzbar_decode(cand, symbols=[ZBarSymbol.QRCODE]):
                        if item.data:
                            raw_str = item.data.decode("utf-8", errors="ignore").strip()
                            if raw_str:
                                eid, sid = _parse_qr_payload(raw_str)
                                if eid or sid:
                                    top_val = item.rect.top if hasattr(item, "rect") else 0
                                    pos = _determine_pos(tag, y1, top_val, scale_roi)
                                    return (eid, sid, pos) if return_position else (eid, sid)
                except Exception:
                    pass

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
                                    top_val = item.rect.top if hasattr(item, "rect") else 0
                                    pos = _determine_pos(tag, y1, top_val, scale_roi)
                                    return (eid, sid, pos) if return_position else (eid, sid)
                except Exception:
                    pass

            try:
                clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(gray_roi)
                for item in pyzbar_decode(clahe, symbols=[ZBarSymbol.QRCODE]):
                    if item.data:
                        raw_str = item.data.decode("utf-8", errors="ignore").strip()
                        if raw_str:
                            eid, sid = _parse_qr_payload(raw_str)
                            if eid or sid:
                                top_val = item.rect.top if hasattr(item, "rect") else 0
                                pos = _determine_pos(tag, y1, top_val, scale_roi)
                                return (eid, sid, pos) if return_position else (eid, sid)
            except Exception:
                pass

        try:
            det = cv2.QRCodeDetector()
            data, points, _ = det.detectAndDecode(roi_proc)
            if data and data.strip():
                eid, sid = _parse_qr_payload(data)
                if eid or sid:
                    top_val = np.mean(points[0, :, 1]) if points is not None else 0
                    pos = _determine_pos(tag, y1, top_val, scale_roi)
                    return (eid, sid, pos) if return_position else (eid, sid)
        except Exception:
            pass

    return (None, None, None) if return_position else (None, None)

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
        blockSize=71, 
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
    output_path: str,
    max_questions: Optional[int] = None
) -> str:
    """
    Draws visual X-Ray inspection overlay:
    - Pre-resizes directly to web width (900px) first, saving 75% CPU and memory.
    - Strictly limits drawing up to max_questions to prevent ghost markings on unused columns.
    - Green circle for correct answers
    - Red circle on wrong bubble with green circle on correct bubble
    - Amber for double marks
    """
    h, w = warped_image.shape[:2]
    web_w = 900
    scale = web_w / float(w)
    web_h = int(h * scale)
    web_preview = cv2.resize(warped_image, (web_w, web_h), interpolation=cv2.INTER_AREA)
    overlay = web_preview.copy()
    bubbles_map = template.get("bubbles", {})
    
    for q_str, options in bubbles_map.items():
        try:
            q_num = int(q_str)
        except (ValueError, TypeError):
            q_num = 0

        # Skip any question beyond the exam's actual question count
        if max_questions is not None and q_num > max_questions:
            continue

        detected = detected_answers.get(q_str, "BLANK")
        correct = answer_key.get(q_str, "").upper()

        # If student marked nothing and there is no official answer key, skip
        if detected == "BLANK" and not correct:
            continue
        
        is_correct = (detected == correct and correct != "")
        
        for opt_letter, coords in options.items():
            cx = int(coords["x"] * scale)
            cy = int(coords["y"] * scale)
            r = max(2, int(coords["radius"] * scale))
            
            # If student marked this option
            if detected == opt_letter:
                if is_correct:
                    # Correct -> Vibrant Green thick circle
                    cv2.circle(overlay, (cx, cy), r + 2, (34, 197, 94), 3) # Green
                else:
                    # Wrong -> Crimson Red thick circle
                    cv2.circle(overlay, (cx, cy), r + 2, (30, 30, 220), 3) # Red
            
            # Show correct answer if student missed it or left blank
            if not is_correct and correct == opt_letter:
                cv2.circle(overlay, (cx, cy), r + 3, (34, 197, 94), 2)
                
            # If double marked
            if detected == "DOUBLE" and opt_letter in options:
                cv2.circle(overlay, (cx, cy), r + 2, (0, 190, 245), 2)

    # Blend overlay with original for a smooth aesthetic
    alpha = 0.85
    cv2.addWeighted(overlay, alpha, web_preview, 1 - alpha, 0, overlay)
    cv2_safe_imwrite(output_path, overlay, 80)
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
    detected_qr_exam_id, detected_qr_student_id, qr_pos = read_qr_metadata(warped, return_position=True)
    if not detected_qr_exam_id and not detected_qr_student_id:
        # Fallback to raw image: downscale first if oversized (> 1280px) to prevent multi-second stalls
        raw_to_scan = image
        if max(image.shape[:2]) > 1280:
            scale_raw = 1280.0 / max(image.shape[:2])
            raw_to_scan = cv2.resize(image, (0, 0), fx=scale_raw, fy=scale_raw, interpolation=cv2.INTER_AREA)
        detected_qr_exam_id, detected_qr_student_id, qr_pos = read_qr_metadata(raw_to_scan, return_position=True)

    # If QR code identified an exam, dynamically switch to it in-place in a single pass
    if detected_qr_exam_id:
        try:
            from app.services.database import get_exam
            detected_exam = get_exam(detected_qr_exam_id)
            if detected_exam:
                exam = detected_exam
        except Exception:
            pass

    # CONDICIONAL: quando QR estiver embaixo ('bottom') é Capa da Prova; se estiver em cima ('top') é Gabarito Oficial
    is_cover = bool(qr_pos == "bottom")
    from app.services.pdf_generator import get_exam_template_for_layout
    template = get_exam_template_for_layout(exam, is_compact=is_compact, is_cover=is_cover)

    # Re-warp only if target dimensions differ from current warped image
    target_w = template.get("canonical_width", CANONICAL_WIDTH)
    target_h = template.get("canonical_height", CANONICAL_HEIGHT_HALF if is_compact else CANONICAL_HEIGHT)
    if warped.shape[1] != target_w or warped.shape[0] != target_h:
        warped, _ = warp_sheet(image, markers, template)
    
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

    # Analyze bubbles: when QR position explicitly defines layout, use that template deterministically
    if qr_pos in ("bottom", "top"):
        detected_answers, fill_ratios = analyze_bubbles(warped, template)
    else:
        # Fallback only when QR code was completely undetected
        from app.services.pdf_generator import get_cover_template
        candidates = [template]
        cover_tpl = get_cover_template(exam.get("id", ""), exam.get("num_questions", 22))
        candidates.append(cover_tpl)

        best_detected = None
        best_ratios = None
        best_score_metric = -1.0
        best_template = template

        for cand_tpl in candidates:
            if not cand_tpl or not cand_tpl.get("bubbles"):
                continue
            det_ans, f_ratios = analyze_bubbles(warped, cand_tpl)
            non_blanks = sum(1 for a in det_ans.values() if a != "BLANK")
            avg_top_ratio = float(np.mean([max(opts.values()) for opts in f_ratios.values()])) if f_ratios else 0.0
            cand_metric = non_blanks * 10.0 + avg_top_ratio
            
            if cand_metric > best_score_metric:
                best_score_metric = cand_metric
                best_detected = det_ans
                best_ratios = f_ratios
                best_template = cand_tpl

        detected_answers = best_detected or {}
        fill_ratios = best_ratios or {}
        template = best_template
    
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
    max_q = int(exam.get("num_questions") or len(template.get("bubbles", {})))
    generate_overlay_visualization(warped, template, detected_answers, answer_key, overlay_disk_path, max_questions=max_q)
    
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
        "sheet_type": "capa_prova" if is_cover else "gabarito_oficial",
        "qr_position": qr_pos,
        "layout_detected": "capa_prova" if is_cover else ("2_por_folha" if is_compact else "pagina_inteira"),
        "is_compact": is_compact
    }
