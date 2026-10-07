(() => {
  const form = document.getElementById('planning-form');
  if (!form) return;
  const button = form.querySelector('button[type="submit"]');
  const status = document.getElementById('planning-status');
  const result = document.getElementById('planning-result');
  const question = document.getElementById('plan-question');
  let busy = false;

  function add(tag, text, parent = result) {
    const element = document.createElement(tag);
    element.textContent = text;
    parent.appendChild(element);
    return element;
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (busy || !form.reportValidity()) return;
    busy = true;
    const body = new FormData(form);
    button.disabled = true;
    question.readOnly = true;
    button.textContent = 'Generating…';
    status.textContent = 'Preparing and running your analysis. This may take a moment…';
    status.classList.add('loading-status');
    result.querySelectorAll('.analysis-chart').forEach(chart => { if (window.Plotly) Plotly.purge(chart); });
    result.replaceChildren();
    result.setAttribute('aria-busy', 'true');
    result.className = 'plan-message';
    try {
      const response = await fetch(form.action, {
        method: 'POST', body, credentials: 'same-origin',
        headers: { Accept: 'application/json' },
      });
      if (!response.headers.get('content-type')?.includes('application/json')) {
        throw new Error(response.status === 403
          ? 'Your session token expired. Refresh the page and try again.'
          : response.status === 404
            ? 'This dataset is no longer available in your session.'
            : 'The server could not complete the request. Please try again.');
      }
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Unable to generate a plan.');
      const plan = data.plan;
      if (!plan || !['clarify', 'analyze'].includes(plan.action)) {
        throw new Error('The server returned an unexpected response. Please try again.');
      }
      add('p', `Your question: ${body.get('question')}`).className = 'submitted-question';
      if (plan.action === 'clarify') {
        add('h3', 'A little more detail');
        add('p', plan.question);
        add('p', 'Update your question above with these details and submit again.').className = 'hint';
      } else {
        add('h3', data.executed ? 'Your analysis results' : 'Your proposed analysis');
        if (data.executed && data.result) {
          const output = data.result;
          if (!output.rows.length) add('p', 'No matching rows were found.');
          else {
            const wrap = add('div', ''); wrap.className = 'table-scroll';
            const table = add('table', '', wrap);
            const heading = add('tr', '', add('thead', '', table));
            output.columns.forEach(name => { const cell = add('th', name, heading); cell.scope = 'col'; });
            const tbody = add('tbody', '', table);
            output.rows.forEach(row => { const tr = add('tr', '', tbody); row.forEach(value => add('td', value === null ? '?' : String(value), tr)); });
          }
          if (output.chart) {
            const chart = add('div', ''); chart.className = 'analysis-chart'; chart.setAttribute('role', 'img'); chart.setAttribute('aria-label', plan.chart?.title || 'Analysis chart');
            try {
              if (!window.Plotly) throw new Error('Chart library unavailable');
              await Plotly.newPlot(chart, output.chart.data, output.chart.layout, { responsive: true, displaylogo: false, toImageButtonOptions: { format: 'png', filename: 'analysis-chart' } });
            } catch (_) { chart.remove(); add('p', 'Chart could not be displayed. The result table is still available.'); }
          }
          if (output.truncated) add('p', 'Result preview is limited; additional rows were omitted.');
          (output.notes || []).forEach(note => add('p', note).className = 'hint');
        }
        add('p', plan.explanation);
        if (plan.assumptions?.length) {
          add('h4', 'Assumptions');
          const list = add('ul', '');
          plan.assumptions.forEach((item) => add('li', item, list));
        }
        
        const details = add('details', '');
        add('summary', 'View analysis SQL', details);
        const pre = add('pre', '', details);
        add('code', plan.sql, pre);
        add('p', data.executed ? 'Calculated from your uploaded dataset.' : 'Plan generated. No query has been executed.').className = 'hint';
      }
      status.textContent = 'Response ready.';
    } catch (error) {
      result.classList.add('plan-error');
      add('h3', 'Could not generate a plan');
      add('p', error instanceof TypeError
        ? 'Connection interrupted. Check your network and try again.'
        : error.message);
      status.textContent = 'Request failed. Your question is preserved; you can retry.';
    } finally {
      busy = false;
      button.disabled = false;
      question.readOnly = false;
      button.textContent = 'Analyze';
      status.classList.remove('loading-status');
      result.setAttribute('aria-busy', 'false');
    }
  });
})();
