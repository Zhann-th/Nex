const state = {
    cameraActive: false,
    theme: 'nebula',
    mode: 'auto',
    audioEnabled: false,
    particleCount: 2500,
    gravity: 2.5,
    handDetected: true,
    handPos: { x: 0.5, y: 0.5, z: 0.0 },
    simAngle: 0
};
let activeFingerCores = [
    { x: window.innerWidth * 0.42, y: window.innerHeight * 0.5 },
    { x: window.innerWidth * 0.58, y: window.innerHeight * 0.5 }
];
let targetFingerCores = [
    { x: window.innerWidth * 0.42, y: window.innerHeight * 0.5 },
    { x: window.innerWidth * 0.58, y: window.innerHeight * 0.5 }
];
const webcamVideo = document.getElementById('webcam-video');
const trackingCanvas = document.getElementById('tracking-canvas');
const ctx = trackingCanvas.getContext('2d');
const cameraToggleBtn = document.getElementById('camera-toggle-btn');
const audioToggleBtn = document.getElementById('audio-toggle-btn');
const snapshotBtn = document.getElementById('snapshot-btn');
const fullscreenBtn = document.getElementById('fullscreen-btn');
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');
const fpsDisplay = document.getElementById('fps-display');
const gestureNameEl = document.getElementById('gesture-name');
const confidenceValEl = document.getElementById('confidence-value');
const confidenceFillEl = document.getElementById('confidence-fill');
const coordXEl = document.getElementById('coord-x');
const coordYEl = document.getElementById('coord-y');
const coordZEl = document.getElementById('coord-z');
const customColorPicker = document.getElementById('custom-color-picker');
const colorHexVal = document.getElementById('color-hex-val');
const themeButtons = document.querySelectorAll('.theme-btn');
const simNotice = document.getElementById('sim-notice');
let activeGlowSprites = [];
function hexToHSL(hex) {
    let result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    if (!result) return { h: 145, s: 75, l: 50 };
    let r = parseInt(result[1], 16) / 255;
    let g = parseInt(result[2], 16) / 255;
    let b = parseInt(result[3], 16) / 255;
    let max = Math.max(r, g, b), min = Math.min(r, g, b);
    let h, s, l = (max + min) / 2;
    if (max === min) {
        h = s = 0;
    } else {
        let d = max - min;
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        switch (max) {
            case r: h = (g - b) / d + (g < b ? 6 : 0); break;
            case g: h = (b - r) / d + 2; break;
            case b: h = (r - g) / d + 4; break;
        }
        h /= 6;
    }
    return { h: Math.round(h * 360), s: Math.round(s * 100), l: Math.round(l * 100) };
}
function updateCustomColor(hexColor) {
    state.currentColorHex = hexColor;
    if (colorHexVal) colorHexVal.textContent = hexColor.toUpperCase();
    if (customColorPicker) customColorPicker.value = hexColor;
    const hsl = hexToHSL(hexColor);
    activeGlowSprites = [];
    const offsets = [-18, -9, -4, 4, 9, 18];
    offsets.forEach(off => {
        const h = (hsl.h + off + 360) % 360;
        const cCore = `hsl(${h}, ${hsl.s}%, ${Math.min(95, hsl.l + 18)}%)`;
        const cOuter = `hsl(${h}, ${hsl.s}%, ${Math.max(20, hsl.l - 5)}%)`;
        activeGlowSprites.push(createGlowSprite(cOuter, cCore));
    });
}
function createGlowSprite(c1, c2) {
    const canvas = document.createElement('canvas');
    canvas.width = 36;
    canvas.height = 36;
    const gCtx = canvas.getContext('2d');
    const grad = gCtx.createRadialGradient(18, 18, 0, 18, 18, 18);
    grad.addColorStop(0, '#ffffff');
    grad.addColorStop(0.3, c2);
    grad.addColorStop(0.65, c1);
    grad.addColorStop(1, 'rgba(0,0,0,0)');
    gCtx.fillStyle = grad;
    gCtx.fillRect(0, 0, 36, 36);
    return canvas;
}
function initGlowSprites() {
    updateCustomColor('#94a3b8');
}
let handStillnessFactor = 0.0;
let prevPrimaryCorePos = { x: 0, y: 0 };
function updateStillnessTracking() {
    if (activeFingerCores.length > 0 && state.handDetected) {
        const primaryCore = activeFingerCores[0];
        const distMoved = Math.hypot(primaryCore.x - prevPrimaryCorePos.x, primaryCore.y - prevPrimaryCorePos.y);
        prevPrimaryCorePos = { x: primaryCore.x, y: primaryCore.y };
        if (distMoved < 3.2) {
            handStillnessFactor = Math.min(1.0, handStillnessFactor + 0.022);
        } else {
            handStillnessFactor = Math.max(0.0, handStillnessFactor - 0.14);
        }
    } else {
        handStillnessFactor = 0.0;
    }
}
let prevHandDetectedState = true;
let shockwaves = [];
let lastHandCenterPos = { x: window.innerWidth / 2, y: window.innerHeight / 2 };
function triggerHandState(detected) {
    if (prevHandDetectedState && !detected) {
        shockwaves.push(
            { x: lastHandCenterPos.x, y: lastHandCenterPos.y, radius: 15, maxRadius: 750, speed: 32, alpha: 1.0, width: 9 },
            { x: lastHandCenterPos.x, y: lastHandCenterPos.y, radius: 10, maxRadius: 550, speed: 22, alpha: 0.85, width: 5 },
            { x: lastHandCenterPos.x, y: lastHandCenterPos.y, radius: 5, maxRadius: 350, speed: 14, alpha: 0.65, width: 3 }
        );
    }
    prevHandDetectedState = detected;
    state.handDetected = detected;
}
let mainCanvas, mainCtx;
let particles = [];
let clickParticles = [];
const BURST_COLORS = ['#ffffff', '#00f2fe', '#a855f7', '#38bdf8', '#2ecc71', '#fbbf24', '#f43f5e'];
class ClickParticle {
    constructor(x, y, colorHex) {
        this.x = x;
        this.y = y;
        this.color = colorHex || BURST_COLORS[Math.floor(Math.random() * BURST_COLORS.length)];
        const angle = Math.random() * Math.PI * 2;
        const speed = Math.random() * 16 + 5;
        this.vx = Math.cos(angle) * speed;
        this.vy = Math.sin(angle) * speed;
        this.size = Math.random() * 14 + 6;
        this.alpha = 1.0;
        this.decay = Math.random() * 0.035 + 0.02;
        this.type = Math.random() < 0.4 ? 'star' : (Math.random() < 0.7 ? 'diamond' : 'orb');
        this.rotation = Math.random() * Math.PI * 2;
        this.spin = (Math.random() - 0.5) * 0.3;
    }
    update() {
        this.x += this.vx;
        this.y += this.vy;
        this.vx *= 0.91;
        this.vy *= 0.91;
        this.size *= 0.95;
        this.rotation += this.spin;
        this.alpha -= this.decay;
    }
    draw(ctx) {
        if (this.alpha <= 0 || this.size <= 0.5) return;
        ctx.save();
        ctx.translate(this.x, this.y);
        ctx.rotate(this.rotation);
        ctx.globalAlpha = Math.max(0, this.alpha);
        ctx.fillStyle = this.color;
        if (this.type === 'star') {
            ctx.beginPath();
            const s = this.size;
            const inner = s * 0.28;
            for (let i = 0; i < 8; i++) {
                const r = (i % 2 === 0) ? s : inner;
                const a = (i * Math.PI) / 4;
                const px = Math.cos(a) * r;
                const py = Math.sin(a) * r;
                if (i === 0) ctx.moveTo(px, py);
                else ctx.lineTo(px, py);
            }
            ctx.closePath();
            ctx.fill();
        } else if (this.type === 'diamond') {
            ctx.beginPath();
            const s = this.size;
            ctx.moveTo(0, -s);
            ctx.lineTo(s * 0.55, 0);
            ctx.lineTo(0, s);
            ctx.lineTo(-s * 0.55, 0);
            ctx.closePath();
            ctx.fill();
        } else {
            ctx.beginPath();
            ctx.arc(0, 0, this.size / 2, 0, Math.PI * 2);
            ctx.fill();
        }
        ctx.restore();
    }
}
function spawnClickBurst(x, y) {
    const themeHex = getThemeHexColor();
    const count = 30;
    for (let i = 0; i < count; i++) {
        const color = Math.random() > 0.35 ? themeHex : BURST_COLORS[Math.floor(Math.random() * BURST_COLORS.length)];
        clickParticles.push(new ClickParticle(x, y, color));
    }
    shockwaves.push(
        { x: x, y: y, radius: 12, maxRadius: 280, speed: 20, alpha: 1.0, width: 7 },
        { x: x, y: y, radius: 6, maxRadius: 180, speed: 13, alpha: 0.8, width: 4 }
    );
    particles.forEach(p => {
        const dx = p.x - x;
        const dy = p.y - y;
        const dist = Math.hypot(dx, dy) + 0.1;
        if (dist < 300) {
            const force = (1 - dist / 300) * 24;
            p.vx += (dx / dist) * force;
            p.vy += (dy / dist) * force;
        }
    });
}
class Particle {
    constructor(w, h) {
        this.variantIndex = Math.floor(Math.random() * 6);
        this.reset(w, h, true);
    }
    reset(w, h, randomPos = false) {
        const width = w || window.innerWidth;
        const height = h || window.innerHeight;
        if (randomPos) {
            this.x = Math.random() * width;
            this.y = Math.random() * height;
        } else {
            const edge = Math.floor(Math.random() * 4);
            if (edge === 0) { this.x = Math.random() * width; this.y = -30; }
            else if (edge === 1) { this.x = width + 30; this.y = Math.random() * height; }
            else if (edge === 2) { this.x = Math.random() * width; this.y = height + 30; }
            else { this.x = -30; this.y = Math.random() * height; }
        }
        this.vx = (Math.random() - 0.5) * 4;
        this.vy = (Math.random() - 0.5) * 4;
        this.size = Math.random() * 8 + 6;
        this.burstSize = this.size * 2;
        this.coreIndex = Math.floor(Math.random() * 10);
        this.orbitAngle = Math.random() * Math.PI * 2;
        this.orbitSpeed = (Math.random() * 0.045 + 0.02) * (Math.random() > 0.5 ? 1 : -1);
        this.baseOrbitRadius = Math.random() * 80 + 30;
        this.noiseOffset = Math.random() * 100;
        this.alpha = Math.random() * 0.5 + 0.5;
        this.scattered = false;
        this.parked = false;
        this.flowT = Math.random();
        this.flowSpeed = Math.random() * 0.015 + 0.008;
        this.streamWidth = Math.random() * 35 + 15;
    }
    update(w, h, handDetected) {
        if (!handDetected || activeFingerCores.length === 0) {
            if (!this.scattered) {
                const originX = lastHandCenterPos.x;
                const originY = lastHandCenterPos.y;
                const blastAngle = Math.atan2(this.y - originY, this.x - originX) + (Math.random() - 0.5) * 0.8;
                const speed = Math.random() * 35 + 30;
                const spin = (Math.random() - 0.5) * 14;
                this.vx = Math.cos(blastAngle) * speed - Math.sin(blastAngle) * spin;
                this.vy = Math.sin(blastAngle) * speed + Math.cos(blastAngle) * spin;
                this.scattered = true;
                this.burstSize = Math.random() * 20 + 12;
                this.parked = false;
            }
            if (!this.parked) {
                this.x += this.vx;
                this.y += this.vy;
                if (this.x < -200 || this.x > w + 200 || this.y < -200 || this.y > h + 200) {
                    this.parked = true;
                    this.x = -600;
                    this.y = -600;
                    this.vx = 0;
                    this.vy = 0;
                }
            }
            return;
        }
        if (this.parked || this.x < -100 || this.x > w + 100 || this.y < -100 || this.y > h + 100) {
            this.reset(w, h, false);
            this.parked = false;
        }
        this.scattered = false;
        const coresCount = activeFingerCores.length;
        this.noiseOffset += 0.04;
        this.orbitAngle += this.orbitSpeed;
        const collapseMultiplier = Math.max(0.0, 1.0 - handStillnessFactor);
        let targetX, targetY;
        let shapeForce = (coresCount >= 6 ? 0.48 : (coresCount === 5 ? 0.32 : 0.22)) * state.gravity;
        let shapeFriction = coresCount >= 6 ? 0.76 : 0.86;
        let vortexMultiplier = coresCount >= 6 ? 0.2 : (coresCount === 5 ? 3.2 : (2.4 * Math.max(0.2, collapseMultiplier)));
        let applyTurbulence = coresCount < 6;
        if (coresCount === 1) {
            const targetCore = activeFingerCores[0];
            const wave = Math.sin(this.noiseOffset) * 8 * collapseMultiplier;
            const currentRadius = (this.baseOrbitRadius * 0.7 + wave) * collapseMultiplier;
            targetX = targetCore.x + Math.cos(this.orbitAngle) * currentRadius;
            targetY = targetCore.y + Math.sin(this.orbitAngle) * currentRadius;
        } else if (coresCount >= 2 && coresCount <= 4) {
            const targetCore = activeFingerCores[this.coreIndex % coresCount];
            const layerOffset = (this.variantIndex - 2.5) * 8;
            const subtleWave = (Math.sin(this.noiseOffset * 0.4) * 4 + Math.cos(this.orbitAngle * 2) * 3) * collapseMultiplier;
            const ringRadius = (58 + layerOffset + subtleWave) * collapseMultiplier;
            targetX = targetCore.x + Math.cos(this.orbitAngle) * ringRadius;
            targetY = targetCore.y + Math.sin(this.orbitAngle) * ringRadius;
            if (Math.random() < 0.012) {
                this.coreIndex = (this.coreIndex + 1) % coresCount;
            }
        } else if (coresCount === 5) {
            let sumX = 0, sumY = 0;
            for (let c of activeFingerCores) { sumX += c.x; sumY += c.y; }
            const palmX = sumX / coresCount;
            const palmY = sumY / coresCount;
            const layerOffset = (this.variantIndex - 2.5) * 14; 
            const subtleWave = Math.sin(this.noiseOffset * 0.3) * 5 + Math.cos(this.orbitAngle * 2) * 4;
            const ringRadius = 220 + layerOffset + subtleWave;
            targetX = palmX + Math.cos(this.orbitAngle) * ringRadius;
            targetY = palmY + Math.sin(this.orbitAngle) * ringRadius;
        } else if (coresCount === 6) {
            let sumX = 0, sumY = 0;
            for (let c of activeFingerCores) { sumX += c.x; sumY += c.y; }
            const centerX = sumX / coresCount;
            const centerY = sumY / coresCount;
            const normId = (this.id !== undefined ? this.id : this.variantIndex * 70) / (particles.length || 450);
            const strand = (this.id % 2 === 0) ? 1 : -1;
            const posX = (normId - 0.5) * 560;
            const t = posX * 0.018 + (this.orbitAngle * 0.3);
            const posY = Math.sin(t) * 85 * strand;
            targetX = centerX + posX;
            targetY = centerY + posY;
        } else if (coresCount === 7) {
            let sumX = 0, sumY = 0;
            for (let c of activeFingerCores) { sumX += c.x; sumY += c.y; }
            const centerX = sumX / coresCount;
            const centerY = sumY / coresCount;
            const normId = (this.id !== undefined ? this.id : this.variantIndex * 70) / (particles.length || 450);
            const angle = normId * Math.PI * 2 + (this.orbitAngle * 0.2);
            const numPoints = 7;
            const starFactor = Math.abs(Math.cos((angle * numPoints) / 2));
            const starRadius = 60 + 170 * starFactor;
            targetX = centerX + starRadius * Math.cos(angle);
            targetY = centerY + starRadius * Math.sin(angle);
        } else if (coresCount === 8) {
            let sumX = 0, sumY = 0;
            for (let c of activeFingerCores) { sumX += c.x; sumY += c.y; }
            const centerX = sumX / coresCount;
            const centerY = sumY / coresCount;
            const normId = (this.id !== undefined ? this.id : this.variantIndex * 70) / (particles.length || 450);
            const t = normId * Math.PI * 2 + (this.orbitAngle * 0.25);
            const scale = 280;
            const denom = 1 + Math.sin(t) * Math.sin(t);
            const offset = (this.variantIndex - 2.5) * 5;
            const rawX = (scale * Math.cos(t)) / denom;
            const rawY = (scale * Math.sin(t) * Math.cos(t)) / denom;
            targetX = centerX + rawX + Math.sin(t) * offset;
            targetY = centerY + rawY + Math.cos(t) * offset;
        } else if (coresCount === 9) {
            let sumX = 0, sumY = 0;
            for (let c of activeFingerCores) { sumX += c.x; sumY += c.y; }
            const centerX = sumX / coresCount;
            const centerY = sumY / coresCount;
            const normId = (this.id !== undefined ? this.id : this.variantIndex * 70) / (particles.length || 450);
            const arm = (this.id % 2 === 0) ? 0 : Math.PI;
            const theta = normId * Math.PI * 4 + (this.orbitAngle * 0.4);
            const r = 20 + theta * 18;
            targetX = centerX + r * Math.cos(theta + arm);
            targetY = centerY + r * Math.sin(theta + arm);
        } else {
            let sumX = 0, sumY = 0;
            for (let c of activeFingerCores) { sumX += c.x; sumY += c.y; }
            const centerX = sumX / coresCount;
            const centerY = sumY / coresCount;
            const normId = (this.id !== undefined ? this.id : this.variantIndex * 70) / (particles.length || 450);
            const ringIdx = (this.id || 0) % 3;
            const ringRadius = 110 + ringIdx * 75;
            const angle = normId * Math.PI * 2 + (this.orbitAngle * (1 + ringIdx * 0.4));
            targetX = centerX + ringRadius * Math.cos(angle);
            targetY = centerY + ringRadius * Math.sin(angle);
        }
        const dx = targetX - this.x;
        const dy = targetY - this.y;
        const dist = Math.hypot(dx, dy) + 0.1;
        this.vx += (dx / dist) * Math.min(dist * 0.6, shapeForce * 20);
        this.vy += (dy / dist) * Math.min(dist * 0.6, shapeForce * 20);
        if (vortexMultiplier > 0.05) {
            const perpX = -dy / dist;
            const perpY = dx / dist;
            this.vx += perpX * vortexMultiplier;
            this.vy += perpY * vortexMultiplier;
        }
        if (applyTurbulence) {
            const turbulenceX = Math.cos(this.noiseOffset * 1.5) * 0.6;
            const turbulenceY = Math.sin(this.noiseOffset * 1.5) * 0.6;
            this.vx += turbulenceX;
            this.vy += turbulenceY;
        }
        this.vx *= shapeFriction;
        this.vy *= shapeFriction;
        this.x += this.vx;
        this.y += this.vy;
        this.alpha = 0.5 + Math.sin(this.noiseOffset * 2.5) * 0.35;
    }
    draw(ctx) {
        if (this.parked || this.x < -100 || this.y < -100) return;
        const sprite = (activeGlowSprites && activeGlowSprites.length > 0)
            ? (activeGlowSprites[this.variantIndex] || activeGlowSprites[0])
            : null;
        const currentSize = this.scattered ? (this.burstSize || this.size * 2) : this.size;
        const speed = Math.hypot(this.vx, this.vy);
        ctx.globalAlpha = Math.min(1.0, Math.max(0.18, this.alpha));
        if (sprite) {
            if (speed > 1.8) {
                ctx.save();
                ctx.translate(this.x, this.y);
                ctx.rotate(Math.atan2(this.vy, this.vx));
                const stretch = Math.min(3.2, 1 + speed * 0.11);
                ctx.drawImage(sprite, -currentSize * stretch / 2, -currentSize / 2, currentSize * stretch, currentSize);
                ctx.restore();
            } else {
                const half = currentSize / 2;
                ctx.drawImage(sprite, this.x - half, this.y - half, currentSize, currentSize);
            }
        } else {
            ctx.fillStyle = state.currentColorHex || '#a855f7';
            ctx.beginPath();
            ctx.arc(this.x, this.y, currentSize / 4, 0, Math.PI * 2);
            ctx.fill();
        }
    }
}
function initParticleEngine() {
    initGlowSprites();
    const container = document.getElementById('canvas-container');
    container.innerHTML = '';
    const w = container ? (container.clientWidth || window.innerWidth) : window.innerWidth;
    const h = container ? (container.clientHeight || window.innerHeight) : window.innerHeight;
    mainCanvas = document.createElement('canvas');
    mainCanvas.width = w;
    mainCanvas.height = h;
    mainCanvas.style.width = '100%';
    mainCanvas.style.height = '100%';
    container.appendChild(mainCanvas);
    mainCtx = mainCanvas.getContext('2d');
    createParticles();
    window.addEventListener('resize', onWindowResize);
}
function createParticles() {
    particles = [];
    const count = state.particleCount || 450;
    for (let i = 0; i < count; i++) {
        const p = new Particle(mainCanvas.width, mainCanvas.height);
        p.id = i;
        p.normId = i / count;
        particles.push(p);
    }
}
function getThemeHexColor() {
    switch (state.theme) {
        case 'plasma': return '#00f2fe';
        case 'nebula': return '#a855f7';
        case 'silver':
        default: return '#94a3b8';
    }
}
function onWindowResize() {
    const container = document.getElementById('canvas-container');
    if (mainCanvas && container) {
        mainCanvas.width = container.clientWidth || window.innerWidth;
        mainCanvas.height = container.clientHeight || window.innerHeight;
    }
    resizeTrackingCanvas();
}
function resizeTrackingCanvas() {
    const rect = trackingCanvas.getBoundingClientRect();
    trackingCanvas.width = rect.width;
    trackingCanvas.height = rect.height;
}
let blackHoleAngle = 0;
function drawBlackHoleSingularity(ctx, cx, cy, colorHex) {
    blackHoleAngle += 0.05;
    ctx.save();
    ctx.translate(cx, cy);
    for (let r = 0; r < 3; r++) {
        const radius = 25 + r * 14;
        const rot = blackHoleAngle * (1.3 + r * 0.3);
        ctx.strokeStyle = colorHex;
        ctx.lineWidth = 2.2 - r * 0.4;
        ctx.globalAlpha = 0.75 - r * 0.15;
        ctx.setLineDash([12, 10, 4, 8]);
        ctx.beginPath();
        ctx.arc(0, 0, radius, rot, rot + Math.PI * 1.6);
        ctx.stroke();
    }
    ctx.setLineDash([]);
    const grad = ctx.createRadialGradient(0, 0, 12, 0, 0, 45);
    grad.addColorStop(0, '#ffffff');
    grad.addColorStop(0.35, colorHex);
    grad.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = grad;
    ctx.globalAlpha = 0.85;
    ctx.beginPath();
    ctx.arc(0, 0, 45, 0, Math.PI * 2);
    ctx.fill();
    ctx.globalCompositeOperation = 'source-over';
    ctx.fillStyle = '#03050a';
    ctx.beginPath();
    ctx.arc(0, 0, 20, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = colorHex;
    ctx.lineWidth = 2.5;
    ctx.stroke();
    ctx.restore();
}
let lastTime = performance.now();
let frameCount = 0;
function animate() {
    requestAnimationFrame(animate);
    frameCount++;
    const now = performance.now();
    if (now - lastTime >= 1000) {
        if (fpsDisplay) fpsDisplay.textContent = `FPS: ${frameCount}`;
        frameCount = 0;
        lastTime = now;
    }
    if (!state.cameraActive) {
        updateSimulation();
    }
    const w = mainCanvas.width;
    const h = mainCanvas.height;
    const themeHex = state.currentColorHex || getThemeHexColor();
    updateStillnessTracking();
    if (targetFingerCores.length > 0) {
        while (activeFingerCores.length < targetFingerCores.length) {
            activeFingerCores.push({ x: targetFingerCores[0].x, y: targetFingerCores[0].y });
        }
        if (activeFingerCores.length > targetFingerCores.length) {
            activeFingerCores.length = targetFingerCores.length;
        }
        for (let i = 0; i < activeFingerCores.length; i++) {
            const dx = targetFingerCores[i].x - activeFingerCores[i].x;
            const dy = targetFingerCores[i].y - activeFingerCores[i].y;
            const dist = Math.hypot(dx, dy);
            const lerpFactor = dist > 20 ? Math.min(0.92, 0.50 + dist * 0.008) : 0.50;
            activeFingerCores[i].x += dx * lerpFactor;
            activeFingerCores[i].y += dy * lerpFactor;
        }
    }
    mainCtx.fillStyle = 'rgba(11, 14, 23, 0.18)';
    mainCtx.fillRect(0, 0, w, h);
    mainCtx.save();
    mainCtx.globalCompositeOperation = 'lighter';
    if (state.handDetected && activeFingerCores.length > 0) {
        activeFingerCores.forEach((core, idx) => {
            mainCtx.fillStyle = themeHex;
            mainCtx.beginPath();
            mainCtx.arc(core.x, core.y, 14, 0, Math.PI * 2);
            mainCtx.fill();
            mainCtx.strokeStyle = themeHex;
            mainCtx.lineWidth = 1.5;
            mainCtx.setLineDash([5, 5]);
            mainCtx.beginPath();
            mainCtx.arc(core.x, core.y, 55, 0, Math.PI * 2);
            mainCtx.stroke();
            mainCtx.setLineDash([]);
            if (idx > 0) {
                const prevCore = activeFingerCores[idx - 1];
                mainCtx.strokeStyle = 'rgba(255, 255, 255, 0.85)';
                mainCtx.lineWidth = 2.5;
                mainCtx.beginPath();
                mainCtx.moveTo(prevCore.x, prevCore.y);
                mainCtx.lineTo(core.x, core.y);
                mainCtx.stroke();
            }
        });
    }
    for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        p.update(w, h, state.handDetected);
        p.draw(mainCtx);
    }
    for (let i = clickParticles.length - 1; i >= 0; i--) {
        const cp = clickParticles[i];
        cp.update();
        cp.draw(mainCtx);
        if (cp.alpha <= 0 || cp.size <= 0.5) {
            clickParticles.splice(i, 1);
        }
    }
    if (state.handDetected && activeFingerCores.length >= 5) {
        let sumX = 0, sumY = 0;
        for (let c of activeFingerCores) { sumX += c.x; sumY += c.y; }
        const palmX = sumX / activeFingerCores.length;
        const palmY = sumY / activeFingerCores.length;
        drawBlackHoleSingularity(mainCtx, palmX, palmY, themeHex);
    }
    for (let i = shockwaves.length - 1; i >= 0; i--) {
        const sw = shockwaves[i];
        sw.radius += sw.speed || 20;
        sw.alpha *= 0.90;
        mainCtx.strokeStyle = themeHex;
        mainCtx.lineWidth = (sw.width || 4) * sw.alpha;
        mainCtx.globalAlpha = sw.alpha;
        mainCtx.beginPath();
        mainCtx.arc(sw.x, sw.y, sw.radius, 0, Math.PI * 2);
        mainCtx.stroke();
        if (sw.alpha < 0.02 || sw.radius > sw.maxRadius) {
            shockwaves.splice(i, 1);
        }
    }
    mainCtx.restore();
}
function updateSimulation() {
    state.simAngle += 0.02;
    state.handDetected = true;
    const mw = mainCanvas ? mainCanvas.width : window.innerWidth;
    const mh = mainCanvas ? mainCanvas.height : window.innerHeight;
    const h1X = 0.35 + Math.sin(state.simAngle) * 0.15;
    const h1Y = 0.5 + Math.cos(state.simAngle * 0.8) * 0.15;
    const h2X = 0.65 - Math.sin(state.simAngle) * 0.15;
    const h2Y = 0.5 + Math.sin(state.simAngle * 0.8) * 0.15;
    const c1x = h1X * mw;
    const c1y = h1Y * mh;
    const c2x = h2X * mw;
    const c2y = h2Y * mh;
    targetFingerCores = [
        { x: c1x - 30, y: c1y },
        { x: c1x + 30, y: c1y },
        { x: c2x - 30, y: c2y },
        { x: c2x + 30, y: c2y }
    ];
    updateTelemetry(h1X, h1Y, 0.0, '2 HANDS ACTIVE (4 FINGER CORES)', 0.992);
    drawSimulatedHandOverlay(h1X, h1Y, h2X, h2Y);
}
function drawSimulatedHandOverlay(h1x, h1y, h2x, h2y) {
    resizeTrackingCanvas();
    const w = trackingCanvas.width;
    const h = trackingCanvas.height;
    ctx.clearRect(0, 0, w, h);
    const themeHex = getThemeHexColor();
    ctx.strokeStyle = themeHex;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(h1x * w, h1y * h, 35, 0, Math.PI * 2);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(h2x * w, h2y * h, 35, 0, Math.PI * 2);
    ctx.stroke();
}
trackingCanvas.addEventListener('mousemove', (e) => {
    if (state.cameraActive) return;
    const rect = trackingCanvas.getBoundingClientRect();
    const mx = (e.clientX - rect.left) / rect.width;
    const my = (e.clientY - rect.top) / rect.height;
    state.handPos.x = mx;
    state.handPos.y = my;
    state.handDetected = true;
    const mw = mainCanvas ? mainCanvas.width : window.innerWidth;
    const mh = mainCanvas ? mainCanvas.height : window.innerHeight;
    targetFingerCores = [
        { x: mx * mw - 80, y: my * mh },
        { x: mx * mw - 30, y: my * mh - 20 },
        { x: mx * mw + 30, y: my * mh - 20 },
        { x: mx * mw + 80, y: my * mh }
    ];
    drawSimulatedHandOverlay(mx - 0.05, my, mx + 0.05, my);
});
trackingCanvas.addEventListener('mouseleave', () => {
    if (!state.cameraActive) {
        state.handDetected = false;
    }
});
function getGestureModeName(count) {
    switch (count) {
        case 1: return '1 FINGER: ORBITING VORTEX';
        case 2: return '2 FINGERS: DUAL PLASMA RINGS';
        case 3: return '3 FINGERS: TRIPLE PLASMA RINGS';
        case 4: return '4 FINGERS: QUAD PLASMA RINGS';
        case 5: return '5 FINGERS: SINGULARITY BLACK HOLE';
        case 6: return '6 FINGERS: DOUBLE DNA HELIX';
        case 7: return '7 FINGERS: QUANTUM 7-HEPTAGRAM';
        case 8: return '8 FINGERS: INFINITY MATRIX (∞)';
        case 9: return '9 FINGERS: GALACTIC SPIRAL';
        case 10: default: return '10 FINGERS: SUPERNOVA HYPER-RING';
    }
}
let currentDemoFingerCount = 4;
trackingCanvas.addEventListener('click', () => {
    if (state.cameraActive) return;
    state.handDetected = true;
    const mw = mainCanvas ? mainCanvas.width : window.innerWidth;
    const mh = mainCanvas ? mainCanvas.height : window.innerHeight;
    const cx = state.handPos.x * mw;
    const cy = state.handPos.y * mh;
    currentDemoFingerCount = (currentDemoFingerCount % 10) + 1;
    let newCores = [];
    for (let i = 0; i < currentDemoFingerCount; i++) {
        let angle = (i / currentDemoFingerCount) * Math.PI * 2;
        let r = 80 + Math.sin(i * 1.5) * 25;
        newCores.push({
            x: cx + Math.cos(angle) * r,
            y: cy + Math.sin(angle) * r
        });
    }
    targetFingerCores = newCores;
    updateTelemetry(state.handPos.x, state.handPos.y, 0.0, getGestureModeName(currentDemoFingerCount), 0.995);
});
function updateTelemetry(x, y, z, gestureText, confidence) {
    state.handPos.x = x;
    state.handPos.y = y;
    state.handPos.z = z;
    state.confidence = confidence;
    updateSpatialSynth(x, y, z);
    if (coordXEl) coordXEl.textContent = x.toFixed(2);
    if (coordYEl) coordYEl.textContent = y.toFixed(2);
    if (coordZEl) coordZEl.textContent = z.toFixed(2);
    const confPct = (confidence * 100).toFixed(1) + '%';
    if (confidenceValEl) confidenceValEl.textContent = confPct;
    if (confidenceFillEl) confidenceFillEl.style.width = confPct;
    const countText = activeFingerCores.length + ' CORES ACTIVE';
    if (gestureNameEl) gestureNameEl.innerHTML = `<i class="fa-solid fa-hands"></i> ${gestureText || countText}`;
}
let hands;
let missedHandFrames = 0;
function initMediaPipe() {
    hands = new Hands({
        locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`
    });
    hands.setOptions({
        maxNumHands: 2,
        modelComplexity: 1,
        minDetectionConfidence: 0.25,
        minTrackingConfidence: 0.25
    });
    hands.onResults(onHandResults);
}
function getLandmarkDist(p1, p2) {
    const dx = p1.x - p2.x;
    const dy = p1.y - p2.y;
    const dz = (p1.z || 0) - (p2.z || 0);
    return Math.hypot(dx, dy, dz);
}
function getActiveFingertipIds(landmarks) {
    const activeTips = [];
    const wrist = landmarks[0];
    const fingers = [
        { id: 8, pip: 6 },
        { id: 12, pip: 10 },
        { id: 16, pip: 14 },
        { id: 20, pip: 18 }
    ];
    fingers.forEach(f => {
        const dTip = getLandmarkDist(landmarks[f.id], wrist);
        const dPip = getLandmarkDist(landmarks[f.pip], wrist);
        if (dTip > dPip * 0.96) {
            activeTips.push(f.id);
        }
    });
    const thumbTip = landmarks[4];
    const thumbIP = landmarks[3];
    const thumbMCP = landmarks[2];
    const indexBase = landmarks[5];
    const dTipMCP = getLandmarkDist(thumbTip, thumbMCP);
    const dIpMCP = getLandmarkDist(thumbIP, thumbMCP);
    const dTipIndexBase = getLandmarkDist(thumbTip, indexBase);
    const isIndexActive = activeTips.includes(8);
    const otherFingersFolded = !activeTips.includes(12) && !activeTips.includes(16) && !activeTips.includes(20);
    const isSingleIndexPointing = isIndexActive && otherFingersFolded;
    const minIndexBaseDist = isSingleIndexPointing ? 0.165 : 0.125;
    const minJointExtension = isSingleIndexPointing ? 1.12 : 1.05;
    if (dTipMCP > dIpMCP * minJointExtension && dTipIndexBase > minIndexBaseDist) {
        activeTips.push(4);
    }
    return activeTips;
}
function onHandResults(results) {
    resizeTrackingCanvas();
    const w = trackingCanvas.width;
    const h = trackingCanvas.height;
    ctx.clearRect(0, 0, w, h);
    if (results.image) {
        ctx.save();
        ctx.scale(-1, 1);
        ctx.drawImage(results.image, -w, 0, w, h);
        ctx.restore();
    }
    if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
        state.handDetected = true;
        const mw = mainCanvas ? mainCanvas.width : window.innerWidth;
        const mh = mainCanvas ? mainCanvas.height : window.innerHeight;
        const newCores = [];
        for (let hIdx = 0; hIdx < results.multiHandLandmarks.length; hIdx++) {
            const landmarks = results.multiHandLandmarks[hIdx];
            const activeTipIds = getActiveFingertipIds(landmarks);
            drawLandmarksOnCanvas(landmarks, w, h, activeTipIds);
            activeTipIds.forEach((id) => {
                if (landmarks[id]) {
                    newCores.push({
                        x: (1 - landmarks[id].x) * mw,
                        y: landmarks[id].y * mh
                    });
                }
            });
        }
        if (newCores.length > 0) {
            missedHandFrames = 0;
            targetFingerCores = newCores;
            triggerHandState(true);
            let sumX = 0, sumY = 0;
            for (let c of activeFingerCores) { sumX += c.x; sumY += c.y; }
            lastHandCenterPos = { x: sumX / activeFingerCores.length, y: sumY / activeFingerCores.length };
            const handCount = results.multiHandLandmarks.length;
            const firstTip = results.multiHandLandmarks[0][8];
            const fingerCount = activeFingerCores.length;
            const gestureMode = getGestureModeName(fingerCount);
            const label = `${handCount} HAND${handCount > 1 ? 'S' : ''} (${fingerCount} FINGERS: ${gestureMode})`;
            updateTelemetry(1 - firstTip.x, firstTip.y, firstTip.z, label, 0.991);
        } else {
            missedHandFrames++;
            if (missedHandFrames >= 5) {
                triggerHandState(false);
                updateTelemetry(0.5, 0.5, 0.0, 'FIST CLOSED', 0.0);
            }
        }
    } else {
        missedHandFrames++;
        if (missedHandFrames >= 5) {
            triggerHandState(false);
            updateTelemetry(0.5, 0.5, 0.0, 'HAND DISAPPEARED', 0.0);
        }
    }
}
function drawLandmarksOnCanvas(landmarks, w, h, activeTipIds = [8, 12, 16, 20, 4]) {
    const themeHex = getThemeHexColor();
    ctx.strokeStyle = themeHex;
    ctx.lineWidth = 2.5;
    const CONNECTIONS = [
        [0,1],[1,2],[2,3],[3,4],
        [0,5],[5,6],[6,7],[7,8],
        [0,9],[9,10],[10,11],[11,12],
        [0,13],[13,14],[14,15],[15,16],
        [0,17],[17,18],[18,19],[19,20]
    ];
    CONNECTIONS.forEach(([i, j]) => {
        const p1 = landmarks[i];
        const p2 = landmarks[j];
        ctx.beginPath();
        ctx.moveTo((1 - p1.x) * w, p1.y * h);
        ctx.lineTo((1 - p2.x) * w, p2.y * h);
        ctx.stroke();
    });
    [4, 8, 12, 16, 20].forEach((id) => {
        const lm = landmarks[id];
        const nx = (1 - lm.x) * w;
        const ny = lm.y * h;
        const isExtended = activeTipIds.includes(id);
        ctx.fillStyle = isExtended ? themeHex : 'rgba(255, 255, 255, 0.4)';
        ctx.beginPath();
        ctx.arc(nx, ny, isExtended ? 7 : 4, 0, Math.PI * 2);
        ctx.fill();
        if (isExtended) {
            ctx.fillStyle = '#ffffff';
            ctx.beginPath();
            ctx.arc(nx, ny, 3, 0, Math.PI * 2);
            ctx.fill();
        }
    });
}
cameraToggleBtn.addEventListener('click', async () => {
    if (!state.cameraActive) {
        try {
            if (statusText) statusText.textContent = 'Connecting Camera...';
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' }
            });
            webcamVideo.srcObject = stream;
            await webcamVideo.play();
            if (!hands) initMediaPipe();
            let isProcessing = false;
            const processFrame = async () => {
                if (!state.cameraActive) return;
                if (!isProcessing && webcamVideo.readyState >= 2) {
                    isProcessing = true;
                    try {
                        await hands.send({ image: webcamVideo });
                    } catch (e) {
                        console.error('MediaPipe error:', e);
                    }
                    isProcessing = false;
                }
                requestAnimationFrame(processFrame);
            };
            state.cameraActive = true;
            cameraToggleBtn.innerHTML = '<i class="fa-solid fa-video-slash"></i> Stop Camera';
            cameraToggleBtn.style.background = '#e74c3c';
            if (statusDot) statusDot.style.backgroundColor = '#2ecc71';
            if (statusText) statusText.textContent = 'Tracking Active';
            if (simNotice) simNotice.style.display = 'none';
            processFrame();
        } catch (err) {
            console.warn('Camera access error:', err);
            if (window.location.protocol === 'file:') {
                alert('⚠️ Запустите проект через локальный сервер или используйте клик мышкой!');
            } else {
                alert('Не удалось получить доступ к веб-камере.');
            }
            if (statusText) statusText.textContent = 'Camera Unavailable';
            if (statusDot) statusDot.style.backgroundColor = '#f39c12';
        }
    } else {
        if (webcamVideo.srcObject) {
            webcamVideo.srcObject.getTracks().forEach(track => track.stop());
            webcamVideo.srcObject = null;
        }
        state.cameraActive = false;
        cameraToggleBtn.innerHTML = '<i class="fa-solid fa-video"></i> Start Camera';
        cameraToggleBtn.style.background = 'linear-gradient(135deg, var(--accent-purple), #7c3aed)';
        if (statusDot) statusDot.style.backgroundColor = '#2ecc71';
        if (statusText) statusText.textContent = 'Interactive Demo Mode';
        if (simNotice) simNotice.style.display = 'flex';
    }
});
let audioCtx, osc, gainNode, filterNode;
function initAudioSynth() {
    if (audioCtx) return;
    try {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        audioCtx = new AudioContext();
        osc = audioCtx.createOscillator();
        gainNode = audioCtx.createGain();
        filterNode = audioCtx.createBiquadFilter();
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(220, audioCtx.currentTime);
        filterNode.type = 'lowpass';
        filterNode.frequency.setValueAtTime(800, audioCtx.currentTime);
        gainNode.gain.setValueAtTime(0.06, audioCtx.currentTime);
        osc.connect(filterNode);
        filterNode.connect(gainNode);
        gainNode.connect(audioCtx.destination);
        osc.start();
    } catch (e) {
        console.warn('Audio Synth init error:', e);
    }
}
function updateSpatialSynth(x, y, z) {
    if (!state.audioEnabled || !audioCtx) return;
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const freq = 180 + x * 700;
    osc.frequency.setTargetAtTime(freq, audioCtx.currentTime, 0.05);
    const cutoff = 300 + (1 - y) * 3200;
    filterNode.frequency.setTargetAtTime(cutoff, audioCtx.currentTime, 0.05);
}
function toggleAudioSynth() {
    state.audioEnabled = !state.audioEnabled;
    if (state.audioEnabled) {
        initAudioSynth();
        if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume();
        audioToggleBtn.innerHTML = '<i class="fa-solid fa-volume-high"></i> Synth ON';
        audioToggleBtn.style.background = 'rgba(46, 204, 113, 0.2)';
        audioToggleBtn.style.borderColor = '#2ecc71';
        audioToggleBtn.style.color = '#2ecc71';
    } else {
        if (gainNode) gainNode.gain.setTargetAtTime(0, audioCtx.currentTime, 0.05);
        audioToggleBtn.innerHTML = '<i class="fa-solid fa-volume-xmark"></i> Synth OFF';
        audioToggleBtn.style.background = 'rgba(255, 255, 255, 0.08)';
        audioToggleBtn.style.borderColor = 'rgba(255, 255, 255, 0.15)';
        audioToggleBtn.style.color = 'var(--text-primary)';
    }
}
function exportCanvasSnapshot() {
    const exportCanvas = document.createElement('canvas');
    exportCanvas.width = window.innerWidth;
    exportCanvas.height = window.innerHeight;
    const expCtx = exportCanvas.getContext('2d');
    expCtx.fillStyle = '#050810';
    expCtx.fillRect(0, 0, exportCanvas.width, exportCanvas.height);
    if (mainCanvas) expCtx.drawImage(mainCanvas, 0, 0);
    expCtx.drawImage(trackingCanvas, 24, 88, trackingCanvas.width, trackingCanvas.height);
    expCtx.font = 'bold 16px Syne, sans-serif';
    expCtx.fillStyle = '#2ecc71';
    expCtx.fillText('NEUROVISION AI', 30, window.innerHeight - 30);
    const link = document.createElement('a');
    link.download = `NeuroVision_${Date.now()}.png`;
    link.href = exportCanvas.toDataURL('image/png');
    link.click();
}
function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(err => console.warn(err));
    } else {
        if (document.exitFullscreen) document.exitFullscreen();
    }
}
if (customColorPicker) {
    customColorPicker.addEventListener('input', (e) => {
        themeButtons.forEach(b => b.classList.remove('active'));
        updateCustomColor(e.target.value);
    });
}
themeButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
        themeButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.theme = btn.dataset.theme;
        let hex = '#2ecc71';
        if (state.theme === 'plasma') hex = '#00f2fe';
        else if (state.theme === 'nebula') hex = '#9b59b6';
        updateCustomColor(hex);
    });
});
if (audioToggleBtn) audioToggleBtn.addEventListener('click', toggleAudioSynth);
if (snapshotBtn) snapshotBtn.addEventListener('click', exportCanvasSnapshot);
if (fullscreenBtn) fullscreenBtn.addEventListener('click', toggleFullscreen);
const heroCameraTrigger = document.getElementById('hero-camera-trigger');
if (heroCameraTrigger) {
    heroCameraTrigger.addEventListener('click', () => {
        cameraToggleBtn.click();
        const workspaceEl = document.getElementById('workspace');
        if (workspaceEl) workspaceEl.scrollIntoView({ behavior: 'smooth' });
    });
}
function initScrollReveal() {
    const reveals = document.querySelectorAll('.reveal');
    // Instantly reveal elements above or near the fold
    reveals.forEach(el => {
        const rect = el.getBoundingClientRect();
        if (rect.top <= window.innerHeight * 1.15) {
            el.classList.add('active');
        }
    });

    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('active');
                }
            });
        }, { threshold: 0.02, rootMargin: '40px' });
        reveals.forEach(el => observer.observe(el));
    } else {
        reveals.forEach(el => el.classList.add('active'));
    }

    // Safety fallback: ensure nothing stays invisible after 500ms
    setTimeout(() => {
        reveals.forEach(el => el.classList.add('active'));
    }, 500);
}
let isEndPageWarpActive = false;
function initEndPageScrollWarp() {
    window.addEventListener('scroll', () => {
        const scrollPos = window.innerHeight + window.scrollY;
        const pageHeight = document.documentElement.scrollHeight;
        if (scrollPos >= pageHeight - 220) {
            if (!isEndPageWarpActive) {
                isEndPageWarpActive = true;
                particles.forEach(p => {
                    p.orbitSpeed *= 2.5;
                    p.alpha = 0.95;
                });
            }
        } else {
            if (isEndPageWarpActive) {
                isEndPageWarpActive = false;
                particles.forEach(p => {
                    p.orbitSpeed /= 2.5;
                });
            }
        }
    });
}
function initBlocksOverscroll() {
    const blocksEl = document.getElementById('blocks-overscroll-container');
    const footerEl = document.querySelector('.app-footer');
    if (!blocksEl || !footerEl) return;
    let currentHeight = 0;
    let targetHeight = 0;
    let isPullingActive = false;
    let springFrame = null;
    let releaseTimeout = null;
    const updateSpring = () => {
        currentHeight += (targetHeight - currentHeight) * 0.28;
        if (Math.abs(targetHeight - currentHeight) < 0.5) {
            currentHeight = targetHeight;
        }
        blocksEl.style.maxHeight = `${currentHeight}px`;
        blocksEl.style.opacity = `${Math.min(1, currentHeight / 30)}`;
        if (currentHeight > 0.5) {
            blocksEl.classList.add('visible');
            springFrame = requestAnimationFrame(updateSpring);
        } else {
            blocksEl.style.maxHeight = '0px';
            blocksEl.style.opacity = '0';
            blocksEl.classList.remove('visible');
            if (springFrame) {
                cancelAnimationFrame(springFrame);
                springFrame = null;
            }
        }
    };
    const checkScrollState = () => {
        const footerRect = footerEl.getBoundingClientRect();
        if (footerRect.top <= window.innerHeight + 40) {
            const visibleFooterAmount = window.innerHeight - footerRect.top;
            let baseH = Math.max(0, Math.min(120, visibleFooterAmount * 0.8));
            if (!isPullingActive) {
                targetHeight = baseH;
            }
            if (!springFrame && targetHeight > 0) {
                springFrame = requestAnimationFrame(updateSpring);
            }
        } else {
            if (!isPullingActive) {
                targetHeight = 0;
            }
        }
    };
    const triggerPull = (delta) => {
        const footerRect = footerEl.getBoundingClientRect();
        if (footerRect.bottom <= window.innerHeight + 80) {
            isPullingActive = true;
            targetHeight = Math.min(180, Math.max(120, targetHeight + Math.max(15, delta * 0.6)));
            if (!springFrame) {
                springFrame = requestAnimationFrame(updateSpring);
            }
            if (releaseTimeout) clearTimeout(releaseTimeout);
            releaseTimeout = setTimeout(() => {
                isPullingActive = false;
                checkScrollState();
            }, 300);
        }
    };
    window.addEventListener('scroll', checkScrollState, { passive: true });
    window.addEventListener('wheel', (e) => {
        if (e.deltaY > 0) {
            triggerPull(e.deltaY);
        }
    }, { passive: true });
    let touchStartY = 0;
    window.addEventListener('touchstart', (e) => {
        touchStartY = e.touches[0].clientY;
    }, { passive: true });
    window.addEventListener('touchmove', (e) => {
        const touchY = e.touches[0].clientY;
        const pullDelta = touchStartY - touchY;
        if (pullDelta > 0) {
            triggerPull(pullDelta * 1.5);
        }
    }, { passive: true });
    window.addEventListener('touchend', () => {
        if (isPullingActive) {
            isPullingActive = false;
            checkScrollState();
        }
    }, { passive: true });
    checkScrollState();
}
if ('scrollRestoration' in history) {
    history.scrollRestoration = 'manual';
}
window.addEventListener('beforeunload', () => {
    window.scrollTo(0, 0);
});
window.addEventListener('pointerdown', (e) => {
    if (e.target.closest('button, a, input, select, .theme-btn')) return;
    spawnClickBurst(e.clientX, e.clientY);
});
function startNexApp() {
    window.scrollTo(0, 0);
    initParticleEngine();
    resizeTrackingCanvas();
    initScrollReveal();
    initEndPageScrollWarp();
    initBlocksOverscroll();
    animate();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startNexApp);
} else {
    startNexApp();
}