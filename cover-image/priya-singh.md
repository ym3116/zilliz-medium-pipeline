# Cover Image Style — Priya Singh

## General Constraints (apply to all personas)
- Landscape format, exactly 10:8 aspect ratio (e.g., 1280×1024 pixels)
- No Zilliz or Milvus logos anywhere in the image
- No readable brand names or product names
- Comic style with high-tech feel, rich visual elements

## Priya Singh Visual Identity

**Color Palette**
- Primary: vivid magenta (#FF2D9B), electric lime (#B2FF00), neon cyan (#00FFF5)
- Accents: bright sky blue (#00CFFF), sunny yellow (#FFE600), bright white (#FFFFFF)
- Background: smoky violet / frosted purple — choose from:
    - Smoky violet (#6B5B8C / #7A6B9D) — violet behind frosted glass
    - Hazy purple (#8777A8) — soft, veiled quality
    - Frosted violet (#8B7BA8) — classic frosted-glass feel
    - Ashen purple (#7D6F94) — gray-tinged, refined
  Use a gradient from one of these to a slightly darker shade. The effect is a dark purple seen through fog or frosted glass — NOT a pure dark background, NOT a bright background. Muted, hazy, sophisticated.
- The neon accent colors (magenta, lime, cyan) POP against this muted purple background

**Big Center Text**
- A large, bold, comic-book style word or short phrase dominates the center of the image
- The text should feel like a comic splash page — thick outlines, bold shadows, dynamic angle
- Examples of the kind of text style: "AI", "RAG", "VECTOR", "DATA", "EMBED", "NEURAL" — in massive, stylized comic lettering
- The word fills roughly 30–40% of the image width
- Text has a bright fill with thick dark outline and a drop shadow or halftone shadow
- Text can be slightly tilted for energy (5–15 degrees)
- This is the visual anchor of the entire composition

**Visual Elements (mix and match based on article topic)**
- Neural network layers: brightly colored node-and-edge diagrams with glowing connections, drawn in vivid neon on the light background
- Embedding space: colorful 3D scatter clusters with bright point markers, floating in the composition
- RAG pipeline: document icons → chunking → bright vector arrows → retrieval box → answer bubble, as a flowing diagram
- LLM/Transformer internals: bright attention grids, stacked transformer blocks in bold candy colors
- Data sources: floating document pages, image thumbnails, code panels — all rendered in bright saturated colors
- Chatbot interface: bold conversation bubbles with faint code inside, a glowing "brain" icon in bright colors
- Speed lines and action bursts radiating outward from the center text
- Halftone dot patterns in background panels for classic comic texture
- Comic panel borders framing different visual zones

**Composition Style**
- FROSTED DARK — the background is a hazy, smoky purple (frosted glass quality), and the vivid neon elements pop out from it
- Center-anchored: the big bold text sits in the middle, surrounded by tech elements on all sides
- Dense and rich — every corner has something: icons, diagrams, sparks, panels, elements
- Action-oriented: speed lines, burst shapes, diagonal energy
- No human figures; all abstract tech elements and bold typography

**Comic Style Details**
- Thick bold outlines on every element (classic American comic style)
- Halftone dot shading in panel shadows
- Bright saturated fills — no muted or desaturated colors
- Action burst shapes (star bursts, speed lines) around key elements
- Feels like a Marvel/DC comic cover reimagined for AI engineering

## Prompt Template

Build the DALL-E prompt using this structure:

```
A vibrant comic-book cover illustration for a technical AI/ML article about [TOPIC]. Landscape 10:8 aspect ratio.
Background: smoky violet / frosted purple — like purple seen through frosted glass or fog. Use a gradient of #6B5B8C to #8B7BA8, hazy and muted, NOT pure dark, NOT pure bright. The feel is a dark-ish purple with a veiled, frosted quality.
Center of the image: massive bold comic-lettering text — a single tech word like "AI" or "DATA" or the key concept from the topic — thick outlines, drop shadow, slightly tilted, filling the center. Text filled with bright neon magenta (#FF2D9B) or electric lime (#B2FF00) to pop against the frosted purple.
Surrounding the text: [2-3 SPECIFIC VISUAL ELEMENTS chosen from the list above, tailored to the topic] — neural networks, vector clusters, pipeline diagrams, transformer blocks, all in vivid neon magenta, cyan, and lime.
Color palette: vivid magenta, electric lime, neon cyan — popping against the frosted purple/smoky violet background. High contrast neon-on-purple.
Style: high-tech Marvel-style comic art, thick outlines, halftone dot shading, action burst shapes, speed lines, dense rich composition. Dark frosted purple background makes neon elements glow.
No brand logos, no product names. Extremely rich in visual detail, vibrant neon-on-purple aesthetic.
```
