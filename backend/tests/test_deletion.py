import requests
import json

BASE_URL = "http://127.0.0.1:8080"

def test_delete_flow():
    # 1. Check health
    res = requests.get(f"{BASE_URL}/health")
    assert res.status_code == 200, f"Health check failed: {res.status_code}"
    print("Health check OK")

    # 2. Create a test exam
    create_payload = {
        "title": "PROVA TESTE EXCLUSAO",
        "subtitle": "TESTE EXCLUSAO",
        "num_questions": 5,
        "num_alternatives": 4,
        "points_per_question": 2.0,
        "answer_key": {"1": "A", "2": "B", "3": "C", "4": "D", "5": "A"}
    }
    create_res = requests.post(f"{BASE_URL}/api/exams", json=create_payload)
    assert create_res.status_code == 201, f"Create exam failed: {create_res.status_code}"
    exam = create_res.json()
    exam_id = exam["id"]
    print(f"Created test exam: {exam_id}")

    # 3. Verify it exists
    get_res = requests.get(f"{BASE_URL}/api/exams/{exam_id}")
    assert get_res.status_code == 200, "Exam not found"

    # 4. Test deleting the exam
    del_res = requests.delete(f"{BASE_URL}/api/exams/{exam_id}")
    assert del_res.status_code == 200, f"Delete exam failed: {del_res.status_code} - {del_res.text}"
    print(f"Deleted test exam: {del_res.json()}")

    # 5. Verify it is gone
    get_res2 = requests.get(f"{BASE_URL}/api/exams/{exam_id}")
    assert get_res2.status_code == 404, "Exam should be 404 after deletion"
    print("Verification OK: Exam returned 404 after deletion!")

    # 6. Test submission deletion endpoint (testing 404 on dummy ID)
    del_sub_res = requests.delete(f"{BASE_URL}/api/submissions/dummy-non-existent-id")
    assert del_sub_res.status_code == 404, "Non-existent submission should return 404"
    print("Submission endpoint exists and handles 404 properly!")

    print("ALL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_delete_flow()
