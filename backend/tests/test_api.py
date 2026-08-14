def create_studiengang(client, name="Mathematik"):
    return client.post("/api/studiengaenge", json={"name": name})


def create_modul(client, studiengang_id, name="Analysis I", credits=9):
    return client.post(
        "/api/module", json={"name": name, "credits": credits, "studiengang_id": studiengang_id}
    )


class TestStudiengaenge:
    def test_create_and_list(self, client):
        resp = create_studiengang(client)
        assert resp.status_code == 201
        assert resp.get_json()["name"] == "Mathematik"

        resp = client.get("/api/studiengaenge")
        assert resp.status_code == 200
        assert len(resp.get_json()) == 1

    def test_duplicate_name_rejected(self, client):
        create_studiengang(client)
        resp = create_studiengang(client)
        assert resp.status_code == 409

    def test_reserved_sonstiges_rejected(self, client):
        resp = create_studiengang(client, name="Sonstiges")
        assert resp.status_code == 400

    def test_delete_sets_module_to_sonstiges(self, client):
        sg = create_studiengang(client).get_json()
        modul = create_modul(client, sg["id"]).get_json()

        client.delete(f"/api/studiengaenge/{sg['id']}")

        resp = client.get(f"/api/module/{modul['id']}")
        assert resp.get_json()["studiengang_id"] is None


class TestModule:
    def test_create_modul_in_sonstiges(self, client):
        resp = client.post("/api/module", json={"name": "Spanisch A1", "credits": 3})
        assert resp.status_code == 201
        assert resp.get_json()["studiengang_id"] is None

    def test_missing_credits_rejected(self, client):
        resp = client.post("/api/module", json={"name": "X"})
        assert resp.status_code == 400

    def test_grade_attempt_upsert_and_final_grade(self, client):
        sg = create_studiengang(client).get_json()
        modul = create_modul(client, sg["id"]).get_json()

        resp = client.post(f"/api/module/{modul['id']}/grades", json={"slot": 1, "kind": "numeric", "value": 2.3})
        assert resp.status_code == 200
        assert resp.get_json()["final_grade"] == {"status": "numeric", "value": 2.3}

        resp = client.post(f"/api/module/{modul['id']}/grades", json={"slot": 2, "kind": "numeric", "value": 1.7})
        assert resp.get_json()["final_grade"] == {"status": "numeric", "value": 1.7}

        # re-upsert slot 1 overwrites rather than duplicating
        client.post(f"/api/module/{modul['id']}/grades", json={"slot": 1, "kind": "numeric", "value": 1.0})
        resp = client.get(f"/api/module/{modul['id']}")
        assert len(resp.get_json()["grade_attempts"]) == 2

    def test_invalid_grade_value_rejected(self, client):
        sg = create_studiengang(client).get_json()
        modul = create_modul(client, sg["id"]).get_json()
        resp = client.post(f"/api/module/{modul['id']}/grades", json={"slot": 1, "kind": "numeric", "value": 9.0})
        assert resp.status_code == 400

    def test_series_and_submission_zulassung(self, client):
        sg = create_studiengang(client).get_json()
        modul = create_modul(client, sg["id"]).get_json()

        series = client.post(
            f"/api/module/{modul['id']}/series", json={"name": "Rechenblatt", "threshold_percent": 50}
        ).get_json()["series"][0]

        client.post(f"/api/series/{series['id']}/submissions", json={"week_number": 1, "points_achieved": 3, "points_max": 10})
        resp = client.get(f"/api/module/{modul['id']}")
        body = resp.get_json()
        assert body["zulassung"] is False
        assert body["series"][0]["progress"]["points_needed"] == 2  # need 5, have 3

        client.post(f"/api/series/{series['id']}/submissions", json={"week_number": 2, "points_achieved": 8, "points_max": 10})
        resp = client.get(f"/api/module/{modul['id']}")
        body = resp.get_json()
        assert body["zulassung"] is True  # 11/20 = 55%


class TestKombiModul:
    def test_combined_grade_is_average_of_sources(self, client):
        mathe = create_studiengang(client, "Mathematik").get_json()
        physik = create_studiengang(client, "Physik").get_json()
        analysis = create_modul(client, mathe["id"], "Analysis I", 9).get_json()
        linalg = create_modul(client, mathe["id"], "Lineare Algebra I", 9).get_json()

        client.post(f"/api/module/{analysis['id']}/grades", json={"slot": 1, "kind": "numeric", "value": 1.0})
        client.post(f"/api/module/{linalg['id']}/grades", json={"slot": 1, "kind": "numeric", "value": 2.0})

        resp = client.post(
            "/api/kombimodule",
            json={
                "name": "Mathe für Physiker",
                "credits": 14,
                "studiengang_id": physik["id"],
                "source_module_ids": [analysis["id"], linalg["id"]],
            },
        )
        assert resp.status_code == 201
        assert resp.get_json()["final_grade"] == {"status": "numeric", "value": 1.5}

    def test_needs_at_least_two_sources(self, client):
        sg = create_studiengang(client).get_json()
        modul = create_modul(client, sg["id"]).get_json()
        resp = client.post(
            "/api/kombimodule",
            json={"name": "X", "credits": 5, "studiengang_id": sg["id"], "source_module_ids": [modul["id"]]},
        )
        assert resp.status_code == 400


class TestStatsOverview:
    def test_overview_reports_weighted_average(self, client):
        sg = create_studiengang(client).get_json()
        m1 = create_modul(client, sg["id"], "A", 9).get_json()
        m2 = create_modul(client, sg["id"], "B", 6).get_json()
        client.post(f"/api/module/{m1['id']}/grades", json={"slot": 1, "kind": "numeric", "value": 1.0})
        client.post(f"/api/module/{m2['id']}/grades", json={"slot": 1, "kind": "numeric", "value": 2.5})

        resp = client.get("/api/stats/overview")
        assert resp.status_code == 200
        body = resp.get_json()
        sg_stats = body["studiengaenge"][0]
        expected = (9 * 1.0 + 6 * 2.5) / 15
        assert sg_stats["average"] == expected
        assert sg_stats["total_credits"] == 15
