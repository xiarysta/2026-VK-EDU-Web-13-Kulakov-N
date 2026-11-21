(() => {
  const config = document.querySelector('#ajax-config');
  const errorBox = document.querySelector('#ajax-error');
  let errorTimer;
  function showError(message) {
    clearTimeout(errorTimer);
    errorBox.setAttribute("role", "alert");
    errorBox.textContent = message;
    errorBox.hidden = false;
    errorTimer = setTimeout(() => { errorBox.hidden = true; }, 8000);
  }
  async function send(url, values) {
    errorBox.hidden = true;
    const response = await fetch(url, {
      method: 'POST', credentials: 'same-origin',
      headers: { 'X-CSRFToken': config.querySelector('[name=csrfmiddlewaretoken]').value },
      body: new URLSearchParams(values),
    });
    if (response.status === 401) {
      window.location.assign(config.dataset.loginUrl + '?next=' + encodeURIComponent(location.pathname + location.search));
      throw new Error('Войдите, чтобы выполнить действие.');
    }
    let data;
    try { data = await response.json(); }
    catch { throw new Error('Сервер вернул ошибку. Обновите страницу и повторите действие.'); }
    if (!response.ok) {
      const errors = Object.values(data.errors || {}).flat().map(error => error.message);
      throw new Error(data.error || errors.join(' ') || 'Не удалось выполнить действие.');
    }
    return data;
  }
  document.addEventListener('click', async event => {
    const button = event.target.closest('[data-vote]');
    if (!button || button.disabled) return;
    const controls = button.closest('[data-vote-url]');
    const buttons = [...controls.querySelectorAll('button')];
    buttons.forEach(item => { item.disabled = true; });
    try {
      const data = await send(controls.dataset.voteUrl, { target: controls.dataset.target, value: button.dataset.vote });
      controls.querySelector('[data-rating]').textContent = data.rating;
      buttons.forEach(item => { item.title = 'Вы уже голосовали'; });
    } catch (error) {
      buttons.forEach(item => { item.disabled = false; });
      showError(error.message);
    }
  });
  document.addEventListener('change', async event => {
    const checkbox = event.target.closest('[data-correct-url]');
    if (!checkbox) return;
    const previous = !checkbox.checked;
    const checkboxes = [...document.querySelectorAll('[data-correct-url]')].filter(item => item.dataset.question === checkbox.dataset.question);
    checkboxes.forEach(item => { item.disabled = true; });
    try {
      const data = await send(checkbox.dataset.correctUrl, {
        question: checkbox.dataset.question, answer: checkbox.dataset.answer, is_correct: String(checkbox.checked),
      });
      checkboxes.forEach(item => { item.checked = Number(item.dataset.answer) === data.correct_answer_id; });
    } catch (error) {
      checkbox.checked = previous;
      showError(error.message);
    } finally {
      checkboxes.forEach(item => { item.disabled = false; });
    }
  });
})();
