class ArticleEditor {
  constructor(options) {
    this._ = (window.gettext) ? window.gettext : (s) => s;

    this.form    = document.querySelector(options.form);
    this.content = document.querySelector(options.content);
    this.output  = document.querySelector(options.output);
    this.toolbar = document.querySelector(options.toolbar);
    this.initEvents();
  }

  initEvents() {
    if (!this.form || !this.content || !this.output || !this.toolbar) return;

    this.toolbar.addEventListener('click', (e) => {
      const cmdEl = e.target.closest('[data-command]');
      const command = cmdEl && cmdEl.dataset.command;
      if (!command) return;

      e.preventDefault();
      const method = `add${command.charAt(0).toUpperCase() + command.slice(1)}Block`;
      if (typeof this[method] === 'function') this[method]();
    });

    this.content.addEventListener('click', (e) => {
      if (e.target.classList.contains('remove-block')) {
        const block = e.target.closest('.editor-block');
        if (block) block.remove();
        this.updateOutput();
      }
    });

    this.form.addEventListener('submit', () => {
      this.updateOutput();
    });
  }

  addTextBlock() {
    const block = document.createElement('div');
    block.className = 'editor-block';
    block.dataset.type = 'text';
    block.innerHTML = `
      <div class="d-flex justify-content-end">
        <button type="button" class="btn btn-sm btn-danger remove-block" aria-label="${this._('Remove block')}">×</button>
      </div>
      <textarea class="form-control mb-2" placeholder="${this._('Enter text…')}"></textarea>
    `;
    this.content.appendChild(block);
  }

  addImageBlock() {
    const block = document.createElement('div');
    block.className = 'editor-block';
    block.dataset.type = 'image_with_caption';
    block.innerHTML = `
      <div class="d-flex justify-content-end">
        <button type="button" class="btn btn-sm btn-danger remove-block" aria-label="${this._('Remove block')}">×</button>
      </div>
      <input type="file" class="form-control mb-2" accept="image/*">
      <input type="text" class="form-control" placeholder="${this._('Image caption…')}">
    `;
    this.content.appendChild(block);
  }

  updateOutput() {
    const blocks = [];
    this.content.querySelectorAll('.editor-block').forEach(blockEl => {
      const type = blockEl.dataset.type;
      const value = this.getBlockValue(blockEl, type);
      if (value !== null && value !== undefined) {
        blocks.push({ type, value });
      }
    });

    this.output.value = JSON.stringify(blocks);
  }

  getBlockValue(blockEl, type) {
    if (type === 'text') {
      const textarea = blockEl.querySelector('textarea');
      return textarea ? textarea.value : '';
    } else if (type === 'image_with_caption') {
      const fileInput    = blockEl.querySelector('input[type="file"]');
      const captionInput = blockEl.querySelector('input[type="text"]');
      return {
        caption: captionInput ? captionInput.value : '',
        image_id: fileInput && fileInput.dataset ? (fileInput.dataset.imageId || null) : null,
        // Note: File objects cannot be serialized to JSON; keep a reference for form submission if needed.
        file: (fileInput && fileInput.files && fileInput.files[0]) ? fileInput.files[0] : null
      };
    }
    return null;
  }

  load(data) {
    if (!Array.isArray(data)) return;

    data.forEach(item => {
      if (item.type === 'text') {
        this.addTextBlock();
        const lastBlock = this.content.lastElementChild;
        const ta = lastBlock && lastBlock.querySelector('textarea');
        if (ta) ta.value = item.value || '';
      } else if (item.type === 'image_with_caption') {
        this.addImageBlock();
        const lastBlock = this.content.lastElementChild;
        if (!lastBlock) return;
        const captionInput = lastBlock.querySelector('input[type="text"]');
        const fileInput    = lastBlock.querySelector('input[type="file"]');
        if (captionInput) captionInput.value = (item.value && item.value.caption) ? item.value.caption : '';
        if (fileInput && item.value && item.value.image_id) {
          fileInput.dataset.imageId = item.value.image_id;
        }
      }
    });
  }
}
