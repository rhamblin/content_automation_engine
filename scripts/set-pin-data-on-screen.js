  const schedule_date = "01/03/2026";  // DD/MM/YYYY
  const schedule_time = "09:30 AM";    // HH:MM AM/PM

  const pin =
{
      "blog_url": "https://chefexotic.com/chia-pudding-bowl-recipe-creamy-overnight-chia-pudding-bowl/",
      "options": [
        {
          "title": "Creamy Chia Pudding Bowls for Busy Mornings",
          "description": "Craving an easy breakfast you can actually look forward to? These creamy chia pudding bowls are ready when you wake up, with flavors the whole family will love. Perfect for prep-ahead mornings and picky eaters alike.\n\nSave this pin and discover all five quick recipes now.",
          "alt_text": "A glass bowl of chia pudding topped with mango cubes and pomegranate seeds with a spoonful of chia seeds beside it",
          "reasoning": "The title uses Style C to target busy weeknight cooks, front-loading the primary keyword 'chia pudding' and highlighting quick variety for busy mornings. The description Style 4 emphasizes convenience and family appeal, suiting Pinterest users who need fast solutions for breakfast."
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
