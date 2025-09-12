(function () {
  const _ = (window.gettext) ? window.gettext : (s) => s;

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

  function showErrorBelowEditor(el, message) {
    const wrapper = el.nextElementSibling && el.nextElementSibling.classList.contains('ck-editor')
      ? el.nextElementSibling
      : el.parentElement;

    let fb = wrapper.querySelector('.ck-invalid-feedback');
    if (!fb) {
      fb = document.createElement('div');
      fb.className = 'ck-invalid-feedback text-danger mt-1';
      wrapper.appendChild(fb);
    }
    fb.textContent = message;
  }

  function clearError(el) {
    const wrapper = el.nextElementSibling && el.nextElementSibling.classList.contains('ck-editor')
      ? el.nextElementSibling
      : el.parentElement;
    const fb = wrapper.querySelector('.ck-invalid-feedback');
    if (fb) fb.remove();
  }

  function initEditor(el) {
    if (!window.CKEDITOR || !CKEDITOR.ClassicEditor) {
      console.warn('CKEditor super-build not loaded');
      return;
    }

    const lang = el.dataset.language || 'en';
    const uploadUrl = el.dataset.uploadUrl || '';
    const placeholder = el.dataset.placeholder || _('Start writing…');
    const requiredMsg = el.dataset.requiredMsg || _('Content is required.');
    const csrfToken = getCsrfToken();

    CKEDITOR.ClassicEditor.create(el, {
      language: lang,
      placeholder: placeholder,
      toolbar: {
        items: [
          'heading', '|',
          'bold', 'italic', 'link', 'blockQuote', 'codeBlock', 'horizontalLine', '|',
          'bulletedList', 'numberedList', '|',
          'insertTable', 'imageUpload', 'mediaEmbed', '|',
          'undo', 'redo'
        ]
      },

      htmlSupport: {
        allow: [
          { name: /^(p|br|strong|em|u|s|a|ul|ol|li|blockquote|code|pre|hr|h2|h3|h4|h5|h6|figure|figcaption)$/, attributes: true, classes: true, styles: true },
          { name: 'img', attributes: ['src', 'alt', 'width', 'height', 'loading', 'class', 'style'] },
          { name: 'table', attributes: true, classes: true, styles: true },
          { name: 'thead', attributes: true }, { name: 'tbody', attributes: true },
          { name: 'tr', attributes: true }, { name: 'th', attributes: ['rowspan', 'colspan', 'style'] },
          { name: 'td', attributes: ['rowspan', 'colspan', 'style'] }
        ],
        disallow: [
          { name: /^(script|style)$/ },
          { attributes: [/^on.*/] }
        ]
      },

      link: {
        addTargetToExternalLinks: true,
        defaultProtocol: 'https://',
        decorators: {
          addRelNoOpener: {
            mode: 'automatic',
            callback: url => /^(https?:)?\/\//.test(url),
            attributes: { rel: 'nofollow noopener noreferrer' }
          }
        }
      },

      image: {
        toolbar: [
          'imageStyle:inline', 'imageStyle:block', 'imageStyle:side',
          'toggleImageCaption', 'linkImage', 'imageTextAlternative'
        ],
        styles: ['inline', 'block', 'side'],
        upload: { types: ['jpeg', 'jpg', 'png', 'gif', 'webp'] }
      },

      table: {
        contentToolbar: [
          'tableColumn', 'tableRow', 'mergeTableCells', 'tableProperties', 'tableCellProperties'
        ]
      },

      mediaEmbed: { previewsInData: true },

      simpleUpload: {
        uploadUrl: uploadUrl,
        headers: { 'X-CSRFToken': csrfToken }
      },

      removePlugins: [
        'CKBox', 'CKFinder', 'EasyImage',
        'ExportPdf', 'ExportWord', 'AIAssistant', 'WProofreader',
        'ImportWord', 'MathType',
        'RealTimeCollaborativeComments', 'RealTimeCollaborativeTrackChanges',
        'RealTimeCollaborativeRevisionHistory', 'PresenceList', 'Comments',
        'TrackChanges', 'TrackChangesData', 'RevisionHistory', 'Users',
        'MultiLevelList', 'Pagination', 'PasteFromOfficeEnhanced', 'CaseChange',
        'SlashCommand', 'Template', 'FormatPainter', 'DocumentOutline', 'TableOfContents'
      ]
    })
      .then(editor => {
        editor.model.document.on('change:data', () => {
          clearError(el);
        });

        const form = el.closest('form');
        if (form) {
          form.addEventListener('submit', e => {
            const html = editor.getData();
            if (isEmptyHtml(html)) {
              e.preventDefault();
              showErrorBelowEditor(el, requiredMsg);
              editor.editing.view.focus();
            }
          });
        }
      })
      .catch(console.error);
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.js-ckeditor').forEach(initEditor);
  });
})();
