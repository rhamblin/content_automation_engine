  const schedule_date = "08/04/2026";  // DD/MM/YYYY
  const schedule_time = "09:30 AM";    // HH:MM AM/PM

  const pin =
    {
      "keyword": "Gourmet french door air fryer review",
      "blog_url": "https://chefexotic.com/shop/",
      "source_image": "Gourmia-French-Door-Air Fryer.jpg",
      "options": [
        {
          "title": "Spacious French Door Air Fryer (Feeds a Crowd)",
          "description": "Tired of juggling multiple pans for family dinner? This large-capacity air fryer gives you room to crisp up everything at once, making weeknight cooking so much simpler for families.\n\n\u2714 Double french doors for easy access\n\u2714 Fits whole meals on roomy racks\n\u2714 12 presets for hands-off cooking\n\nTap to see how it tested in real life and get our full review.",
          "alt_text": "A stainless steel french door air fryer oven with a digital control panel, wire racks, and a mesh basket inside",
          "reasoning": "Primary keyword 'Gourmet french door air fryer review' is featured up front using Style A for strong Pinterest SEO; benefit-driven Style 1 description speaks directly to Busy Weeknight Cooks by highlighting capacity, convenience, and family appeal."
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
