'use strict';

document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('nav-sidebar');
    const toggle = document.getElementById('toggle-nav-sidebar');

    if (!sidebar || !toggle) {
        return;
    }

    const mobileQuery = window.matchMedia('(max-width: 767px)');
    const sidebarHeader = document.createElement('div');
    sidebarHeader.className = 'admin-sidebar-heading';
    sidebarHeader.innerHTML = '<span><strong>قائمة الإدارة</strong><small>وصول سريع لأقسام المتجر</small></span>';

    const closeButton = document.createElement('button');
    closeButton.type = 'button';
    closeButton.className = 'admin-sidebar-close';
    closeButton.setAttribute('aria-label', 'إغلاق القائمة الجانبية');
    closeButton.innerHTML = '<span aria-hidden="true">×</span>';
    sidebarHeader.appendChild(closeButton);
    sidebar.prepend(sidebarHeader);

    const backdrop = document.createElement('button');
    backdrop.type = 'button';
    backdrop.className = 'admin-sidebar-backdrop';
    backdrop.setAttribute('aria-label', 'إغلاق القائمة الجانبية');
    document.body.appendChild(backdrop);

    const navFilter = document.getElementById('nav-filter');
    if (navFilter) {
        navFilter.placeholder = 'ابحث في أقسام الإدارة…';
        navFilter.setAttribute('aria-label', 'البحث في أقسام الإدارة');
    }

    toggle.setAttribute('aria-label', 'فتح القائمة الجانبية');
    toggle.setAttribute('title', 'القائمة الجانبية');

    function setMobileSidebar(open, returnFocus = false) {
        document.body.classList.toggle('admin-sidebar-open', open);
        sidebar.setAttribute('aria-expanded', String(open));
        toggle.setAttribute('aria-expanded', String(open));
        toggle.setAttribute('aria-label', open ? 'إغلاق القائمة الجانبية' : 'فتح القائمة الجانبية');

        if (open) {
            window.setTimeout(() => (navFilter || closeButton).focus(), 180);
        } else if (returnFocus) {
            toggle.focus();
        }
    }

    toggle.addEventListener('click', (event) => {
        if (!mobileQuery.matches) {
            return;
        }
        event.preventDefault();
        event.stopImmediatePropagation();
        setMobileSidebar(!document.body.classList.contains('admin-sidebar-open'));
    }, true);

    closeButton.addEventListener('click', () => setMobileSidebar(false, true));
    backdrop.addEventListener('click', () => setMobileSidebar(false, true));

    sidebar.addEventListener('click', (event) => {
        if (mobileQuery.matches && event.target.closest('a')) {
            setMobileSidebar(false);
        }
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && document.body.classList.contains('admin-sidebar-open')) {
            setMobileSidebar(false, true);
        }
    });

    function handleViewportChange(event) {
        if (!event.matches) {
            document.body.classList.remove('admin-sidebar-open');
            toggle.setAttribute('aria-label', 'طي أو فتح القائمة الجانبية');
        } else {
            document.body.classList.remove('admin-sidebar-open');
            sidebar.setAttribute('aria-expanded', 'false');
            toggle.setAttribute('aria-expanded', 'false');
            toggle.setAttribute('aria-label', 'فتح القائمة الجانبية');
        }
    }

    mobileQuery.addEventListener('change', handleViewportChange);
    handleViewportChange(mobileQuery);
    document.body.classList.add('admin-sidebar-ready');
});
