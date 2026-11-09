#!/usr/bin/env python3
"""
Update script for Nex index.html:
1. Fix 3D door opening animation (negative angle, outwards towards user into +Z, smooth progress 0.35..0.65).
2. Eliminate jerky transition between Stage 2 and Stage 3 with continuous Steadicam lookAt & position interpolation.
3. Remove "VBOX ACTIVE VISION" badge and reduce overuse of "VBOX", replacing with AUTONOMOUS VISION / UNIVERSAL RETROFIT.
4. Custom redesign of the 4 stacking cards with technical metadata header, module kickers, spec matrix chips, corner reticles, and new custom editorial posters.
"""

import re
import shutil

FILE_PATH = "/Users/zhanasyl/Desktop/Code/Nex/index.html"
BACKUP_PATH = "/Users/zhanasyl/Desktop/Code/Nex/index.html.bak_before_user_feedback"

shutil.copyfile(FILE_PATH, BACKUP_PATH)
print(f"Backed up index.html to {BACKUP_PATH}")

with open(FILE_PATH, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Meta Description
html = html.replace(
    'content="Nex eliminates vending theft. Plug-and-play 120 FPS stereoscopic computer vision for smart fridges like VBox, preventing multi-item grab-and-run shrinkage in real-time."',
    'content="Nex eliminates micromarket shrinkage. Plug-and-play 120 FPS stereoscopic computer vision for smart fridges and micromarkets, preventing multi-item theft in real-time."'
)

# 2. Header Brand Badge: VBOX ACTIVE VISION -> AUTONOMOUS VISION
html = html.replace(
    '<span class="brand-badge">VBOX ACTIVE VISION</span>',
    '<span class="brand-badge">AUTONOMOUS VISION</span>'
)

# 3. Hero Micro-Stats: VBox Retrofit -> Universal Retrofit
html = html.replace(
    '<span class="stat-val">100%</span>\n                        <span>VBox Retrofit</span>',
    '<span class="stat-val">100%</span>\n                        <span>Universal Retrofit</span>'
)
# Also handle single-line variant if any
html = html.replace('<span>VBox Retrofit</span>', '<span>Universal Retrofit</span>')

# 4. Stage 2 Card Kicker: STAGE 02 • THE VBOX EXPLOIT -> STAGE 02 • DOOR UNLOCK VULNERABILITY
html = html.replace(
    '<span>STAGE 02 • THE VBOX EXPLOIT</span>',
    '<span>STAGE 02 • DOOR UNLOCK VULNERABILITY</span>'
)

# 5. Running Marquee Strip: 100% VBOX RETROFIT READY -> 100% UNIVERSAL RETROFIT
html = html.replace(
    '<span class="marquee-item"><span class="badge">100%</span> VBOX RETROFIT READY</span>',
    '<span class="marquee-item"><span class="badge">100%</span> UNIVERSAL RETROFIT</span>'
)

# 6. Canvas Texture Header Marquee on 3D Fridge: NEX • VBOX ACTIVE -> NEX • NEURAL VISION
html = html.replace(
    "ctx.fillText('NEX • VBOX ACTIVE', 512, 142);",
    "ctx.fillText('NEX • NEURAL VISION', 512, 142);"
)
html = html.replace(
    '// High-Resolution Top Marquee Canvas ("NEX • VBOX ACTIVE")',
    '// High-Resolution Top Marquee Canvas ("NEX • NEURAL VISION")'
)
html = html.replace(
    '// ── Top Header Brand Marquee ("NEX • VBOX ACTIVE") ──',
    '// ── Top Header Brand Marquee ("NEX • NEURAL VISION") ──'
)

# 7. CSS for .c-panel Stacking Cards Redesign
old_panel_css_pattern = re.compile(
    r'/\* ═══════════════════════════════════════════════════════════════\s+'
    r'PAPER TIGER SIGNATURE STACKING PANELS.*?@media \(max-width: 960px\) \{',
    re.DOTALL
)

new_panel_css = """/* ═══════════════════════════════════════════════════════════════
   SIGNATURE STACKING PANELS (c-panel-scroll)
   High-tech editorial brutalist architecture:
   Full-page sticky stacking panels with technical metadata headers,
   index badges, specification matrix chips, corner reticles,
   monumental titles, and custom high-resolution editorial posters.
   ═══════════════════════════════════════════════════════════════ */
        .c-panel-scroll {
            width: 100%;
            position: relative;
            background: #000000;
        }

        .c-panel {
            position: sticky;
            top: 0;
            height: 100vh;
            min-height: 720px;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
            padding: 2.2rem 6vw 3.2rem;
            overflow: hidden;
            will-change: transform;
            /* Elevation shadow separating stacking panels */
            box-shadow: 0 -24px 60px rgba(0, 0, 0, 0.55);
        }

        .c-panel.is-1 {
            background-color: #07080a;
            color: #FFFFFF;
            z-index: 10;
        }

        .c-panel.is-2 {
            background-color: #9589d3;
            color: #09090b;
            z-index: 20;
        }

        .c-panel.is-3 {
            background-color: #fa435b;
            color: #000000;
            z-index: 30;
        }

        .c-panel.is-4 {
            background-color: #07090e;
            color: #FFFFFF;
            z-index: 40;
        }

        /* Top Technical Metadata Rail on Each Panel */
        .c-panel-top-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 1.1rem;
            margin-bottom: 1.4rem;
            border-bottom: 1px solid currentColor;
            opacity: 0.82;
            font-family: var(--font-mono);
            font-size: 11px;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            font-weight: 700;
        }

        .c-panel-top-meta .meta-tag {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .c-panel-top-meta .meta-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: currentColor;
            display: inline-block;
        }

        .c-panel-top-meta .meta-badge {
            padding: 4px 10px;
            border: 1px solid currentColor;
            border-radius: 3px;
            font-size: 10px;
            letter-spacing: 0.14em;
            font-weight: 800;
        }

        .c-panel-grid {
            display: grid;
            grid-template-columns: 1.15fr 0.85fr;
            align-items: stretch;
            flex: 1;
            min-height: 0;
            gap: 2rem;
        }

        .c-panel-main {
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            max-width: 620px;
            z-index: 2;
            padding-right: 1.5rem;
        }

        .c-panel-top {
            display: flex;
            flex-direction: column;
            align-items: flex-start;
        }

        .c-panel-badge-row {
            display: flex;
            align-items: center;
            gap: 14px;
            margin-bottom: 1.2rem;
        }

        .c-panel-num {
            width: 38px;
            height: 38px;
            border-radius: 50%;
            border: 1.5px solid currentColor;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            font-weight: 700;
            font-family: var(--font-mono);
            flex-shrink: 0;
            line-height: 1;
        }

        .c-panel-kicker {
            font-family: var(--font-mono);
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            opacity: 0.75;
        }

        .c-panel-desc {
            max-width: 48ch;
            margin-bottom: 1.3rem;
        }

        .c-panel-desc p {
            font-family: var(--font-body);
            font-size: 16px;
            line-height: 1.55;
            letter-spacing: -0.01em;
            margin: 0;
            opacity: 0.92;
        }

        .c-panel-desc strong {
            font-weight: 600;
            display: block;
            margin-bottom: 6px;
        }

        /* Technical Specification Matrix Chips */
        .c-panel-specs {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 1.3rem;
        }

        .c-spec-chip {
            padding: 7px 12px;
            border: 1px solid currentColor;
            opacity: 0.9;
            border-radius: 4px;
            display: flex;
            flex-direction: column;
            gap: 2px;
            font-family: var(--font-mono);
        }

        .c-spec-chip .spec-label {
            font-size: 9px;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            opacity: 0.7;
        }

        .c-spec-chip .spec-val {
            font-size: 12px;
            font-weight: 700;
            letter-spacing: -0.01em;
        }

        .c-panel.is-1 .c-spec-chip {
            background: rgba(255, 255, 255, 0.05);
            border-color: rgba(255, 255, 255, 0.2);
        }
        .c-panel.is-1 .c-spec-chip.is-alert .spec-val {
            color: #fa435b;
        }

        .c-panel.is-2 .c-spec-chip {
            background: rgba(0, 0, 0, 0.06);
            border-color: rgba(0, 0, 0, 0.2);
        }

        .c-panel.is-3 .c-spec-chip {
            background: rgba(0, 0, 0, 0.08);
            border-color: rgba(0, 0, 0, 0.25);
        }

        .c-panel.is-4 .c-spec-chip {
            background: rgba(56, 189, 248, 0.06);
            border-color: rgba(56, 189, 248, 0.25);
        }
        .c-panel.is-4 .c-spec-chip.is-accent .spec-val {
            color: #38bdf8;
        }

        .c-panel_bt {
            display: flex;
            flex-direction: column;
            width: 100%;
            margin-top: auto;
        }

        .panel-title {
            font-family: 'Rightgrotesk', var(--font-headline), sans-serif;
            font-size: clamp(72px, 11vw, 175px);
            line-height: 0.78;
            letter-spacing: -0.025em;
            text-transform: uppercase;
            font-weight: 900;
            margin: 0 0 1.2rem 0;
            color: inherit;
            word-break: break-word;
        }

        .c-panel-link {
            display: flex;
            justify-content: space-between;
            align-items: center;
            width: 100%;
            padding-top: 1.1rem;
            border-top: 1px solid currentColor;
            text-decoration: none;
            color: inherit;
            font-family: var(--font-body);
            font-size: 15px;
            font-weight: 500;
            letter-spacing: -0.01em;
            opacity: 0.85;
            transition: opacity 0.2s ease;
        }

        .c-panel-link:hover {
            opacity: 1;
        }

        .c-panel-link .arrow {
            font-size: 19px;
            margin-left: 12px;
            transition: transform 0.2s ease;
        }

        .c-panel-link:hover .arrow {
            transform: translate(3px, -3px);
        }

        .c-panel-visual {
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            z-index: 1;
        }

        .panel-poster-frame {
            position: relative;
            max-width: 450px;
            width: 88%;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        /* Technical Corner Reticles */
        .poster-reticle {
            position: absolute;
            width: 14px;
            height: 14px;
            border-color: currentColor;
            opacity: 0.6;
            pointer-events: none;
            z-index: 4;
        }
        .poster-reticle.top-left {
            top: -8px;
            left: -8px;
            border-top: 2px solid currentColor;
            border-left: 2px solid currentColor;
        }
        .poster-reticle.top-right {
            top: -8px;
            right: -8px;
            border-top: 2px solid currentColor;
            border-right: 2px solid currentColor;
        }
        .poster-reticle.bottom-left {
            bottom: -8px;
            left: -8px;
            border-bottom: 2px solid currentColor;
            border-left: 2px solid currentColor;
        }
        .poster-reticle.bottom-right {
            bottom: -8px;
            right: -8px;
            border-bottom: 2px solid currentColor;
            border-right: 2px solid currentColor;
        }

        .panel-poster-img {
            width: 100%;
            height: auto;
            max-height: 72vh;
            object-fit: contain;
            border-radius: 4px;
            box-shadow: 12px 20px 50px rgba(0, 0, 0, 0.55);
            display: block;
            user-select: none;
            -webkit-user-drag: none;
            transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.4s ease;
        }

        .panel-poster-frame:hover .panel-poster-img {
            transform: perspective(1200px) rotate(0deg) scale(1.02) translateY(-4px);
            box-shadow: 0 28px 70px rgba(0, 0, 0, 0.65);
        }

        .c-panel.is-1 .panel-poster-img {
            transform: perspective(1200px) rotate(-1.5deg);
        }

        .c-panel.is-2 .panel-poster-img {
            transform: perspective(1200px) rotate(1.8deg);
            box-shadow: 12px 20px 50px rgba(0, 0, 0, 0.35);
        }

        .c-panel.is-3 .panel-poster-img {
            transform: perspective(1200px) rotate(-1.6deg);
            box-shadow: 12px 20px 50px rgba(0, 0, 0, 0.4);
        }

        .c-panel.is-4 .panel-poster-img {
            transform: perspective(1200px) rotate(1.5deg);
        }

        @media (max-width: 960px) {"""

assert old_panel_css_pattern.search(html), "Could not find old_panel_css in index.html"
html = old_panel_css_pattern.sub(new_panel_css, html)
print("Updated CSS for .c-panel stacking cards!")

# 8. HTML Stacking Cards Structure
old_panels_html_pattern = re.compile(
    r'<div class="c-panel-scroll" id="panels">.*?</div>\s+<!-- ═══════════════════════════════════════════════════════════════\s+FINAL CALL TO ACTION',
    re.DOTALL
)

new_panels_html = """<div class="c-panel-scroll" id="panels">
        
        <!-- ════ PANEL 1: PITCH BLACK / BLINDSPOT ════ -->
        <section class="c-panel is-1" id="panel-1">
            <div class="c-panel-top-meta">
                <div class="meta-tag"><span class="meta-dot"></span> THREAT VECTOR 01 // SURVEILLANCE PARADOX</div>
                <div class="meta-badge">UNRESOLVED LOSS: 18% – 28%</div>
            </div>

            <div class="c-panel-grid">
                <div class="c-panel-main">
                    <div class="c-panel-top">
                        <div class="c-panel-badge-row">
                            <span class="c-panel-num">01</span>
                            <span class="c-panel-kicker">PASSIVE CCTV COLLAPSE</span>
                        </div>
                        <div class="c-panel-desc">
                            <p>
                                <strong>Обычные камеры создают фальшивое чувство безопасности.</strong> Пассивная камера — это просто слепая видеозапись без синхронизации с корзиной. Она не способна понять в моменте, кто оплатил товар, а кто украл. При инциденте оператору приходится вручную отсматривать 70+ часов архива, пока нарушитель безнаказанно обчищает следующую точку.
                            </p>
                        </div>

                        <!-- Technical Specification Matrix Chips -->
                        <div class="c-panel-specs">
                            <div class="c-spec-chip">
                                <span class="spec-label">Задержка аудита</span>
                                <span class="spec-val">72+ часа (вручную)</span>
                            </div>
                            <div class="c-spec-chip">
                                <span class="spec-label">Точность фиксации</span>
                                <span class="spec-val">0.0% на точке</span>
                            </div>
                            <div class="c-spec-chip is-alert">
                                <span class="spec-label">Списания сети</span>
                                <span class="spec-val">18% – 28% выручки</span>
                            </div>
                        </div>
                    </div>

                    <div class="c-panel_bt">
                        <h2 class="panel-title">BLINDSPOT</h2>
                        <a href="#panel-2" class="c-panel-link">
                            <span>Архитектура защиты от скрытых краж</span>
                            <span class="arrow">↗</span>
                        </a>
                    </div>
                </div>

                <div class="c-panel-visual">
                    <div class="panel-poster-frame">
                        <div class="poster-reticle top-left"></div>
                        <div class="poster-reticle top-right"></div>
                        <div class="poster-reticle bottom-left"></div>
                        <div class="poster-reticle bottom-right"></div>
                        <img class="panel-poster-img" src="./posters/poster_1_blindspot.webp" alt="NEX Blindspot Technical Architecture Poster" />
                    </div>
                </div>
            </div>
        </section>

        <!-- ════ PANEL 2: LAVENDER / THEFT VAULT ════ -->
        <section class="c-panel is-2" id="panel-2">
            <div class="c-panel-top-meta">
                <div class="meta-tag"><span class="meta-dot"></span> NEURAL MODULE 02 // REAL-TIME IDENTITY COMMIT</div>
                <div class="meta-badge">EDGE INFERENCE: 11 MS</div>
            </div>

            <div class="c-panel-grid">
                <div class="c-panel-main">
                    <div class="c-panel-top">
                        <div class="c-panel-badge-row">
                            <span class="c-panel-num">02</span>
                            <span class="c-panel-kicker">BIOMETRIC BLACKLISTING</span>
                        </div>
                        <div class="c-panel-desc">
                            <p>
                                <strong>Фиксация нарушителя ровно в момент кражи, а не недели спустя.</strong> Потолочные стереокамеры Nex непрерывно отслеживают 3D-траекторию рук по всем полкам. Как только товар покидает полку без последующей оплаты в корзине, 512-мерный биометрический вектор лица нарушителя мгновенно коммитится в распределенную базу Theft Vault.
                            </p>
                        </div>

                        <!-- Technical Specification Matrix Chips -->
                        <div class="c-panel-specs">
                            <div class="c-spec-chip">
                                <span class="spec-label">Скорость коммита</span>
                                <span class="spec-val">&lt; 15 миллисекунд</span>
                            </div>
                            <div class="c-spec-chip">
                                <span class="spec-label">Точность распознавания</span>
                                <span class="spec-val">99.8% (FP16 NPU)</span>
                            </div>
                            <div class="c-spec-chip">
                                <span class="spec-label">Приватность</span>
                                <span class="spec-val">Без сырых фото</span>
                            </div>
                        </div>
                    </div>

                    <div class="c-panel_bt">
                        <h2 class="panel-title">THEFT VAULT</h2>
                        <a href="#panel-3" class="c-panel-link">
                            <span>Как работает биометрический протокол</span>
                            <span class="arrow">↗</span>
                        </a>
                    </div>
                </div>

                <div class="c-panel-visual">
                    <div class="panel-poster-frame">
                        <div class="poster-reticle top-left"></div>
                        <div class="poster-reticle top-right"></div>
                        <div class="poster-reticle bottom-left"></div>
                        <div class="poster-reticle bottom-right"></div>
                        <img class="panel-poster-img" src="./posters/poster_2_vault.webp" alt="NEX Biometric Theft Vault Technical Poster" />
                    </div>
                </div>
            </div>
        </section>

        <!-- ════ PANEL 3: TART CORAL / LOCKOUT ════ -->
        <section class="c-panel is-3" id="panel-3">
            <div class="c-panel-top-meta">
                <div class="meta-tag"><span class="meta-dot"></span> HARDWARE ENFORCEMENT 03 // DISTRIBUTED IMMUNITY</div>
                <div class="meta-badge">LOCK FORCE: 300 KG</div>
            </div>

            <div class="c-panel-grid">
                <div class="c-panel-main">
                    <div class="c-panel-top">
                        <div class="c-panel-badge-row">
                            <span class="c-panel-num">03</span>
                            <span class="c-panel-kicker">PHYSICAL ACCESS DENIAL</span>
                        </div>
                        <div class="c-panel-desc">
                            <p>
                                <strong>Один инцидент защищает сразу всю сеть микромаркетов.</strong> Лицо нарушителя синхронизируется по всем аппаратам оператора. Когда вор подходит к любому другому холодильнику сети и сканирует Kaspi QR — контроллер наотрез отказывается разблокировать электромагнитный замок с усилием удержания 300 кг.
                            </p>
                        </div>

                        <!-- Technical Specification Matrix Chips -->
                        <div class="c-panel-specs">
                            <div class="c-spec-chip">
                                <span class="spec-label">Усилие замка</span>
                                <span class="spec-val">300 кг (2940 Н)</span>
                            </div>
                            <div class="c-spec-chip">
                                <span class="spec-label">Синхронизация</span>
                                <span class="spec-val">&lt; 120ms по всей сети</span>
                            </div>
                            <div class="c-spec-chip">
                                <span class="spec-label">Kaspi / QR отказ</span>
                                <span class="spec-val">Мгновенный блок</span>
                            </div>
                        </div>
                    </div>

                    <div class="c-panel_bt">
                        <h2 class="panel-title">LOCKOUT</h2>
                        <a href="#panel-4" class="c-panel-link">
                            <span>Спецификация сетевой блокировки</span>
                            <span class="arrow">↗</span>
                        </a>
                    </div>
                </div>

                <div class="c-panel-visual">
                    <div class="panel-poster-frame">
                        <div class="poster-reticle top-left"></div>
                        <div class="poster-reticle top-right"></div>
                        <div class="poster-reticle bottom-left"></div>
                        <div class="poster-reticle bottom-right"></div>
                        <img class="panel-poster-img" src="./posters/poster_3_lockout.webp" alt="NEX Autonomous Lockout Technical Poster" />
                    </div>
                </div>
            </div>
        </section>

        <!-- ════ PANEL 4: PITCH BLACK / RETROFIT ════ -->
        <section class="c-panel is-4" id="panel-4">
            <div class="c-panel-top-meta">
                <div class="meta-tag"><span class="meta-dot"></span> INTEGRATION SPEC 04 // UNIVERSAL PLUG-AND-PLAY</div>
                <div class="meta-badge">INSTALL: 30 MIN</div>
            </div>

            <div class="c-panel-grid">
                <div class="c-panel-main">
                    <div class="c-panel-top">
                        <div class="c-panel-badge-row">
                            <span class="c-panel-num">04</span>
                            <span class="c-panel-kicker">RAPID FLEET INTEGRATION</span>
                        </div>
                        <div class="c-panel-desc">
                            <p>
                                <strong>Вам не нужно менять холодильники и списывать существующий парк.</strong> Модуль Nex монтируется в любые микромаркеты (совместимо с VBox, Unicum и кастомными шкафами с замками 12V/24V) прямо на торговой точке за 30 минут: стереопод крепится на потолок, шлейф подключается к контроллеру замка. Экономика автомата выходит в плюс с первого месяца.
                            </p>
                        </div>

                        <!-- Technical Specification Matrix Chips -->
                        <div class="c-panel-specs">
                            <div class="c-spec-chip">
                                <span class="spec-label">Время монтажа</span>
                                <span class="spec-val">30 минут на точке</span>
                            </div>
                            <div class="c-spec-chip">
                                <span class="spec-label">Совместимость</span>
                                <span class="spec-val">VBox, Unicum, 12V/24V</span>
                            </div>
                            <div class="c-spec-chip is-accent">
                                <span class="spec-label">Окупаемость</span>
                                <span class="spec-val">1-й месяц работы</span>
                            </div>
                        </div>
                    </div>

                    <div class="c-panel_bt">
                        <h2 class="panel-title">RETROFIT</h2>
                        <a href="#cta" class="c-panel-link">
                            <span>Запросить пилот на 3 аппарата</span>
                            <span class="arrow">↗</span>
                        </a>
                    </div>
                </div>

                <div class="c-panel-visual">
                    <div class="panel-poster-frame">
                        <div class="poster-reticle top-left"></div>
                        <div class="poster-reticle top-right"></div>
                        <div class="poster-reticle bottom-left"></div>
                        <div class="poster-reticle bottom-right"></div>
                        <img class="panel-poster-img" src="./posters/poster_4_retrofit.webp" alt="NEX Universal Retrofit Technical Poster" />
                    </div>
                </div>
            </div>
        </section>

    </div>

    <!-- ═══════════════════════════════════════════════════════════════
         FINAL CALL TO ACTION"""

assert old_panels_html_pattern.search(html), "Could not find old_panels_html in index.html"
html = old_panels_html_pattern.sub(new_panels_html, html)
print("Updated HTML for .c-panel stacking cards!")

# 9. Three.js renderLoop Continuous Choreography
old_render_loop_pattern = re.compile(
    r'// ── SCROLL PHASES CHOREOGRAPHY ──.*?renderer\.render\(scene, camera\);',
    re.DOTALL
)

new_render_loop = """// ── SCROLL PHASES CHOREOGRAPHY (SMOOTH CONTINUOUS STEADICAM & LOOKAT) ──
            
            // 1. Door opening: smoothly between p = 0.35 and p = 0.65
            // NEGATIVE angle swings door OUTWARDS towards user in +Z (-1.95 rad = -112 deg)
            const doorP = Math.max(0.0, Math.min(1.0, (p - 0.35) / 0.30));
            const smoothDoor = doorP * doorP * (3.0 - 2.0 * doorP);
            doorPivot.rotation.y = -smoothDoor * 1.95;

            // Interior illumination flares up smoothly as door unlocks
            interiorCeilingLight.intensity = 3.4 + smoothDoor * 2.6;

            // 2. Machine Chassis 3D Rotation
            let rotY;
            if (p < 0.18) {
                rotY = -0.22;
            } else if (p < 0.38) {
                const t = (p - 0.18) / 0.20;
                const st = t * t * (3.0 - 2.0 * t);
                rotY = -0.22 + st * 0.60; // -0.22 -> +0.38
            } else {
                const t = Math.min(1.0, (p - 0.38) / 0.22);
                const st = t * t * (3.0 - 2.0 * t);
                rotY = 0.38 - st * 0.33; // +0.38 -> +0.05
            }
            machineGroup.rotation.y = rotY;
            machineGroup.rotation.x = (p < 0.18) ? 0.04 * (1.0 - p / 0.18) : 0;

            // 3. Right optical lens target in world coordinates
            const lensTargetX = 0.315;
            const lensTargetY = 1.562;
            const lensTargetZ = 0.646;

            // Continuous LookAt Vector: smoothly ascends from (0, 0.05, 0) between p = 0.45 and p = 0.85
            // This ELIMINATES the violent instantaneous lookAt snap that previously whipped the camera!
            const targetT = Math.max(0.0, Math.min(1.0, (p - 0.45) / 0.40));
            const smoothTargetT = targetT * targetT * (3.0 - 2.0 * targetT);
            const lookAtX = smoothTargetT * lensTargetX;
            const lookAtY = 0.05 + smoothTargetT * (lensTargetY - 0.05);
            const lookAtZ = smoothTargetT * lensTargetZ;
            camera.lookAt(lookAtX, lookAtY, lookAtZ);

            // 4. Continuous Camera Position Interpolation
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
            camera.position.set(camX, camY, camZ);

            // 5. HUD Step Indicator Text
            if (p < 0.20) {
                hudStep.textContent = "STANDBY STATE";
            } else if (p < 0.45) {
                hudStep.textContent = "HARDWARE ARCHITECTURE";
            } else if (p < 0.72) {
                hudStep.textContent = "DOOR UNLOCK VULNERABILITY";
            } else {
                hudStep.textContent = "STEREOSCOPIC OPTICAL ARRAY";
            }

            // 6. UI Narrative Cards & Lens Plunge Transitions
            // Stage 2 Exploit Card (smooth fade in 0.42..0.48, fade out 0.68..0.74)
            let exploitOpacity = 0;
            if (p >= 0.42 && p <= 0.74) {
                if (p < 0.48) exploitOpacity = (p - 0.42) / 0.06;
                else if (p > 0.68) exploitOpacity = (0.74 - p) / 0.06;
                else exploitOpacity = 1;
            }
            stageCardExploit.style.opacity = `${exploitOpacity}`;
            stageCardExploit.style.pointerEvents = (exploitOpacity > 0.1) ? 'auto' : 'none';
            if (exploitOpacity > 0.02) stageCardExploit.classList.add('is-visible');
            else stageCardExploit.classList.remove('is-visible');

            // Stage 3 Active Vision Card (smooth fade in 0.72..0.78, fade out >= 0.94)
            let visionOpacity = 0;
            if (p >= 0.72) {
                if (p < 0.78) visionOpacity = (p - 0.72) / 0.06;
                else if (p >= 0.94) visionOpacity = Math.max(0, 1 - (p - 0.94) / 0.06);
                else visionOpacity = 1;
            }
            stageCardVision.style.opacity = `${visionOpacity}`;
            stageCardVision.style.pointerEvents = (visionOpacity > 0.1) ? 'auto' : 'none';
            if (visionOpacity > 0.02) stageCardVision.classList.add('is-visible');
            else stageCardVision.classList.remove('is-visible');

            // Optical Iris Black Plunge Overlay (p >= 0.94)
            if (p >= 0.94) {
                const plungeRatio = Math.min(1.0, (p - 0.94) / 0.06);
                lensPlungeOverlay.style.opacity = `${plungeRatio}`;
                hudTopBar.style.opacity = `${1 - plungeRatio}`;
            } else {
                lensPlungeOverlay.style.opacity = "0";
                hudTopBar.style.opacity = "1";
            }
            scrollPrompt.style.opacity = (p > 0.90) ? "0" : "1";

            renderer.render(scene, camera);"""

assert old_render_loop_pattern.search(html), "Could not find old_render_loop in index.html"
html = old_render_loop_pattern.sub(new_render_loop, html)
print("Updated Three.js renderLoop continuous choreography!")

# 10. Enhance Glass Material and Door Highlights
old_glass_mat = """        const glassMat = new THREE.MeshPhysicalMaterial({
            color: 0xffffff,
            transparent: true,
            opacity: 0.14,
            roughness: 0.03,
            metalness: 0.05,
            transmission: 0.94,
            ior: 1.5,
            clearcoat: 1.0,
            clearcoatRoughness: 0.03
        });"""

new_glass_mat = """        const glassMat = new THREE.MeshPhysicalMaterial({
            color: 0xf5f8ff,
            transparent: true,
            opacity: 0.22,
            roughness: 0.05,
            metalness: 0.1,
            transmission: 0.90,
            ior: 1.52,
            clearcoat: 1.0,
            clearcoatRoughness: 0.04
        });"""

if old_glass_mat in html:
    html = html.replace(old_glass_mat, new_glass_mat)
    print("Enhanced glass material!")

with open(FILE_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print("SUCCESS: index.html has been completely updated!")
