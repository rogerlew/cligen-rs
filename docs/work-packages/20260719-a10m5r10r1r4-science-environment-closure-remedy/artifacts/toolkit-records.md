# Toolkit records

- Authority revision: `0b9bc39625cb164c6ca7720e2ea634179195cdda7a9d6051eb7ae0436377634e`.
- Plan: `cdce8b81b4bf355278dc77c0b011dfac1849b25090d077fc3b13aab0e6c56d16`.
- Published source: `decbe1ababddaf54a3c0cbd88b6f5b1cdb847937` on `main`.
- Authenticated collection: 6,952,960 bytes, SHA-256
  `aa83f2d047a30ae2ac8412fdeb5fe33fcdb6e43407405aa235180d3d6d6b8483`;
  153 present, zero absent.
- Collection record: SHA-256
  `f451beedca28374897395415b71910f3369b7a62209c9530a592d2d4474102b4`.
- Cleanup receipt: record
  `fd3381519e40c4265daca40c47b5789df395cfb295cb6f861b418d7b5bed23f7`,
  committed file
  `e02efb3ae41570f4aed283e0a653271b7c29fc5cd505d6517179c23a4cb0fcc1`.
- Terminal receipt: record
  `7aa1734918fea333ef0832478437ed22e1b31fabcb8a687e9330ab62c6853804`,
  committed file
  `e45f6335cc96d61458e85055c252e0f5fd36e39581471fd28b9f5845d63eb0be`.
- Final toolkit terminal: `LEMHI-TOOLKIT-RUN-CLOSED`, 11 attempts, no stopped
  role, verified job-local and durable-root absence.

The selector was run twice against the unchanged raw result tree before exact
root cleanup. Both runs emitted `A10M5R10-PORTFOLIO-SELECTOR-SELF-TEST-PASS`
and `A10M5R10-PORTFOLIO-READY`; comparison, decision, selection-evidence, and
Pareto files were byte-identical between runs. The toolkit collection then
authenticated the complete allowlisted archive and projected its contents into
the committed public evidence surface. Projected path-bearing metadata is not
fed back through the selector because redaction necessarily changes the
control-summary digest bound by each candidate.
