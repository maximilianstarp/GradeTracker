def create_studiengang(client, headers, name="Mathematik"):
    return client.post("/api/studiengaenge", json={"name": name}, headers=headers)


def create_modul(client, headers, studiengang_ids, name="Analysis I", credits=9):
    return client.post(
        "/api/module",
        json={"name": name, "credits": credits, "studiengang_ids": studiengang_ids},
        headers=headers,
    )


class TestStudiengaenge:
    def test_create_and_list(self, client, auth_header):
        resp = create_studiengang(client, auth_header)
        assert resp.status_code == 201
        assert resp.get_json()["name"] == "Mathematik"

        resp = client.get("/api/studiengaenge", headers=auth_header)
        assert resp.status_code == 200
        assert len(resp.get_json()) == 1

    def test_requires_auth(self, client):
        resp = client.get("/api/studiengaenge")
        assert resp.status_code == 401

    def test_duplicate_name_rejected(self, client, auth_header):
        create_studiengang(client, auth_header)
        resp = create_studiengang(client, auth_header)
        assert resp.status_code == 409

    def test_reserved_sonstiges_rejected(self, client, auth_header):
        resp = create_studiengang(client, auth_header, name="Sonstiges")
        assert resp.status_code == 400

    def test_delete_sets_module_to_sonstiges(self, client, auth_header):
        sg = create_studiengang(client, auth_header).get_json()
        modul = create_modul(client, auth_header, [sg["id"]]).get_json()

        client.delete(f"/api/studiengaenge/{sg['id']}", headers=auth_header)

        resp = client.get(f"/api/module/{modul['id']}", headers=auth_header)
        assert resp.get_json()["studiengang_ids"] == []

    def test_delete_with_multi_assigned_modul_keeps_it_in_other_studiengang(self, client, auth_header):
        mathe = create_studiengang(client, auth_header, "Mathematik").get_json()
        physik = create_studiengang(client, auth_header, "Physik").get_json()
        modul = create_modul(client, auth_header, [mathe["id"], physik["id"]]).get_json()

        resp = client.delete(f"/api/studiengaenge/{mathe['id']}", headers=auth_header)
        assert resp.status_code == 204

        resp = client.get(f"/api/module/{modul['id']}", headers=auth_header)
        assert resp.get_json()["studiengang_ids"] == [physik["id"]]

    def test_delete_cascades_to_its_kombimodule(self, client, auth_header):
        mathe = create_studiengang(client, auth_header, "Mathematik").get_json()
        physik = create_studiengang(client, auth_header, "Physik").get_json()
        m1 = create_modul(client, auth_header, [mathe["id"]], "A", 9).get_json()
        m2 = create_modul(client, auth_header, [mathe["id"]], "B", 9).get_json()
        kombi = client.post(
            "/api/kombimodule",
            json={
                "name": "Kombi",
                "credits": 14,
                "studiengang_id": physik["id"],
                "source_module_ids": [m1["id"], m2["id"]],
            },
            headers=auth_header,
        ).get_json()

        resp = client.delete(f"/api/studiengaenge/{physik['id']}", headers=auth_header)
        assert resp.status_code == 204

        resp = client.get(f"/api/kombimodule/{kombi['id']}", headers=auth_header)
        assert resp.status_code == 404


class TestModule:
    def test_create_modul_in_sonstiges(self, client, auth_header):
        resp = client.post(
            "/api/module", json={"name": "Spanisch A1", "credits": 3}, headers=auth_header
        )
        assert resp.status_code == 201
        assert resp.get_json()["studiengang_ids"] == []

    def test_create_modul_in_multiple_studiengaenge(self, client, auth_header):
        mathe = create_studiengang(client, auth_header, "Mathematik").get_json()
        physik = create_studiengang(client, auth_header, "Physik").get_json()
        resp = create_modul(client, auth_header, [mathe["id"], physik["id"]], "Mathe-Physik-Modul", 6)
        assert resp.status_code == 201
        body = resp.get_json()
        assert sorted(body["studiengang_ids"]) == sorted([mathe["id"], physik["id"]])

    def test_missing_credits_rejected(self, client, auth_header):
        resp = client.post("/api/module", json={"name": "X"}, headers=auth_header)
        assert resp.status_code == 400

    def test_grade_attempt_upsert_and_final_grade(self, client, auth_header):
        sg = create_studiengang(client, auth_header).get_json()
        modul = create_modul(client, auth_header, [sg["id"]]).get_json()

        resp = client.post(
            f"/api/module/{modul['id']}/grades",
            json={"slot": 1, "kind": "numeric", "value": 2.3},
            headers=auth_header,
        )
        assert resp.status_code == 200
        assert resp.get_json()["final_grade"] == {"status": "numeric", "value": 2.3}

        resp = client.post(
            f"/api/module/{modul['id']}/grades",
            json={"slot": 2, "kind": "numeric", "value": 1.7},
            headers=auth_header,
        )
        assert resp.get_json()["final_grade"] == {"status": "numeric", "value": 1.7}

        # re-upsert slot 1 overwrites rather than duplicating
        client.post(
            f"/api/module/{modul['id']}/grades",
            json={"slot": 1, "kind": "numeric", "value": 1.0},
            headers=auth_header,
        )
        resp = client.get(f"/api/module/{modul['id']}", headers=auth_header)
        assert len(resp.get_json()["grade_attempts"]) == 2

    def test_invalid_grade_value_rejected(self, client, auth_header):
        sg = create_studiengang(client, auth_header).get_json()
        modul = create_modul(client, auth_header, [sg["id"]]).get_json()
        resp = client.post(
            f"/api/module/{modul['id']}/grades",
            json={"slot": 1, "kind": "numeric", "value": 9.0},
            headers=auth_header,
        )
        assert resp.status_code == 400

    def test_series_and_submission_zulassung(self, client, auth_header):
        sg = create_studiengang(client, auth_header).get_json()
        modul = create_modul(client, auth_header, [sg["id"]]).get_json()

        series = client.post(
            f"/api/module/{modul['id']}/series",
            json={"name": "Rechenblatt", "threshold_percent": 50},
            headers=auth_header,
        ).get_json()["series"][0]

        client.post(
            f"/api/series/{series['id']}/submissions",
            json={"week_number": 1, "points_achieved": 3, "points_max": 10},
            headers=auth_header,
        )
        resp = client.get(f"/api/module/{modul['id']}", headers=auth_header)
        body = resp.get_json()
        assert body["zulassung"] is False
        assert body["series"][0]["progress"]["points_needed"] == 2  # need 5, have 3

        client.post(
            f"/api/series/{series['id']}/submissions",
            json={"week_number": 2, "points_achieved": 8, "points_max": 10},
            headers=auth_header,
        )
        resp = client.get(f"/api/module/{modul['id']}", headers=auth_header)
        body = resp.get_json()
        assert body["zulassung"] is True  # 11/20 = 55%

    def test_create_series_with_total_weeks_prefills_submissions(self, client, auth_header):
        sg = create_studiengang(client, auth_header).get_json()
        modul = create_modul(client, auth_header, [sg["id"]]).get_json()

        resp = client.post(
            f"/api/module/{modul['id']}/series",
            json={"name": "Problem Set", "total_weeks": 13, "points_per_week": 10},
            headers=auth_header,
        )
        series = resp.get_json()["series"][0]
        assert len(series["submissions"]) == 13
        assert [s["week_number"] for s in series["submissions"]] == list(range(1, 14))
        assert all(s["points_achieved"] == 0 and s["points_max"] == 10 for s in series["submissions"])
        assert series["progress"]["percent"] == 0

    def test_create_series_total_weeks_requires_points_per_week(self, client, auth_header):
        sg = create_studiengang(client, auth_header).get_json()
        modul = create_modul(client, auth_header, [sg["id"]]).get_json()
        resp = client.post(
            f"/api/module/{modul['id']}/series",
            json={"name": "Problem Set", "total_weeks": 13},
            headers=auth_header,
        )
        assert resp.status_code == 400

    def test_create_series_without_total_weeks_has_no_prefill(self, client, auth_header):
        sg = create_studiengang(client, auth_header).get_json()
        modul = create_modul(client, auth_header, [sg["id"]]).get_json()
        resp = client.post(
            f"/api/module/{modul['id']}/series",
            json={"name": "Problem Set"},
            headers=auth_header,
        )
        assert resp.get_json()["series"][0]["submissions"] == []

    def test_graded_defaults_true_and_is_toggleable(self, client, auth_header):
        sg = create_studiengang(client, auth_header).get_json()
        resp = create_modul(client, auth_header, [sg["id"]])
        modul = resp.get_json()
        assert modul["graded"] is True

        resp = client.patch(
            f"/api/module/{modul['id']}", json={"graded": False}, headers=auth_header
        )
        assert resp.status_code == 200
        assert resp.get_json()["graded"] is False

    def test_ungraded_module_rejects_numeric_grade(self, client, auth_header):
        sg = create_studiengang(client, auth_header).get_json()
        resp = client.post(
            "/api/module",
            json={"name": "Spanisch A1", "credits": 3, "studiengang_ids": [sg["id"]], "graded": False},
            headers=auth_header,
        )
        modul = resp.get_json()
        resp = client.post(
            f"/api/module/{modul['id']}/grades",
            json={"slot": 1, "kind": "numeric", "value": 1.7},
            headers=auth_header,
        )
        assert resp.status_code == 400

    def test_ungraded_module_allows_pass_fail(self, client, auth_header):
        sg = create_studiengang(client, auth_header).get_json()
        resp = client.post(
            "/api/module",
            json={"name": "Spanisch A1", "credits": 3, "studiengang_ids": [sg["id"]], "graded": False},
            headers=auth_header,
        )
        modul = resp.get_json()
        resp = client.post(
            f"/api/module/{modul['id']}/grades",
            json={"slot": 1, "kind": "pass"},
            headers=auth_header,
        )
        assert resp.status_code == 200
        assert resp.get_json()["final_grade"] == {"status": "passed", "value": None}

    def test_cannot_mark_module_ungraded_with_existing_numeric_grade(self, client, auth_header):
        sg = create_studiengang(client, auth_header).get_json()
        modul = create_modul(client, auth_header, [sg["id"]]).get_json()
        client.post(
            f"/api/module/{modul['id']}/grades",
            json={"slot": 1, "kind": "numeric", "value": 1.7},
            headers=auth_header,
        )
        resp = client.patch(
            f"/api/module/{modul['id']}", json={"graded": False}, headers=auth_header
        )
        assert resp.status_code == 400

    def test_ungraded_module_credits_count_towards_total_not_average(self, client, auth_header):
        sg = create_studiengang(client, auth_header).get_json()
        graded_modul = create_modul(client, auth_header, [sg["id"]], "Analysis I", 9).get_json()
        client.post(
            f"/api/module/{graded_modul['id']}/grades",
            json={"slot": 1, "kind": "numeric", "value": 2.0},
            headers=auth_header,
        )
        resp = client.post(
            "/api/module",
            json={"name": "Spanisch A1", "credits": 3, "studiengang_ids": [sg["id"]], "graded": False},
            headers=auth_header,
        )
        ungraded_modul = resp.get_json()
        client.post(
            f"/api/module/{ungraded_modul['id']}/grades",
            json={"slot": 1, "kind": "pass"},
            headers=auth_header,
        )

        resp = client.get("/api/stats/overview", headers=auth_header)
        sg_stats = resp.get_json()["studiengaenge"][0]
        assert sg_stats["average"] == 2.0  # only the graded module counts
        assert sg_stats["graded_credits"] == 9
        assert sg_stats["ungraded_pass_credits"] == 3
        assert sg_stats["total_credits"] == 12


class TestKombiModul:
    def test_combined_grade_is_average_of_sources(self, client, auth_header):
        mathe = create_studiengang(client, auth_header, "Mathematik").get_json()
        physik = create_studiengang(client, auth_header, "Physik").get_json()
        analysis = create_modul(client, auth_header, [mathe["id"]], "Analysis I", 9).get_json()
        linalg = create_modul(client, auth_header, [mathe["id"]], "Lineare Algebra I", 9).get_json()

        client.post(
            f"/api/module/{analysis['id']}/grades",
            json={"slot": 1, "kind": "numeric", "value": 1.0},
            headers=auth_header,
        )
        client.post(
            f"/api/module/{linalg['id']}/grades",
            json={"slot": 1, "kind": "numeric", "value": 2.0},
            headers=auth_header,
        )

        resp = client.post(
            "/api/kombimodule",
            json={
                "name": "Math for Physicists",
                "credits": 14,
                "studiengang_id": physik["id"],
                "source_module_ids": [analysis["id"], linalg["id"]],
            },
            headers=auth_header,
        )
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["final_grade"] == {"status": "numeric", "value": 1.5}
        assert body["graded"] is True

    def test_zero_sources_rejected(self, client, auth_header):
        sg = create_studiengang(client, auth_header).get_json()
        resp = client.post(
            "/api/kombimodule",
            json={"name": "X", "credits": 5, "studiengang_id": sg["id"], "source_module_ids": []},
            headers=auth_header,
        )
        assert resp.status_code == 400

    def test_single_source_module_allowed(self, client, auth_header):
        """Re-crediting one module under different credits via its own
        combined module - e.g. a module recognized from another program
        with fewer credits than it's worth there."""
        sg = create_studiengang(client, auth_header).get_json()
        other_sg = create_studiengang(client, auth_header, "Physik").get_json()
        modul = create_modul(client, auth_header, [sg["id"]], "Analysis I", 9).get_json()
        client.post(
            f"/api/module/{modul['id']}/grades",
            json={"slot": 1, "kind": "numeric", "value": 1.7},
            headers=auth_header,
        )

        resp = client.post(
            "/api/kombimodule",
            json={
                "name": "Analysis (angerechnet)",
                "credits": 4,
                "studiengang_id": other_sg["id"],
                "source_module_ids": [modul["id"]],
            },
            headers=auth_header,
        )
        assert resp.status_code == 201
        assert resp.get_json()["final_grade"] == {"status": "numeric", "value": 1.7}

    def test_graded_defaults_true_and_is_toggleable(self, client, auth_header):
        sg = create_studiengang(client, auth_header).get_json()
        modul = create_modul(client, auth_header, [sg["id"]]).get_json()

        resp = client.post(
            "/api/kombimodule",
            json={"name": "X", "credits": 5, "studiengang_id": sg["id"], "source_module_ids": [modul["id"]]},
            headers=auth_header,
        )
        kombi = resp.get_json()
        assert kombi["graded"] is True

        resp = client.patch(
            f"/api/kombimodule/{kombi['id']}", json={"graded": False}, headers=auth_header
        )
        assert resp.status_code == 200
        assert resp.get_json()["graded"] is False

    def test_ungraded_kombimodul_passes_once_all_sources_pass(self, client, auth_header):
        mathe = create_studiengang(client, auth_header, "Mathematik").get_json()
        physik = create_studiengang(client, auth_header, "Physik").get_json()
        analysis = create_modul(client, auth_header, [mathe["id"]], "Analysis I", 9).get_json()
        linalg = create_modul(client, auth_header, [mathe["id"]], "Lineare Algebra I", 9).get_json()

        resp = client.post(
            "/api/kombimodule",
            json={
                "name": "Math for Physicists",
                "credits": 14,
                "studiengang_id": physik["id"],
                "source_module_ids": [analysis["id"], linalg["id"]],
                "graded": False,
            },
            headers=auth_header,
        )
        kombi_id = resp.get_json()["id"]
        assert resp.get_json()["final_grade"] == {"status": "none", "value": None}

        client.post(
            f"/api/module/{analysis['id']}/grades",
            json={"slot": 1, "kind": "numeric", "value": 1.7},
            headers=auth_header,
        )
        client.post(
            f"/api/module/{linalg['id']}/grades",
            json={"slot": 1, "kind": "pass"},
            headers=auth_header,
        )

        resp = client.get(f"/api/kombimodule/{kombi_id}", headers=auth_header)
        assert resp.get_json()["final_grade"] == {"status": "passed", "value": None}

    def test_ungraded_kombimodul_fails_if_a_source_fails(self, client, auth_header):
        mathe = create_studiengang(client, auth_header, "Mathematik").get_json()
        physik = create_studiengang(client, auth_header, "Physik").get_json()
        analysis = create_modul(client, auth_header, [mathe["id"]], "Analysis I", 9).get_json()
        linalg = create_modul(client, auth_header, [mathe["id"]], "Lineare Algebra I", 9).get_json()
        client.post(
            f"/api/module/{analysis['id']}/grades",
            json={"slot": 1, "kind": "numeric", "value": 1.7},
            headers=auth_header,
        )
        client.post(
            f"/api/module/{linalg['id']}/grades",
            json={"slot": 1, "kind": "fail"},
            headers=auth_header,
        )

        resp = client.post(
            "/api/kombimodule",
            json={
                "name": "Math for Physicists",
                "credits": 14,
                "studiengang_id": physik["id"],
                "source_module_ids": [analysis["id"], linalg["id"]],
                "graded": False,
            },
            headers=auth_header,
        )
        assert resp.get_json()["final_grade"] == {"status": "failed", "value": None}

    def test_ungraded_kombimodul_excluded_from_overview_average(self, client, auth_header):
        """Regression test: /api/stats/overview used to recompute every
        KombiModul's grade with the default graded=True, ignoring its
        actual `graded` flag - an ungraded, passed combined module would
        silently pull a "passed" (non-numeric) entry into what should have
        been a plain numeric average, and worse, once it had a numeric
        source average of its own it would count as graded credits."""
        mathe = create_studiengang(client, auth_header, "Mathematik").get_json()
        physik = create_studiengang(client, auth_header, "Physik").get_json()
        analysis = create_modul(client, auth_header, [mathe["id"]], "Analysis I", 9).get_json()
        linalg = create_modul(client, auth_header, [mathe["id"]], "Lineare Algebra I", 9).get_json()
        client.post(
            f"/api/module/{analysis['id']}/grades",
            json={"slot": 1, "kind": "numeric", "value": 1.7},
            headers=auth_header,
        )
        client.post(
            f"/api/module/{linalg['id']}/grades",
            json={"slot": 1, "kind": "numeric", "value": 2.3},
            headers=auth_header,
        )
        client.post(
            "/api/kombimodule",
            json={
                "name": "Math for Physicists",
                "credits": 14,
                "studiengang_id": physik["id"],
                "source_module_ids": [analysis["id"], linalg["id"]],
                "graded": False,
            },
            headers=auth_header,
        )

        resp = client.get("/api/stats/overview", headers=auth_header)
        overview = resp.get_json()
        physik_stats = next(s for s in overview["studiengaenge"] if s["name"] == "Physik")
        assert physik_stats["average"] is None  # no graded entries in this program
        assert physik_stats["graded_credits"] == 0
        assert physik_stats["ungraded_pass_credits"] == 14


class TestStatsOverview:
    def test_overview_reports_weighted_average(self, client, auth_header):
        sg = create_studiengang(client, auth_header).get_json()
        m1 = create_modul(client, auth_header, [sg["id"]], "A", 9).get_json()
        m2 = create_modul(client, auth_header, [sg["id"]], "B", 6).get_json()
        client.post(f"/api/module/{m1['id']}/grades", json={"slot": 1, "kind": "numeric", "value": 1.0}, headers=auth_header)
        client.post(f"/api/module/{m2['id']}/grades", json={"slot": 1, "kind": "numeric", "value": 2.5}, headers=auth_header)

        resp = client.get("/api/stats/overview", headers=auth_header)
        assert resp.status_code == 200
        body = resp.get_json()
        sg_stats = body["studiengaenge"][0]
        expected = (9 * 1.0 + 6 * 2.5) / 15
        assert sg_stats["average"] == expected
        assert sg_stats["total_credits"] == 15


class TestUserIsolation:
    def _other_user_header(self, client):
        resp = client.post(
            "/api/auth/register",
            json={"username": "otheruser", "email": "other@example.com", "password": "otherpass123"},
        )
        return {"Authorization": f"Bearer {resp.get_json()['token']}"}

    def test_users_cannot_see_each_others_studiengaenge(self, client, auth_header):
        create_studiengang(client, auth_header, "Mathematik")
        other_header = self._other_user_header(client)

        resp = client.get("/api/studiengaenge", headers=other_header)
        assert resp.get_json() == []

    def test_users_cannot_access_each_others_module_by_id(self, client, auth_header):
        sg = create_studiengang(client, auth_header).get_json()
        modul = create_modul(client, auth_header, [sg["id"]]).get_json()
        other_header = self._other_user_header(client)

        resp = client.get(f"/api/module/{modul['id']}", headers=other_header)
        assert resp.status_code == 404
