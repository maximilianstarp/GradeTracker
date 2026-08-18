import Link from "next/link";
import { Card } from "@/components/Card";

export const metadata = { title: "Impressum – Grade Tracker" };

export default function ImpressumPage() {
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-2xl font-semibold text-text-primary">Impressum</h1>

      <Card className="space-y-4 text-sm text-text-secondary">
        <section>
          <h2 className="mb-1 font-semibold text-text-primary">
            Angaben gemäß § 5 TMG
          </h2>
          <p>
            Maximilian Starp
            <br />
            Robert-Havemann-Str. 3
            <br />
            53121 Bonn
          </p>
        </section>

        <section>
          <h2 className="mb-1 font-semibold text-text-primary">Kontakt</h2>
          <p>E-Mail: maximilian@starp.email</p>
        </section>

        <section>
          <h2 className="mb-1 font-semibold text-text-primary">
            Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV
          </h2>
          <p>Maximilian Starp, Anschrift wie oben</p>
        </section>

        <section>
          <h2 className="mb-1 font-semibold text-text-primary">Hosting</h2>
          <p>
            Diese Anwendung wird bei Hetzner Online GmbH, Industriestr. 25,
            91710 Gunzenhausen, betrieben.
          </p>
        </section>

        <section>
          <h2 className="mb-1 font-semibold text-text-primary">
            Haftungsausschluss
          </h2>
          <p>
            Trotz sorgfältiger inhaltlicher Kontrolle übernehmen wir keine
            Haftung für die Inhalte externer Links. Für den Inhalt der
            verlinkten Seiten sind ausschließlich deren Betreiber
            verantwortlich.
          </p>
        </section>
      </Card>

      <p className="text-sm text-text-secondary">
        <Link href="/datenschutz" className="text-series-1 hover:underline">
          Datenschutzerklärung
        </Link>
      </p>
    </div>
  );
}
