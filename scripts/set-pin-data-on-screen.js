  const schedule_date = "25/02/2026";  // DD/MM/YYYY
  const schedule_time = "09:30 AM";    // HH:MM AM/PM

  const pin =       {
        "title": "Chilli shrimps cups delight",
        "description": "Rich spicy shrimp cups burst with smoky heat and juicy bites. A quick crowd pleasing starter that comes together in minutes for weeknights or parties. Save this delicious idea for your next get together.",
        "alt_text": "Crispy bite sized cups filled with spicy chilli shrimp topping",
        "reasoning": "The title front loads the exact keyword for Pinterest SEO and uses crave worthy sensory language to drive saves and clicks."
      };

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
  fillTextarea("Add your title", pin.title);
  fillDraftJs(pin.description);
  fillTextarea("Add a destination link", pin.link);

  // Alt text is behind a toggle — click it, then fill after DOM updates
  const altBtn = document.querySelector('[data-test-id="pin-draft-alttext-expand"]')
    || [...document.querySelectorAll('button')].find(b => b.textContent.includes('alt text') || b.textContent.includes('Alt text'));
  if (altBtn) {
    altBtn.click();
    setTimeout(() => fillTextarea("Explain what people can see in the Pin", pin.alt_text), 300);
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
