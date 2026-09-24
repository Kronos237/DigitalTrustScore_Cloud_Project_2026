const form = document.querySelector('#score-form');
const result = document.querySelector('#result');
const status = document.querySelector('#status');
const history = document.querySelector('#history');
const exampleUrl = document.querySelector('#example-url');

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, character => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#039;'}[character]));
}

function renderHistory(items) {
  history.innerHTML = items.length ? items.map(item => `<div class="history-row"><span>${escapeHtml(item.url)}</span><strong>${escapeHtml(item.score)}/100</strong></div>`).join('') : '<p class="empty">No assessments yet. Submit a URL to create the first result.</p>';
}

function renderCategories(scores) {
  document.querySelector('#category-list').innerHTML = Object.entries(scores).map(([name, score]) => `<div class="category"><div><span>${escapeHtml(name)}</span><strong>${escapeHtml(score)}/100</strong></div><div class="bar"><i style="width:${score}%"></i></div></div>`).join('');
}

function renderEvidence(data) {
  const values = [['HTTPS', data.security.https ? 'detected' : 'not_detected'], ['TLS', data.security.tls.status], ['HTTP status', data.reliability.http_status || 'unavailable'], ['Response time', data.reliability.response_time_ms ? `${data.reliability.response_time_ms} ms` : 'unavailable'], ['Privacy policy', data.transparency.privacy_policy], ['Contact page', data.transparency.contact_page], ['Reputation', data.reputation.message]];
  document.querySelector('#evidence-list').innerHTML = values.map(([name, value]) => `<div class="evidence-row"><span>${escapeHtml(name)}</span><strong>${escapeHtml(value)}</strong></div>`).join('');
  document.querySelector('#header-list').innerHTML = Object.entries(data.security.headers).map(([name, value]) => `<div class="evidence-row"><span>${escapeHtml(name)}</span><strong>${escapeHtml(value)}</strong></div>`).join('');
}

async function loadHistory() {
  const response = await fetch('/api/history');
  renderHistory((await response.json()).results);
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  status.textContent = 'Assessing...';
  try {
    const response = await fetch('/api/score', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({url:form.url.value}) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error);
    document.querySelector('#score').textContent = data.score;
    document.querySelector('#label').textContent = `${data.label} trust signal`;
    document.querySelector('#factor-list').innerHTML = data.factors.map(factor => `<div class="factor"><span>${escapeHtml(factor.feature.replaceAll('_', ' '))}</span><strong class="${escapeHtml(factor.direction)}">${factor.impact > 0 ? '+' : ''}${escapeHtml(factor.impact)}</strong></div>`).join('');
    renderCategories(data.category_scores);
    renderEvidence(data.features);
    document.querySelector('#ml-status').textContent = data.ml_prediction.message;
    result.hidden = false;
    document.querySelector('#categories').hidden = false;
    document.querySelector('#evidence').hidden = false;
    status.textContent = 'Updated just now';
    await loadHistory();
  } catch (error) { status.textContent = error.message; }
});

loadHistory().catch(() => { status.textContent = 'API unavailable'; });
exampleUrl.addEventListener('click', () => { form.url.value = exampleUrl.textContent; });