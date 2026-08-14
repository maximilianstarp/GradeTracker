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
        assert resp.get_json()["final_grade"] == {"status": "numeric", "value": 1.5}

    def test_needs_at_least_two_sources(self, client, auth_header):
        sg = create_studiengang(client, auth_header).get_json()
        modul = create_modul(client, auth_header, [sg["id"]]).get_json()
        resp = client.post(
            "/api/kombimodule",
            json={"name": "X", "credits": 5, "studiengang_id": sg["id"], "source_module_ids": [modul["id"]]},
            headers=auth_header,
        )
        assert resp.status_code == 400


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
            json={"name": "Other User", "email": "other@example.com", "password": "otherpass123"},
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
