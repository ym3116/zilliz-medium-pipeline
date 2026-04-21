# Cover Image Style — Alex Chen

## General Constraints (apply to all personas)
- Landscape format, exactly 10:8 aspect ratio (e.g., 1280×1024 pixels)
- No Zilliz or Milvus logos anywhere in the image
- No readable brand names or product names
- Comic style with high-tech feel, rich visual elements

## Alex Chen Visual Identity

**Color Palette**
- Primary: deep navy (#0B1929), electric blue (#00A8FF), cyan (#00FFF5)
- Accents: silver-white (#E8F4F8), cool gray (#4A6B8A)
- No warm tones — Alex's world is cold, precise, and technical

**Visual Elements (mix and match based on article topic)**
- Graph data structures: nodes connected by edges, clearly drawn in network form (HNSW-style layered graphs, Vamana graph connectivity diagrams)
- Database internals: layered storage diagrams, WAL logs, LSM trees, segment blocks, index structures
- Performance charts: benchmark curves, latency histograms, memory-usage bars — drawn in infographic/comic style
- Server and hardware: SSD chips, NVMe drive cross-sections, RAM sticks, abstract server clusters
- Code panels: faint Go or Python code snippets visible in background panels, slightly out-of-focus
- Data flow: vectors as glowing points moving through a pipeline or graph, with arrows showing direction
- Abstract: isometric 3D grids, circuit board traces, binary rain in background (subtle)

**Composition Style**
- Clean, structured, isometric or flat-3D perspective
- Precise linework — feels engineered, not artistic
- Main focal element is large and central; supporting elements fill the frame
- No human figures; all abstract and data-centric
- Slight dark vignette on edges; the center glows

**Comic Style Details**
- Bold outlines on key elements
- Halftone dot patterns in shadow areas
- Speed lines on data flows
- Panel-style layout with 2–3 distinct visual zones if the composition allows

## Prompt Template

Build the DALL-E prompt using this structure:

```
A wide landscape comic-style cover illustration for a technical engineering article about [TOPIC].
The scene shows [2-3 SPECIFIC VISUAL ELEMENTS chosen from the list above, tailored to the topic].
Color palette: deep navy background, electric blue and cyan highlights, silver-white details.
Style: high-tech comic art, isometric 3D elements, precise linework, bold outlines, halftone shading.
No text, no logos, no brand names. Rich in visual detail, futuristic database engineering aesthetic.
```
