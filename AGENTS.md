# AGENTS.md

- If using XcodeBuildMCP, use the installed XcodeBuildMCP skill before calling XcodeBuildMCP tools.

## Rechte, Beiträge und neue Abhängigkeiten

- Vor neuen/importierten Abhängigkeiten, kopiertem Code, Fonts, Medien oder
  Binärartefakten [`RIGHTS.md`](RIGHTS.md) und
  [`docs/licensing/README.md`](docs/licensing/README.md) lesen.
- Eigene Beiträge, Swiftfin-Bestand und Drittcode getrennt nachweisen. Ein CLA
  überträgt keine fremden Rechte; frühere Beiträge gelten nicht rückwirkend als
  unterschrieben. Vorhandene Lizenz-/Copyright-Hinweise erhalten.
- Neue oder geänderte Abhängigkeiten einschließlich transitiver Lockfile- und
  Build-Recipe-Änderungen brauchen einen belegten Eintrag in
  `docs/licensing/dependencies.json`. Hashes nicht lediglich aktualisieren,
  um die Prüfung grün zu machen. Ungeklärte Auslieferungspflichten als
  Release-Blocker dokumentieren und auflösen, nicht als freigegeben markieren.
- `python3 Tools/licensing/verify-rights.py` muss vor Abschluss bestehen;
  vor Paketierung/Veröffentlichung zusätzlich `--release`. Neue Bezugspfade
  oder Paketmanager auch in Erkennung und Tests der Prüfung aufnehmen.
- Neue externe Originalbeiträge benötigen die tatsächliche CLA-Annahme;
  keine Unterschriften oder Rechtebestätigungen für Dritte erfinden.
