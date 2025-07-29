class ArticleEditor {
  constructor(options) {
    this.form = document.querySelector(options.form);
    this.content = document.querySelector(options.content);
    this.output = document.querySelector(options.output);
    this.toolbar = document.querySelector(options.toolbar);
    this.initEvents();
  }

  initEvents() {
    this.toolbar.addEventListener('click', (e) => {
      const command = e.target.closest('[data-command]')?.dataset.command;
      if (!command) return;

      e.preventDefault();
      this[`add${command.charAt(0).toUpperCase() + command.slice(1)}Block`]();
    });

    this.content.addEventListener('click', (e) => {
      if (e.target.classList.contains('remove-block')) {
        e.target.closest('.editor-block').remove();
        this.updateOutput();
      }
    });

    this.form.addEventListener('submit', (e) => {
      this.updateOutput();
    });
  }

  addTextBlock() {
    const block = document.createElement('div');
    block.className = 'editor-block';
    block.dataset.type = 'text';
    block.innerHTML = `
      <div class="d-flex justify-content-end">
        <button type="button" class="btn btn-sm btn-danger remove-block">×</button>
      </div>
      <textarea class="form-control mb-2" placeholder="Введите текст..."></textarea>
    `;
    this.content.appendChild(block);
  }

  addImageBlock() {
    const block = document.createElement('div');
    block.className = 'editor-block';
    block.dataset.type = 'image_with_caption';
    block.innerHTML = `
      <div class="d-flex justify-content-end">
        <button type="button" class="btn btn-sm btn-danger remove-block">×</button>
      </div>
      <input type="file" class="form-control mb-2" accept="image/*">
      <input type="text" class="form-control" placeholder="Подпись к изображению...">
    `;
    this.content.appendChild(block);
  }

  updateOutput() {
    const blocks = [];
    
    this.content.querySelectorAll('.editor-block').forEach(blockEl => {
      const type = blockEl.dataset.type;
      const value = this.getBlockValue(blockEl, type);
      if (value) blocks.push({ type, value });
    });

    this.output.value = JSON.stringify(blocks);
  }

  getBlockValue(blockEl, type) {
    if (type === 'text') {
      const textarea = blockEl.querySelector('textarea');
      return textarea.value;
    } else if (type === 'image_with_caption') {
      const fileInput = blockEl.querySelector('input[type="file"]');
      const captionInput = blockEl.querySelector('input[type="text"]');
      
      return {
        caption: captionInput.value,
        image_id: fileInput.dataset.imageId || null,
        file: fileInput.files[0] || null
      };
    }
    return null;
  }

  load(data) {
    if (!data) return;
    
    data.forEach(item => {
      if (item.type === 'text') {
        this.addTextBlock();
        const lastBlock = this.content.lastChild;
        lastBlock.querySelector('textarea').value = item.value;
      } else if (item.type === 'image_with_caption') {
        this.addImageBlock();
        const lastBlock = this.content.lastChild;
        lastBlock.querySelector('input[type="text"]').value = item.value.caption;
        if (item.value.image_id) {
          lastBlock.querySelector('input[type="file"]').dataset.imageId = item.value.image_id;
        }
      }
    });
  }
}