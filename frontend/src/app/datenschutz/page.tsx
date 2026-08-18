import Link from "next/link";
import { Card } from "@/components/Card";

export const metadata = { title: "Datenschutzerklärung – Grade Tracker" };

export default function DatenschutzPage() {
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-2xl font-semibold text-text-primary">
        Datenschutzerklärung
      </h1>

      <Card className="border-status-warning/40">
        <p className="text-sm text-status-warning">
          <strong>TODO vor Live-Betrieb:</strong> Verantwortlicher und
          Hosting-/Mail-Anbieter (<code>[…]</code>) unten eintragen. Der Rest
          beschreibt, was diese Anwendung technisch tatsächlich speichert und
          verarbeitet.
        </p>
      </Card>

      <Card className="space-y-4 text-sm text-text-secondary">
        <section>
          <h2 className="mb-1 font-semibold text-text-primary">
            Verantwortlicher
          </h2>
          <p>
            [Vor- und Nachname]
            <br />
            [Straße Hausnummer, PLZ Ort]
            <br />
            E-Mail: [kontakt@example.com]
          </p>
        </section>

        <section>
          <h2 className="mb-1 font-semibold text-text-primary">
            Welche Daten wir verarbeiten
          </h2>
          <ul className="list-disc space-y-1 pl-5">
            <li>
              <strong>Account:</strong> Nutzername, E-Mail-Adresse,
              Passwort (als Hash, niemals im Klartext gespeichert)
            </li>
            <li>
              <strong>Fachliche Daten:</strong> die von dir eingetragenen
              Studiengänge, Module, Noten und Punktestände - ausschließlich
              für dich sichtbar
            </li>
            <li>
              <strong>Verifizierungscodes</strong> für E-Mail-Bestätigung und
              Passwort-Reset (als Hash, 15 Minuten gültig, danach ungültig)
            </li>
            <li>
              <strong>IP-Adresse:</strong> kurzzeitig zur Missbrauchserkennung
              (Rate-Limiting bei Login/Registrierung), nicht dauerhaft
              gespeichert
            </li>
            <li>
              <strong>Login-Token:</strong> wird nach dem Login lokal in
              deinem Browser (localStorage) gespeichert, nicht auf dem Server
            </li>
          </ul>
        </section>

        <section>
          <h2 className="mb-1 font-semibold text-text-primary">
            Zweck und Rechtsgrundlage
          </h2>
          <p>
            Die Verarbeitung erfolgt zur Bereitstellung des Dienstes (Art. 6
            Abs. 1 lit. b DSGVO - Vertragserfüllung) sowie zum Schutz vor
            Missbrauch, z. B. automatisierten Anmeldeversuchen (Art. 6 Abs. 1
            lit. f DSGVO - berechtigtes Interesse).
          </p>
        </section>

        <section>
          <h2 className="mb-1 font-semibold text-text-primary">
            E-Mail-Versand
          </h2>
          <p>
            Für Verifizierungs- und Reset-Codes wird deine E-Mail-Adresse an
            unseren E-Mail-Versanddienstleister [Name des SMTP-/Mail-Anbieters]
            übermittelt.
          </p>
        </section>

        <section>
          <h2 className="mb-1 font-semibold text-text-primary">Hosting</h2>
          <p>
            Diese Anwendung läuft auf Servern von [Name des
            Hosting-Anbieters, Standort].
          </p>
        </section>

        <section>
          <h2 className="mb-1 font-semibold text-text-primary">
            Cookies & Tracking
          </h2>
          <p>
            Es werden keine Cookies und kein Tracking durch Dritte
            eingesetzt.
          </p>
        </section>

        <section>
          <h2 className="mb-1 font-semibold text-text-primary">
            Speicherdauer
          </h2>
          <p>
            Deine Daten bleiben gespeichert, bis du dein Konto löschst. Die
            Löschung kannst du jederzeit selbst in den Account-Einstellungen
            auslösen; sie entfernt Account und alle zugehörigen Daten
            unwiderruflich und sofort.
          </p>
        </section>

        <section>
          <h2 className="mb-1 font-semibold text-text-primary">
            Deine Rechte
          </h2>
          <p>
            Du hast das Recht auf Auskunft, Berichtigung, Löschung,
            Einschränkung der Verarbeitung, Datenübertragbarkeit und
            Widerspruch (Art. 15-21 DSGVO). Wende dich dazu an die oben
            genannte Kontaktadresse. Außerdem hast du das Recht, dich bei
            einer Datenschutzaufsichtsbehörde zu beschweren.
          </p>
        </section>
      </Card>

      <p className="text-sm text-text-secondary">
        <Link href="/impressum" className="text-series-1 hover:underline">
          Impressum
        </Link>
      </p>
    </div>
  );
}
