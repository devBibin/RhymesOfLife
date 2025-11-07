// info_scripts.js (clean)

document.addEventListener('DOMContentLoaded', function () {
  // ================= ПЕРЕМЕННЫЕ И СОСТОЯНИЕ =================
  const burgerBtn = document.querySelector('.burger-btn');
  const mobileMenu = document.querySelector('.mobile-menu');
  const closeBtn = document.querySelector('.mobile-menu__close');
  let isMobileMenuOpen = false;

  // ================= СИСТЕМА ВОССТАНОВЛЕНИЯ ПАРОЛЯ (UI) =================
  class PasswordRecovery {
    constructor() {
      this.currentStep = 1;
      this.steps = {
        1: 'step-email',
        2: 'step-sent',
        3: 'step-password',
        4: 'step-success',
      };
      this.init();
    }

    init() {
      this.bindEvents();
      this.showStep(1);
    }

    bindEvents() {
      const emailForm = document.querySelector('.recovery-email-form');
      if (emailForm) {
        emailForm.addEventListener('submit', (e) => this.handleEmailSubmit(e));
      }

      const passwordForm = document.querySelector('.recovery-password-form');
      if (passwordForm) {
        passwordForm.addEventListener('submit', (e) => this.handlePasswordSubmit(e));
      }

      this.bindRealTimeValidation();
    }

    bindRealTimeValidation() {
      const emailInput = document.querySelector('.recovery-email-input');
      if (emailInput) {
        emailInput.addEventListener('input', () => {
          this.hideError('email');
        });
      }

      const confirmPasswordInput = document.querySelector('.confirm-password-input');
      if (confirmPasswordInput) {
        confirmPasswordInput.addEventListener('input', () => {
          this.hideError('password');
        });
      }
    }

    handleEmailSubmit(e) {
      e.preventDefault();
      const emailInput = document.querySelector('.recovery-email-input');
      const email = (emailInput?.value || '').trim();

      if (!this.validateEmail(email)) {
        this.showError('email', 'Введите корректный email адрес');
        return;
      }

      // Здесь ожидается реальный вызов бэкенда для отправки письма.
      // После успешного ответа — показываем шаг "отправлено".
      this.showStep(2);
    }

    handlePasswordSubmit(e) {
      e.preventDefault();
      const passwordInput = document.querySelector('.new-password-input');
      const confirmPasswordInput = document.querySelector('.confirm-password-input');

      if (!passwordInput || !confirmPasswordInput) return;

      const password = passwordInput.value;
      const confirmPassword = confirmPasswordInput.value;

      if (!this.validatePassword(password)) {
        this.showError('password', 'Пароль должен содержать минимум 6 символов');
        return;
      }

      if (password !== confirmPassword) {
        this.showError('password', 'Пароли не совпадают');
        return;
      }

      // Здесь ожидается реальный вызов бэкенда для сохранения пароля.
      // После успешного ответа — показываем финальный шаг.
      this.showStep(4);
    }

    validateEmail(email) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return emailRegex.test(email);
    }

    validatePassword(password) {
      return (password || '').length >= 6;
    }

    showStep(stepNumber) {
      this.currentStep = stepNumber;
      document.querySelectorAll('.recovery-step').forEach((step) => {
        step.classList.remove('active');
      });
      const currentStepElement = document.getElementById(this.steps[stepNumber]);
      if (currentStepElement) currentStepElement.classList.add('active');

      this.hideAllErrors();
      this.focusFirstInput(stepNumber);
    }

    focusFirstInput(stepNumber) {
      let firstInput = null;
      switch (stepNumber) {
        case 1:
          firstInput = document.querySelector('.recovery-email-input');
          break;
        case 3:
          firstInput = document.querySelector('.new-password-input');
          break;
      }
      if (firstInput) setTimeout(() => firstInput.focus(), 300);
    }

    showError(type, message) {
      const errorElement = document.querySelector(`.${type}-error`);
      if (errorElement) {
        errorElement.textContent = message;
        errorElement.classList.add('active');
        const inputSelector = type === 'email' ? '.recovery-email-input' : '.confirm-password-input';
        const inputElement = document.querySelector(inputSelector);
        if (inputElement) inputElement.style.borderBottomColor = '#ff4444';
      }
    }

    hideError(type) {
      const errorElement = document.querySelector(`.${type}-error`);
      if (errorElement) {
        errorElement.classList.remove('active');
        const inputSelector = type === 'email' ? '.recovery-email-input' : '.confirm-password-input';
        const inputElement = document.querySelector(inputSelector);
        if (inputElement) inputElement.style.borderBottomColor = '';
      }
    }

    hideAllErrors() {
      document.querySelectorAll('.form-error').forEach((error) => {
        error.classList.remove('active');
      });
      document.querySelectorAll('.form-input').forEach((input) => {
        input.style.borderBottomColor = '';
      });
    }
  }

  // ================= МОБИЛЬНОЕ МЕНЮ =================
  function toggleMobileMenu() {
    isMobileMenuOpen = !isMobileMenuOpen;

    if (mobileMenu) {
      mobileMenu.classList.toggle('mobile-menu--active', isMobileMenuOpen);
      mobileMenu.setAttribute('aria-hidden', String(!isMobileMenuOpen));
    }
    if (burgerBtn) {
      burgerBtn.setAttribute('aria-expanded', String(isMobileMenuOpen));
    }
    document.body.classList.toggle('no-scroll', isMobileMenuOpen);

    if (isMobileMenuOpen) {
      if (closeBtn) closeBtn.focus();
    } else {
      if (burgerBtn) burgerBtn.focus();
      closeAllMobileDropdowns();
    }
  }

  // ================= ВЫПАДАЮЩИЕ МЕНЮ =================
  function initDropdowns() {
    const desktopDropdownToggles = document.querySelectorAll('.nav .dropdown__toggle');
    desktopDropdownToggles.forEach((toggle) => {
      toggle.addEventListener('click', (e) => handleDropdownClick(e, toggle));
    });

    const mobileDropdownToggles = document.querySelectorAll('.mobile-menu .dropdown__toggle');
    mobileDropdownToggles.forEach((toggle) => {
      toggle.addEventListener('click', (e) => handleDropdownClick(e, toggle));
    });
  }

  function handleDropdownClick(e, toggle) {
    e.preventDefault();
    e.stopPropagation();

    const isExpanded = toggle.getAttribute('aria-expanded') === 'true';
    const dropdownId = toggle.getAttribute('aria-controls');
    const dropdownMenu = document.getElementById(dropdownId);
    if (!dropdownMenu) return;

    const isMobile = !!toggle.closest('.mobile-menu');
    if (isMobile) {
      closeAllMobileDropdowns(toggle);
    } else {
      closeAllDesktopDropdowns(toggle);
    }

    toggle.setAttribute('aria-expanded', String(!isExpanded));
    dropdownMenu.classList.toggle('dropdown__menu--active', !isExpanded);
  }

  function closeAllDesktopDropdowns(excludeToggle = null) {
    const desktopToggles = document.querySelectorAll('.nav .dropdown__toggle');
    desktopToggles.forEach((toggle) => {
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

    mobileToggles.forEach((toggle) => {
      if (toggle !== excludeToggle) {
        toggle.setAttribute('aria-expanded', 'false');
      }
    });

    mobileMenus.forEach((menu) => {
      menu.classList.remove('dropdown__menu--active');
    });
  }

  // ================= АККОРДЕОН =================
  function initAccordion() {
    const accordionHeaders = document.querySelectorAll('.accordion__header');

    accordionHeaders.forEach((header) => {
      header.setAttribute('aria-expanded', 'false');
      const body = header.nextElementSibling;
      if (body) body.style.maxHeight = '0';

      header.addEventListener('click', function () {
        const isExpanded = this.getAttribute('aria-expanded') === 'true';

        accordionHeaders.forEach((otherHeader) => {
          if (otherHeader !== header) {
            otherHeader.setAttribute('aria-expanded', 'false');
            const otherBody = otherHeader.nextElementSibling;
            if (otherBody) otherBody.style.maxHeight = '0';
          }
        });

        if (isExpanded) {
          this.setAttribute('aria-expanded', 'false');
          if (body) body.style.maxHeight = '0';
        } else {
          this.setAttribute('aria-expanded', 'true');
          if (body) body.style.maxHeight = body.scrollHeight + 'px';
        }
      });
    });
  }

  // ================= ПЕРЕКЛЮЧЕНИЕ ТАБОВ ФОРМ =================
  function initFormTabs() {
    const tabs = document.querySelectorAll('.form-tab');
    const forms = document.querySelectorAll('.form-container');

    if (!tabs.length || !forms.length) return;

    tabs.forEach((tab) => {
      if (tab.tagName === 'BUTTON') tab.type = 'button';
      tab.addEventListener('click', function (e) {
        e.preventDefault();
        const targetTab = this.getAttribute('data-tab');

        tabs.forEach((t) => {
          t.classList.remove('active');
          t.setAttribute('aria-selected', 'false');
        });

        this.classList.add('active');
        this.setAttribute('aria-selected', 'true');

        forms.forEach((form) => form.classList.remove('active'));

        const targetForm = document.getElementById(`${targetTab}-form`);
        if (targetForm) targetForm.classList.add('active');
      });
    });

    const activeTab = document.querySelector('.form-tab.active');
    if (activeTab) {
      const targetTab = activeTab.getAttribute('data-tab');
      const targetForm = document.getElementById(`${targetTab}-form`);
      if (targetForm) targetForm.classList.add('active');
    }
  }

  // ================= НАВИГАЦИЯ МЕЖДУ ФОРМАМИ (восстановление) =================
  function initAuthNavigation() {
    const showRecoveryBtn = document.getElementById('show-recovery');
    const backToLoginBtn = document.getElementById('back-to-login');
    const backToEmailLink = document.querySelector('.back-to-email-link');
    const successLoginBtn = document.getElementById('success-login-btn');
    const authSection = document.getElementById('auth-section');
    const recoverySection = document.getElementById('recovery-section');

    if (showRecoveryBtn && authSection && recoverySection) {
      showRecoveryBtn.addEventListener('click', function (e) {
        e.preventDefault();
        authSection.style.display = 'none';
        recoverySection.style.display = 'block';
        if (window.passwordRecovery) window.passwordRecovery.showStep(1);
      });
    }

    if (backToLoginBtn && authSection && recoverySection) {
      backToLoginBtn.addEventListener('click', function (e) {
        e.preventDefault();
        recoverySection.style.display = 'none';
        authSection.style.display = 'block';
        if (window.passwordRecovery) window.passwordRecovery.showStep(1);
      });
    }

    if (backToEmailLink) {
      backToEmailLink.addEventListener('click', function (e) {
        e.preventDefault();
        if (window.passwordRecovery) window.passwordRecovery.showStep(1);
      });
    }

    if (successLoginBtn && authSection && recoverySection) {
      successLoginBtn.addEventListener('click', function (e) {
        e.preventDefault();
        recoverySection.style.display = 'none';
        authSection.style.display = 'block';
        const loginTab = document.querySelector('.form-tab[data-tab="login"]');
        const loginForm = document.getElementById('login-form');
        if (loginTab && loginForm) {
          document.querySelectorAll('.form-tab').forEach((t) => t.classList.remove('active'));
          document.querySelectorAll('.form-container').forEach((f) => f.classList.remove('active'));
          loginTab.classList.add('active');
          loginForm.classList.add('active');
        }
        if (window.passwordRecovery) window.passwordRecovery.showStep(1);
      });
    }
  }

  // ================= FIX ХОВЕРОВ/АНИМАЦИЙ =================
  function fixLinkJumping() {
    const interactive = document.querySelectorAll(
      '.forgot-password, .recovery-link, .form-btn, .form-tab, .success-login-btn'
    );
    interactive.forEach((el) => {
      el.style.transform = 'none';
      el.style.transition =
        'color 0.3s ease, background-color 0.3s ease, opacity 0.3s ease';
      el.addEventListener('mouseenter', function () {
        this.style.transform = 'none';
      });
      el.addEventListener('mouseleave', function () {
        this.style.transform = 'none';
      });
    });
  }

  // ================= ГЛОБАЛЬНЫЕ ОБРАБОТЧИКИ =================
  function initGlobalEventHandlers() {
    if (burgerBtn) burgerBtn.addEventListener('click', toggleMobileMenu);
    if (closeBtn) closeBtn.addEventListener('click', toggleMobileMenu);

    document.addEventListener('click', (e) => {
      if (!e.target.closest('.dropdown')) closeAllDesktopDropdowns();
      if (
        isMobileMenuOpen &&
        !e.target.closest('.mobile-menu') &&
        !e.target.closest('.burger-btn')
      ) {
        toggleMobileMenu();
      }
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        if (isMobileMenuOpen) toggleMobileMenu();
        else closeAllDesktopDropdowns();
      }
    });

    window.addEventListener('resize', () => {
      if (window.innerWidth > 768 && isMobileMenuOpen) toggleMobileMenu();
    });

    if (mobileMenu) {
      mobileMenu.addEventListener('click', (e) => {
        if (e.target.tagName === 'A' && !e.target.classList.contains('dropdown__toggle')) {
          toggleMobileMenu();
        }
      });
    }
  }

  // ================= ARIA =================
  function initAriaAttributes() {
    if (mobileMenu) mobileMenu.setAttribute('aria-hidden', 'true');
    if (burgerBtn) burgerBtn.setAttribute('aria-expanded', 'false');
    document.querySelectorAll('.dropdown__toggle').forEach((toggle) => {
      toggle.setAttribute('aria-expanded', 'false');
    });
  }

  // ================= ИНИТ =================
  function init() {
    initAriaAttributes();
    initGlobalEventHandlers();
    initDropdowns();
    initAccordion();
    initFormTabs();
    initAuthNavigation();
    window.passwordRecovery = new PasswordRecovery();
    fixLinkJumping();
  }

  init();
});
