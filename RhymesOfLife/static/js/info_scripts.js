document.addEventListener("DOMContentLoaded", function () {
  console.log("JavaScript is loaded and working!");

  let heading = document.getElementById("welcome-heading");
  if (heading) {
    heading.addEventListener("click", function () {
      heading.style.color = "red";
    });
  }
});

// Хедер
document.addEventListener('DOMContentLoaded', () => {
  const menuBtn = document.querySelector('.header__nav-menu-btn');
  const nav = document.querySelector('.header__nav');
  const closeBtn = document.querySelector('.close-menu');

  // Открыть/закрыть бургер
  if (menuBtn && nav) {
    menuBtn.addEventListener('click', () => {
      nav.classList.toggle('active');
      document.body.classList.toggle('menu-open');
      menuBtn.setAttribute('aria-expanded', nav.classList.contains('active'));
    });
  }

  // Кнопка "×"
  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      nav.classList.remove('active');
      document.body.classList.remove('menu-open');
      menuBtn && menuBtn.setAttribute('aria-expanded', 'false');
    });
  }

  // Делегирование на выпадашку "Классификация"
  document.addEventListener('click', e => {
    const toggle = e.target.closest('.dropdown-toggle');
    if (!toggle) return;

    e.preventDefault();
    const dropdown = toggle.closest('.dropdown');
    const menu = dropdown.querySelector('.dropdown-menu');
    const open = dropdown.classList.toggle('active');

    toggle.setAttribute('aria-expanded', open);
    // Автовысота для плавной анимации
    menu.style.maxHeight = open ? menu.scrollHeight + 'px' : 0;
  });

  // Закрываем меню при клике по пункту
  document.querySelectorAll('.header__nav-list-item-link, .dropdown-item').forEach(item => {
    item.addEventListener('click', () => {
      nav.classList.remove('active');
      document.body.classList.remove('menu-open');
    });
  });
});

document.addEventListener('DOMContentLoaded', () => {
  const headers = document.querySelectorAll('.accordion-header.sed');

  headers.forEach(header => {
    const panel = header.nextElementSibling;
    if (!panel) return;

    // Убедимся в начальном состоянии
    if (header.getAttribute('aria-expanded') === 'true') {
      panel.style.maxHeight = panel.scrollHeight + 'px';
    } else {
      panel.style.maxHeight = '0';
    }

    header.addEventListener('click', () => {
      const isOpen = header.getAttribute('aria-expanded') === 'true';

      if (isOpen) {
        // Закрываем текущий
        header.setAttribute('aria-expanded', 'false');

        // Установим текущее значение, затем в следующем кадре — 0, чтобы анимация сработала
        panel.style.maxHeight = panel.scrollHeight + 'px';
        requestAnimationFrame(() => {
          panel.style.maxHeight = '0';
        });
        return;
      }

      // Закрываем все остальные (если нужен «только один открыт» режим)
      headers.forEach(h => {
        if (h === header) return;
        if (h.getAttribute('aria-expanded') === 'true') {
          h.setAttribute('aria-expanded', 'false');
          const p = h.nextElementSibling;
          p.style.maxHeight = p.scrollHeight + 'px';
          requestAnimationFrame(() => {
            p.style.maxHeight = '0';
          });
        }
      });

      // Открываем кликнутый
      header.setAttribute('aria-expanded', 'true');
      panel.style.maxHeight = panel.scrollHeight + 'px';

      // По завершении анимации убираем inline maxHeight, но только если это наш panel
      const onTransitionEnd = (e) => {
        if (e.target === panel && e.propertyName === 'max-height' && header.getAttribute('aria-expanded') === 'true') {
          // Сброс inline-стиля ('' лучше, чем 'none')
          panel.style.maxHeight = '';
        }
        panel.removeEventListener('transitionend', onTransitionEnd);
      };
      panel.addEventListener('transitionend', onTransitionEnd);
    });
  });
});







