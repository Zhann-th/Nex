#!/usr/bin/env python3
import os
import shutil
import re

INDEX_PATH = "/Users/zhanasyl/Desktop/Code/Nex/index.html"
BACKUP_PATH = "/Users/zhanasyl/Desktop/Code/Nex/index.html.bak_before_mobile_opt"

shutil.copyfile(INDEX_PATH, BACKUP_PATH)
print(f"Backed up to {BACKUP_PATH}")

with open(INDEX_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# ─────────────────────────────────────────────────────────────────────────────
# 1. ADD MOBILE MENU BUTTON & REVISE HEADER
# ─────────────────────────────────────────────────────────────────────────────

old_header = """    <!-- ════════════ TOP HEADER BAR (FIXED) ════════════ -->
    <header class="site-header">
        <div class="header-brand">
            <a href="/" class="brand-wordmark">NEX</a>
        </div>

        <nav class="header-nav">
            <a href="#scrolly-root" class="nav-link">Architecture</a>
            <a href="#panel-1" class="nav-link">Blindspot</a>
            <a href="#panel-2" class="nav-link">Theft Vault</a>
            <a href="#panel-3" class="nav-link">Lockout</a>
            <a href="#panel-4" class="nav-link">Retrofit</a>
        </nav>

        <div class="header-actions">
            <a href="/dashboard" class="btn btn-black" title="Open Computer Vision Control Workspace">
                Control Workspace →
            </a>
        </div>
    </header>"""

new_header = """    <!-- ════════════ TOP HEADER BAR (FIXED) ════════════ -->
    <header class="site-header">
        <div class="header-brand">
            <a href="/" class="brand-wordmark">NEX</a>
            <span class="brand-badge header-badge-desktop">AUTONOMOUS VISION</span>
        </div>

        <nav class="header-nav">
            <a href="#scrolly-root" class="nav-link">Architecture</a>
            <a href="#panel-1" class="nav-link">Blindspot</a>
            <a href="#panel-2" class="nav-link">Theft Vault</a>
            <a href="#panel-3" class="nav-link">Lockout</a>
            <a href="#panel-4" class="nav-link">Retrofit</a>
        </nav>

        <div class="header-actions">
            <a href="/dashboard" class="btn btn-black header-cta-btn" title="Open Computer Vision Control Workspace">
                <span class="btn-text-full">Control Workspace →</span>
                <span class="btn-text-mobile">Workspace →</span>
            </a>
            <button class="mobile-menu-toggle" id="mobileMenuBtn" aria-label="Toggle Navigation Menu">
                <span class="menu-bar"></span>
                <span class="menu-bar"></span>
                <span class="menu-bar"></span>
            </button>
        </div>
    </header>

    <!-- ════════════ MOBILE NAVIGATION DRAWER ════════════ -->
    <div class="mobile-nav-drawer" id="mobileNavDrawer" aria-hidden="true">
        <div class="mobile-drawer-top">
            <span class="drawer-meta-tag"><span class="meta-dot"></span> SYSTEM NAVIGATION</span>
            <span class="drawer-status-pill">120 FPS CV ONLINE</span>
        </div>
        <nav class="mobile-drawer-nav">
            <a href="#scrolly-root" class="mobile-nav-link">
                <span class="nav-idx">00</span>
                <div class="nav-info">
                    <span class="nav-text">ARCHITECTURE</span>
                    <span class="nav-sub">3D Interactive Inspection</span>
                </div>
            </a>
            <a href="#panel-1" class="mobile-nav-link">
                <span class="nav-idx">01</span>
                <div class="nav-info">
                    <span class="nav-text">BLINDSPOT</span>
                    <span class="nav-sub">Passive CCTV Collapse</span>
                </div>
            </a>
            <a href="#panel-2" class="mobile-nav-link">
                <span class="nav-idx">02</span>
                <div class="nav-info">
                    <span class="nav-text">THEFT VAULT</span>
                    <span class="nav-sub">Real-Time Evidence Logging</span>
                </div>
            </a>
            <a href="#panel-3" class="mobile-nav-link">
                <span class="nav-idx">03</span>
                <div class="nav-info">
                    <span class="nav-text">LOCKOUT</span>
                    <span class="nav-sub">Autonomous Interlock Security</span>
                </div>
            </a>
            <a href="#panel-4" class="mobile-nav-link">
                <span class="nav-idx">04</span>
                <div class="nav-info">
                    <span class="nav-text">RETROFIT</span>
                    <span class="nav-sub">Universal 30-Min Deployment</span>
                </div>
            </a>
        </nav>
        <div class="mobile-drawer-actions">
            <a href="/dashboard" class="btn btn-coral drawer-btn">
                Open Control Workspace →
            </a>
            <a href="mailto:thzhanasyl@gmail.com" class="btn drawer-btn drawer-btn-white">
                Inquire For Pilot Fleet
            </a>
        </div>
    </div>"""

assert old_header in content, "old_header not found in content"
content = content.replace(old_header, new_header)

# ─────────────────────────────────────────────────────────────────────────────
# 2. UPDATE CSS FOR MOBILE RESPONSIVENESS AND PERFORMANCE
# ─────────────────────────────────────────────────────────────────────────────

# Replace the media queries section (from line 1060: @media (max-width: 960px) to </style>)
media_queries_pattern = re.compile(r"(\s+@media \(max-width: 960px\).*?</style>)", re.DOTALL)

new_styles = """
        /* ═══════════════════════════════════════════════════════════════
           MOBILE NAVIGATION DRAWER & TOGGLE STYLES
           ═══════════════════════════════════════════════════════════════ */
        .mobile-menu-toggle {
            display: none;
            background: transparent;
            border: var(--border-heavy);
            width: 38px;
            height: 38px;
            padding: 8px 6px;
            flex-direction: column;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            z-index: 1002;
            box-shadow: var(--shadow-brutal-sm);
            color: currentColor;
            flex-shrink: 0;
            transition: background 0.15s ease, border-color 0.15s ease, transform 0.1s ease;
        }

        .site-header.is-dark .mobile-menu-toggle {
            border-color: #FFFFFF;
            box-shadow: 2px 2px 0px rgba(255, 255, 255, 0.25);
            color: #FFFFFF;
        }

        .mobile-menu-toggle:active {
            transform: translate(1px, 1px);
            box-shadow: none;
        }

        .mobile-menu-toggle .menu-bar {
            display: block;
            width: 100%;
            height: 2px;
            background: currentColor;
            transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.15s ease;
            transform-origin: center;
        }

        .mobile-menu-toggle.is-active .menu-bar:nth-child(1) {
            transform: translateY(7px) rotate(45deg);
        }

        .mobile-menu-toggle.is-active .menu-bar:nth-child(2) {
            opacity: 0;
            transform: scaleX(0);
        }

        .mobile-menu-toggle.is-active .menu-bar:nth-child(3) {
            transform: translateY(-7px) rotate(-45deg);
        }

        .mobile-nav-drawer {
            position: fixed;
            top: 60px;
            left: 0;
            width: 100%;
            height: calc(100dvh - 60px);
            background: #000000;
            color: #FFFFFF;
            z-index: 999;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 24px 20px 32px;
            box-sizing: border-box;
            transform: translateX(100%);
            transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            overflow-y: auto;
            border-top: 1.5px solid #27272A;
            -webkit-overflow-scrolling: touch;
        }

        .mobile-nav-drawer.is-open {
            transform: translateX(0);
        }

        .mobile-drawer-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 16px;
            border-bottom: 1px solid #27272A;
            font-family: var(--font-mono);
            font-size: 10px;
            color: #A1A1AA;
            letter-spacing: 0.08em;
        }

        .drawer-meta-tag {
            display: flex;
            align-items: center;
            gap: 8px;
            text-transform: uppercase;
            font-weight: 700;
        }

        .drawer-status-pill {
            padding: 3px 8px;
            background: rgba(16, 185, 129, 0.12);
            color: #10B981;
            border: 1px solid rgba(16, 185, 129, 0.4);
            font-weight: 800;
            letter-spacing: 0.06em;
            font-size: 9px;
        }

        .mobile-drawer-nav {
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin: 20px 0;
            flex: 1;
        }

        .mobile-nav-link {
            display: flex;
            align-items: center;
            padding: 13px 14px;
            background: #09090B;
            border: 1.5px solid #27272A;
            text-decoration: none;
            color: #FFFFFF;
            gap: 14px;
            transition: background 0.15s ease, border-color 0.15s ease, transform 0.1s ease;
        }

        .mobile-nav-link:active {
            background: #18181B;
            border-color: var(--accent-coral);
            transform: scale(0.99);
        }

        .mobile-nav-link .nav-idx {
            font-family: var(--font-mono);
            font-size: 13px;
            font-weight: 800;
            color: var(--accent-coral);
            min-width: 24px;
        }

        .mobile-nav-link .nav-info {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .mobile-nav-link .nav-text {
            font-family: var(--font-headline);
            font-size: 19px;
            letter-spacing: 0.03em;
            text-transform: uppercase;
            line-height: 1;
            color: #FFFFFF;
        }

        .mobile-nav-link .nav-sub {
            font-family: var(--font-mono);
            font-size: 9.5px;
            color: #71717A;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .mobile-drawer-actions {
            display: flex;
            flex-direction: column;
            gap: 10px;
            padding-top: 16px;
            border-top: 1px solid #27272A;
        }

        .drawer-btn {
            width: 100%;
            padding: 13px 18px;
            font-size: 12px;
            text-align: center;
            box-sizing: border-box;
        }

        .drawer-btn-white {
            background: #FFFFFF;
            color: #000000;
            border-color: #FFFFFF;
        }

        .btn-text-mobile {
            display: none;
        }

        /* ═══════════════════════════════════════════════════════════════
           SECTION: FINAL ACTION BANNER & FOOTER (PITCH BLACK THEME)
           ═══════════════════════════════════════════════════════════════ */
        .section-cta {
            background: #000000;
            color: #FFFFFF;
            padding: 120px 48px;
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 28px;
            position: relative;
            z-index: 30;
            border-top: var(--border-dark-subtle);
        }

        .cta-massive-title {
            font-family: var(--font-headline);
            font-size: clamp(48px, 8.5vw, 110px);
            text-transform: uppercase;
            line-height: 0.92;
            letter-spacing: -0.02em;
            color: #FFFFFF;
        }

        .cta-sub {
            max-width: 600px;
            font-size: 16px;
            color: #A1A1AA;
            line-height: 1.6;
        }

        .cta-btn-group {
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
            justify-content: center;
            margin-top: 8px;
        }

        .site-footer {
            background: #000000;
            border-top: var(--border-dark-subtle);
            padding: 32px 48px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-family: var(--font-mono);
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.04em;
            color: #71717A;
            position: relative;
            z-index: 30;
        }

        .site-footer strong {
            color: #FFFFFF;
        }

        .footer-nav-row {
            display: flex;
            gap: 24px;
        }

        .footer-nav-row a {
            color: #D4D4D8;
            text-decoration: none;
            font-weight: 800;
            transition: color 0.15s ease;
        }

        .footer-nav-row a:hover {
            color: var(--accent-coral);
        }

        /* ═══════════════════════════════════════════════════════════════
           RESPONSIVE BREAKPOINTS (TABLET & DESKTOP: <= 1024px)
           ═══════════════════════════════════════════════════════════════ */
        @media (max-width: 1024px) {
            .site-header {
                padding: 0 20px;
                height: 58px;
            }
            .header-nav {
                display: none;
            }
            .mobile-menu-toggle {
                display: flex;
            }
            .header-badge-desktop {
                display: none;
            }
            .mobile-nav-drawer {
                top: 58px;
                height: calc(100dvh - 58px);
            }
            .hero-bottom-dock {
                bottom: 16px;
                left: 20px;
                right: 20px;
            }
            .hud-top-bar {
                top: 70px;
                left: 20px;
                right: 20px;
            }
            .stage-card {
                left: 20px !important;
                right: 20px !important;
                max-width: none;
            }
        }

        /* ═══════════════════════════════════════════════════════════════
           RESPONSIVE BREAKPOINTS (TABLETS & MOBILE: <= 960px)
           Stacking Panels Flow Naturally on Small Viewports
           ═══════════════════════════════════════════════════════════════ */
        @media (max-width: 960px) {
            .c-panel {
                height: auto;
                min-height: auto;
                display: flex;
                flex-direction: column;
                padding: 3rem 20px 3.5rem;
                position: relative !important;
                top: 0 !important;
                box-shadow: none;
                border-bottom: 2px solid #000000;
            }
            .c-panel-grid {
                display: flex;
                flex-direction: column;
                gap: 2rem;
            }
            .c-panel-main {
                max-width: 100%;
                padding-right: 0;
                margin-bottom: 0;
            }
            .panel-title {
                font-size: clamp(48px, 14vw, 92px);
                margin: 0.8rem 0 1rem;
                line-height: 0.84;
            }
            .c-panel-visual {
                width: 100%;
                margin-top: 1rem;
            }
            .panel-poster-frame {
                width: 100%;
                max-width: 380px;
                margin: 0 auto;
            }
            .panel-poster-img {
                max-height: 52vh;
                transform: none !important;
                box-shadow: 8px 14px 40px rgba(0, 0, 0, 0.4);
            }
        }

        /* ═══════════════════════════════════════════════════════════════
           RESPONSIVE BREAKPOINTS (SMARTPHONES: <= 768px)
           Ultra-optimized for touch devices, performance, and narrow viewports
           ═══════════════════════════════════════════════════════════════ */
        @media (max-width: 768px) {
            .site-header {
                padding: 0 16px;
                height: 54px;
            }
            .brand-wordmark {
                font-size: 26px;
            }
            .btn-text-full {
                display: none;
            }
            .btn-text-mobile {
                display: inline;
            }
            .header-cta-btn {
                padding: 6px 12px;
                font-size: 10px;
            }
            .mobile-nav-drawer {
                top: 54px;
                height: calc(100dvh - 54px);
                padding: 18px 16px 28px;
            }

            /* Optimized Scrollytelling Viewport for Mobile Phones */
            .scrolly-section {
                height: 340vh;
            }
            .sticky-viewport {
                height: 100dvh;
                min-height: 100dvh;
            }

            /* HUD Top Controls */
            .hud-top-bar {
                top: 64px;
                left: 14px;
                right: 14px;
            }
            .hud-step-pill {
                font-size: 8.5px;
                padding: 4px 8px;
                letter-spacing: 0.05em;
            }
            .scroll-prompt-pill {
                font-size: 8.5px;
                padding: 4px 8px;
                gap: 4px;
            }

            /* Responsive Hero Headlines: Prevent Wrapping & Overlap */
            .hero-headline-top {
                top: 92px;
                font-size: clamp(32px, 10.5vw, 54px);
                line-height: 0.88;
                letter-spacing: -0.01em;
            }
            .hero-headline-bottom {
                bottom: 142px;
                font-size: clamp(32px, 10.5vw, 54px);
                line-height: 0.88;
                letter-spacing: -0.01em;
            }

            /* Hero Backing Cards Sized for Narrow Viewport */
            .hero-backing-frame {
                width: 220px;
                height: 330px;
            }

            /* Hero Bottom Dock: 2-Column Grid + Compact Editorial Note */
            .hero-bottom-dock {
                bottom: 12px;
                left: 14px;
                right: 14px;
                flex-direction: column;
                align-items: stretch;
                gap: 8px;
            }
            .hero-micro-stats {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 4px 12px;
                font-size: 9.5px;
            }
            .hero-micro-stats .stat-val {
                font-size: 14px;
                min-width: 36px;
            }
            .hero-manifesto-box {
                font-size: 11px;
                line-height: 1.4;
                text-align: left;
                max-width: 100%;
                border-top: 1px solid rgba(0, 0, 0, 0.12);
                padding-top: 6px;
            }
            .hero-manifesto-box em {
                font-size: 11.5px;
            }

            /* Mobile-Docked Stage Narrative Cards (Bottom Sheet Style) */
            .stage-card {
                position: absolute;
                left: 12px !important;
                right: 12px !important;
                max-width: none !important;
                top: auto !important;
                bottom: 16px !important;
                padding: 14px 16px;
                gap: 7px;
                background: rgba(255, 255, 255, 0.96);
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
                border: 2px solid #000000;
                box-shadow: 4px 4px 0px #000000;
                transform: translateY(24px) !important;
                z-index: 25;
            }
            .stage-card.is-visible {
                transform: translateY(0) !important;
            }
            .stage-card .card-kicker {
                font-size: 9px;
            }
            .stage-card .card-title {
                font-size: 16px;
                line-height: 1.15;
            }
            .stage-card .card-body {
                font-size: 11.5px;
                line-height: 1.45;
            }
            .stage-card .pt-pill {
                font-size: 8px;
                padding: 2px 6px;
            }

            /* Marquee Strip */
            .pt-marquee-strip {
                padding: 10px 0;
            }
            .marquee-item {
                font-size: 14px;
                gap: 6px;
            }
            .marquee-item .badge {
                font-size: 8.5px;
                padding: 1px 5px;
            }

            /* Panel Specifications 2-Column Grid */
            .c-panel-top-meta {
                font-size: 9px;
                padding-bottom: 0.7rem;
                margin-bottom: 0.9rem;
                flex-wrap: wrap;
                gap: 6px;
            }
            .c-panel-badge-row {
                gap: 10px;
                margin-bottom: 0.6rem;
            }
            .c-panel-num {
                width: 32px;
                height: 32px;
                font-size: 12px;
            }
            .c-panel-kicker {
                font-size: 10px;
            }
            .c-panel-desc p {
                font-size: 13.5px;
                line-height: 1.5;
            }
            .c-panel-specs {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 6px;
                margin-bottom: 1rem;
            }
            .c-spec-chip {
                padding: 6px 9px;
            }
            .c-spec-chip .spec-label {
                font-size: 8px;
            }
            .c-spec-chip .spec-val {
                font-size: 11px;
            }
            .panel-title {
                font-size: clamp(38px, 13vw, 68px);
                line-height: 0.85;
                margin: 0.4rem 0 0.8rem;
            }
            .c-panel-link {
                font-size: 13px;
                padding-top: 0.8rem;
            }
            .panel-poster-frame {
                max-width: 320px;
            }
            .panel-poster-img {
                max-height: 44vh;
            }

            /* CTA Section Full Width Buttons */
            .section-cta {
                padding: 56px 16px;
                gap: 20px;
            }
            .cta-massive-title {
                font-size: clamp(28px, 8.8vw, 44px);
                line-height: 0.94;
            }
            .cta-sub {
                font-size: 13px;
                line-height: 1.5;
            }
            .cta-btn-group {
                flex-direction: column;
                width: 100%;
                max-width: 300px;
                gap: 10px;
            }
            .cta-btn-group .btn {
                width: 100%;
                padding: 14px 20px !important;
                font-size: 12px !important;
            }

            /* Footer Responsive Stack */
            .site-footer {
                padding: 24px 16px;
                flex-direction: column;
                align-items: flex-start;
                gap: 16px;
            }
            .footer-nav-row {
                flex-wrap: wrap;
                gap: 10px 16px;
                font-size: 11px;
            }
        }

        /* ═══════════════════════════════════════════════════════════════
           EXTRA SMALL PHONES (<= 380px, e.g. iPhone SE)
           ═══════════════════════════════════════════════════════════════ */
        @media (max-width: 380px) {
            .hero-headline-top, .hero-headline-bottom {
                font-size: clamp(28px, 9.5vw, 36px);
            }
            .hero-micro-stats {
                grid-template-columns: 1fr;
                gap: 3px;
            }
            .c-panel-specs {
                grid-template-columns: 1fr;
            }
        }
    </style>"""

content, count = media_queries_pattern.subn(new_styles, content)
assert count == 1, f"Expected 1 replacement of media queries, got {count}"

# ─────────────────────────────────────────────────────────────────────────────
# 3. UPDATE THREE.JS CAMERA SETUP & RENDER LOOP FOR MOBILE
# ─────────────────────────────────────────────────────────────────────────────

# Setup dynamic camera distance function and mobile detection
old_setup = """        // 1. Scene, Camera, Renderer Setup
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(36, window.innerWidth / window.innerHeight, 0.1, 100);
        
        // Initial Stage 0 distance: 13.5 (Bigger & bolder machine framing)
        camera.position.set(0, 0, 13.5);

        let renderer = null;
        try {
            renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            renderer.toneMapping = THREE.ACESFilmicToneMapping;
            renderer.toneMappingExposure = 1.18;
            container.appendChild(renderer.domElement);
        } catch (e) {
            console.warn("WebGL not available or failed to initialize:", e);
        }"""

new_setup = """        // Detect Mobile Device / Touch
        const isMobileScreen = () => window.innerWidth < 768;
        
        // Adaptive Stage 0 Base Distance (Guarantees Full Machine Framing on Portrait Phones)
        function getBaseCameraDistance() {
            const aspect = window.innerWidth / window.innerHeight;
            if (aspect < 0.6) return 22.5;       // Tall modern phones (e.g. iPhone 14/15/16, Galaxy S23)
            if (aspect < 0.85) return 18.5;      // Compact phones & small tablets
            if (aspect < 1.1) return 15.5;       // Square-ish / iPad portrait
            return 13.5;                         // Desktop landscape
        }

        // 1. Scene, Camera, Renderer Setup
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(36, window.innerWidth / window.innerHeight, 0.1, 100);
        
        // Initial Stage 0 distance scaled for device aspect ratio
        camera.position.set(0, 0, getBaseCameraDistance());

        let renderer = null;
        try {
            renderer = new THREE.WebGLRenderer({ 
                antialias: !isMobileScreen(), // Disable MSAA on mobile for massive GPU battery savings
                alpha: true, 
                powerPreference: isMobileScreen() ? 'default' : 'high-performance' 
            });
            renderer.setSize(window.innerWidth, window.innerHeight);
            
            // Cap pixel ratio at 1.5 on mobile to avoid 3x retina fillrate throttling
            const maxPR = isMobileScreen() ? 1.5 : 2.0;
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, maxPR));
            
            // Shadows disabled on mobile devices to preserve 60fps & prevent phone overheating
            if (isMobileScreen()) {
                renderer.shadowMap.enabled = false;
            } else {
                renderer.shadowMap.enabled = true;
                renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            }
            
            renderer.toneMapping = THREE.ACESFilmicToneMapping;
            renderer.toneMappingExposure = 1.18;
            container.appendChild(renderer.domElement);
        } catch (e) {
            console.warn("WebGL not available or failed to initialize:", e);
        }"""

assert old_setup in content, "old_setup not found in content"
content = content.replace(old_setup, new_setup)

# Camera interpolation update in renderLoop
old_cam_interp = """            // 4. Continuous Camera Position Interpolation
            let camX, camY, camZ;
            if (p < 0.18) {
                // Stage 0: Hero resting 3D perspective
                const subP = p / 0.18;
                camX = 0;
                camY = 0;
                camZ = 13.5 - subP * 0.3; // 13.5 -> 13.2
            } else if (p < 0.45) {
                // Stage 1: Gliding approach
                const subP = (p - 0.18) / 0.27;
                const st = subP * subP * (3.0 - 2.0 * subP);
                camX = st * 0.10;
                camY = st * 0.05;
                camZ = 13.2 - st * 5.0; // 13.2 -> 8.2
            } else if (p < 0.72) {
                // Stage 2: Approach opening door & interior cavity
                const subP = (p - 0.45) / 0.27;
                const st = subP * subP * (3.0 - 2.0 * subP);
                camX = 0.10 + st * 0.08; // 0.10 -> 0.18
                camY = 0.05 + st * 0.30; // 0.05 -> 0.35
                camZ = 8.2 - st * 3.2;   // 8.2 -> 5.0
            } else if (p < 0.90) {
                // Stage 3: Smooth swoop up towards stereo optical array
                const subP = (p - 0.72) / 0.18;
                const st = subP * subP * (3.0 - 2.0 * subP);
                camX = 0.18 + st * (lensTargetX - 0.18); // 0.18 -> 0.315
                camY = 0.35 + st * (1.45 - 0.35);       // 0.35 -> 1.45
                camZ = 5.0 - st * 3.5;                  // 5.0 -> 1.50
            } else {
                // Stage 3 Final: Move directly into the lens aperture/pupil
                const subP = (p - 0.90) / 0.10;
                const st = subP * subP * (3.0 - 2.0 * subP);
                camX = lensTargetX;
                camY = 1.45 + st * (lensTargetY - 1.45); // 1.45 -> 1.562
                camZ = 1.50 - st * 0.85;                // 1.50 -> 0.65
            }
            camera.position.set(camX, camY, camZ);"""

new_cam_interp = """            // 4. Continuous Camera Position Interpolation (Adaptive for Mobile & Desktop)
            const baseDist = getBaseCameraDistance();
            const zScale = baseDist / 13.5;
            const stage1StartZ = 13.2 * zScale;
            const stage1EndZ = 8.2 * zScale;

            let camX, camY, camZ;
            if (p < 0.18) {
                // Stage 0: Hero resting 3D perspective
                const subP = p / 0.18;
                camX = 0;
                camY = 0;
                camZ = baseDist - subP * (0.3 * zScale);
            } else if (p < 0.45) {
                // Stage 1: Gliding approach
                const subP = (p - 0.18) / 0.27;
                const st = subP * subP * (3.0 - 2.0 * subP);
                camX = st * 0.10;
                camY = st * 0.05;
                camZ = stage1StartZ - st * (stage1StartZ - stage1EndZ);
            } else if (p < 0.72) {
                // Stage 2: Approach opening door & interior cavity (smoothly converges to 5.0)
                const subP = (p - 0.45) / 0.27;
                const st = subP * subP * (3.0 - 2.0 * subP);
                camX = 0.10 + st * 0.08;
                camY = 0.05 + st * 0.30;
                camZ = stage1EndZ - st * (stage1EndZ - 5.0);
            } else if (p < 0.90) {
                // Stage 3: Smooth swoop up towards stereo optical array
                const subP = (p - 0.72) / 0.18;
                const st = subP * subP * (3.0 - 2.0 * subP);
                camX = 0.18 + st * (lensTargetX - 0.18);
                camY = 0.35 + st * (1.45 - 0.35);
                camZ = 5.0 - st * 3.5;
            } else {
                // Stage 3 Final: Move directly into the lens aperture/pupil
                const subP = (p - 0.90) / 0.10;
                const st = subP * subP * (3.0 - 2.0 * subP);
                camX = lensTargetX;
                camY = 1.45 + st * (lensTargetY - 1.45);
                camZ = 1.50 - st * 0.85;
            }
            camera.position.set(camX, camY, camZ);"""

assert old_cam_interp in content, "old_cam_interp not found in content"
content = content.replace(old_cam_interp, new_cam_interp)

# Optimization: Pause rendering when scrolly section is out of viewport
old_render_end = """            if (renderer) renderer.render(scene, camera);
        }
        renderLoop();

        // Responsive Resizing
        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            if (renderer) renderer.setSize(window.innerWidth, window.innerHeight);
        });

        // ═══════════════════════════════════════════════════════════════
        // SIGNATURE PAPER TIGER STACKING PANELS CONTROLLER
        // ═══════════════════════════════════════════════════════════════
        const panels = document.querySelectorAll('.c-panel');

        function updatePanelStacking() {
            const vh = window.innerHeight;
            panels.forEach((panel, i) => {
                if (i < panels.length - 1) {
                    const nextPanel = panels[i + 1];
                    const rect = nextPanel.getBoundingClientRect();
                    if (rect.top <= vh && rect.top >= 0) {
                        const progress = 1 - (rect.top / vh);
                        const scale = 1 - (progress * 0.04);
                        const brightness = 1 - (progress * 0.25);
                        panel.style.transform = `scale(${scale})`;
                        panel.style.filter = `brightness(${brightness})`;
                    } else if (rect.top < 0) {
                        panel.style.transform = 'scale(0.96)';
                        panel.style.filter = 'brightness(0.75)';
                    } else {
                        panel.style.transform = 'scale(1)';
                        panel.style.filter = 'brightness(1)';
                    }
                }
            });
        }

        window.addEventListener('scroll', updatePanelStacking, { passive: true });
        window.addEventListener('resize', updatePanelStacking, { passive: true });
        updatePanelStacking();"""

new_render_end = """            // Battery / Performance Saver: Only execute WebGL render if scrolly section is visible
            if (renderer && isHeroScrollyVisible) {
                renderer.render(scene, camera);
            }
        }

        // Visibility Observer for WebGL rendering pause when user scrolls down into panels
        let isHeroScrollyVisible = true;
        if ('IntersectionObserver' in window) {
            const scrollyObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    isHeroScrollyVisible = entry.isIntersecting;
                });
            }, { threshold: 0.02 });
            scrollyObserver.observe(scrollyRoot);
        }

        renderLoop();

        // Responsive Resizing
        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            if (renderer) {
                renderer.setSize(window.innerWidth, window.innerHeight);
                const maxPR = isMobileScreen() ? 1.5 : 2.0;
                renderer.setPixelRatio(Math.min(window.devicePixelRatio, maxPR));
            }
        });

        // ═══════════════════════════════════════════════════════════════
        // MOBILE NAVIGATION DRAWER CONTROLLER
        // ═══════════════════════════════════════════════════════════════
        const mobileMenuBtn = document.getElementById('mobileMenuBtn');
        const mobileNavDrawer = document.getElementById('mobileNavDrawer');

        if (mobileMenuBtn && mobileNavDrawer) {
            mobileMenuBtn.addEventListener('click', () => {
                const isOpen = mobileNavDrawer.classList.toggle('is-open');
                mobileMenuBtn.classList.toggle('is-active', isOpen);
                mobileNavDrawer.setAttribute('aria-hidden', !isOpen);
                document.body.style.overflow = isOpen ? 'hidden' : '';
            });

            // Auto-close drawer when clicking any link
            mobileNavDrawer.querySelectorAll('a').forEach(link => {
                link.addEventListener('click', () => {
                    mobileNavDrawer.classList.remove('is-open');
                    mobileMenuBtn.classList.remove('is-active');
                    mobileNavDrawer.setAttribute('aria-hidden', 'true');
                    document.body.style.overflow = '';
                });
            });
        }

        // ═══════════════════════════════════════════════════════════════
        // SIGNATURE PAPER TIGER STACKING PANELS CONTROLLER
        // ═══════════════════════════════════════════════════════════════
        const panels = document.querySelectorAll('.c-panel');

        function updatePanelStacking() {
            // On mobile / tablet screens (< 960px), panels scroll natively without sticky scaling
            if (window.innerWidth < 960) {
                panels.forEach(panel => {
                    panel.style.transform = '';
                    panel.style.filter = '';
                });
                return;
            }

            const vh = window.innerHeight;
            panels.forEach((panel, i) => {
                if (i < panels.length - 1) {
                    const nextPanel = panels[i + 1];
                    const rect = nextPanel.getBoundingClientRect();
                    if (rect.top <= vh && rect.top >= 0) {
                        const progress = 1 - (rect.top / vh);
                        const scale = 1 - (progress * 0.04);
                        const brightness = 1 - (progress * 0.25);
                        panel.style.transform = `scale(${scale})`;
                        panel.style.filter = `brightness(${brightness})`;
                    } else if (rect.top < 0) {
                        panel.style.transform = 'scale(0.96)';
                        panel.style.filter = 'brightness(0.75)';
                    } else {
                        panel.style.transform = 'scale(1)';
                        panel.style.filter = 'brightness(1)';
                    }
                }
            });
        }

        window.addEventListener('scroll', updatePanelStacking, { passive: true });
        window.addEventListener('resize', updatePanelStacking, { passive: true });
        updatePanelStacking();"""

assert old_render_end in content, "old_render_end not found in content"
content = content.replace(old_render_end, new_render_end)

with open(INDEX_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Successfully updated {INDEX_PATH} with mobile responsiveness and performance optimizations!")
