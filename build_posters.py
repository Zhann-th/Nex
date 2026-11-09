#!/usr/bin/env python3
"""
Custom Editorial Vector Poster Generator for NEX Autonomous Vision & Loss Prevention OS.
Generates 4 high-resolution, editorial brutalist posters (1800x2400) embedding Rightgrotesk and DM Mono fonts,
fine technical schematics, biometric mesh, solenoid electromagnetic flux lines, and exploded view blueprints.
"""

import os
import base64
import subprocess

POSTER_DIR = "/Users/zhanasyl/Desktop/Code/Nex/posters"
FONTS_DIR = "/Users/zhanasyl/Desktop/Code/Nex/fonts"

# Load fonts as base64
with open(os.path.join(FONTS_DIR, "RightGrotesk-TightBlack.woff2"), "rb") as f:
    B64_RIGHTGROTESK = base64.b64encode(f.read()).decode("ascii")

with open(os.path.join(FONTS_DIR, "dmmono-medium.woff2"), "rb") as f:
    B64_DMMONO = base64.b64encode(f.read()).decode("ascii")

with open(os.path.join(FONTS_DIR, "OnsiteStandard-Regular.woff2"), "rb") as f:
    B64_ONSITE = base64.b64encode(f.read()).decode("ascii")

FONT_STYLE = f"""
    @font-face {{
        font-family: 'Rightgrotesk';
        src: url('data:font/woff2;base64,{B64_RIGHTGROTESK}') format('woff2');
        font-weight: 900;
        font-style: normal;
    }}
    @font-face {{
        font-family: 'DMMono';
        src: url('data:font/woff2;base64,{B64_DMMONO}') format('woff2');
        font-weight: 500;
        font-style: normal;
    }}
    @font-face {{
        font-family: 'Onsite';
        src: url('data:font/woff2;base64,{B64_ONSITE}') format('woff2');
        font-weight: 400;
        font-style: normal;
    }}
"""

def generate_poster_1():
    """Poster 1: BLINDSPOT // SURVEILLANCE PARADOX (Coral/Red theme)"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1800 2400" width="1800" height="2400">
    <defs>
        <style>
            {FONT_STYLE}
            .mono {{ font-family: 'DMMono', monospace; }}
            .grotesk {{ font-family: 'Rightgrotesk', sans-serif; font-weight: 900; }}
            .sans {{ font-family: 'Onsite', sans-serif; }}
        </style>
        <radialGradient id="bgGrad" cx="50%" cy="40%" r="65%">
            <stop offset="0%" stop-color="#fa435b" />
            <stop offset="60%" stop-color="#e83049" />
            <stop offset="100%" stop-color="#c91830" />
        </radialGradient>
        <pattern id="dotGrid" width="40" height="40" patternUnits="userSpaceOnUse">
            <circle cx="20" cy="20" r="1.5" fill="#000000" opacity="0.12" />
        </pattern>
        <pattern id="hatchDeadZone" width="20" height="20" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
            <line x1="0" y1="0" x2="0" y2="20" stroke="#000000" stroke-width="2.5" opacity="0.35" />
        </pattern>
    </defs>

    <!-- Base Canvas -->
    <rect width="1800" height="2400" fill="url(#bgGrad)" />
    <rect width="1800" height="2400" fill="url(#dotGrid)" />

    <!-- Outer Fine Technical Framing -->
    <rect x="80" y="80" width="1640" height="2240" fill="none" stroke="#000000" stroke-width="3" opacity="0.85" />
    <line x1="80" y1="200" x2="1720" y2="200" stroke="#000000" stroke-width="2" opacity="0.8" />
    <line x1="80" y1="2160" x2="1720" y2="2160" stroke="#000000" stroke-width="2" opacity="0.8" />

    <!-- Corner Reticles -->
    <path d="M 60 100 L 60 60 L 100 60" fill="none" stroke="#000000" stroke-width="4" />
    <path d="M 1740 100 L 1740 60 L 1700 60" fill="none" stroke="#000000" stroke-width="4" />
    <path d="M 60 2300 L 60 2340 L 100 2340" fill="none" stroke="#000000" stroke-width="4" />
    <path d="M 1740 2300 L 1740 2340 L 1700 2340" fill="none" stroke="#000000" stroke-width="4" />

    <!-- TOP TECHNICAL HEADER -->
    <text x="120" y="152" class="mono" font-size="28" font-weight="700" fill="#000000" letter-spacing="2">NEX SECURITY AUDIT // ARCHITECTURE REF: 01-BLIND</text>
    <rect x="1350" y="118" width="330" height="52" fill="#000000" rx="4" />
    <text x="1515" y="154" class="mono" font-size="22" font-weight="700" fill="#fa435b" text-anchor="middle" letter-spacing="3">UNRESOLVED LOSS: 28%</text>

    <!-- SECTION TITLE & EDITORIAL HERO -->
    <text x="120" y="310" class="mono" font-size="24" fill="#000000" letter-spacing="4" opacity="0.7">THREAT VECTOR 01 • SURVEILLANCE PARADOX</text>
    
    <text x="110" y="470" class="grotesk" font-size="168" fill="#000000" letter-spacing="-3">SURVEILLANCE</text>
    <text x="110" y="620" class="grotesk" font-size="168" fill="#000000" letter-spacing="-3">PARADOX</text>

    <!-- MASSIVE STAT DISPLAY -->
    <g transform="translate(120, 680)">
        <text x="0" y="170" class="grotesk" font-size="220" fill="#000000" letter-spacing="-5">72 HRS</text>
        <rect x="740" y="40" width="860" height="140" fill="#000000" rx="8" />
        <text x="770" y="90" class="mono" font-size="26" fill="#fa435b" font-weight="700" letter-spacing="1">OF UNINDEXED RAW CCTV FOOTAGE</text>
        <text x="770" y="130" class="mono" font-size="21" fill="#FFFFFF" letter-spacing="0.5">UNABLE TO IDENTIFY SINGLE-ITEM THEFT IN REAL TIME</text>
    </g>

    <!-- TECHNICAL SCHEMATIC: CAMERA FOV VS DEAD OCCLUSION ZONE -->
    <g transform="translate(900, 1420)">
        <!-- Coordinate Grid Center -->
        <circle cx="0" cy="0" r="420" fill="none" stroke="#000000" stroke-width="1.5" stroke-dasharray="8 8" opacity="0.3" />
        <circle cx="0" cy="0" r="280" fill="none" stroke="#000000" stroke-width="1.5" stroke-dasharray="6 6" opacity="0.35" />
        <circle cx="0" cy="0" r="140" fill="none" stroke="#000000" stroke-width="1.5" opacity="0.4" />
        <line x1="-480" y1="0" x2="480" y2="0" stroke="#000000" stroke-width="1.5" opacity="0.4" />
        <line x1="0" y1="-480" x2="0" y2="480" stroke="#000000" stroke-width="1.5" opacity="0.4" />

        <!-- CCTV Dome Housing at Top -->
        <path d="M -110 -380 L 110 -380 L 80 -340 L -80 -340 Z" fill="#000000" />
        <path d="M -70 -340 A 70 70 0 0 0 70 -340 Z" fill="#111111" />
        <circle cx="0" cy="-330" r="28" fill="#ffffff" opacity="0.9" />
        <circle cx="0" cy="-330" r="12" fill="#000000" />
        <text x="0" y="-405" class="mono" font-size="18" fill="#000000" font-weight="700" text-anchor="middle" letter-spacing="2">PASSIVE DOME CCTV (2.8M CEILING)</text>

        <!-- Wide Vision Cone (Clear / Ineffective) -->
        <polygon points="0,-330 -580,260 580,260" fill="#ffffff" opacity="0.18" stroke="#000000" stroke-width="2" stroke-dasharray="10 6" />

        <!-- Blind Occlusion Zone (Behind Customer Body Angle) -->
        <polygon points="-60,-120 480,260 -60,260" fill="url(#hatchDeadZone)" stroke="#000000" stroke-width="3" />
        
        <!-- Target Shopper Body Occlusion Silhouette Vector -->
        <ellipse cx="-60" cy="-120" rx="80" ry="110" fill="#000000" opacity="0.85" />
        <text x="-60" y="-115" class="mono" font-size="18" fill="#ffffff" text-anchor="middle" font-weight="700">SHOPPER</text>
        <text x="-60" y="-95" class="mono" font-size="14" fill="#fa435b" text-anchor="middle">BODY OCCLUSION</text>

        <!-- Hand Trajectory Arrow into Blind Zone -->
        <path d="M 0 -70 C 120 -30 220 50 280 160" fill="none" stroke="#000000" stroke-width="6" stroke-dasharray="12 8" />
        <circle cx="280" cy="160" r="16" fill="#000000" />
        
        <!-- Warning Pill in Dead Zone -->
        <rect x="40" y="60" width="360" height="90" fill="#000000" rx="6" />
        <text x="60" y="98" class="mono" font-size="22" font-weight="700" fill="#fa435b">BLIND OCCLUSION CONE</text>
        <text x="60" y="130" class="mono" font-size="16" fill="#FFFFFF">0% OPTICAL LINE-OF-SIGHT</text>

        <!-- Technical Annotation Callouts -->
        <line x1="280" y1="160" x2="420" y2="120" stroke="#000000" stroke-width="2" />
        <circle cx="420" cy="120" r="4" fill="#000000" />
        <text x="440" y="126" class="mono" font-size="18" fill="#000000" font-weight="700">POCKET CONCEALMENT</text>
        <text x="440" y="148" class="mono" font-size="14" fill="#000000" opacity="0.8">UNINDEXED THEFT EVENT</text>

        <!-- Angular Arc Measurement -->
        <path d="M -240 -120 A 280 280 0 0 1 240 -120" fill="none" stroke="#000000" stroke-width="2" />
        <text x="0" y="-140" class="mono" font-size="16" fill="#000000" text-anchor="middle" font-weight="700">ANGULAR OBTUSE FIELD: 78.4°</text>
    </g>

    <!-- BOTTOM COMPARISON METRICS MATRIX -->
    <g transform="translate(120, 1960)">
        <rect x="0" y="0" width="730" height="150" fill="#000000" rx="6" />
        <text x="40" y="44" class="mono" font-size="22" font-weight="700" fill="#fa435b">CONVENTIONAL PASSIVE CCTV</text>
        <text x="40" y="82" class="mono" font-size="17" fill="#FFFFFF">• 72+ Hours Delayed Manual Review</text>
        <text x="40" y="112" class="mono" font-size="17" fill="#FFFFFF">• 0% Correlation With Point-of-Sale</text>

        <rect x="790" y="0" width="770" height="150" fill="#FFFFFF" stroke="#000000" stroke-width="3" rx="6" />
        <text x="830" y="44" class="mono" font-size="22" font-weight="700" fill="#000000">NEX ACTIVE VISION</text>
        <text x="830" y="82" class="mono" font-size="17" fill="#000000">• &lt;15ms Synchronous Shelf-Cart Resolution</text>
        <text x="830" y="112" class="mono" font-size="17" fill="#000000">• Immediate Perpetrator Blacklist Tagging</text>
    </g>

    <!-- FOOTER TECHNICAL BARCODE & CREDITS -->
    <g transform="translate(120, 2220)">
        <text x="0" y="24" class="mono" font-size="20" fill="#000000" font-weight="700" letter-spacing="2">SPECIFICATION: PASSIVE SURVEILLANCE FAILURE</text>
        <text x="0" y="52" class="mono" font-size="16" fill="#000000" opacity="0.7">HARDWARE CLASS: CEILING ANALOG / RTSP DUMB IP CAMERAS</text>
        
        <!-- Barcode Graphic on Right -->
        <g transform="translate(1280, 0)">
            <rect x="0" y="0" width="6" height="55" fill="#000000" />
            <rect x="12" y="0" width="3" height="55" fill="#000000" />
            <rect x="22" y="0" width="10" height="55" fill="#000000" />
            <rect x="38" y="0" width="4" height="55" fill="#000000" />
            <rect x="48" y="0" width="8" height="55" fill="#000000" />
            <rect x="62" y="0" width="3" height="55" fill="#000000" />
            <rect x="72" y="0" width="12" height="55" fill="#000000" />
            <rect x="90" y="0" width="5" height="55" fill="#000000" />
            <rect x="102" y="0" width="8" height="55" fill="#000000" />
            <rect x="116" y="0" width="4" height="55" fill="#000000" />
            <rect x="128" y="0" width="14" height="55" fill="#000000" />
            <rect x="148" y="0" width="6" height="55" fill="#000000" />
            <rect x="160" y="0" width="3" height="55" fill="#000000" />
            <rect x="170" y="0" width="10" height="55" fill="#000000" />
            <rect x="186" y="0" width="5" height="55" fill="#000000" />
            <rect x="198" y="0" width="8" height="55" fill="#000000" />
            <text x="100" y="74" class="mono" font-size="14" fill="#000000" text-anchor="middle">NEX-DOC-01</text>
        </g>
    </g>
</svg>"""

def generate_poster_2():
    """Poster 2: THEFT VAULT // BIOMETRIC COMMIT (Lavender/Violet theme)"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1800 2400" width="1800" height="2400">
    <defs>
        <style>
            {FONT_STYLE}
            .mono {{ font-family: 'DMMono', monospace; }}
            .grotesk {{ font-family: 'Rightgrotesk', sans-serif; font-weight: 900; }}
            .sans {{ font-family: 'Onsite', sans-serif; }}
        </style>
        <radialGradient id="lavenderGrad" cx="50%" cy="40%" r="65%">
            <stop offset="0%" stop-color="#a499df" />
            <stop offset="60%" stop-color="#9589d3" />
            <stop offset="100%" stop-color="#7d6fc7" />
        </radialGradient>
        <pattern id="coordGrid" width="60" height="60" patternUnits="userSpaceOnUse">
            <line x1="0" y1="0" x2="60" y2="0" stroke="#000000" stroke-width="0.8" opacity="0.15" />
            <line x1="0" y1="0" x2="0" y2="60" stroke="#000000" stroke-width="0.8" opacity="0.15" />
        </pattern>
    </defs>

    <!-- Base Canvas -->
    <rect width="1800" height="2400" fill="url(#lavenderGrad)" />
    <rect width="1800" height="2400" fill="url(#coordGrid)" />

    <!-- Framing -->
    <rect x="80" y="80" width="1640" height="2240" fill="none" stroke="#000000" stroke-width="3" opacity="0.85" />
    <line x1="80" y1="200" x2="1720" y2="200" stroke="#000000" stroke-width="2" opacity="0.8" />
    <line x1="80" y1="2160" x2="1720" y2="2160" stroke="#000000" stroke-width="2" opacity="0.8" />

    <!-- Reticles -->
    <path d="M 60 100 L 60 60 L 100 60" fill="none" stroke="#000000" stroke-width="4" />
    <path d="M 1740 100 L 1740 60 L 1700 60" fill="none" stroke="#000000" stroke-width="4" />
    <path d="M 60 2300 L 60 2340 L 100 2340" fill="none" stroke="#000000" stroke-width="4" />
    <path d="M 1740 2300 L 1740 2340 L 1700 2340" fill="none" stroke="#000000" stroke-width="4" />

    <!-- HEADER -->
    <text x="120" y="152" class="mono" font-size="28" font-weight="700" fill="#000000" letter-spacing="2">NEX NEURAL CORE // BIOMETRIC THEFT VAULT</text>
    <rect x="1350" y="118" width="330" height="52" fill="#000000" rx="4" />
    <text x="1515" y="154" class="mono" font-size="22" font-weight="700" fill="#10b981" text-anchor="middle" letter-spacing="3">ACCURACY: 99.8%</text>

    <!-- TITLES -->
    <text x="120" y="310" class="mono" font-size="24" fill="#000000" letter-spacing="4" opacity="0.7">DEFENSE MODULE 02 • REAL-TIME IDENTITY COMMIT</text>
    <text x="110" y="470" class="grotesk" font-size="168" fill="#000000" letter-spacing="-3">BIOMETRIC</text>
    <text x="110" y="620" class="grotesk" font-size="168" fill="#000000" letter-spacing="-3">THEFT VAULT</text>

    <!-- STAT ROW -->
    <g transform="translate(120, 680)">
        <text x="0" y="170" class="grotesk" font-size="220" fill="#000000" letter-spacing="-5">11 MS</text>
        <rect x="680" y="40" width="920" height="140" fill="#000000" rx="8" />
        <text x="710" y="90" class="mono" font-size="24" fill="#10b981" font-weight="700" letter-spacing="1">BIOMETRIC FACE VECTOR COMMITTED TO BLACKLIST</text>
        <text x="710" y="130" class="mono" font-size="20" fill="#FFFFFF" letter-spacing="0.5">THE EXACT MILLISECOND UNPAID ITEMS LEAVE THE SHELF</text>
    </g>

    <!-- TECHNICAL BIOMETRIC MESH VISUALIZATION -->
    <g transform="translate(900, 1420)">
        <!-- Outer Targeting Bracket 700x700 -->
        <rect x="-350" y="-350" width="700" height="700" fill="none" stroke="#000000" stroke-width="2" opacity="0.4" stroke-dasharray="16 16" />
        <!-- Corner Target Reticles -->
        <path d="M -350 -270 L -350 -350 L -270 -350" fill="none" stroke="#000000" stroke-width="6" />
        <path d="M 350 -270 L 350 -350 L 270 -350" fill="none" stroke="#000000" stroke-width="6" />
        <path d="M -350 270 L -350 350 L -270 350" fill="none" stroke="#000000" stroke-width="6" />
        <path d="M 350 270 L 350 350 L 270 350" fill="none" stroke="#000000" stroke-width="6" />

        <!-- Biometric Target HUD Badges -->
        <rect x="-330" y="-330" width="280" height="50" fill="#000000" rx="4" />
        <text x="-190" y="-298" class="mono" font-size="18" fill="#10b981" font-weight="700" text-anchor="middle">TARGET: PERPETRATOR_#819</text>
        
        <rect x="80" y="-330" width="250" height="50" fill="#000000" rx="4" />
        <text x="205" y="-298" class="mono" font-size="18" fill="#FFFFFF" font-weight="700" text-anchor="middle">512-D VECTOR EMBED</text>

        <!-- Triangulated Wireframe Facial Mesh Contour -->
        <g stroke="#000000" stroke-width="2.5" fill="none" opacity="0.9">
            <!-- Face Oval & Jawline -->
            <polygon points="0,-240 -120,-180 -180,-60 -190,80 -120,220 0,280 120,220 190,80 180,-60 120,-180" fill="#ffffff" fill-opacity="0.12" />
            
            <!-- Forehead & Eyebrows -->
            <line x1="-120" y1="-180" x2="-60" y2="-120" />
            <line x1="-60" y1="-120" x2="0" y2="-140" />
            <line x1="0" y1="-140" x2="60" y2="-120" />
            <line x1="60" y1="-120" x2="120" y2="-180" />
            <line x1="0" y1="-240" x2="0" y2="-140" />
            <line x1="-180" y1="-60" x2="-80" y2="-60" />
            <line x1="180" y1="-60" x2="80" y2="-60" />

            <!-- Left Eye Wireframe -->
            <polygon points="-110,-50 -60,-80 -10,-50 -60,-30" fill="#000000" fill-opacity="0.2" />
            <circle cx="-60" cy="-55" r="8" fill="#10b981" />

            <!-- Right Eye Wireframe -->
            <polygon points="10,-50 60,-80 110,-50 60,-30" fill="#000000" fill-opacity="0.2" />
            <circle cx="60" cy="-55" r="8" fill="#10b981" />

            <!-- Nose Bridge & Base -->
            <polygon points="0,-140 -25,40 25,40" />
            <polygon points="-50,70 0,40 50,70 0,90" fill="#000000" fill-opacity="0.15" />
            <line x1="-25" y1="40" x2="-50" y2="70" />
            <line x1="25" y1="40" x2="50" y2="70" />

            <!-- Mouth & Lips -->
            <polygon points="-80,140 0,120 80,140 0,180" fill="#000000" fill-opacity="0.2" />
            <line x1="-80" y1="140" x2="80" y2="140" stroke-width="3" />

            <!-- Cheek Triangulation -->
            <line x1="-180" y1="-60" x2="-110" y2="-50" />
            <line x1="-190" y1="80" x2="-80" y2="140" />
            <line x1="-120" y1="220" x2="0" y2="180" />
            <line x1="180" y1="-60" x2="110" y2="-50" />
            <line x1="190" y1="80" x2="80" y2="140" />
            <line x1="120" y1="220" x2="0" y2="180" />

            <!-- Landmark Dots (68 nodes) -->
            <circle cx="0" cy="-240" r="5" fill="#000000" />
            <circle cx="-120" cy="-180" r="5" fill="#000000" />
            <circle cx="120" cy="-180" r="5" fill="#000000" />
            <circle cx="-180" cy="-60" r="5" fill="#000000" />
            <circle cx="180" cy="-60" r="5" fill="#000000" />
            <circle cx="-190" cy="80" r="5" fill="#000000" />
            <circle cx="190" cy="80" r="5" fill="#000000" />
            <circle cx="-120" cy="220" r="5" fill="#000000" />
            <circle cx="120" cy="220" r="5" fill="#000000" />
            <circle cx="0" cy="280" r="5" fill="#000000" />
            <circle cx="0" cy="40" r="5" fill="#000000" />
            <circle cx="0" cy="90" r="5" fill="#000000" />
            <circle cx="-80" cy="140" r="5" fill="#000000" />
            <circle cx="80" cy="140" r="5" fill="#000000" />
        </g>

        <!-- Laser Reticle Scanning Line -->
        <line x1="-340" y1="0" x2="340" y2="0" stroke="#10b981" stroke-width="3" opacity="0.8" />
        
        <!-- Live Embedding Tensor Stream Pill -->
        <rect x="-300" y="300" width="600" height="50" fill="#000000" rx="6" />
        <text x="0" y="332" class="mono" font-size="16" fill="#10b981" font-weight="700" text-anchor="middle">EMBEDDING: [ +0.482, -0.193, +0.884, +0.021, -0.719... ]</text>
    </g>

    <!-- BOTTOM EXECUTION PIPELINE TIMELINE -->
    <g transform="translate(120, 1960)">
        <rect x="0" y="0" width="1560" height="150" fill="#000000" rx="6" />
        
        <text x="40" y="44" class="mono" font-size="20" font-weight="700" fill="#10b981">EXECUTION PIPELINE // T=0 TO T=11MS</text>
        
        <g transform="translate(40, 75)">
            <!-- Step 1 -->
            <rect x="0" y="0" width="460" height="55" fill="#1a1a24" rx="4" />
            <text x="20" y="34" class="mono" font-size="15" fill="#FFFFFF">T=0ms • Shelf Plane Exit</text>
            <!-- Step 2 -->
            <rect x="500" y="0" width="460" height="55" fill="#1a1a24" rx="4" />
            <text x="520" y="34" class="mono" font-size="15" fill="#FFFFFF">T=4ms • Stereo 3D Hand Tracking</text>
            <!-- Step 3 -->
            <rect x="1000" y="0" width="480" height="55" fill="#2d284a" stroke="#10b981" stroke-width="1.5" rx="4" />
            <text x="1020" y="34" class="mono" font-size="15" fill="#10b981" font-weight="700">T=11ms • Theft Vault Commit</text>
        </g>
    </g>

    <!-- FOOTER -->
    <g transform="translate(120, 2220)">
        <text x="0" y="24" class="mono" font-size="20" fill="#000000" font-weight="700" letter-spacing="2">SPECIFICATION: EDGE BIOMETRIC INFERENCE PIPELINE</text>
        <text x="0" y="52" class="mono" font-size="16" fill="#000000" opacity="0.7">PRIVACY COMPLIANCE: ZERO LOCAL RAW FRAME STORAGE • EPHEMERAL VECTORS ONLY</text>
        
        <!-- Status Symbol -->
        <g transform="translate(1420, 10)">
            <circle cx="30" cy="20" r="16" fill="#000000" />
            <circle cx="30" cy="20" r="8" fill="#10b981" />
            <text x="65" y="26" class="mono" font-size="18" fill="#000000" font-weight="700">ACTIVE</text>
        </g>
    </g>
</svg>"""

def generate_poster_3():
    """Poster 3: LOCKOUT // AUTONOMOUS FLEET LOCKOUT (High-Contrast Stark White / Coral)"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1800 2400" width="1800" height="2400">
    <defs>
        <style>
            {FONT_STYLE}
            .mono {{ font-family: 'DMMono', monospace; }}
            .grotesk {{ font-family: 'Rightgrotesk', sans-serif; font-weight: 900; }}
            .sans {{ font-family: 'Onsite', sans-serif; }}
        </style>
        <pattern id="whiteGrid" width="50" height="50" patternUnits="userSpaceOnUse">
            <line x1="0" y1="0" x2="50" y2="0" stroke="#e4e4e7" stroke-width="1.5" />
            <line x1="0" y1="0" x2="0" y2="50" stroke="#e4e4e7" stroke-width="1.5" />
        </pattern>
    </defs>

    <!-- Stark Architectural White Canvas -->
    <rect width="1800" height="2400" fill="#fdfdfd" />
    <rect width="1800" height="2400" fill="url(#whiteGrid)" />

    <!-- Framing -->
    <rect x="80" y="80" width="1640" height="2240" fill="none" stroke="#000000" stroke-width="3" />
    <line x1="80" y1="200" x2="1720" y2="200" stroke="#000000" stroke-width="2" />
    <line x1="80" y1="2160" x2="1720" y2="2160" stroke="#000000" stroke-width="2" />

    <!-- Reticles -->
    <path d="M 60 100 L 60 60 L 100 60" fill="none" stroke="#000000" stroke-width="4" />
    <path d="M 1740 100 L 1740 60 L 1700 60" fill="none" stroke="#000000" stroke-width="4" />
    <path d="M 60 2300 L 60 2340 L 100 2340" fill="none" stroke="#000000" stroke-width="4" />
    <path d="M 1740 2300 L 1740 2340 L 1700 2340" fill="none" stroke="#000000" stroke-width="4" />

    <!-- HEADER -->
    <text x="120" y="152" class="mono" font-size="28" font-weight="700" fill="#000000" letter-spacing="2">NEX HARDWARE INTERLOCK // DISTRIBUTED IMMUNITY</text>
    <rect x="1350" y="118" width="330" height="52" fill="#fa435b" rx="4" />
    <text x="1515" y="154" class="mono" font-size="22" font-weight="700" fill="#FFFFFF" text-anchor="middle" letter-spacing="3">STATUS: LOCKED</text>

    <!-- TITLES -->
    <text x="120" y="310" class="mono" font-size="24" fill="#fa435b" font-weight="700" letter-spacing="4">COUNTERMEASURE 03 • PHYSICAL FLEET DENIAL</text>
    <text x="110" y="470" class="grotesk" font-size="168" fill="#000000" letter-spacing="-3">AUTONOMOUS</text>
    <text x="110" y="620" class="grotesk" font-size="168" fill="#000000" letter-spacing="-3">FLEET LOCKOUT</text>

    <!-- STAT ROW -->
    <g transform="translate(120, 680)">
        <text x="0" y="170" class="grotesk" font-size="220" fill="#fa435b" letter-spacing="-5">300 KG</text>
        <rect x="740" y="40" width="860" height="140" fill="#000000" rx="8" />
        <text x="770" y="90" class="mono" font-size="24" fill="#fa435b" font-weight="700" letter-spacing="1">TENSILE HOLDING FORCE APPLIED</text>
        <text x="770" y="130" class="mono" font-size="20" fill="#FFFFFF" letter-spacing="0.5">MAGNETIC LATCH REFUSES TO OPEN FOR BLACKLISTED FACES</text>
    </g>

    <!-- TECHNICAL SCHEMATIC: 300KG SOLENOID ELECTROMAGNETIC LOCK CLAMP -->
    <g transform="translate(900, 1420)">
        <!-- Coordinate Frame -->
        <circle cx="0" cy="0" r="440" fill="none" stroke="#000000" stroke-width="1.5" stroke-dasharray="10 10" opacity="0.2" />
        
        <!-- Heavy Mechanical Steel Solenoid Housing Outer -->
        <rect x="-380" y="-180" width="380" height="360" fill="#18181b" rx="8" />
        <rect x="-360" y="-160" width="340" height="320" fill="#27272a" rx="4" />
        
        <!-- Copper Coil Windings (Cross section) -->
        <rect x="-310" y="-120" width="90" height="240" fill="#ca8a04" />
        <line x1="-265" y1="-120" x2="-265" y2="120" stroke="#a16207" stroke-width="4" stroke-dasharray="8 8" />
        <text x="-265" y="160" class="mono" font-size="16" fill="#fef08a" text-anchor="middle" font-weight="700">COIL A</text>

        <rect x="-170" y="-120" width="90" height="240" fill="#ca8a04" />
        <line x1="-125" y1="-120" x2="-125" y2="120" stroke="#a16207" stroke-width="4" stroke-dasharray="8 8" />
        <text x="-125" y="160" class="mono" font-size="16" fill="#fef08a" text-anchor="middle" font-weight="700">COIL B</text>

        <!-- Solid Steel Core Pole Piece -->
        <rect x="-220" y="-140" width="50" height="280" fill="#71717a" />
        <rect x="-80" y="-150" width="60" height="300" fill="#52525b" />

        <!-- Armature Steel Strike Plate (Right Edge, clamping tightly) -->
        <rect x="0" y="-190" width="70" height="380" fill="#3f3f46" stroke="#fa435b" stroke-width="4" rx="4" />
        <text x="35" y="225" class="mono" font-size="16" fill="#fa435b" text-anchor="middle" font-weight="700">STRIKE PLATE</text>

        <!-- Magnetic Flux Loops (Field lines in coral/red) -->
        <g stroke="#fa435b" stroke-width="3" fill="none" opacity="0.85">
            <ellipse cx="0" cy="0" rx="90" ry="120" stroke-dasharray="8 6" />
            <ellipse cx="0" cy="0" rx="160" ry="200" stroke-dasharray="10 8" />
            <ellipse cx="0" cy="0" rx="230" ry="270" stroke-dasharray="12 10" />
        </g>

        <!-- Tensile Shear Force Vector Arrows -->
        <g stroke="#000000" stroke-width="6" fill="#000000">
            <!-- Arrow pulling left -->
            <line x1="-380" y1="0" x2="-490" y2="0" />
            <polygon points="-490,0 -460,-15 -460,15" />
            <text x="-520" y="-20" class="mono" font-size="22" font-weight="700" text-anchor="end">F = 2940 N</text>
            <text x="-520" y="8" class="mono" font-size="16" fill="#71717a" text-anchor="end">(300 KG HOLD)</text>

            <!-- Arrow resisting right -->
            <line x1="70" y1="0" x2="200" y2="0" />
            <polygon points="200,0 170,-15 170,15" />
            <text x="230" y="-20" class="mono" font-size="22" font-weight="700">SHEAR RESISTANCE</text>
            <text x="230" y="8" class="mono" font-size="16" fill="#71717a">ANTI-PRY INTERLOCK</text>
        </g>

        <!-- Lockout Status Annotation Pill -->
        <rect x="140" y="110" width="340" height="95" fill="#000000" rx="6" />
        <text x="160" y="148" class="mono" font-size="20" font-weight="700" fill="#fa435b">SOLENOID: DE-ENERGIZED</text>
        <text x="160" y="180" class="mono" font-size="15" fill="#FFFFFF">QR SCAN REJECTED BY FLEET OS</text>
    </g>

    <!-- BOTTOM NETWORK TOPOLOGY SPEC -->
    <g transform="translate(120, 1960)">
        <rect x="0" y="0" width="1560" height="150" fill="#000000" rx="6" />
        <text x="40" y="44" class="mono" font-size="22" font-weight="700" fill="#fa435b">DISTRIBUTED FLEET REPLICATION (KASPI / STRIPE KIOSKS)</text>
        <text x="40" y="82" class="mono" font-size="17" fill="#FFFFFF">• 1 Kiosk Infraction Triggers Instant Mesh Synchronization Across 1,000+ Kiosks</text>
        <text x="40" y="112" class="mono" font-size="17" fill="#FFFFFF">• Zero Latency Physical Solenoid Lockout on Subsequent Approach</text>
    </g>

    <!-- FOOTER -->
    <g transform="translate(120, 2220)">
        <text x="0" y="24" class="mono" font-size="20" fill="#000000" font-weight="700" letter-spacing="2">SPECIFICATION: PHYSICAL INTERLOCK &amp; FLEET LOCKOUT</text>
        <text x="0" y="52" class="mono" font-size="16" fill="#000000" opacity="0.7">ELECTRICAL: 12V/24V DC FAIL-SECURE • REVERSE SPIKE SURGE PROTECTED</text>
        
        <!-- Status Symbol -->
        <g transform="translate(1380, 10)">
            <rect x="0" y="0" width="180" height="40" fill="#fa435b" rx="4" />
            <text x="90" y="26" class="mono" font-size="18" fill="#FFFFFF" font-weight="700" text-anchor="middle">ARMED</text>
        </g>
    </g>
</svg>"""

def generate_poster_4():
    """Poster 4: RETROFIT // UNIVERSAL INTEGRATION (Architectural Blueprint Midnight Black)"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1800 2400" width="1800" height="2400">
    <defs>
        <style>
            {FONT_STYLE}
            .mono {{ font-family: 'DMMono', monospace; }}
            .grotesk {{ font-family: 'Rightgrotesk', sans-serif; font-weight: 900; }}
            .sans {{ font-family: 'Onsite', sans-serif; }}
        </style>
        <pattern id="blueprintGrid" width="40" height="40" patternUnits="userSpaceOnUse">
            <line x1="0" y1="0" x2="40" y2="0" stroke="#1e293b" stroke-width="1.2" />
            <line x1="0" y1="0" x2="0" y2="40" stroke="#1e293b" stroke-width="1.2" />
        </pattern>
    </defs>

    <!-- Deep Technical Midnight Canvas -->
    <rect width="1800" height="2400" fill="#07090e" />
    <rect width="1800" height="2400" fill="url(#blueprintGrid)" />

    <!-- Framing -->
    <rect x="80" y="80" width="1640" height="2240" fill="none" stroke="#38bdf8" stroke-width="2" opacity="0.8" />
    <line x1="80" y1="200" x2="1720" y2="200" stroke="#38bdf8" stroke-width="1.5" opacity="0.6" />
    <line x1="80" y1="2160" x2="1720" y2="2160" stroke="#38bdf8" stroke-width="1.5" opacity="0.6" />

    <!-- Reticles -->
    <path d="M 60 100 L 60 60 L 100 60" fill="none" stroke="#38bdf8" stroke-width="3" />
    <path d="M 1740 100 L 1740 60 L 1700 60" fill="none" stroke="#38bdf8" stroke-width="3" />
    <path d="M 60 2300 L 60 2340 L 100 2340" fill="none" stroke="#38bdf8" stroke-width="3" />
    <path d="M 1740 2300 L 1740 2340 L 1700 2340" fill="none" stroke="#38bdf8" stroke-width="3" />

    <!-- HEADER -->
    <text x="120" y="152" class="mono" font-size="28" font-weight="700" fill="#38bdf8" letter-spacing="2">NEX HARDWARE DEPLOYMENT // UNIVERSAL RETROFIT KIT</text>
    <rect x="1350" y="118" width="330" height="52" fill="#0284c7" rx="4" />
    <text x="1515" y="154" class="mono" font-size="22" font-weight="700" fill="#FFFFFF" text-anchor="middle" letter-spacing="3">PLUG &amp; PLAY</text>

    <!-- TITLES -->
    <text x="120" y="310" class="mono" font-size="24" fill="#38bdf8" letter-spacing="4" opacity="0.8">SYSTEM SPECIFICATION 04 • RAPID FLEET RETROFIT</text>
    <text x="110" y="470" class="grotesk" font-size="168" fill="#FFFFFF" letter-spacing="-3">UNIVERSAL</text>
    <text x="110" y="620" class="grotesk" font-size="168" fill="#FFFFFF" letter-spacing="-3">INTEGRATION</text>

    <!-- STAT ROW -->
    <g transform="translate(120, 680)">
        <text x="0" y="170" class="grotesk" font-size="220" fill="#38bdf8" letter-spacing="-5">30 MIN</text>
        <rect x="680" y="40" width="920" height="140" fill="#0f172a" stroke="#0284c7" stroke-width="2" rx="8" />
        <text x="710" y="90" class="mono" font-size="24" fill="#38bdf8" font-weight="700" letter-spacing="1">COMPLETE RETROFIT FOR EXISTING SMART FRIDGES</text>
        <text x="710" y="130" class="mono" font-size="20" fill="#94a3b8" letter-spacing="0.5">NO REFRIGERATION CABINET REPLACEMENT • ZERO DOWNTIME</text>
    </g>

    <!-- TECHNICAL SCHEMATIC: EXPLODED VIEW OF THE NEX RETROFIT POD -->
    <g transform="translate(900, 1420)">
        <!-- Center Axis of Assembly -->
        <line x1="0" y1="-460" x2="0" y2="440" stroke="#38bdf8" stroke-width="1.5" stroke-dasharray="14 8" opacity="0.5" />
        
        <!-- COMPONENT 1: CEILING HEADER FRAME (Existing fridge) -->
        <g transform="translate(0, -320)">
            <rect x="-380" y="-40" width="760" height="60" fill="#1e293b" stroke="#64748b" stroke-width="2" rx="4" />
            <text x="0" y="-5" class="mono" font-size="18" fill="#94a3b8" text-anchor="middle" font-weight="700">EXISTING SMART FRIDGE CEILING HEADER</text>
            <text x="-400" y="-5" class="mono" font-size="16" fill="#38bdf8" text-anchor="end">[CABINET WALL]</text>
        </g>

        <!-- COMPONENT 2: QUICK-SNAP MAGNETIC MOUNTING PLATE -->
        <g transform="translate(0, -180)">
            <rect x="-260" y="-15" width="520" height="30" fill="#0f172a" stroke="#38bdf8" stroke-width="2" rx="2" />
            <!-- Neodymium Magnet Pods -->
            <circle cx="-180" cy="0" r="12" fill="#38bdf8" />
            <circle cx="0" cy="0" r="12" fill="#38bdf8" />
            <circle cx="180" cy="0" r="12" fill="#38bdf8" />
            <text x="300" y="6" class="mono" font-size="16" fill="#38bdf8">[01] MAGNETIC MOUNT BRACKET</text>
        </g>

        <!-- COMPONENT 3: NEX STEREO ACTIVE OPTICAL POD -->
        <g transform="translate(0, 0)">
            <!-- Aluminum CNC Housing -->
            <rect x="-300" y="-70" width="600" height="140" fill="#090d16" stroke="#38bdf8" stroke-width="3" rx="10" />
            
            <!-- Left 120 FPS Lens -->
            <circle cx="-180" cy="0" r="45" fill="#1e293b" stroke="#38bdf8" stroke-width="2" />
            <circle cx="-180" cy="0" r="28" fill="#0284c7" />
            <circle cx="-180" cy="0" r="12" fill="#000000" />
            <text x="-180" y="70" class="mono" font-size="14" fill="#38bdf8" text-anchor="middle" font-weight="700">CAM L (120 FPS)</text>

            <!-- Center ToF IR Depth Projector & Neural LED -->
            <rect x="-50" y="-35" width="100" height="70" fill="#0f172a" stroke="#64748b" stroke-width="1.5" rx="4" />
            <circle cx="0" cy="-10" r="14" fill="#fa435b" />
            <circle cx="0" cy="18" r="8" fill="#10b981" />
            <text x="0" y="70" class="mono" font-size="14" fill="#fa435b" text-anchor="middle" font-weight="700">IR DEPTH + NPU</text>

            <!-- Right 120 FPS Lens -->
            <circle cx="180" cy="0" r="45" fill="#1e293b" stroke="#38bdf8" stroke-width="2" />
            <circle cx="180" cy="0" r="28" fill="#0284c7" />
            <circle cx="180" cy="0" r="12" fill="#000000" />
            <text x="180" y="70" class="mono" font-size="14" fill="#38bdf8" text-anchor="middle" font-weight="700">CAM R (120 FPS)</text>

            <text x="-330" y="6" class="mono" font-size="16" fill="#38bdf8" text-anchor="end">[02] STEREOSCOPIC RIG</text>
        </g>

        <!-- COMPONENT 4: INLINE HARNESS & SOLENOID INTERCEPT CABLE -->
        <g transform="translate(0, 180)">
            <path d="M 0 -70 C 0 -20 120 -20 120 40 L 120 100" fill="none" stroke="#f59e0b" stroke-width="5" stroke-dasharray="10 6" />
            <rect x="60" y="100" width="120" height="40" fill="#1e293b" stroke="#f59e0b" stroke-width="2" rx="4" />
            <text x="120" y="126" class="mono" font-size="15" fill="#f59e0b" text-anchor="middle" font-weight="700">12V INTERCEPT</text>
            <text x="-20" y="80" class="mono" font-size="16" fill="#f59e0b" text-anchor="end">[03] PLUG-IN HARNESS</text>
        </g>

        <!-- COMPONENT 5: SOLENOID RELAY CONTROLLER -->
        <g transform="translate(0, 340)">
            <rect x="-180" y="-30" width="360" height="60" fill="#090d16" stroke="#10b981" stroke-width="2" rx="6" />
            <text x="0" y="6" class="mono" font-size="17" fill="#10b981" text-anchor="middle" font-weight="700">[04] FAIL-SAFE SOLENOID INTERLOCK</text>
        </g>

        <!-- Dimension Lines (Blueprint Callouts) -->
        <g stroke="#64748b" stroke-width="1.5">
            <line x1="-300" y1="-95" x2="300" y2="-95" />
            <line x1="-300" y1="-105" x2="-300" y2="-85" />
            <line x1="300" y1="-105" x2="300" y2="-85" />
            <text x="0" y="-110" class="mono" font-size="15" fill="#94a3b8" text-anchor="middle">OVERALL WIDTH: 240 MM (COMPACT FORM)</text>
        </g>
    </g>

    <!-- BOTTOM HARDWARE COMPATIBILITY MATRIX -->
    <g transform="translate(120, 1960)">
        <rect x="0" y="0" width="1560" height="150" fill="#0f172a" stroke="#1e293b" stroke-width="2" rx="6" />
        <text x="40" y="44" class="mono" font-size="22" font-weight="700" fill="#38bdf8">HARDWARE COMPATIBILITY &amp; INTERFACES</text>
        <g transform="translate(40, 75)">
            <rect x="0" y="0" width="340" height="50" fill="#1e293b" rx="4" />
            <text x="170" y="32" class="mono" font-size="16" fill="#FFFFFF" text-anchor="middle">✓ VBox 100 / 200 / 300</text>

            <rect x="380" y="0" width="340" height="50" fill="#1e293b" rx="4" />
            <text x="550" y="32" class="mono" font-size="16" fill="#FFFFFF" text-anchor="middle">✓ Unicum Smart Fridge</text>

            <rect x="760" y="0" width="340" height="50" fill="#1e293b" rx="4" />
            <text x="930" y="32" class="mono" font-size="16" fill="#FFFFFF" text-anchor="middle">✓ Custom 12V/24V Kiosks</text>

            <rect x="1140" y="0" width="340" height="50" fill="#1e293b" rx="4" />
            <text x="1310" y="32" class="mono" font-size="16" fill="#38bdf8" font-weight="700" text-anchor="middle">✓ RS-485 / Relay I/O</text>
        </g>
    </g>

    <!-- FOOTER -->
    <g transform="translate(120, 2220)">
        <text x="0" y="24" class="mono" font-size="20" fill="#38bdf8" font-weight="700" letter-spacing="2">SPECIFICATION: FIELD RETROFIT PROCEDURE</text>
        <text x="0" y="52" class="mono" font-size="16" fill="#94a3b8">POWER REQUIREMENT: 12V DC @ 1.2A • ZERO REFRIGERANT LOOP MODIFICATION</text>
        
        <!-- Status Symbol -->
        <g transform="translate(1380, 10)">
            <rect x="0" y="0" width="180" height="40" fill="#0284c7" rx="4" />
            <text x="90" y="26" class="mono" font-size="18" fill="#FFFFFF" font-weight="700" text-anchor="middle">CERTIFIED</text>
        </g>
    </g>
</svg>"""

def main():
    print("Generating 4 custom editorial posters for NEX...")
    posters = [
        ("poster_1_blindspot.svg", generate_poster_1()),
        ("poster_2_vault.svg", generate_poster_2()),
        ("poster_3_lockout.svg", generate_poster_3()),
        ("poster_4_retrofit.svg", generate_poster_4()),
    ]
    
    for filename, content in posters:
        path = os.path.join(POSTER_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  -> Generated {filename} ({len(content)} bytes)")

if __name__ == "__main__":
    main()
