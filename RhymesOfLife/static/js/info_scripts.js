// info_scripts.js

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM загружен, инициализируем компоненты...');

    // ================= ПЕРЕМЕННЫЕ И СОСТОЯНИЕ =================
    const burgerBtn = document.querySelector('.burger-btn');
    const mobileMenu = document.querySelector('.mobile-menu');
    const closeBtn = document.querySelector('.mobile-menu__close');
    let isMobileMenuOpen = false;

    // ================= СИСТЕМА ВОССТАНОВЛЕНИЯ ПАРОЛЯ =================
    class PasswordRecovery {
        constructor() {
            this.currentStep = 1;
            this.steps = {
                1: 'step-email',
                2: 'step-sent', 
                3: 'step-password',
                4: 'step-success'
            };
            
            this.init();
        }
        
        init() {
            this.bindEvents();
            this.showStep(1);
        }
        
        bindEvents() {
            // Форма email
            const emailForm = document.querySelector('.recovery-email-form');
            if (emailForm) {
                emailForm.addEventListener('submit', (e) => this.handleEmailSubmit(e));
            }
            
            // Форма пароля
            const passwordForm = document.querySelector('.recovery-password-form');
            if (passwordForm) {
                passwordForm.addEventListener('submit', (e) => this.handlePasswordSubmit(e));
            }
            
            // Валидация в реальном времени
            this.bindRealTimeValidation();
        }
        
        bindRealTimeValidation() {
            // Сброс ошибки email при вводе
            const emailInput = document.querySelector('.recovery-email-input');
            if (emailInput) {
                emailInput.addEventListener('input', () => {
                    this.hideError('email');
                });
            }
            
            // Сброс ошибки пароля при вводе
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
            const email = emailInput.value.trim();
            
            if (!this.validateEmail(email)) {
                this.showError('email', 'Введите корректный email адрес');
                return;
            }
            
            // Симуляция проверки существования email
            if (this.isEmailNotFound(email)) {
                this.showError('email', 'Email не найден. Проверьте правильность введенного адреса.');
                return;
            }
            
            // Email найден - отправляем код
            this.sendRecoveryCode(email);
        }
        
        handlePasswordSubmit(e) {
            e.preventDefault();
            
            const passwordInput = document.querySelector('.new-password-input');
            const confirmPasswordInput = document.querySelector('.confirm-password-input');
            
            if (!passwordInput || !confirmPasswordInput) {
                console.error('Password inputs not found');
                return;
            }
            
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
            
            // Пароли валидны - сохраняем
            this.saveNewPassword(password);
        }
        
        validateEmail(email) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return emailRegex.test(email);
        }
        
        validatePassword(password) {
            return password.length >= 6;
        }
        
        isEmailNotFound(email) {
            // Симуляция проверки - в реальном приложении это будет API запрос
            const notFoundEmails = ['wrong@example.com', 'notfound@example.com', 'test@test.com'];
            return notFoundEmails.includes(email.toLowerCase());
        }
        
        sendRecoveryCode(email) {
            // Симуляция отправки кода
            console.log('Отправка кода восстановления на:', email);
            
            // Показываем сообщение об отправке
            this.showStep(2);
        }
        
        saveNewPassword(password) {
            // Симуляция сохранения пароля
            console.log('Сохранение нового пароля');
            
            // Показываем сообщение об успехе
            this.showStep(4);
        }
        
        showStep(stepNumber) {
            this.currentStep = stepNumber;
            
            // Скрываем все шаги
            document.querySelectorAll('.recovery-step').forEach(step => {
                step.classList.remove('active');
            });
            
            // Показываем текущий шаг
            const currentStepElement = document.getElementById(this.steps[stepNumber]);
            if (currentStepElement) {
                currentStepElement.classList.add('active');
            }
            
            // Сбрасываем ошибки
            this.hideAllErrors();
            
            // Фокусировка на первом поле ввода
            this.focusFirstInput(stepNumber);
        }
        
        focusFirstInput(stepNumber) {
            let firstInput = null;
            
            switch(stepNumber) {
                case 1:
                    firstInput = document.querySelector('.recovery-email-input');
                    break;
                case 3:
                    firstInput = document.querySelector('.new-password-input');
                    break;
            }
            
            if (firstInput) {
                setTimeout(() => firstInput.focus(), 300);
            }
        }
        
        showError(type, message) {
            const errorElement = document.querySelector(`.${type}-error`);
            if (errorElement) {
                errorElement.textContent = message;
                errorElement.classList.add('active');
                
                // Подсветка соответствующего поля
                const inputElement = document.querySelector(`.${type === 'email' ? 'recovery-email' : 'confirm-password'}-input`);
                if (inputElement) {
                    inputElement.style.borderBottomColor = '#ff4444';
                }
            }
        }
        
        hideError(type) {
            const errorElement = document.querySelector(`.${type}-error`);
            if (errorElement) {
                errorElement.classList.remove('active');
                
                // Сброс цвета поля
                const inputElement = document.querySelector(`.${type === 'email' ? 'recovery-email' : 'confirm-password'}-input`);
                if (inputElement) {
                    inputElement.style.borderBottomColor = '';
                }
            }
        }
        
        hideAllErrors() {
            document.querySelectorAll('.form-error').forEach(error => {
                error.classList.remove('active');
            });
            
            document.querySelectorAll('.form-input').forEach(input => {
                input.style.borderBottomColor = '';
            });
        }
    }

    // ================= МОБИЛЬНОЕ МЕНЮ =================
    function toggleMobileMenu() {
        isMobileMenuOpen = !isMobileMenuOpen;
        
        if (mobileMenu) {
            mobileMenu.classList.toggle('mobile-menu--active', isMobileMenuOpen);
            mobileMenu.setAttribute('aria-hidden', !isMobileMenuOpen);
        }
        if (burgerBtn) {
            burgerBtn.setAttribute('aria-expanded', isMobileMenuOpen);
        }
        document.body.classList.toggle('no-scroll', isMobileMenuOpen);

        if (isMobileMenuOpen) {
            closeBtn?.focus();      
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

    // ================= АККОРДЕОН =================
    function initAccordion() {
        const accordionHeaders = document.querySelectorAll('.accordion__header');
        
        accordionHeaders.forEach(header => {
            // Initialize
            header.setAttribute('aria-expanded', 'false');
            const body = header.nextElementSibling;
            if (body) {
                body.style.maxHeight = '0';
            }
            
            header.addEventListener('click', function() {
                const isExpanded = this.getAttribute('aria-expanded') === 'true';
                
                // Close all other accordions
                accordionHeaders.forEach(otherHeader => {
                    if (otherHeader !== header) {
                        otherHeader.setAttribute('aria-expanded', 'false');
                        const otherBody = otherHeader.nextElementSibling;
                        if (otherBody) {
                            otherBody.style.maxHeight = '0';
                        }
                    }
                });
                
                // Toggle current accordion
                if (isExpanded) {
                    this.setAttribute('aria-expanded', 'false');
                    if (body) {
                        body.style.maxHeight = '0';
                    }
                } else {
                    this.setAttribute('aria-expanded', 'true');
                    if (body) {
                        body.style.maxHeight = body.scrollHeight + 'px';
                    }
                }
            });
        });
    }

    // ================= ФОРМЫ АУТЕНТИФИКАЦИИ =================
    function initAuthForms() {
        const registerForm = document.getElementById('register-form');
        const loginForm = document.getElementById('login-form');
        
        if (registerForm) {
            registerForm.addEventListener('submit', handleRegister);
        }
        
        if (loginForm) {
            loginForm.addEventListener('submit', handleLogin);
        }
    }

    function handleRegister(e) {
        e.preventDefault();
        
        const inputs = e.target.querySelectorAll('input');
        const username = inputs[0]?.value || '';
        const email = inputs[1]?.value || '';
        const password = inputs[2]?.value || '';
        const confirmPassword = inputs[3]?.value || '';
        
        // Валидация
        const errors = validateRegistration(username, email, password, confirmPassword);
        
        if (errors.length > 0) {
            showFormErrors(e.target, errors);
            return;
        }
        
        // Симуляция успешной регистрации
        const userData = {
            username,
            email,
            password,
            registeredAt: new Date().toISOString()
        };
        
        // Сохраняем в localStorage для тестирования
        const testUsers = JSON.parse(localStorage.getItem('testUsers') || '{}');
        testUsers[email] = userData;
        localStorage.setItem('testUsers', JSON.stringify(testUsers));
        
        console.log('✅ Тестовая регистрация успешна:', userData);
        alert('✅ Регистрация успешна! Данные сохранены в localStorage. Проверьте консоль браузера.');
        
        // Переключаем на форму входа
        const loginTab = document.querySelector('.form-tab[data-tab="login"]');
        if (loginTab) loginTab.click();
        
        e.target.reset();
    }

    function handleLogin(e) {
        e.preventDefault();
        
        const inputs = e.target.querySelectorAll('input');
        const email = inputs[0]?.value || '';
        const password = inputs[1]?.value || '';
        
        // Проверяем существующих пользователей
        const testUsers = JSON.parse(localStorage.getItem('testUsers') || '{}');
        const user = testUsers[email];
        
        if (user && user.password === password) {
            console.log('✅ Тестовый вход успешен:', user);
            alert('✅ Вход выполнен! Проверьте консоль браузера.');
            
            // Сохраняем сессию
            localStorage.setItem('currentUser', JSON.stringify(user));
        } else {
            console.log('❌ Ошибка входа: неверный email или пароль');
            alert('❌ Ошибка: неверный email или пароль. Сначала зарегистрируйтесь.');
        }
        
        e.target.reset();
    }

    function validateRegistration(username, email, password, confirmPassword) {
        const errors = [];
        
        if (!username || username.length < 3) {
            errors.push('Имя пользователя должно содержать минимум 3 символа');
        }
        
        if (!email || !validateEmail(email)) {
            errors.push('Введите корректный email адрес');
        }
        
        if (!password || password.length < 6) {
            errors.push('Пароль должен содержать минимум 6 символов');
        }
        
        if (password !== confirmPassword) {
            errors.push('Пароли не совпадают');
        }
        
        // Проверяем, не занят ли email
        const testUsers = JSON.parse(localStorage.getItem('testUsers') || '{}');
        if (testUsers[email]) {
            errors.push('Пользователь с таким email уже зарегистрирован');
        }
        
        return errors;
    }

    function validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    function showFormErrors(form, errors) {
        console.log('❌ Ошибки формы:', errors);
        alert('❌ Ошибки:\n' + errors.join('\n'));
    }

    // ================= ПЕРЕКЛЮЧЕНИЕ ТАБОВ ФОРМ =================
    function initFormTabs() {
        const tabs = document.querySelectorAll('.form-tab');
        const forms = document.querySelectorAll('.form-container');
        
        console.log('Найдено табов:', tabs.length);
        console.log('Найдено форм:', forms.length);
        
        if (tabs.length === 0 || forms.length === 0) {
            console.error('Табы или формы не найдены!');
            return;
        }
        
        tabs.forEach(tab => {
            // Убедимся, что у табов нет type="submit"
            if (tab.tagName === 'BUTTON') {
                tab.type = 'button';
            }
            
            tab.addEventListener('click', function(e) {
                e.preventDefault();
                console.log('Клик по табу:', this.getAttribute('data-tab'));
                
                const targetTab = this.getAttribute('data-tab');
                
                // Убираем активный класс со всех табов
                tabs.forEach(t => {
                    t.classList.remove('active');
                    t.setAttribute('aria-selected', 'false');
                });
                
                // Добавляем активный класс текущему табу
                this.classList.add('active');
                this.setAttribute('aria-selected', 'true');
                
                // Скрываем все формы
                forms.forEach(form => {
                    form.classList.remove('active');
                });
                
                // Показываем нужную форму
                const targetForm = document.getElementById(`${targetTab}-form`);
                if (targetForm) {
                    targetForm.classList.add('active');
                    console.log('Показана форма:', targetForm.id);
                } else {
                    console.error('Форма не найдена:', `${targetTab}-form`);
                }
            });
        });
        
        // Активируем первый активный таб
        const activeTab = document.querySelector('.form-tab.active');
        if (activeTab) {
            const targetTab = activeTab.getAttribute('data-tab');
            const targetForm = document.getElementById(`${targetTab}-form`);
            if (targetForm) {
                targetForm.classList.add('active');
            }
        }
    }

    // ================= НАВИГАЦИЯ МЕЖДУ ФОРМАМИ =================
    function initAuthNavigation() {
        const showRecoveryBtn = document.getElementById('show-recovery');
        const backToLoginBtn = document.getElementById('back-to-login');
        const backToEmailLink = document.querySelector('.back-to-email-link');
        const successLoginBtn = document.getElementById('success-login-btn');
        const authSection = document.getElementById('auth-section');
        const recoverySection = document.getElementById('recovery-section');

        // Показ формы восстановления пароля
        if (showRecoveryBtn && authSection && recoverySection) {
            showRecoveryBtn.addEventListener('click', function(e) {
                e.preventDefault();
                authSection.style.display = 'none';
                recoverySection.style.display = 'block';
                // Сбрасываем форму восстановления к первому шагу
                if (window.passwordRecovery) {
                    window.passwordRecovery.showStep(1);
                }
            });
        }

        // Возврат к форме входа из восстановления пароля
        if (backToLoginBtn && authSection && recoverySection) {
            backToLoginBtn.addEventListener('click', function(e) {
                e.preventDefault();
                recoverySection.style.display = 'none';
                authSection.style.display = 'block';
                // Сбрасываем форму восстановления к первому шагу
                if (window.passwordRecovery) {
                    window.passwordRecovery.showStep(1);
                }
            });
        }

        // Возврат к вводу email
        if (backToEmailLink) {
            backToEmailLink.addEventListener('click', function(e) {
                e.preventDefault();
                if (window.passwordRecovery) {
                    window.passwordRecovery.showStep(1);
                }
            });
        }

        // Успешный вход после восстановления пароля
        if (successLoginBtn && authSection && recoverySection) {
            successLoginBtn.addEventListener('click', function(e) {
                e.preventDefault();
                recoverySection.style.display = 'none';
                authSection.style.display = 'block';
                // Активируем таб входа
                const loginTab = document.querySelector('.form-tab[data-tab="login"]');
                const loginForm = document.getElementById('login-form');
                if (loginTab && loginForm) {
                    document.querySelectorAll('.form-tab').forEach(tab => tab.classList.remove('active'));
                    document.querySelectorAll('.form-container').forEach(form => form.classList.remove('active'));
                    loginTab.classList.add('active');
                    loginForm.classList.add('active');
                }
                // Сбрасываем форму восстановления к первому шагу
                if (window.passwordRecovery) {
                    window.passwordRecovery.showStep(1);
                }
            });
        }
    }

    // ================= УСТРАНЕНИЕ ПОДПРЫГИВАНИЯ ССЫЛОК =================
    function fixLinkJumping() {
        const interactiveElements = document.querySelectorAll('.forgot-password, .recovery-link, .form-btn, .form-tab, .success-login-btn');
        
        interactiveElements.forEach(element => {
            // Убираем все трансформации
            element.style.transform = 'none';
            element.style.transition = 'color 0.3s ease, background-color 0.3s ease, opacity 0.3s ease';
            
            // Добавляем обработчики для предотвращения трансформаций
            element.addEventListener('mouseenter', function() {
                this.style.transform = 'none';
            });
            
            element.addEventListener('mouseleave', function() {
                this.style.transform = 'none';
            });
        });
    }

    // ================= ГЛОБАЛЬНЫЕ ОБРАБОТЧИКИ СОБЫТИЙ =================
    function initGlobalEventHandlers() {
        // Бургер меню
        burgerBtn?.addEventListener('click', toggleMobileMenu);
        closeBtn?.addEventListener('click', toggleMobileMenu);

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

        // Закрытие по Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                if (isMobileMenuOpen) {
                    toggleMobileMenu();
                } else {
                    closeAllDesktopDropdowns();
                }
            }
        });

        // Адаптация к изменению размера окна
        window.addEventListener('resize', () => {
            if (window.innerWidth > 768 && isMobileMenuOpen) {
                toggleMobileMenu();
            }
        });

        // Закрытие мобильного меню при клике на ссылку (кроме dropdown toggle)
        mobileMenu?.addEventListener('click', (e) => {
            if (e.target.tagName === 'A' && !e.target.classList.contains('dropdown__toggle')) {
                toggleMobileMenu();
            }
        });
    }

    // ================= ИНИЦИАЛИЗАЦИЯ ARIA АТРИБУТОВ =================
    function initAriaAttributes() {
        mobileMenu?.setAttribute('aria-hidden', 'true');
        burgerBtn?.setAttribute('aria-expanded', 'false');
        
        // Инициализация всех dropdown
        const allDropdownToggles = document.querySelectorAll('.dropdown__toggle');
        allDropdownToggles.forEach(toggle => {
            toggle.setAttribute('aria-expanded', 'false');
        });
    }

    // ================= ОТЛАДОЧНАЯ ИНФОРМАЦИЯ =================
    function debugInit() {
        console.log('=== ИНИЦИАЛИЗАЦИЯ КОМПОНЕНТОВ ===');
        console.log('Бургер кнопка:', !!burgerBtn);
        console.log('Мобильное меню:', !!mobileMenu);
        console.log('Табы форм:', document.querySelectorAll('.form-tab').length);
        console.log('Аккордеоны:', document.querySelectorAll('.accordion__header').length);
        console.log('Dropdowns:', document.querySelectorAll('.dropdown__toggle').length);
    }

    // ================= ОСНОВНАЯ ИНИЦИАЛИЗАЦИЯ =================
    function init() {
        debugInit();
        
        // 1. Сначала инициализируем ARIA атрибуты
        initAriaAttributes();
        
        // 2. Глобальные обработчики событий
        initGlobalEventHandlers();
        
        // 3. Компоненты интерфейса
        initDropdowns();
        initAccordion();
        initFormTabs();
        
        // 4. Системы аутентификации
        initAuthForms();
        initAuthNavigation();
        window.passwordRecovery = new PasswordRecovery();
        
        // 5. Визуальные исправления
        fixLinkJumping();
        
        console.log('✅ Все компоненты инициализированы');
    }

    // ЗАПУСК
    init();
});

// Быстрые команды для тестирования в консоли
window.testAuth = {
    clearData: function() {
        localStorage.removeItem('testUsers');
        localStorage.removeItem('currentUser');
        console.log('✅ Тестовые данные очищены');
    },
    
    createTestUser: function() {
        const testUser = {
            username: 'testuser',
            email: 'test@example.com',
            password: 'password123',
            registeredAt: new Date().toISOString()
        };
        
        const testUsers = JSON.parse(localStorage.getItem('testUsers') || '{}');
        testUsers[testUser.email] = testUser;
        localStorage.setItem('testUsers', JSON.stringify(testUsers));
        
        console.log('✅ Тестовый пользователь создан:', testUser);
        console.log('📧 Email: test@example.com');
        console.log('🔑 Password: password123');
    },
    
    showUsers: function() {
        const users = JSON.parse(localStorage.getItem('testUsers') || '{}');
        console.log('👥 Тестовые пользователи:', users);
        return users;
    }
};

// ================= ТЕСТИРОВАНИЕ ФОРМ =================
class FormTester {
    constructor() {
        this.testResults = [];
        this.currentTest = null;
    }

    // Основные тесты
    runAllTests() {
        console.log('🧪 ЗАПУСК ВСЕХ ТЕСТОВ ФОРМ');
        this.testResults = [];
        
        this.testFormTabs();
        this.testRegistrationForm();
        this.testLoginForm();
        this.testPasswordRecovery();
        this.testFormValidation();
        this.testLocalStorage();
        
        this.printTestResults();
    }

    // Тест переключения табов
    testFormTabs() {
        this.currentTest = 'Переключение табов форм';
        try {
            const registerTab = document.querySelector('.form-tab[data-tab="register"]');
            const loginTab = document.querySelector('.form-tab[data-tab="login"]');
            const registerForm = document.getElementById('register-form');
            const loginForm = document.getElementById('login-form');

            if (!registerTab || !loginTab || !registerForm || !loginForm) {
                throw new Error('Не найдены элементы табов или форм');
            }

            // Тест переключения на вход
            loginTab.click();
            if (!loginForm.classList.contains('active') || registerForm.classList.contains('active')) {
                throw new Error('Таб входа не активировался');
            }

            // Тест переключения на регистрацию
            registerTab.click();
            if (!registerForm.classList.contains('active') || loginForm.classList.contains('active')) {
                throw new Error('Таб регистрации не активировался');
            }

            this.recordTestResult(true, 'Табы форм переключаются корректно');
        } catch (error) {
            this.recordTestResult(false, error.message);
        }
    }

    // Тест формы регистрации
    testRegistrationForm() {
        this.currentTest = 'Форма регистрации';
        try {
            const form = document.getElementById('register-form');
            if (!form) throw new Error('Форма регистрации не найдена');

            const inputs = form.querySelectorAll('input');
            if (inputs.length !== 4) throw new Error('Неверное количество полей в форме регистрации');

            // Тест валидации
            const testCases = [
                {
                    data: { username: 'ab', email: 'invalid', password: '123', confirmPassword: '456' },
                    shouldPass: false,
                    description: 'Валидация должна отклонять неверные данные'
                },
                {
                    data: { username: 'testuser', email: 'test@example.com', password: 'password123', confirmPassword: 'password123' },
                    shouldPass: true,
                    description: 'Валидация должна принимать корректные данные'
                }
            ];

            testCases.forEach(testCase => {
                const isValid = this.validateRegistrationData(
                    testCase.data.username,
                    testCase.data.email,
                    testCase.data.password,
                    testCase.data.confirmPassword
                );

                if (isValid === testCase.shouldPass) {
                    this.recordTestResult(true, testCase.description);
                } else {
                    throw new Error(`Ошибка валидации: ${testCase.description}`);
                }
            });

        } catch (error) {
            this.recordTestResult(false, error.message);
        }
    }

    // Тест формы входа
    testLoginForm() {
        this.currentTest = 'Форма входа';
        try {
            const form = document.getElementById('login-form');
            if (!form) throw new Error('Форма входа не найдена');

            const inputs = form.querySelectorAll('input');
            if (inputs.length !== 2) throw new Error('Неверное количество полей в форме входа');

            // Создаем тестового пользователя
            this.createTestUser();

            // Тестируем вход с правильными данными
            const testUser = JSON.parse(localStorage.getItem('testUsers'))['test@example.com'];
            if (!testUser) throw new Error('Тестовый пользователь не создан');

            this.recordTestResult(true, 'Форма входа готова к тестированию');

        } catch (error) {
            this.recordTestResult(false, error.message);
        }
    }

    // Тест восстановления пароля
    testPasswordRecovery() {
        this.currentTest = 'Восстановление пароля';
        try {
            const recoverySection = document.getElementById('recovery-section');
            const authSection = document.getElementById('auth-section');
            const showRecoveryBtn = document.getElementById('show-recovery');

            if (!recoverySection || !authSection || !showRecoveryBtn) {
                throw new Error('Элементы восстановления пароля не найдены');
            }

            // Тест перехода к восстановлению пароля
            showRecoveryBtn.click();
            if (recoverySection.style.display !== 'block' || authSection.style.display !== 'none') {
                throw new Error('Не удалось переключиться на форму восстановления');
            }

            this.recordTestResult(true, 'Навигация восстановления пароля работает');

            // Тест шагов восстановления
            if (window.passwordRecovery) {
                window.passwordRecovery.showStep(1);
                const step1 = document.getElementById('step-email');
                if (!step1.classList.contains('active')) {
                    throw new Error('Шаг 1 восстановления не активирован');
                }

                this.recordTestResult(true, 'Система шагов восстановления работает');
            }

        } catch (error) {
            this.recordTestResult(false, error.message);
        }
    }

    // Тест валидации форм
    testFormValidation() {
        this.currentTest = 'Валидация форм';
        try {
            const testCases = [
                {
                    email: 'invalid-email',
                    expected: false,
                    description: 'Невалидный email должен быть отклонен'
                },
                {
                    email: 'test@example.com',
                    expected: true,
                    description: 'Валидный email должен быть принят'
                },
                {
                    password: '123',
                    expected: false,
                    description: 'Короткий пароль должен быть отклонен'
                },
                {
                    password: 'password123',
                    expected: true,
                    description: 'Длинный пароль должен быть принят'
                }
            ];

            testCases.forEach(testCase => {
                if (testCase.email !== undefined) {
                    const isValid = this.validateEmail(testCase.email);
                    if (isValid !== testCase.expected) {
                        throw new Error(testCase.description);
                    }
                }
                if (testCase.password !== undefined) {
                    const isValid = this.validatePassword(testCase.password);
                    if (isValid !== testCase.expected) {
                        throw new Error(testCase.description);
                    }
                }
                this.recordTestResult(true, testCase.description);
            });

        } catch (error) {
            this.recordTestResult(false, error.message);
        }
    }

    // Тест localStorage
    testLocalStorage() {
        this.currentTest = 'LocalStorage';
        try {
            // Очищаем предыдущие тестовые данные
            localStorage.removeItem('testUsers');
            localStorage.removeItem('currentUser');

            // Создаем тестового пользователя
            this.createTestUser();

            // Проверяем сохранение
            const testUsers = JSON.parse(localStorage.getItem('testUsers'));
            if (!testUsers || !testUsers['test@example.com']) {
                throw new Error('Тестовый пользователь не сохранен в localStorage');
            }

            // Тестируем вход
            localStorage.setItem('currentUser', JSON.stringify(testUsers['test@example.com']));
            const currentUser = JSON.parse(localStorage.getItem('currentUser'));
            if (!currentUser) {
                throw new Error('Текущий пользователь не сохранен в localStorage');
            }

            this.recordTestResult(true, 'LocalStorage операции работают корректно');

            // Очищаем тестовые данные
            localStorage.removeItem('testUsers');
            localStorage.removeItem('currentUser');

        } catch (error) {
            this.recordTestResult(false, error.message);
        }
    }

    // Вспомогательные методы
    validateRegistrationData(username, email, password, confirmPassword) {
        const errors = [];
        
        if (!username || username.length < 3) errors.push('Имя слишком короткое');
        if (!this.validateEmail(email)) errors.push('Неверный email');
        if (!this.validatePassword(password)) errors.push('Пароль слишком короткий');
        if (password !== confirmPassword) errors.push('Пароли не совпадают');
        
        return errors.length === 0;
    }

    validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    validatePassword(password) {
        return password.length >= 6;
    }

    createTestUser() {
        const testUser = {
            username: 'testuser',
            email: 'test@example.com',
            password: 'password123',
            registeredAt: new Date().toISOString()
        };
        
        const testUsers = JSON.parse(localStorage.getItem('testUsers') || '{}');
        testUsers[testUser.email] = testUser;
        localStorage.setItem('testUsers', JSON.stringify(testUsers));
        
        return testUser;
    }

    recordTestResult(passed, message) {
        this.testResults.push({
            test: this.currentTest,
            passed: passed,
            message: message,
            timestamp: new Date().toISOString()
        });

        const status = passed ? '✅' : '❌';
        console.log(`${status} ${this.currentTest}: ${message}`);
    }

    printTestResults() {
        console.log('\n📊 ИТОГИ ТЕСТИРОВАНИЯ:');
        console.log('=' .repeat(50));
        
        const passedTests = this.testResults.filter(result => result.passed).length;
        const totalTests = this.testResults.length;
        
        console.log(`✅ Пройдено: ${passedTests}/${totalTests}`);
        console.log(`❌ Провалено: ${totalTests - passedTests}/${totalTests}`);
        
        this.testResults.forEach(result => {
            const status = result.passed ? '✅' : '❌';
            console.log(`${status} ${result.test}: ${result.message}`);
        });
        
        console.log('=' .repeat(50));
        
        if (passedTests === totalTests) {
            console.log('🎉 Все тесты пройдены успешно!');
        } else {
            console.log('💥 Некоторые тесты провалились. Проверьте консоль для деталей.');
        }
    }

    // Автоматическое заполнение форм для ручного тестирования
    autoFillRegisterForm() {
        const form = document.getElementById('register-form');
        if (!form) {
            console.error('❌ Форма регистрации не найдена');
            return;
        }

        const inputs = form.querySelectorAll('input');
        if (inputs.length >= 4) {
            inputs[0].value = 'testuser';
            inputs[1].value = 'test@example.com';
            inputs[2].value = 'password123';
            inputs[3].value = 'password123';
            console.log('✅ Форма регистрации автоматически заполнена');
        }
    }

    autoFillLoginForm() {
        const form = document.getElementById('login-form');
        if (!form) {
            console.error('❌ Форма входа не найдена');
            return;
        }

        const inputs = form.querySelectorAll('input');
        if (inputs.length >= 2) {
            inputs[0].value = 'test@example.com';
            inputs[1].value = 'password123';
            console.log('✅ Форма входа автоматически заполнена');
        }
    }

    // Быстрое создание тестового пользователя
    setupTestEnvironment() {
        this.createTestUser();
        console.log('✅ Тестовое окружение настроено');
        console.log('📧 Email: test@example.com');
        console.log('🔑 Password: password123');
    }
}

// ================= ГЛОБАЛЬНЫЕ ТЕСТОВЫЕ КОМАНДЫ =================
window.FormTester = FormTester;
window.formTester = new FormTester();

// Команды для тестирования из консоли
window.testForms = {
    // Запуск всех тестов
    runAll: function() {
        window.formTester.runAllTests();
    },
    
    // Создание тестового пользователя
    createUser: function() {
        window.formTester.setupTestEnvironment();
    },
    
    // Автозаполнение форм
    fillRegister: function() {
        window.formTester.autoFillRegisterForm();
    },
    
    fillLogin: function() {
        window.formTester.autoFillLoginForm();
    },
    
    // Очистка данных
    clearData: function() {
        localStorage.removeItem('testUsers');
        localStorage.removeItem('currentUser');
        console.log('✅ Все тестовые данные очищены');
    },
    
    // Проверка данных
    checkData: function() {
        const testUsers = JSON.parse(localStorage.getItem('testUsers') || '{}');
        const currentUser = JSON.parse(localStorage.getItem('currentUser') || 'null');
        
        console.log('📊 ТЕКУЩИЕ ДАННЫЕ:');
        console.log('👥 Тестовые пользователи:', testUsers);
        console.log('👤 Текущий пользователь:', currentUser);
    },
    
    // Тест конкретных функций
    testValidation: function() {
        window.formTester.testFormValidation();
    },
    
    testNavigation: function() {
        window.formTester.testFormTabs();
        window.formTester.testPasswordRecovery();
    }
};

// ================= ИНИЦИАЛИЗАЦИЯ ТЕСТИРОВАНИЯ ПРИ ЗАГРУЗКЕ =================
document.addEventListener('DOMContentLoaded', function() {
    // Добавляем тестовые команды в глобальную область видимости
    setTimeout(() => {
        console.log(`
🎯 КОМАНДЫ ДЛЯ ТЕСТИРОВАНИЯ ФОРМ:

🔧 Основные команды:
• testForms.runAll()     - Запустить все тесты
• testForms.createUser() - Создать тестового пользователя
• testForms.clearData()  - Очистить тестовые данные
• testForms.checkData()  - Показать текущие данные

📝 Автозаполнение форм:
• testForms.fillRegister() - Заполнить форму регистрации
• testForms.fillLogin()    - Заполнить форму входа

🧪 Отдельные тесты:
• testForms.testValidation() - Тест валидации
• testForms.testNavigation() - Тест навигации

📚 Продвинутые команды:
• formTester.runAllTests() - Полный тест (объект FormTester)
• formTester.autoFillRegisterForm() - Заполнить регистрацию
• formTester.autoFillLoginForm() - Заполнить вход

💡 Пример использования:
1. testForms.createUser()
2. testForms.fillRegister()
3. Нажать кнопку "Регистрация"
4. testForms.fillLogin() 
5. Нажать кнопку "Войти"
        `);
    }, 1000);
});