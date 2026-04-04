import { Editor } from 'https://esm.sh/@tiptap/core@2.26.4';
import StarterKit from 'https://esm.sh/@tiptap/starter-kit@2.26.4';
import Placeholder from 'https://esm.sh/@tiptap/extension-placeholder@2.26.4';
import Underline from 'https://esm.sh/@tiptap/extension-underline@2.26.4';
import Link from 'https://esm.sh/@tiptap/extension-link@2.26.4';
import Image from 'https://esm.sh/@tiptap/extension-image@2.26.4';
import TextAlign from 'https://esm.sh/@tiptap/extension-text-align@2.26.4';
import { Extension } from 'https://esm.sh/@tiptap/core@2.26.4';
import TextStyle from 'https://esm.sh/@tiptap/extension-text-style@2.26.4';
import Color from 'https://esm.sh/@tiptap/extension-color@2.26.4';
import Highlight from 'https://esm.sh/@tiptap/extension-highlight@2.26.4';
import FontFamily from 'https://esm.sh/@tiptap/extension-font-family@2.26.4';
import Table from 'https://esm.sh/@tiptap/extension-table@2.26.4';
import TableRow from 'https://esm.sh/@tiptap/extension-table-row@2.26.4';
import TableHeader from 'https://esm.sh/@tiptap/extension-table-header@2.26.4';
import TableCell from 'https://esm.sh/@tiptap/extension-table-cell@2.26.4';

const gettext = window.gettext || ((s) => s);

const FontSize = Extension.create({
  name: 'fontSize',

  addGlobalAttributes() {
    return [
      {
        types: ['textStyle'],
        attributes: {
          fontSize: {
            default: null,
            parseHTML: (element) => element.style.fontSize || null,
            renderHTML: (attributes) => {
              if (!attributes.fontSize) {
                return {};
              }
              return { style: `font-size: ${attributes.fontSize}` };
            },
          },
        },
      },
    ];
  },

  addCommands() {
    return {
      setFontSize: (fontSize) => ({ chain }) => chain().setMark('textStyle', { fontSize }).run(),
      unsetFontSize: () => ({ chain }) => chain().setMark('textStyle', { fontSize: null }).removeEmptyTextStyle().run(),
    };
  },
});

function getCookie(name) {
  const m = document.cookie.match('(?:^|;)\\s*' + name.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, '\\$&') + '=([^;]*)');
  return m ? decodeURIComponent(m[1]) : null;
}

function getCsrfToken() {
  const input = document.querySelector('input[name=csrfmiddlewaretoken]');
  return (input && input.value) || getCookie('csrftoken') || '';
}

function isEmptyHtml(html) {
  const div = document.createElement('div');
  div.innerHTML = html || '';
  const text = (div.textContent || '').replace(/\u00A0/g, ' ').trim();
  const hasMedia = div.querySelector('img,table,iframe,video,embed,figure,blockquote,pre,code,ul,ol,li');
  return !text && !hasMedia;
}

function decodeInitialEditorContent(raw) {
  const value = raw || '';
  const hasHtmlTags = /<\/?[a-z][^>]*>/i.test(value);
  const hasEscapedHtml = /&lt;\/?[a-z][\s\S]*?&gt;/i.test(value);
  if (hasHtmlTags || !hasEscapedHtml) {
    return value;
  }

  const textarea = document.createElement('textarea');
  textarea.innerHTML = value;
  return textarea.value;
}

function showErrorBelowEditor(wrapper, message) {
  let fb = wrapper.querySelector('.tiptap-invalid-feedback');
  if (!fb) {
    fb = document.createElement('div');
    fb.className = 'tiptap-invalid-feedback text-danger mt-1';
    wrapper.appendChild(fb);
  }
  fb.textContent = message;
}

function clearError(wrapper) {
  const fb = wrapper.querySelector('.tiptap-invalid-feedback');
  if (fb) fb.remove();
}

function button(iconClass, title, onClick, textLabel = '') {
  const el = document.createElement('button');
  el.type = 'button';
  el.className = 'tiptap-toolbtn btn btn-sm btn-outline-secondary';
  el.title = title;
  el.setAttribute('aria-label', title);
  el.innerHTML = `
    <i class="bi ${iconClass}" aria-hidden="true"></i>
    ${textLabel ? `<span class="tiptap-tooltext">${textLabel}</span>` : ''}
  `;
  el.addEventListener('mousedown', (e) => {
    e.preventDefault();
  });
  el.addEventListener('click', onClick);
  return el;
}

function createGroup(label) {
  const group = document.createElement('div');
  group.className = 'tiptap-group';

  const body = document.createElement('div');
  body.className = 'tiptap-group-body';

  const caption = document.createElement('div');
  caption.className = 'tiptap-group-label';
  caption.textContent = label;

  group.appendChild(body);
  group.appendChild(caption);

  return { group, body };
}

function createSelect(options, title, onChange) {
  const select = document.createElement('select');
  select.className = 'form-select form-select-sm tiptap-select';
  select.title = title;
  options.forEach(({ value, label }) => {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = label;
    select.appendChild(option);
  });
  select.addEventListener('change', onChange);
  return select;
}

function createColorInput(title, onInput) {
  const input = document.createElement('input');
  input.type = 'color';
  input.className = 'form-control form-control-color form-control-sm tiptap-color';
  input.title = title;
  input.value = '#111827';
  input.addEventListener('input', onInput);
  return input;
}

async function uploadImage(file, uploadUrl, csrfToken) {
  const formData = new FormData();
  formData.append('upload', file);

  const response = await fetch(uploadUrl, {
    method: 'POST',
    headers: { 'X-CSRFToken': csrfToken },
    body: formData,
    credentials: 'same-origin',
  });

  const data = await response.json();
  if (!response.ok) {
    const message = data && data.error && data.error.message
      ? data.error.message
      : gettext('Upload error.');
    throw new Error(message);
  }

  return data.url;
}

function buildToolbar(editor, options) {
  const toolbar = document.createElement('div');
  toolbar.className = 'tiptap-ribbon';
  const syncHandlers = [];

  const chain = () => editor.chain().focus();
  const mode = options.mode || 'full';
  const registerSync = (handler) => syncHandlers.push(handler);
  const syncToolbarState = () => {
    syncHandlers.forEach((handler) => handler());
  };
  const makeButton = (iconClass, title, onClick, textLabel = '', isActive = null) => {
    const el = button(iconClass, title, onClick, textLabel);
    if (isActive) {
      registerSync(() => {
        el.classList.toggle('is-active', Boolean(isActive()));
      });
    }
    return el;
  };

  const fontGroup = createGroup(gettext('Font'));
  const fontFamilySelect = createSelect([
    { value: '', label: gettext('Default') },
    { value: 'Georgia', label: 'Georgia' },
    { value: 'Arial', label: 'Arial' },
    { value: '"Trebuchet MS"', label: 'Trebuchet MS' },
    { value: '"Times New Roman"', label: 'Times New Roman' },
    { value: 'Verdana', label: 'Verdana' },
  ], gettext('Font family'), (e) => {
    const value = e.target.value;
    if (!value) {
      chain().unsetFontFamily().run();
      syncToolbarState();
      return;
    }
    chain().setFontFamily(value).run();
    syncToolbarState();
  });
  const fontSizeSelect = createSelect([
    { value: '', label: gettext('Size') },
    { value: '12px', label: '12' },
    { value: '14px', label: '14' },
    { value: '16px', label: '16' },
    { value: '18px', label: '18' },
    { value: '20px', label: '20' },
    { value: '24px', label: '24' },
    { value: '28px', label: '28' },
    { value: '32px', label: '32' },
  ], gettext('Font size'), (e) => {
    const value = e.target.value;
    if (!value) {
      chain().unsetFontSize().run();
      syncToolbarState();
      return;
    }
    chain().setFontSize(value).run();
    syncToolbarState();
  });
  const textColor = createColorInput(gettext('Text color'), (e) => {
    chain().setColor(e.target.value).run();
    syncToolbarState();
  });
  const highlightColor = createColorInput(gettext('Highlight color'), (e) => {
    chain().setHighlight({ color: e.target.value }).run();
    syncToolbarState();
  });
  registerSync(() => {
    fontFamilySelect.value = editor.getAttributes('textStyle').fontFamily || '';
    fontSizeSelect.value = editor.getAttributes('textStyle').fontSize || '';
    textColor.value = editor.getAttributes('textStyle').color || '#111827';
    if (mode !== 'post') {
      highlightColor.value = editor.getAttributes('highlight').color || '#fff59d';
    }
  });
  fontGroup.body.appendChild(fontFamilySelect);
  fontGroup.body.appendChild(fontSizeSelect);
  fontGroup.body.appendChild(textColor);
  if (mode !== 'post') {
    fontGroup.body.appendChild(highlightColor);
  }
  toolbar.appendChild(fontGroup.group);

  const styleGroup = createGroup(gettext('Style'));
  [
    ['bi-type-bold', gettext('Bold'), () => chain().toggleBold().run(), '', () => editor.isActive('bold')],
    ['bi-type-italic', gettext('Italic'), () => chain().toggleItalic().run(), '', () => editor.isActive('italic')],
    ['bi-type-underline', gettext('Underline'), () => chain().toggleUnderline().run(), '', () => editor.isActive('underline')],
    ['bi-type-strikethrough', gettext('Strike'), () => chain().toggleStrike().run(), '', () => editor.isActive('strike')],
    ['bi-blockquote-left', gettext('Quote'), () => chain().toggleBlockquote().run(), '', () => editor.isActive('blockquote')],
    ['bi-code-slash', gettext('Code block'), () => chain().toggleCodeBlock().run(), '', () => editor.isActive('codeBlock')],
    ['bi-eraser', gettext('Clear formatting'), () => chain().unsetAllMarks().clearNodes().run()],
  ].forEach(([iconClass, title, onClick, textLabel, isActive]) => styleGroup.body.appendChild(makeButton(iconClass, title, onClick, textLabel || '', isActive)));
  toolbar.appendChild(styleGroup.group);

  const paragraphGroup = createGroup(gettext('Paragraph'));
  const formatSelect = createSelect([
    { value: 'paragraph', label: gettext('Paragraph') },
    { value: 'h2', label: gettext('Heading 2') },
    { value: 'h3', label: gettext('Heading 3') },
  ], gettext('Text style'), (e) => {
    const value = e.target.value;
    if (value === 'paragraph') {
      chain().setParagraph().run();
      syncToolbarState();
      return;
    }
    chain().toggleHeading({ level: value === 'h2' ? 2 : 3 }).run();
    syncToolbarState();
  });
  registerSync(() => {
    if (editor.isActive('heading', { level: 2 })) {
      formatSelect.value = 'h2';
    } else if (editor.isActive('heading', { level: 3 })) {
      formatSelect.value = 'h3';
    } else {
      formatSelect.value = 'paragraph';
    }
  });
  paragraphGroup.body.appendChild(formatSelect);
  [
    ['bi-list-ul', gettext('Bulleted list'), () => chain().toggleBulletList().run(), '', () => editor.isActive('bulletList')],
    ['bi-list-ol', gettext('Numbered list'), () => chain().toggleOrderedList().run(), '', () => editor.isActive('orderedList')],
    ['bi-justify-left', gettext('Align left'), () => chain().setTextAlign('left').run(), '', () => editor.isActive({ textAlign: 'left' })],
    ['bi-justify', gettext('Align center'), () => chain().setTextAlign('center').run(), gettext('C'), () => editor.isActive({ textAlign: 'center' })],
    ['bi-justify-right', gettext('Align right'), () => chain().setTextAlign('right').run(), '', () => editor.isActive({ textAlign: 'right' })],
  ].forEach(([iconClass, title, onClick, textLabel, isActive]) => paragraphGroup.body.appendChild(makeButton(iconClass, title, onClick, textLabel || '', isActive)));
  if (mode !== 'post') {
    paragraphGroup.body.appendChild(makeButton('bi-justify', gettext('Justify'), () => chain().setTextAlign('justify').run(), gettext('J'), () => editor.isActive({ textAlign: 'justify' })));
  }
  toolbar.appendChild(paragraphGroup.group);

  const insertGroup = createGroup(gettext('Insert'));
  insertGroup.body.appendChild(makeButton('bi-link-45deg', gettext('Add link'), () => setLink(editor), '', () => editor.isActive('link')));
  if (mode !== 'post') {
    insertGroup.body.appendChild(makeButton('bi-image', gettext('Upload image'), () => openImagePicker(editor, options)));
    insertGroup.body.appendChild(makeButton('bi-table', gettext('Insert table'), () => chain().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run(), '', () => editor.isActive('table')));
    insertGroup.body.appendChild(makeButton('bi-dash', gettext('Horizontal line'), () => chain().setHorizontalRule().run()));
  }
  toolbar.appendChild(insertGroup.group);

  if (mode !== 'post') {
    const tableGroup = createGroup(gettext('Table'));
    [
      ['bi-plus-square', gettext('Add row after'), () => chain().addRowAfter().run(), gettext('R')],
      ['bi-plus-square', gettext('Add column after'), () => chain().addColumnAfter().run(), gettext('C')],
      ['bi-dash-square', gettext('Delete row'), () => chain().deleteRow().run(), gettext('R')],
      ['bi-dash-square', gettext('Delete column'), () => chain().deleteColumn().run(), gettext('C')],
      ['bi-intersect', gettext('Merge cells'), () => chain().mergeCells().run()],
      ['bi-border-all', gettext('Split cell'), () => chain().splitCell().run()],
    ].forEach(([iconClass, title, onClick, textLabel]) => tableGroup.body.appendChild(makeButton(iconClass, title, onClick, textLabel || '', () => editor.isActive('table'))));
    toolbar.appendChild(tableGroup.group);
  }

  const historyGroup = createGroup(gettext('History'));
  historyGroup.body.appendChild(makeButton('bi-arrow-counterclockwise', gettext('Undo'), () => chain().undo().run()));
  historyGroup.body.appendChild(makeButton('bi-arrow-clockwise', gettext('Redo'), () => chain().redo().run()));
  toolbar.appendChild(historyGroup.group);

  editor.on('selectionUpdate', syncToolbarState);
  editor.on('transaction', syncToolbarState);
  editor.on('focus', syncToolbarState);
  editor.on('blur', syncToolbarState);
  syncToolbarState();

  return toolbar;
}

function setLink(editor) {
  const previousUrl = editor.getAttributes('link').href || '';
  const url = window.prompt(gettext('Enter URL'), previousUrl);
  if (url === null) return;

  const value = url.trim();
  if (!value) {
    editor.chain().focus().unsetLink().run();
    return;
  }

  editor.chain().focus().extendMarkRange('link').setLink({
    href: value,
    target: '_blank',
    rel: 'nofollow noopener noreferrer',
  }).run();
}

function openImagePicker(editor, options) {
  if (!options.uploadUrl) return;

  const input = document.createElement('input');
  input.type = 'file';
  input.accept = 'image/*';
  input.addEventListener('change', async () => {
    const file = input.files && input.files[0];
    if (!file) return;

    try {
      const url = await uploadImage(file, options.uploadUrl, options.csrfToken);
      editor.chain().focus().setImage({ src: url, alt: file.name }).run();
    } catch (error) {
      window.alert(error.message || gettext('Upload error.'));
    }
  });
  input.click();
}

function initEditor(textarea) {
  const mode = textarea.dataset.editorMode || 'full';
  const placeholder = textarea.dataset.placeholder || gettext('Start writing...');
  const requiredMsg = textarea.dataset.requiredMsg || gettext('Content is required.');
  const uploadUrl = textarea.dataset.uploadUrl || '';
  const disableUploads = textarea.dataset.disableUploads === '1';
  const csrfToken = getCsrfToken();

  const wrapper = document.createElement('div');
  wrapper.className = `tiptap-shell ${mode === 'post' ? 'tiptap-shell-post' : 'tiptap-shell-full'}`;

  const editorEl = document.createElement('div');
  editorEl.className = 'tiptap-editor';

  textarea.insertAdjacentElement('afterend', wrapper);
  textarea.classList.add('d-none');

  const initialContent = decodeInitialEditorContent(textarea.value || '');

  const editor = new Editor({
    element: editorEl,
    extensions: [
      StarterKit.configure({
        heading: { levels: [2, 3] },
      }),
      Placeholder.configure({
        placeholder,
      }),
      Underline,
      TextStyle,
      Color,
      Highlight.configure({ multicolor: true }),
      FontFamily,
      FontSize,
      Link.configure({
        openOnClick: false,
        autolink: true,
        linkOnPaste: true,
        HTMLAttributes: {
          rel: 'nofollow noopener noreferrer',
          target: '_blank',
        },
      }),
      TextAlign.configure({
        types: ['heading', 'paragraph'],
      }),
      ...(mode === 'post' ? [] : [
        Table.configure({
          resizable: true,
        }),
        TableRow,
        TableHeader,
        TableCell,
      ]),
      ...(disableUploads ? [] : [Image]),
    ],
    content: initialContent,
    editorProps: {
      attributes: {
        class: 'tiptap-content form-control',
      },
    },
    onUpdate: ({ editor: current }) => {
      textarea.value = current.getHTML();
      clearError(wrapper);
    },
  });

  const toolbar = buildToolbar(editor, {
    mode,
    uploadUrl: disableUploads ? '' : uploadUrl,
    csrfToken,
  });

  textarea.value = initialContent;

  wrapper.appendChild(toolbar);
  wrapper.appendChild(editorEl);

  const form = textarea.closest('form');
  if (form) {
    form.addEventListener('submit', (e) => {
      textarea.value = editor.getHTML();
      if (isEmptyHtml(textarea.value)) {
        e.preventDefault();
        showErrorBelowEditor(wrapper, requiredMsg);
        editor.commands.focus();
      }
    });
  }
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.js-tiptap').forEach(initEditor);
});
