/* ═══════════════════════════════════════════
   MEDISCAN PRO — APPLICATION LOGIC
═══════════════════════════════════════════ */

// ── STATE ─────────────────────────────────
let currentDisease = 'Diabetes Mellitus';

// ── PAGE NAVIGATION ───────────────────────
function showPage(pageId) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  const target = document.getElementById('page-' + pageId);
  if (target) {
    target.classList.add('active');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
}

// ── HOME NAV ──────────────────────────────
function scrollToSection(id) {
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  closeMobileNav();
}

function toggleMobileNav() {
  document.getElementById('mobileNav').classList.toggle('open');
}
function closeMobileNav() {
  document.getElementById('mobileNav').classList.remove('open');
}

// ── AUTH ──────────────────────────────────
function switchTab(tab) {
  document.getElementById('tab-signin').classList.toggle('active', tab === 'signin');
  document.getElementById('tab-signup').classList.toggle('active', tab === 'signup');
  document.getElementById('form-signin').classList.toggle('hidden', tab !== 'signin');
  document.getElementById('form-signup').classList.toggle('hidden', tab !== 'signup');
}

function togglePassword(inputId, btn) {
  const input = document.getElementById(inputId);
  const isText = input.type === 'text';
  input.type = isText ? 'password' : 'text';
  btn.innerHTML = isText
    ? `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`
    : `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24M1 1l22 22"/></svg>`;
}

function checkPasswordStrength(value) {
  const fill  = document.getElementById('pw-fill');
  const label = document.getElementById('pw-label');
  let strength = 0;
  if (value.length >= 8) strength++;
  if (/[A-Z]/.test(value)) strength++;
  if (/[0-9]/.test(value)) strength++;
  if (/[^A-Za-z0-9]/.test(value)) strength++;

  const levels = [
    { w: '25%', color: '#ef4444', text: 'Weak' },
    { w: '50%', color: '#f59e0b', text: 'Fair' },
    { w: '75%', color: '#22d3ee', text: 'Good' },
    { w: '100%', color: '#34d399', text: 'Strong' },
  ];
  const lvl = levels[Math.max(0, strength - 1)] || levels[0];
  fill.style.width = value.length ? lvl.w : '0';
  fill.style.background = lvl.color;
  label.textContent = value.length ? lvl.text : 'Enter password';
  label.style.color = lvl.color;
}

function handleSignIn(e) {
  e.preventDefault();
  const email = document.getElementById('signin-email').value;
  const pw    = document.getElementById('signin-password').value;
  const err   = document.getElementById('signin-error');

  if (!email.includes('@')) {
    err.textContent = 'Please enter a valid email address.'; return;
  }
  if (pw.length < 6) {
    err.textContent = 'Password must be at least 6 characters.'; return;
  }
  err.textContent = '';
  showPage('dashboard');
}

function handleSignUp(e) {
  e.preventDefault();
  const pw      = document.getElementById('signup-password').value;
  const confirm = document.getElementById('signup-confirm').value;
  const err     = document.getElementById('signup-error');

  if (pw.length < 8) {
    err.textContent = 'Password must be at least 8 characters.'; return;
  }
  if (pw !== confirm) {
    err.textContent = 'Passwords do not match.'; return;
  }
  err.textContent = '';
  showPage('dashboard');
}

// ── SIDEBAR ───────────────────────────────
function toggleSidebar() {
  const sidebars = document.querySelectorAll('.sidebar');
  sidebars.forEach(sb => {
    if (window.innerWidth <= 768) {
      sb.classList.toggle('mobile-open');
    } else {
      sb.classList.toggle('collapsed');
    }
  });
}

function setActiveNav(el) {
  el.closest('.sidebar-nav').querySelectorAll('.sidebar-item').forEach(i => i.classList.remove('active'));
  el.classList.add('active');
}

// ── DISEASE SELECTION ─────────────────────
function selectDisease(name) {
  currentDisease = name;
  const chips = document.querySelectorAll('#diseaseChips .chip');
  chips.forEach(c => {
    c.classList.toggle('active', c.onclick.toString().includes(name.replace("'","\\'")));
  });
  document.getElementById('result-disease-name').textContent = name;
}

function selectChip(el, name) {
  document.querySelectorAll('#diseaseChips .chip').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  currentDisease = name;
}

// ── PREDICTION FLOW ───────────────────────
function runPrediction(e) {
  e.preventDefault();

  const overlay = document.getElementById('loadingOverlay');
  const bar     = document.getElementById('loadingBar');
  overlay.classList.remove('hidden');

  // Animate steps
  const steps = ['step1','step2','step3','step4'];
  const durations = [800, 1200, 900, 700];
  let elapsed = 0;
  let cumulative = 0;
  const total = durations.reduce((a,b) => a+b, 0);

  // Reset
  steps.forEach(s => {
    const el = document.getElementById(s);
    el.classList.remove('active','done');
  });
  bar.style.width = '0';

  steps.forEach((stepId, i) => {
    const delay = cumulative;
    cumulative += durations[i];

    setTimeout(() => {
      // Mark previous as done
      if (i > 0) {
        document.getElementById(steps[i-1]).classList.remove('active');
        document.getElementById(steps[i-1]).classList.add('done');
      }
      document.getElementById(stepId).classList.add('active');

      const pct = Math.round(((cumulative) / total) * 100);
      bar.style.width = pct + '%';
    }, delay);
  });

  // Finish
  const finishDelay = total + 400;
  setTimeout(() => {
    document.getElementById(steps[steps.length-1]).classList.remove('active');
    document.getElementById(steps[steps.length-1]).classList.add('done');
    bar.style.width = '100%';
  }, total);

  setTimeout(() => {
    overlay.classList.add('hidden');
    showResultsPage();
  }, finishDelay);
}

function showResultsPage() {
  // Randomize a low/moderate result for demo
  const riskPct = Math.floor(Math.random() * 35) + 8;
  const isLow = riskPct < 30;
  const isMod = riskPct >= 30 && riskPct < 60;

  // Update result page
  document.getElementById('result-disease-name').textContent = currentDisease;
  document.getElementById('result-date').textContent = new Date().toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: 'numeric', minute: '2-digit'
  });

  const icon  = document.getElementById('verdictIcon');
  const title = document.getElementById('verdictTitle');
  const sub   = document.getElementById('verdictSub');

  if (isLow) {
    icon.className  = 'verdict-icon';
    icon.textContent = '✓';
    title.textContent = 'Low Risk Detected';
    sub.textContent = `No significant indicators for ${currentDisease} found in your parameters.`;
  } else if (isMod) {
    icon.className  = 'verdict-icon warn';
    icon.textContent = '⚠';
    title.textContent = 'Moderate Risk Detected';
    sub.textContent = `Some elevated risk markers for ${currentDisease} were found. Lifestyle changes recommended.`;
  } else {
    icon.className  = 'verdict-icon danger';
    icon.textContent = '!';
    title.textContent = 'Elevated Risk Detected';
    sub.textContent = `Multiple risk indicators for ${currentDisease} detected. Please consult a physician promptly.`;
  }

  // Animate gauge
  document.getElementById('gaugePct').textContent = riskPct + '%';
  const dashoffset = 251 - (251 * riskPct / 100);
  document.getElementById('gaugeFill').style.strokeDashoffset = dashoffset;

  showPage('results');
}

function resetForm() {
  document.getElementById('predictForm').reset();
  document.querySelectorAll('#diseaseChips .chip').forEach((c,i) => c.classList.toggle('active', i===0));
  currentDisease = 'Diabetes Mellitus';
}

// ── REPORT DOWNLOAD (mock) ─────────────────
function downloadReport() {
  const btn = event.currentTarget;
  const orig = btn.innerHTML;
  btn.innerHTML = '⟳ Generating...';
  btn.disabled = true;

  setTimeout(() => {
    const content = `MEDISCAN PRO — PREDICTION REPORT
================================
Patient: John Doe
Date: ${new Date().toLocaleString()}
Disease Module: ${currentDisease}

DISCLAIMER: This is a screening tool only.
Consult a qualified healthcare professional for diagnosis.

================================
MediScan Pro | clinicalgrade.ai
`;
    const blob = new Blob([content], { type: 'text/plain' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = `mediscan-report-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);

    btn.innerHTML = orig;
    btn.disabled  = false;
  }, 1200);
}

// ── ANIMATE CHART BARS ON SCROLL ──────────
function observeChartBars() {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.querySelectorAll('.chart-bar-fill').forEach(bar => {
          const w = bar.style.width;
          bar.style.width = '0';
          requestAnimationFrame(() => {
            setTimeout(() => { bar.style.width = w; }, 100);
          });
        });
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.3 });

  document.querySelectorAll('.about-chart').forEach(el => observer.observe(el));
}

// ── INIT ──────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  observeChartBars();

  // Stagger hero content animation
  const heroItems = document.querySelectorAll('.hero-badge, .hero-title, .hero-desc, .hero-actions, .hero-stats');
  heroItems.forEach((el, i) => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = `opacity 0.6s ease ${i * 0.12}s, transform 0.6s ease ${i * 0.12}s`;
    requestAnimationFrame(() => {
      setTimeout(() => {
        el.style.opacity = '1';
        el.style.transform = 'translateY(0)';
      }, 50);
    });
  });

  // Close mobile nav on outside click
  document.addEventListener('click', e => {
    const nav  = document.getElementById('mobileNav');
    const ham  = document.getElementById('hamburger');
    if (nav && !nav.contains(e.target) && !ham.contains(e.target)) {
      closeMobileNav();
    }
  });
});