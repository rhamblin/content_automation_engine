  const schedule_date = "21/03/2026";  // DD/MM/YYYY
  const schedule_time = "09:30 AM";    // HH:MM AM/PM

  const pin =
{
      "blog_url": "https://chefexotic.com/keto-bread-recipe-book-quick-preview/",
      "options": [
        {
          "title": "Crispy Keto French Bread (Easy Bake)",
          "description": "Craving that crunchy bread fix but staying low carb? This crispy keto french bread is ready in under an hour and bakes up golden with almond flour for authentic flavor.\nPerfect for busy weeknight cooks needing quick sides or sandwich options.\n\n\u2714 Just 5 simple ingredients\n\u2714 No kneading required\n\u2714 Kid and family approved\n\nSave and click for the full step-by-step recipe.",
          "alt_text": "A loaf of keto french bread on a wooden cutting board with a dish of olive oil and basil leaves",
          "reasoning": "Chose Style A for strong keto french bread SEO targeting and clear value for busy weeknight cooks; combined with Description Style 1 for instant skimmable benefits and a save-worthy CTA."
        }
      ]
    }
  ;

  function fillTextarea(placeholder, value) {
    const el = document.querySelector(`textarea[placeholder="${placeholder}"]`);
    if (!el) { console.warn('Not found:', placeholder); return; }
    const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
    setter.call(el, value);
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
  }

  function fillInput(el, value) {
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
    setter.call(el, value);
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
    el.dispatchEvent(new Event('blur', { bubbles: true }));
  }

  function fillDraftJs(value) {
    const el = document.querySelector('.public-DraftEditor-content[contenteditable="true"]');
    if (!el) { console.warn('DraftJS editor not found'); return; }
    el.focus();
    const dt = new DataTransfer();
    dt.setData('text/plain', value);
    el.dispatchEvent(new ClipboardEvent('paste', { bubbles: true, cancelable: true, clipboardData: dt }));
  }

  // Fill text fields
  fillTextarea("Add your title", pin.options[0].title);
  fillDraftJs(pin.options[0].description);
  fillTextarea("Add a destination link", pin.blog_url);

  // Alt text is behind a toggle — click it, then fill after DOM updates
  const altBtn = document.querySelector('[data-test-id="pin-draft-alttext-expand"]')
    || [...document.querySelectorAll('button')].find(b => b.textContent.includes('alt text') || b.textContent.includes('Alt text'));
  if (altBtn) {
    altBtn.click();
    setTimeout(() => fillTextarea("Explain what people can see in the Pin", pin.options[0].alt_text), 300);
  } else {
    fillTextarea("Explain what people can see in the Pin", pin.alt_text);
  }

  // Select "Publish at a later date", then set date & time after fields render
  const laterRadio = document.querySelector('input[type="radio"][value="publish-later"]');
  if (laterRadio) {
    laterRadio.click();
    setTimeout(() => {
      const dateInput = document.querySelector('input[placeholder="DD/MM/YYYY"]');
      if (dateInput) fillInput(dateInput, schedule_date);

      const timeInput = document.querySelector('input[data-test-id="text-field"][placeholder="Time"]');
      if (timeInput) fillInput(timeInput, schedule_time);
    }, 300);
  }
