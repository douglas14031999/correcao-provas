import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.database import get_macro_dashboard_data, list_exams

def test_macro_dashboard_all_exams():
    data = get_macro_dashboard_data(None)
    assert data is not None
    assert "kpis" in data
    assert "schools_table" in data
    assert "years_data" in data

    kpis = data["kpis"]
    assert kpis["total_students"] >= 0
    assert kpis["total_graded"] >= 0
    assert kpis["participation_rate"] >= 0.0
    assert kpis["participation_rate"] <= 100.0, f"Participation rate exceeded 100%: {kpis['participation_rate']}"
    assert "evaluated_students" in kpis
    assert kpis["evaluated_students"] <= kpis["total_students"]

    # Check school table
    for school in data["schools_table"]:
        sc_rate = school["participation_rate"]
        assert sc_rate >= 0.0
        assert sc_rate <= 100.0, f"School {school['school_name']} participation exceeded 100%: {sc_rate}"
        assert "evaluated_students" in school
        assert school["evaluated_students"] <= school["total_students"]

def test_macro_dashboard_specific_exam():
    exams = list_exams()
    if not exams:
        return

    # Test with first exam
    first_exam_id = exams[0]["id"]
    data = get_macro_dashboard_data(first_exam_id)
    assert data is not None
    assert "kpis" in data

    kpis = data["kpis"]
    assert kpis["participation_rate"] >= 0.0
    assert kpis["participation_rate"] <= 100.0

    for school in data["schools_table"]:
        sc_rate = school["participation_rate"]
        assert sc_rate >= 0.0
        assert sc_rate <= 100.0

def test_macro_dashboard_years_data():
    data = get_macro_dashboard_data(None)
    years = data["years_data"]
    assert len(years) == 9  # 1º ao 9º Ano

    for yr in years:
        assert "grade_year" in yr
        assert "graded_count" in yr
        if yr["graded_count"] == 0:
            assert yr["average_pct"] is None
        else:
            assert yr["average_pct"] is not None
            assert 0.0 <= yr["average_pct"] <= 100.0
