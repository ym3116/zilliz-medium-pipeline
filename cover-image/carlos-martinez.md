# Cover Image Style — Carlos Martinez

## General Constraints (apply to all personas)
- Landscape format, exactly 10:8 aspect ratio (e.g., 1280×1024 pixels)
- No Zilliz or Milvus logos anywhere in the image
- No readable brand names or product names
- Comic style with high-tech feel, rich visual elements

## Carlos Martinez Visual Identity

**Color Palette**
- Primary: near-black charcoal (#0D1117), terminal green (#00FF41), amber alert (#FFA500)
- Accents: steel blue (#4488AA), electric white (#F0F0F0) for highlights
- Dark ops-center aesthetic — Carlos's world is production, reliability, and scale

**Visual Elements (mix and match based on article topic)**
- Kubernetes cluster: hexagonal pod icons arranged in a grid, some active (green glow), some in warning state (amber), connected by network lines
- Kafka pipeline: message queue with stacked message envelopes flowing through partitioned topics, consumer group icons downstream
- ETL pipeline: data flowing from source boxes → transformation gears → sink databases, shown as a side-scrolling diagram
- Server infrastructure: rack-mounted servers in isometric view, LED status lights, cable bundles, cooling fans
- Monitoring dashboard: abstract Grafana-style panels with metric lines, spike events highlighted in amber/red, p99 latency curves
- Data lake architecture: layered storage zones (bronze/silver/gold layers), file icons, transformation arrows
- Deployment: Helm chart deployments shown as packaging boxes being deployed onto Kubernetes pods
- Failure/incident: warning triangles, red alert indicators, a timeline showing incident and recovery — ops war story feel
- Distributed system: multiple nodes in a cluster map with data replication arrows, partition leader indicators

**Composition Style**
- Dense, technical, information-rich — feels like a war room or NOC display
- Dark background with glowing green and amber elements
- Grid-based layout: feels like monitoring panels or infrastructure diagrams
- Hard edges, precise geometry, no softness
- Terminal/console aesthetic for small secondary details

**Comic Style Details**
- High contrast — dark backgrounds, bright neon highlights
- Matrix-style data streams in background (subtle)
- Bold, industrial linework
- Alert badges and status indicators as visual decoration
- Feels like a developer who runs things at 3am would recognize it

## Prompt Template

Build the DALL-E prompt using this structure:

```
A wide landscape comic-style cover illustration for a technical DevOps/data infrastructure article about [TOPIC].
The scene shows [2-3 SPECIFIC VISUAL ELEMENTS chosen from the list above, tailored to the topic].
Color palette: near-black charcoal background, terminal green and amber highlights, steel blue accents, high contrast neon glow.
Style: dark industrial comic art, ops-center aesthetic, dense technical diagram feel, high contrast, precise bold linework.
No text, no logos, no brand names. Rich in infrastructure and systems detail, serious production engineering feel.
```
