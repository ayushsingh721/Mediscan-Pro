/* ═══════════════════════════════════════════
   MEDISCAN PRO — CLINICAL INTELLIGENCE JAVASCRIPT
═══════════════════════════════════════════ */

// ── NAVIGATION & MOBILE MENU ──────────────
function toggleMobileNav() {
  const nav = document.getElementById('mobileNav');
  if (nav) nav.classList.toggle('open');
}

function closeMobileNav() {
  const nav = document.getElementById('mobileNav');
  if (nav) nav.classList.remove('open');
}

function scrollToSection(id) {
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  closeMobileNav();
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

// ── AUTHENTICATION TABS & PASSWORD ────────
function switchTab(tab) {
  const tabSignin = document.getElementById('tab-signin');
  const tabSignup = document.getElementById('tab-signup');
  const formSignin = document.getElementById('form-signin');
  const formSignup = document.getElementById('form-signup');

  if (tabSignin) tabSignin.classList.toggle('active', tab === 'signin');
  if (tabSignup) tabSignup.classList.toggle('active', tab === 'signup');
  if (formSignin) formSignin.classList.toggle('hidden', tab !== 'signin');
  if (formSignup) formSignup.classList.toggle('hidden', tab !== 'signup');
}

function togglePassword(inputId, btn) {
  const input = document.getElementById(inputId);
  if (!input) return;
  const isText = input.type === 'text';
  input.type = isText ? 'password' : 'text';
  if (btn) {
    btn.innerHTML = isText
      ? `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`
      : `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24M1 1l22 22"/></svg>`;
  }
}

function checkPasswordStrength(value) {
  const fill  = document.getElementById('pw-fill');
  const label = document.getElementById('pw-label');
  if (!fill || !label) return;

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

// ── DAILY TASKS TOGGLE (AJAX) ─────────────
function toggleTask(taskId) {
  const csrfEl = document.getElementById('csrf-token');
  const csrfToken = csrfEl ? csrfEl.getAttribute('data-token') : '';

  fetch(`/dashboard/tasks/${taskId}/toggle`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken
    }
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      const row = document.getElementById(`task-row-${taskId}`);
      const chk = document.getElementById(`check-${taskId}`);
      if (row) {
        const text = row.querySelector('.task-text');
        const badge = row.querySelector('.task-status-badge');

        if (data.is_completed) {
          row.classList.add('task-done');
          if (chk) chk.checked = true;
          if (text) {
            text.style.textDecoration = 'line-through';
            text.style.color = 'var(--text-3)';
          }
          if (badge) {
            badge.textContent = 'Completed ✓';
            badge.style.color = 'var(--green)';
          }
        } else {
          row.classList.remove('task-done');
          if (chk) chk.checked = false;
          if (text) {
            text.style.textDecoration = 'none';
            text.style.color = 'var(--text-1)';
          }
          if (badge) {
            badge.textContent = 'Pending';
            badge.style.color = 'var(--text-3)';
          }
        }
      }

      // Update dashboard progress metrics
      const countEl = document.getElementById('tasksCompletedCount');
      const pctTextEl = document.getElementById('tasksPctText');
      const barEl = document.getElementById('tasksProgressBar');
      const streakEl = document.getElementById('healthStreakCount');

      if (countEl) countEl.textContent = `${data.completed}/${data.total}`;
      if (pctTextEl) pctTextEl.textContent = `${data.pct}%`;
      if (barEl) barEl.style.width = `${data.pct}%`;
      if (streakEl) {
        streakEl.innerHTML = `${data.streak} <small style="font-size: 0.85rem; font-weight: normal; color: var(--text-2);">days</small>`;
      }
    }
  })
  .catch(err => console.error('Task toggle error:', err));
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

// ── AI HEALTH TIP REFRESHER ───────────────
function initAiTipRefresher() {
  const btn = document.getElementById('refreshAiTipBtn');
  if (!btn) return;

  btn.addEventListener('click', () => {
    const icon = document.getElementById('refreshAiTipIcon');
    if (icon) {
      icon.style.transition = 'transform 0.5s ease';
      icon.style.transform = 'rotate(360deg)';
    }
    btn.style.opacity = '0.6';
    btn.disabled = true;

    fetch('/dashboard/ai-health-tip', {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCsrfToken(),
        'Content-Type': 'application/json'
      }
    })
    .then(res => res.json())
    .then(data => {
      if (data.success && data.tip) {
        const tip = data.tip;
        const catBadge = document.getElementById('aiTipCategoryBadge');
        const iconEl = document.getElementById('aiTipIcon');
        const titleEl = document.getElementById('aiTipTitle');
        const ratEl = document.getElementById('aiTipRationale');
        const actEl = document.getElementById('aiTipAction');
        const bioEl = document.getElementById('aiTipBiomarker');
        const impEl = document.getElementById('aiTipImpact');

        const card = document.getElementById('aiHealthTipCard');
        if (card) {
          card.style.transition = 'opacity 0.2s ease';
          card.style.opacity = '0.4';
          setTimeout(() => {
            if (catBadge) catBadge.textContent = tip.category;
            if (iconEl) iconEl.textContent = tip.icon;
            if (titleEl) titleEl.textContent = tip.title;
            if (ratEl) ratEl.textContent = tip.rationale;
            if (actEl) actEl.textContent = tip.action_step;
            if (bioEl) bioEl.textContent = tip.target_biomarker;
            if (impEl) impEl.textContent = tip.impact;
            card.style.opacity = '1';
          }, 200);
        }
      }
    })
    .catch(err => console.error('AI Tip error:', err))
    .finally(() => {
      setTimeout(() => {
        if (icon) icon.style.transform = 'rotate(0deg)';
        btn.style.opacity = '1';
        btn.disabled = false;
      }, 500);
    });
  });
}

// ── DYNAMIC GREETING TIME SYNC ────────────
function updateGreeting() {
  const el = document.getElementById('greetingTimeOfDay');
  if (!el) return;
  const h = new Date().getHours();
  if (h < 12) {
    el.textContent = 'Morning';
  } else if (h < 17) {
    el.textContent = 'Afternoon';
  } else {
    el.textContent = 'Evening';
  }
}

// ── INITIALIZATION ────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  observeChartBars();
  initAiTipRefresher();
  updateGreeting();

  // Close mobile nav when clicking outside
  document.addEventListener('click', e => {
    const nav = document.getElementById('mobileNav');
    const ham = document.getElementById('hamburger');
    if (nav && !nav.contains(e.target) && !ham.contains(e.target)) {
      closeMobileNav();
    }
  });
});