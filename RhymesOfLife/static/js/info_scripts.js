document.addEventListener("DOMContentLoaded", function () {
  console.log("JavaScript is loaded and working!");

  // ===== Пример тестового клика (не трогаем) =====
  let heading = document.getElementById("welcome-heading");
  if (heading) {
    heading.addEventListener("click", function () {
      heading.style.color = "red";
    });
  }

  // ======== Хедер ========
  const menuBtn = document.querySelector('.header__nav-menu-btn');
  const nav = document.querySelector('.header__nav');
  const closeBtn = document.querySelector('.close-menu');
  const dropdownToggles = document.querySelectorAll('.dropdown-toggle');

  // --- Открытие/закрытие бургера ---
  if (menuBtn && nav) {
    menuBtn.addEventListener('click', () => {
      const expanded = nav.classList.toggle('active');
      document.body.classList.toggle('menu-open', expanded);
      menuBtn.setAttribute('aria-expanded', expanded);
    });
  }

  // --- Кнопка "×" (если будет добавлена) ---
  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      nav.classList.remove('active');
      document.body.classList.remove('menu-open');
      menuBtn && menuBtn.setAttribute('aria-expanded', 'false');
    });
  }

  // --- Подменю "Классификация ДСТ" (мобильная версия) ---
  dropdownToggles.forEach(toggle => {
    toggle.addEventListener('click', e => {
      if (window.innerWidth <= 768) {
        e.preventDefault();

        const dropdown = toggle.closest('.dropdown');
        const menu = dropdown.querySelector('.dropdown-menu');
        const isActive = dropdown.classList.contains('active');

        // Закрываем другие подменю
        document.querySelectorAll('.dropdown').forEach(d => {
          d.classList.remove('active');
          const m = d.querySelector('.dropdown-menu');
          if (m) m.style.maxHeight = 0;
        });

        // Переключаем текущее
        if (!isActive) {
          dropdown.classList.add('active');
          menu.style.maxHeight = menu.scrollHeight + 'px';
        }
      }
    });
  });

  // --- Закрытие меню при клике по пункту ---
document.querySelectorAll('.header__nav-list-item-link, .dropdown-item').forEach(item => {
  item.addEventListener('click', e => {
    // Если кликнули по кнопке, которая раскрывает подменю — не закрываем меню
    if (e.target.closest('.dropdown-toggle')) return;

    nav.classList.remove('active');
    document.body.classList.remove('menu-open');
  });
});

  // --- Сброс при ресайзе ---
  window.addEventListener('resize', () => {
    if (window.innerWidth > 768) {
      document.querySelectorAll('.dropdown-menu').forEach(m => (m.style.maxHeight = ''));
      nav.classList.remove('active');
      document.body.classList.remove('menu-open');
      menuBtn.setAttribute('aria-expanded', 'false');
    }
  });

  // ======== Аккордеон .sed ========
  const headers = document.querySelectorAll('.accordion-header.sed');

  headers.forEach(header => {
    const panel = header.nextElementSibling;
    if (!panel) return;

    // Начальное состояние
    if (header.getAttribute('aria-expanded') === 'true') {
      panel.style.maxHeight = panel.scrollHeight + 'px';
    } else {
      panel.style.maxHeight = '0';
    }

    header.addEventListener('click', () => {
      const isOpen = header.getAttribute('aria-expanded') === 'true';

      // Закрываем все
      headers.forEach(h => {
        if (h === header) return;
        h.setAttribute('aria-expanded', 'false');
        const p = h.nextElementSibling;
        p.style.maxHeight = '0';
      });

      if (!isOpen) {
        header.setAttribute('aria-expanded', 'true');
        panel.style.maxHeight = panel.scrollHeight + 'px';
      } else {
        header.setAttribute('aria-expanded', 'false');
        panel.style.maxHeight = '0';
      }
    });
  });
});









