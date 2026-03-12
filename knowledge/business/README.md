# knowledge/business/ -- Business Intelligence Bucket

The third knowledge bucket in Mega Brain's architecture. This directory stores business intelligence gathered from internal meetings, calls, recordings, and day-to-day operations. Unlike `knowledge/external/` (expert knowledge from courses and mentors) and `knowledge/personal/` (private cognitive data), this bucket captures organizational knowledge that emerges from the company's own activities -- decisions made, people involved, themes discussed, and standard operating procedures distilled from real operations.

## Directory Structure

```
knowledge/business/
├── inbox/                  <- Raw business materials (L3, gitignored)
│   ├── calls/              <- Call transcripts and notes
│   ├── recordings/         <- Meeting recordings (audio/video refs)
│   ├── documents/          <- Business documents, decks, reports
│   └── screenshots/        <- Visual captures from tools/dashboards
├── people/                 <- People profiles (internal + external contacts)
├── dossiers/               <- Consolidated intelligence dossiers
│   ├── companies/          <- Company-level dossiers (clients, partners, competitors)
│   ├── operations/         <- Operational area dossiers (sales ops, marketing ops, etc.)
│   └── themes/             <- Theme-based dossiers (pricing strategy, hiring, etc.)
├── insights/               <- Extracted insights organized by dimension
│   ├── by-meeting/         <- Insights grouped by meeting/call
│   ├── by-person/          <- Insights grouped by person discussed
│   └── by-theme/           <- Insights grouped by business theme
├── narratives/             <- Cross-referenced narrative summaries
│   ├── cross-person/       <- Narratives spanning multiple people
│   └── by-person/          <- Person-specific narrative arcs
├── decisions/              <- Decision log (what was decided, by whom, why)
└── sops/                   <- Standard Operating Procedures distilled from operations
```
