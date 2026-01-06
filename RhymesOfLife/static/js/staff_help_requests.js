// Staff Help Requests JavaScript - Light Theme (Fixed Version)
document.addEventListener('DOMContentLoaded', function() {
    console.log('Staff Help Requests script loaded');
    
    const hrRoot = document.getElementById('hr-root');
    if (!hrRoot) {
        console.error('HR root element not found');
        return;
    }
    
    const urls = {
        data: hrRoot.dataset.urlData,
        api: hrRoot.dataset.urlApi
    };
    
    console.log('URLs:', urls);
    
    // Current state
    let currentPage = 1;
    let currentFilters = {
        status: 'all',
        q: ''
    };
    
    // Initialize
    init();
    
    function init() {
        console.log('Initializing...');
        
        // Initialize from URL params
        initFilters();
        
        // Load initial data
        loadData();
        
        // Filter form submission
        const filterForm = document.getElementById('hr-filter');
        if (filterForm) {
            filterForm.addEventListener('submit', function(e) {
                e.preventDefault();
                console.log('Filter form submitted');
                
                currentFilters = {
                    status: document.getElementById('hr-status').value || 'all',
                    q: document.getElementById('hr-q').value
                };
                currentPage = 1;
                loadData();
            });
        }
        
        // Clear search button
        const clearSearchBtn = document.getElementById('hr-clear-search');
        if (clearSearchBtn) {
            clearSearchBtn.addEventListener('click', function() {
                console.log('Clearing search');
                document.getElementById('hr-q').value = '';
                currentFilters.q = '';
                currentPage = 1;
                loadData();
            });
        }
        
        // Reset filters button
        const resetFiltersBtn = document.getElementById('hr-reset-filters');
        if (resetFiltersBtn) {
            resetFiltersBtn.addEventListener('click', function() {
                console.log('Resetting filters');
                document.getElementById('hr-status').value = 'all';
                document.getElementById('hr-q').value = '';
                currentFilters = { status: 'all', q: '' };
                currentPage = 1;
                loadData();
            });
        }
        
        // Event delegation for dynamic elements
        document.addEventListener('click', function(e) {
            // Page button clicks
            if (e.target.closest('.hr-page-btn')) {
                e.preventDefault();
                const btn = e.target.closest('.hr-page-btn');
                currentPage = parseInt(btn.dataset.page);
                console.log('Page button clicked, going to page:', currentPage);
                loadData();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
            
            // Status toggle buttons
            if (e.target.closest('.hr-toggle-btn')) {
                e.preventDefault();
                const btn = e.target.closest('.hr-toggle-btn');
                const id = btn.dataset.id;
                const action = btn.dataset.action;
                console.log('Toggle button clicked:', { id, action });
                updateStatus(id, action);
            }
            
            // Row click to open modal (except action buttons)
            if (e.target.closest('.hr-row') && !e.target.closest('.hr-actions') && !e.target.closest('a')) {
                const row = e.target.closest('.hr-row');
                console.log('Row clicked, id:', row.dataset.id);
                showModal(row);
            }
            
            // Modal action buttons
            const modalBtn = e.target.closest('#hm-undo, #hm-work, #hm-process');
            if (modalBtn) {
                e.preventDefault();
                const modal = document.getElementById('hr-modal');
                const id = modal.dataset.currentId;
                const action = modalBtn.id.replace('hm-', '');
                console.log('Modal action button clicked:', { id, action });
                updateStatus(id, action);
                
                // Close modal after action
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) {
                    modalInstance.hide();
                }
            }
        });
    }
    
    // Initialize filter values from URL
    function initFilters() {
        const params = new URLSearchParams(window.location.search);
        const status = params.get('status') || 'all';
        const q = params.get('q') || '';
        
        const statusElement = document.getElementById('hr-status');
        const qElement = document.getElementById('hr-q');
        
        if (statusElement) statusElement.value = status;
        if (qElement) qElement.value = q;
        
        currentFilters = { status, q };
        console.log('Filters initialized:', currentFilters);
    }
    
    // Load data from server - FIXED VERSION
    function loadData() {
        console.log('Loading data...', { page: currentPage, filters: currentFilters });
        
        showLoading(true);
        
        const params = new URLSearchParams({
            page: currentPage,
            ...currentFilters
        });
        
        fetch(`${urls.data}?${params}`)
            .then(response => {
                console.log('Response received:', response.status, response.statusText);
                
                // Check if response is JSON or HTML
                const contentType = response.headers.get('content-type') || '';
                
                if (contentType.includes('application/json')) {
                    console.log('Response is JSON');
                    return response.json().then(data => {
                        console.log('JSON data received:', data);
                        return { type: 'json', data };
                    });
                } else {
                    console.log('Response is HTML');
                    return response.text().then(html => {
                        console.log('HTML length:', html.length, 'chars');
                        return { type: 'html', data: html };
                    });
                }
            })
            .then(result => {
                console.log('Processing response type:', result.type);
                
                if (result.type === 'json') {
                    // Handle JSON response
                    const jsonData = result.data;
                    
                    // Check for error
                    if (jsonData.error) {
                        showError(jsonData.error);
                        return;
                    }
                    
                    // Update table rows
                    if (jsonData.rows !== undefined) {
                        document.getElementById('hr-list').innerHTML = jsonData.rows;
                    } else if (jsonData.html) {
                        document.getElementById('hr-list').innerHTML = jsonData.html;
                    }
                    
                    // Update pagination
                    if (jsonData.pager && document.getElementById('hr-pager')) {
                        document.getElementById('hr-pager').innerHTML = jsonData.pager;
                    }
                    
                    // Update counter if provided
                    if (jsonData.total !== undefined) {
                        updateCounter(jsonData.total);
                    } else {
                        updateCounter();
                    }
                    
                } else {
                    // Handle HTML response
                    const html = result.data;
                    
                    // Try to parse as JSON first (in case content-type was wrong)
                    try {
                        const jsonData = JSON.parse(html);
                        console.log('HTML was actually JSON:', jsonData);
                        
                        if (jsonData.rows !== undefined) {
                            document.getElementById('hr-list').innerHTML = jsonData.rows;
                        }
                        if (jsonData.pager && document.getElementById('hr-pager')) {
                            document.getElementById('hr-pager').innerHTML = jsonData.pager;
                        }
                        if (jsonData.total !== undefined) {
                            updateCounter(jsonData.total);
                        }
                    } catch (e) {
                        // Not JSON, use as HTML
                        console.log('Response is plain HTML');
                        document.getElementById('hr-list').innerHTML = html;
                        updateCounter();
                    }
                }
                
                showLoading(false);
                
                // Show success message if it was a filter change
                if (currentFilters.status || currentFilters.q) {
                    showToast('Filters applied', 'success');
                }
                
            })
            .catch(error => {
                console.error('Error loading data:', error);
                showLoading(false);
                showError('Failed to load data. Please try again.');
                showToast('Error loading data', 'danger');
            });
    }
    
    // Update status via API
    function updateStatus(id, action) {
        console.log('Updating status:', { id, action });
        
        const row = document.querySelector(`.hr-row[data-id="${id}"]`);
        if (!row) {
            console.error('Row not found for id:', id);
            return;
        }
        
        // Add loading state
        row.classList.add('loading');
        
        const fd = new FormData();
        fd.append('id', id);
        fd.append('action', action);
        fetch(urls.api, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: fd
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Update response:', data);
            
            if (data.ok) {
                // Reload data to reflect changes
                loadData();
                
                // Show success message
                showToast('Status updated successfully', 'success');
                
                // Update modal if open
                updateModalStatus(id, action);
            } else {
                showToast(data.error || 'Failed to update status', 'danger');
            }
            row.classList.remove('loading');
        })
        .catch(error => {
            console.error('Error updating status:', error);
            showToast('Error updating status. Please try again.', 'danger');
            row.classList.remove('loading');
        });
    }
    
    // Show modal with details
    function showModal(row) {
        console.log('Showing modal for row:', row.dataset.id);
        
        const modal = document.getElementById('hr-modal');
        if (!modal) {
            console.error('Modal element not found');
            return;
        }
        
        // Extract data from row attributes
        const modalData = {
            id: row.dataset.id,
            created: row.dataset.created,
            username: row.dataset.username,
            telegram: row.dataset.telegram,
            email: row.dataset.email,
            phone: row.dataset.phone,
            birth: row.dataset.birth,
            city: row.dataset.city,
            syndrome: row.dataset.syndrome,
            gen: row.dataset.gen,
            medications: row.dataset.medications,
            status: row.dataset.status,
            processor: row.dataset.processor,
            profile: row.dataset.profile,
            profileName: row.dataset.profileName,
            message: row.dataset.message
        };
        
        console.log('Modal data:', modalData);
        
        // Populate modal fields
        populateModal(modalData);
        
        // Store current ID for actions
        modal.dataset.currentId = row.dataset.id;
        
        // Show modal
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
    }
    
    // Populate modal with data
    function populateModal(data) {
        console.log('Populating modal with data');
        
        // Helper function to safely set content
        const setElementContent = (id, content, isHtml = false) => {
            const element = document.getElementById(id);
            if (element) {
                if (isHtml) {
                    element.innerHTML = content || '—';
                } else {
                    element.textContent = content || '—';
                }
            } else {
                console.warn('Element not found:', id);
            }
        };
        
        // Set basic info
        setElementContent('hm-id', data.id);
        setElementContent('hm-created', formatDateTime(data.created));
        setElementContent('hm-processor', data.processor || 'Not assigned');
        
        // Set contact info
        setElementContent('hm-username', data.username);
        
        if (data.telegram && data.telegram !== '—' && data.telegram !== '') {
            const handle = data.telegram.startsWith('@') ? data.telegram : `@${data.telegram}`;
            setElementContent('hm-telegram', 
                `<a href="https://t.me/${handle.replace('@', '')}" target="_blank" class="text-decoration-none">${handle}</a>`, 
                true
            );
        } else {
            setElementContent('hm-telegram', '—');
        }
        
        if (data.email && data.email !== '—' && data.email !== '') {
            setElementContent('hm-email', 
                `<a href="mailto:${data.email}" class="text-decoration-none">${data.email}</a>`, 
                true
            );
        } else {
            setElementContent('hm-email', '—');
        }
        
        setElementContent('hm-phone', data.phone);
        
        // Set user details
        if (data.profile && data.profileName && data.profile !== '—' && data.profile !== '') {
            setElementContent('hm-profile', 
                `<a href="${data.profile}" target="_blank" class="text-decoration-none">${data.profileName}</a>`, 
                true
            );
        } else {
            setElementContent('hm-profile', '—');
        }
        
        setElementContent('hm-birth', data.birth ? formatDate(data.birth) : '—');
        setElementContent('hm-city', data.city);
        setElementContent('hm-syndrome', data.syndrome);
        setElementContent('hm-gen', data.gen);
        
        // Set medications and message (preserve whitespace)
        const medicationsElement = document.getElementById('hm-medications');
        if (medicationsElement) {
            medicationsElement.textContent = data.medications || 'Not specified';
            medicationsElement.style.whiteSpace = 'pre-wrap';
            medicationsElement.style.wordBreak = 'break-word';
            medicationsElement.style.fontSize = '0.9rem';
        }
        
        const messageElement = document.getElementById('hm-message');
        if (messageElement) {
            messageElement.textContent = data.message || 'No message provided';
            messageElement.style.whiteSpace = 'pre-wrap';
            messageElement.style.wordBreak = 'break-word';
        }
        
        // Set status badge
        const statusElement = document.getElementById('hm-status');
        if (statusElement) {
            let badgeClass = 'badge bg-secondary';
            let text = 'Open';
            let icon = 'bi-clock';
            
            if (data.status === 'done') {
                badgeClass = 'badge bg-success';
                text = 'Completed';
                icon = 'bi-check-circle-fill';
            } else if (data.status === 'in_work') {
                badgeClass = 'badge bg-primary';
                text = 'In Progress';
                icon = 'bi-hourglass-split';
            }
            
            statusElement.innerHTML = `<span class="${badgeClass} d-inline-flex align-items-center gap-1"><i class="bi ${icon}"></i>${text}</span>`;
        }
        
        // Show/hide action buttons based on status
        const undoBtn = document.getElementById('hm-undo');
        const workBtn = document.getElementById('hm-work');
        const processBtn = document.getElementById('hm-process');
        
        // Hide all first
        if (undoBtn) undoBtn.classList.add('d-none');
        if (workBtn) workBtn.classList.add('d-none');
        if (processBtn) processBtn.classList.add('d-none');
        
        // Show relevant buttons
        const status = data.status;
        if (status === 'done') {
            if (undoBtn) undoBtn.classList.remove('d-none');
        } else if (status === 'in_work') {
            if (processBtn) processBtn.classList.remove('d-none');
            if (undoBtn) undoBtn.classList.remove('d-none');
        } else {
            if (workBtn) workBtn.classList.remove('d-none');
            if (processBtn) processBtn.classList.remove('d-none');
        }
    }
    
    // Update modal status after change
    function updateModalStatus(id, action) {
        const modal = document.getElementById('hr-modal');
        if (modal && modal.dataset.currentId === id) {
            const statusElement = document.getElementById('hm-status');
            if (!statusElement) return;
            
            let newStatus = '';
            
            if (action === 'process') newStatus = 'done';
            else if (action === 'work') newStatus = 'in_work';
            else if (action === 'undo') newStatus = 'open';
            
            let badgeClass = 'badge bg-secondary';
            let text = 'Open';
            let icon = 'bi-clock';
            
            if (newStatus === 'done') {
                badgeClass = 'badge bg-success';
                text = 'Completed';
                icon = 'bi-check-circle-fill';
            } else if (newStatus === 'in_work') {
                badgeClass = 'badge bg-primary';
                text = 'In Progress';
                icon = 'bi-hourglass-split';
            }
            
            statusElement.innerHTML = `<span class="${badgeClass} d-inline-flex align-items-center gap-1"><i class="bi ${icon}"></i>${text}</span>`;
        }
    }
    
    // Update counter
    function updateCounter(totalCount = null) {
        let count;
        
        if (totalCount !== null) {
            // Use provided total count
            count = totalCount;
        } else {
            // Count rows in table
            const rows = document.querySelectorAll('.hr-row:not(#hr-empty-row)');
            count = rows.length;
        }
        
        const text = count === 0 ? 'No requests' : `${count} request${count !== 1 ? 's' : ''}`;
        
        const countElement = document.getElementById('hr-count-text');
        if (countElement) {
            countElement.textContent = text;
        }
        
        console.log('Counter updated:', count);
    }
    
    // Show/hide loading state
    function showLoading(show) {
        const loading = document.getElementById('hr-loading');
        const list = document.getElementById('hr-list');
        const empty = document.getElementById('hr-empty');
        
        if (loading && list && empty) {
            if (show) {
                loading.classList.remove('d-none');
                list.classList.add('d-none');
                empty.classList.add('d-none');
                console.log('Loading state shown');
            } else {
                loading.classList.add('d-none');
                list.classList.remove('d-none');
                
                const rows = document.querySelectorAll('.hr-row:not(#hr-empty-row)');
                if (rows.length === 0) {
                    empty.classList.remove('d-none');
                } else {
                    empty.classList.add('d-none');
                }
                console.log('Loading state hidden');
            }
        }
    }
    
    // Show error state
    function showError(message = 'Failed to load data. Please try again.') {
        const list = document.getElementById('hr-list');
        if (list) {
            list.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-danger py-5">
                        <div class="mb-3">
                            <i class="bi bi-exclamation-triangle fs-1"></i>
                        </div>
                        <h5>Error loading data</h5>
                        <p class="small mb-0">${message}</p>
                        <button class="btn btn-sm btn-outline-primary mt-3" onclick="location.reload()">
                            <i class="bi bi-arrow-clockwise me-1"></i>
                            Reload Page
                        </button>
                    </td>
                </tr>
            `;
        }
        
        // Also update pagination to be empty
        const pager = document.getElementById('hr-pager');
        if (pager) {
            pager.innerHTML = '';
        }
        
        // Update counter
        updateCounter(0);
        
        console.error('Error shown:', message);
    }
    
    // Show toast notification
    function showToast(message, type = 'info') {
        console.log('Showing toast:', message, type);
        
        // Create toast container if it doesn't exist
        let toastContainer = document.getElementById('hr-toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'hr-toast-container';
            toastContainer.className = 'position-fixed bottom-0 end-0 p-3';
            toastContainer.style.zIndex = '1060';
            document.body.appendChild(toastContainer);
        }
        
        // Create toast
        const toastId = 'toast-' + Date.now();
        const toastHtml = `
            <div id="${toastId}" class="toast align-items-center text-bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="bi ${type === 'success' ? 'bi-check-circle' : type === 'danger' ? 'bi-exclamation-circle' : 'bi-info-circle'} me-2"></i>
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;
        
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        
        // Show toast
        const toastElement = document.getElementById(toastId);
        if (toastElement) {
            const toast = new bootstrap.Toast(toastElement, {
                autohide: true,
                delay: 3000
            });
            toast.show();
            
            // Remove toast after it's hidden
            toastElement.addEventListener('hidden.bs.toast', function() {
                toastElement.remove();
            });
        }
    }
    
    // Get CSRF token
    function getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        if (token) {
            return token.value;
        }
        
        // Alternative ways to get CSRF token
        const cookieToken = document.cookie.split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        
        if (cookieToken) {
            return cookieToken;
        }
        
        console.warn('CSRF token not found');
        return '';
    }
    
    // Format date
    function formatDate(dateString) {
        if (!dateString || dateString === '—') return '—';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('ru-RU', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        } catch (e) {
            return dateString;
        }
    }
    
    // Format date time
    function formatDateTime(dateTimeString) {
        if (!dateTimeString || dateTimeString === '—') return '—';
        try {
            const date = new Date(dateTimeString);
            return date.toLocaleString('ru-RU', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (e) {
            return dateTimeString;
        }
    }
    
    // Debug function to log current state
    window.debugHR = function() {
        console.log('Current state:', {
            page: currentPage,
            filters: currentFilters,
            urls: urls,
            rows: document.querySelectorAll('.hr-row').length
        });
    };
});
