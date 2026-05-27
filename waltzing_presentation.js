"use strict";
const PptxGenJS = require("/Users/user/Library/Application Support/Zed/node/node-v24.11.0-darwin-x64/lib/node_modules/pptxgenjs");
const fs = require("fs");

const pres = new PptxGenJS();
pres.layout  = "LAYOUT_16x9";
pres.author  = "Marc Lamberts – Waltzing Analytics";
pres.title   = "Waltzing Analytics";

const LOGO = "/Users/user/Downloads/ChatGPT Image 17 mei 2026, 16_23_37.png";

// ── Palette: white base, black text, yellow accent ─────────────────────────
const Y = "F5C400";   // brand yellow
const B = "111111";   // near-black
const W = "FFFFFF";   // white
const G = "F4F4F4";   // light gray (card bg)
const M = "666666";   // muted text
const D = "333333";   // dark secondary text

// ── Helpers ────────────────────────────────────────────────────────────────
const mkShadow = () => ({
  type: "outer", blur: 6, offset: 2, angle: 135, color: "000000", opacity: 0.10,
});

// Yellow underline after each page header
function yellowRule(slide, x = 0.55, y = 0.98, w = 8.9) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h: 0.04,
    fill: { color: Y }, line: { color: Y },
  });
}

// Standard content-slide header
function header(slide, title, sub) {
  slide.background = { color: W };
  slide.addText(title, {
    x: 0.55, y: 0.22, w: 8.9, h: 0.65,
    fontSize: 27, bold: true, color: B,
    align: "left", valign: "middle", margin: 0,
  });
  if (sub) {
    slide.addText(sub, {
      x: 0.55, y: 0.88, w: 8.9, h: 0.28,
      fontSize: 11, color: M,
      align: "left", valign: "middle", margin: 0,
    });
  }
  yellowRule(slide);

  // small logo watermark
  if (fs.existsSync(LOGO)) {
    slide.addImage({ path: LOGO, x: 9.1, y: 0.06, w: 0.72, h: 0.72 });
  }

  // bottom rule
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 5.38, w: 10, h: 0.245,
    fill: { color: Y }, line: { color: Y },
  });
  slide.addText("Waltzing Analytics  ·  Marc Lamberts  ·  2026", {
    x: 0.3, y: 5.38, w: 9.4, h: 0.245,
    fontSize: 8.5, color: B,
    align: "center", valign: "middle", margin: 0,
  });
}

// Yellow stat badge
function badge(slide, x, y, value, label) {
  const w = 2.05, h = 1.28;
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: Y }, line: { color: Y },
    shadow: mkShadow(),
  });
  slide.addText(value, {
    x, y: y + 0.05, w, h: 0.72,
    fontSize: 32, bold: true, color: B,
    align: "center", valign: "middle", margin: 0,
  });
  slide.addText(label, {
    x, y: y + 0.78, w, h: 0.4,
    fontSize: 9, color: B,
    align: "center", valign: "middle", margin: 0,
  });
}

// White card with yellow left stripe
function rowCard(slide, x, y, w, h, label, body, labelW = 2.0) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: G }, line: { color: G },
    shadow: mkShadow(),
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w: 0.06, h,
    fill: { color: Y }, line: { color: Y },
  });
  slide.addText(label, {
    x: x + 0.16, y, w: labelW, h,
    fontSize: 11, bold: true, color: B,
    align: "left", valign: "middle", margin: 0,
  });
  slide.addText(body, {
    x: x + 0.16 + labelW, y, w: w - 0.22 - labelW, h,
    fontSize: 11, color: D,
    align: "left", valign: "middle", margin: 0,
  });
}

// Step box for pipeline
function step(slide, x, y, num, title, desc) {
  const w = 1.6, h = 2.22;
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h, fill: { color: G }, line: { color: G }, shadow: mkShadow(),
  });
  // top yellow band
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h: 0.42, fill: { color: Y }, line: { color: Y },
  });
  slide.addText(String(num), {
    x, y, w, h: 0.42,
    fontSize: 17, bold: true, color: B,
    align: "center", valign: "middle", margin: 0,
  });
  slide.addText(title, {
    x: x + 0.08, y: y + 0.48, w: w - 0.16, h: 0.5,
    fontSize: 10, bold: true, color: B,
    align: "center", valign: "middle", margin: 0,
  });
  slide.addText(desc, {
    x: x + 0.1, y: y + 1.02, w: w - 0.2, h: 1.1,
    fontSize: 8.5, color: M,
    align: "center", valign: "top", margin: 0,
  });
}

// ===========================================================================
// SLIDE 1 — Cover
// ===========================================================================
{
  const slide = pres.addSlide();
  slide.background = { color: W };

  // Yellow left half
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 4.6, h: 5.625,
    fill: { color: Y }, line: { color: Y },
  });

  // Logo on yellow side
  if (fs.existsSync(LOGO)) {
    slide.addImage({ path: LOGO, x: 0.6, y: 0.6, w: 3.4, h: 3.4 });
  }

  // Name below logo
  slide.addText("MARC LAMBERTS", {
    x: 0.3, y: 4.15, w: 4.0, h: 0.48,
    fontSize: 13, bold: true, color: B, charSpacing: 4,
    align: "center", valign: "middle", margin: 0,
  });
  slide.addText("Waltzing Analytics", {
    x: 0.3, y: 4.65, w: 4.0, h: 0.32,
    fontSize: 10.5, color: B,
    align: "center", valign: "middle", margin: 0,
  });

  // Right side — white
  slide.addText("Football\nIntelligence", {
    x: 5.0, y: 0.7, w: 4.7, h: 2.4,
    fontSize: 46, bold: true, color: B,
    align: "left", valign: "top", margin: 0,
  });
  slide.addText("for the\nModern Game", {
    x: 5.0, y: 3.1, w: 4.7, h: 1.4,
    fontSize: 26, color: M,
    align: "left", valign: "top", margin: 0,
  });

  // Date / info strip
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 4.6, y: 5.1, w: 5.4, h: 0.525,
    fill: { color: B }, line: { color: B },
  });
  slide.addText("Mei 2026  ·  marclambertsanalysis@gmail.com", {
    x: 4.7, y: 5.1, w: 5.2, h: 0.525,
    fontSize: 9.5, color: W,
    align: "center", valign: "middle", margin: 0,
  });
}

// ===========================================================================
// SLIDE 2 — Who am I
// ===========================================================================
{
  const slide = pres.addSlide();
  header(slide, "Who am I?", "");

  // Left: logo + name
  if (fs.existsSync(LOGO)) {
    slide.addImage({ path: LOGO, x: 0.45, y: 1.15, w: 2.5, h: 2.5 });
  }
  slide.addText("Marc Lamberts", {
    x: 0.45, y: 3.75, w: 2.5, h: 0.42,
    fontSize: 13.5, bold: true, color: B,
    align: "center", valign: "middle", margin: 0,
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.85, y: 4.2, w: 1.7, h: 0.28,
    fill: { color: Y }, line: { color: Y },
  });
  slide.addText("Football Data Analyst", {
    x: 0.45, y: 4.2, w: 2.5, h: 0.28,
    fontSize: 9.5, bold: true, color: B,
    align: "center", valign: "middle", margin: 0,
  });

  // Right: bio cards
  const bio = [
    { label: "Background",  body: "BI Specialist met een passie voor voetbaldata. Combineert statistisch denken met voetbalkennis." },
    { label: "Focus",       body: "Set-piece analyse, spelersprofielen, multi-league benchmarking en tactische dashboards." },
    { label: "Tools",       body: "Python · Streamlit · StatsBomb · xG modellen · Machine learning." },
    { label: "Missie",      body: "Data omzetten naar inzichten die coaches en analisten écht kunnen gebruiken op de training." },
  ];
  bio.forEach((r, i) => {
    rowCard(slide, 3.25, 1.22 + i * 0.93, 6.2, 0.78, r.label, r.body, 1.5);
  });
}

// ===========================================================================
// SLIDE 3 — What do I do
// ===========================================================================
{
  const slide = pres.addSlide();
  header(slide, "What do I do?", "Van ruwe voetbaldata naar bruikbare voetbalinformatie");

  // Three columns
  const cols = [
    {
      icon: "📥", title: "Data verzamelen",
      items: ["Event-data per wedstrijd (passes, schoten, set pieces)", "Tracking-feeds en StatsBomb-exportbestanden", "Meerdere competities tegelijk: Eredivisie, Bundesliga, …"],
    },
    {
      icon: "⚙️", title: "Analyseren & modelleren",
      items: ["xG-modellen per set-piece type", "Spelerratings (HOPS: kopduel­profiel)", "Patroonherkenning: techniek, zone, hoogte, uitkomst"],
    },
    {
      icon: "📊", title: "Inzichten leveren",
      items: ["Interactieve dashboards via SetPlayPro", "Pre-match PDF-rapporten per tegenstander", "League-brede benchmarks voor clubs & staf"],
    },
  ];

  cols.forEach((c, i) => {
    const x = 0.5 + i * 3.12;
    const y = 1.4;
    const w = 2.9, h = 3.62;
    // card
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h, fill: { color: G }, line: { color: G }, shadow: mkShadow(),
    });
    // top yellow
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h: 0.5, fill: { color: Y }, line: { color: Y },
    });
    // icon circle
    slide.addShape(pres.shapes.OVAL, {
      x: x + 0.12, y: y + 0.08, w: 0.34, h: 0.34,
      fill: { color: B }, line: { color: B },
    });
    slide.addText(c.icon, {
      x: x + 0.12, y: y + 0.08, w: 0.34, h: 0.34,
      fontSize: 11, align: "center", valign: "middle", margin: 0,
    });
    slide.addText(c.title, {
      x: x + 0.56, y, w: w - 0.66, h: 0.5,
      fontSize: 11.5, bold: true, color: B,
      align: "left", valign: "middle", margin: 0,
    });
    // bullet items
    const bulletItems = c.items.map((t, idx) => ({
      text: t,
      options: { bullet: true, breakLine: idx < c.items.length - 1 },
    }));
    slide.addText(bulletItems, {
      x: x + 0.16, y: y + 0.62, w: w - 0.28, h: 2.86,
      fontSize: 10, color: D,
      align: "left", valign: "top", margin: 0, paraSpaceAfter: 8,
    });
  });
}

// ===========================================================================
// SLIDE 4 — Raw data to insights
// ===========================================================================
{
  const slide = pres.addSlide();
  header(slide, "Raw Data → Insights", "De reis van ruwe event-data naar een beslissing op het veld");

  // Pipeline steps
  const steps = [
    { num: 1, title: "Raw event data",       desc: "StatsBomb XML/JSON: elke pass, schot, tackle — tijdstempel en coördinaat." },
    { num: 2, title: "Cleaning & parsing",   desc: "Ontbrekende waarden opvullen, coördinaten normaliseren, wedstrijden linken." },
    { num: 3, title: "Feature engineering",  desc: "Zone, hoogte, techniek, balbezit, speler­rollen en set-piece type extraheren." },
    { num: 4, title: "Modelling",            desc: "xG per set-piece type. HOPS spelerscore. Patroon­classificatie per fase." },
    { num: 5, title: "Dashboard & rapport",  desc: "SetPlayPro: interactief + downloadbaar PDF-rapport voor de coaching-staff." },
  ];

  steps.forEach((s, i) => {
    step(slide, 0.45 + i * 1.83, 1.42, s.num, s.title, s.desc);
  });

  // Arrow connectors
  for (let i = 0; i < 4; i++) {
    slide.addShape(pres.shapes.LINE, {
      x: 2.0 + i * 1.83, y: 2.52, w: 0.28, h: 0,
      line: { color: Y, width: 2.5 },
    });
  }

  // Bottom callout row
  const callouts = [
    { stat: "< 1 min",  label: "per club rapport" },
    { stat: "6+",       label: "datalagen per set piece" },
    { stat: "100%",     label: "herhaalbaar & schaalbaar" },
    { stat: "Elke week", label: "nieuwe wedstrijddata" },
  ];
  callouts.forEach((c, i) => {
    badge(slide, 0.45 + i * 2.3, 3.85, c.stat, c.label);
  });
}

// ===========================================================================
// SLIDE 5 — Algorithms & multi-club models
// ===========================================================================
{
  const slide = pres.addSlide();
  header(slide, "Algoritmes & Multi-Club Modellen", "Eén gedeeld model, toegepast over meerdere clubs en competities");

  // Left column — model descriptions
  const models = [
    {
      name: "xG Model (per fase)",
      desc: "Aparte expected-goals modellen voor corners, vrije trappen en inworpen. Inputvariabelen: leveringszone, hoogte, techniek, spelerposities en balsnelheid.",
    },
    {
      name: "HOPS Spelersrating",
      desc: "Header- en luchtduelprofielen per speler. Percentielscores over alle getrackte spelers. Tiers: Elite – Strong – Rotation – Depth. Snel selectierisico identificeren.",
    },
    {
      name: "Patroonbibliotheek",
      desc: "Automatische classificatie van set-piece patronen: looplijnen, eerste contact, zone vs man-dekking. Opgeslagen en doorzoekbaar per club.",
    },
  ];

  models.forEach((m, i) => {
    const y = 1.35 + i * 1.3;
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.45, y, w: 5.35, h: 1.12,
      fill: { color: G }, line: { color: G }, shadow: mkShadow(),
    });
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.45, y, w: 0.06, h: 1.12,
      fill: { color: Y }, line: { color: Y },
    });
    slide.addText(m.name, {
      x: 0.62, y: y + 0.06, w: 5.1, h: 0.32,
      fontSize: 11.5, bold: true, color: B,
      align: "left", valign: "middle", margin: 0,
    });
    slide.addText(m.desc, {
      x: 0.62, y: y + 0.42, w: 5.1, h: 0.62,
      fontSize: 9.5, color: D,
      align: "left", valign: "top", margin: 0,
    });
  });

  // Right column — multi-club advantages
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 6.05, y: 1.35, w: 3.45, h: 3.9,
    fill: { color: Y }, line: { color: Y }, shadow: mkShadow(),
  });
  slide.addText("Multi-Club\nVoordeel", {
    x: 6.15, y: 1.5, w: 3.25, h: 0.9,
    fontSize: 17, bold: true, color: B,
    align: "left", valign: "top", margin: 0,
  });
  const advantages = [
    "Eén model getraind op data van meerdere clubs en competities",
    "League-brede benchmarks: vergelijk jouw corner-xG met de Eredivisie",
    "Meer data = betere modelnauwkeurigheid, zelfs voor kleinere clubs",
    "Patronen van succesvolle clubs schaalbaar toepasbaar op nieuwe cliënten",
  ];
  advantages.forEach((a, i) => {
    slide.addShape(pres.shapes.OVAL, {
      x: 6.18, y: 2.52 + i * 0.58, w: 0.28, h: 0.28,
      fill: { color: B }, line: { color: B },
    });
    slide.addText(String(i + 1), {
      x: 6.18, y: 2.52 + i * 0.58, w: 0.28, h: 0.28,
      fontSize: 8, bold: true, color: W,
      align: "center", valign: "middle", margin: 0,
    });
    slide.addText(a, {
      x: 6.55, y: 2.5 + i * 0.58, w: 2.8, h: 0.5,
      fontSize: 9, color: B,
      align: "left", valign: "middle", margin: 0,
    });
  });
}

// ===========================================================================
// SLIDE 6 — AI: nuances
// ===========================================================================
{
  const slide = pres.addSlide();
  header(slide, "AI: de Nuances", "Wat AI wél en niet kan — en waar de analist het verschil maakt");

  // Two-column layout
  // Left: AI strengths
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.45, y: 1.35, w: 4.3, h: 3.62,
    fill: { color: G }, line: { color: G }, shadow: mkShadow(),
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.45, y: 1.35, w: 4.3, h: 0.48,
    fill: { color: Y }, line: { color: Y },
  });
  slide.addText("Wat AI goed doet", {
    x: 0.45, y: 1.35, w: 4.3, h: 0.48,
    fontSize: 13, bold: true, color: B,
    align: "center", valign: "middle", margin: 0,
  });
  const aiGood = [
    { icon: "✅", text: "Schaal: honderden wedstrijden in één analyse" },
    { icon: "✅", text: "Patroonherkenning in grote datasets" },
    { icon: "✅", text: "Consistentie: geen vermoeidheid, geen bias" },
    { icon: "✅", text: "Snelheid: rapport in seconden, niet uren" },
    { icon: "✅", text: "Benchmarking over meerdere competities" },
  ];
  aiGood.forEach((a, i) => {
    slide.addText(a.icon + "  " + a.text, {
      x: 0.62, y: 1.96 + i * 0.5, w: 4.0, h: 0.45,
      fontSize: 10.5, color: D,
      align: "left", valign: "middle", margin: 0,
    });
  });

  // Right: human needed
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.25, y: 1.35, w: 4.3, h: 3.62,
    fill: { color: B }, line: { color: B }, shadow: mkShadow(),
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.25, y: 1.35, w: 4.3, h: 0.48,
    fill: { color: B }, line: { color: B },
  });
  slide.addText("Waar de mens onmisbaar is", {
    x: 5.25, y: 1.35, w: 4.3, h: 0.48,
    fontSize: 13, bold: true, color: Y,
    align: "center", valign: "middle", margin: 0,
  });
  const humanNeed = [
    { icon: "⚡", text: "Context: spelersfit, moraal, wedstrijddruk" },
    { icon: "⚡", text: "Footballtaal: van xG naar coaching-cue" },
    { icon: "⚡", text: "Validatie: wanneer klopt het model niet?" },
    { icon: "⚡", text: "Ethiek: welke data gebruik je, en hoe?" },
    { icon: "⚡", text: "Relatie: vertrouwen opbouwen met de staf" },
  ];
  humanNeed.forEach((h, i) => {
    slide.addText(h.icon + "  " + h.text, {
      x: 5.42, y: 1.96 + i * 0.5, w: 4.0, h: 0.45,
      fontSize: 10.5, color: W,
      align: "left", valign: "middle", margin: 0,
    });
  });

  // Bottom message
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.45, y: 5.0, w: 9.1, h: 0.28,
    fill: { color: Y }, line: { color: Y },
  });
  slide.addText("AI versterkt de analist — het vervangt hem niet. De combinatie is de echte edge.", {
    x: 0.45, y: 5.0, w: 9.1, h: 0.28,
    fontSize: 9.5, bold: true, color: B,
    align: "center", valign: "middle", margin: 0,
  });
}

// ===========================================================================
// Write
// ===========================================================================
pres.writeFile({ fileName: "Waltzing_Analytics_Presentation.pptx" })
  .then(() => console.log("Done: Waltzing_Analytics_Presentation.pptx"))
  .catch(err => { console.error(err); process.exit(1); });
