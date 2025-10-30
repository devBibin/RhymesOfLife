// info_scripts.js

document.addEventListener('DOMContentLoaded', function() {
    // Элементы
    const burgerBtn = document.querySelector('.burger-btn');
    const mobileMenu = document.querySelector('.mobile-menu');
    const closeBtn = document.querySelector('.mobile-menu__close');

    // Состояние
    let isMobileMenuOpen = false;

    // ================= МОБИЛЬНОЕ МЕНЮ =================
    function toggleMobileMenu() {
        isMobileMenuOpen = !isMobileMenuOpen;
        
        mobileMenu.classList.toggle('mobile-menu--active', isMobileMenuOpen);
        mobileMenu.setAttribute('aria-hidden', !isMobileMenuOpen);
        burgerBtn.setAttribute('aria-expanded', isMobileMenuOpen);
        document.body.classList.toggle('no-scroll', isMobileMenuOpen);

if (isMobileMenuOpen) {
    closeBtn?.focus();            // <-- вот эта проверка обязательна
} else {
    burgerBtn?.focus();
    closeAllMobileDropdowns();
}
    }

    // ================= ВЫПАДАЮЩИЕ МЕНЮ =================
    function initDropdowns() {
        // Desktop dropdowns
        const desktopDropdownToggles = document.querySelectorAll('.nav .dropdown__toggle');
        desktopDropdownToggles.forEach(toggle => {
            toggle.addEventListener('click', (e) => handleDropdownClick(e, toggle));
        });

        // Mobile dropdowns
        const mobileDropdownToggles = document.querySelectorAll('.mobile-menu .dropdown__toggle');
        mobileDropdownToggles.forEach(toggle => {
            toggle.addEventListener('click', (e) => handleDropdownClick(e, toggle));
        });
    }

    function handleDropdownClick(e, toggle) {
        e.preventDefault();
        e.stopPropagation();
        
        const isExpanded = toggle.getAttribute('aria-expanded') === 'true';
        const dropdownId = toggle.getAttribute('aria-controls');
        const dropdownMenu = document.getElementById(dropdownId);
        
        if (!dropdownMenu) {
            console.error('Dropdown menu not found:', dropdownId);
            return;
        }

        // Закрываем другие dropdown того же типа
        const isMobile = toggle.closest('.mobile-menu');
        if (isMobile) {
            closeAllMobileDropdowns(toggle);
        } else {
            closeAllDesktopDropdowns(toggle);
        }

        // Переключаем текущий
        toggle.setAttribute('aria-expanded', !isExpanded);
        dropdownMenu.classList.toggle('dropdown__menu--active', !isExpanded);
    }

    function closeAllDesktopDropdowns(excludeToggle = null) {
        const desktopToggles = document.querySelectorAll('.nav .dropdown__toggle');
        desktopToggles.forEach(toggle => {
            if (toggle !== excludeToggle) {
                toggle.setAttribute('aria-expanded', 'false');
                const menu = document.getElementById(toggle.getAttribute('aria-controls'));
                if (menu) menu.classList.remove('dropdown__menu--active');
            }
        });
    }

    function closeAllMobileDropdowns(excludeToggle = null) {
        const mobileToggles = document.querySelectorAll('.mobile-menu .dropdown__toggle');
        const mobileMenus = document.querySelectorAll('.mobile-menu .dropdown__menu');
        
        mobileToggles.forEach(toggle => {
            if (toggle !== excludeToggle) {
                toggle.setAttribute('aria-expanded', 'false');
            }
        });
        
        mobileMenus.forEach(menu => {
            menu.classList.remove('dropdown__menu--active');
        });
    }

    // ================= ОБРАБОТЧИКИ СОБЫТИЙ =================
    burgerBtn.addEventListener('click', toggleMobileMenu);
    closeBtn?.addEventListener('click', toggleMobileMenu);

    // Инициализация dropdown при загрузке
    initDropdowns();

    // Закрытие dropdown при клике вне элемента
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.dropdown')) {
            closeAllDesktopDropdowns();
        }
        
        // Закрытие мобильного меню
        if (isMobileMenuOpen && 
            !e.target.closest('.mobile-menu') && 
            !e.target.closest('.burger-btn')) {
            toggleMobileMenu();
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            if (isMobileMenuOpen) {
                toggleMobileMenu();
            } else {
                closeAllDesktopDropdowns();
            }
        }
    });

    window.addEventListener('resize', () => {
        if (window.innerWidth > 768 && isMobileMenuOpen) {
            toggleMobileMenu();
        }
    });

    // Закрытие мобильного меню при клике на ссылку (кроме dropdown toggle)
    mobileMenu.addEventListener('click', (e) => {
        if (e.target.tagName === 'A' && !e.target.classList.contains('dropdown__toggle')) {
            toggleMobileMenu();
        }
    });

    // Инициализация ARIA
    mobileMenu.setAttribute('aria-hidden', 'true');
    burgerBtn.setAttribute('aria-expanded', 'false');
    
    // Инициализация всех dropdown
    const allDropdownToggles = document.querySelectorAll('.dropdown__toggle');
    allDropdownToggles.forEach(toggle => {
        toggle.setAttribute('aria-expanded', 'false');
    });
});






  // ===== Аккордеон .sed (как было) =====
  const sedHeaders = document.querySelectorAll('.accordion-header.sed');
  sedHeaders.forEach(header => {
    const panel = header.nextElementSibling;
    if (!panel) return;

    panel.style.maxHeight =
      header.getAttribute('aria-expanded') === 'true' ? panel.scrollHeight + 'px' : '0';

    header.addEventListener('click', () => {
      const isOpen = header.getAttribute('aria-expanded') === 'true';

      sedHeaders.forEach(h => {
        if (h === header) return;
        h.setAttribute('aria-expanded', 'false');
        const p = h.nextElementSibling;
        if (p) p.style.maxHeight = '0';
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
