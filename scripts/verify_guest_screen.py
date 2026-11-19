import re

def verify():
    with open('frontend/index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Check hidden classes on guest blocks
    assert 'id="nav-tabs-container" class="hidden' in html, "nav-tabs-container not hidden"
    assert 'id="app-mode-switcher" class="hidden' in html, "app-mode-switcher not hidden"
    assert 'id="header-quick-actions" class="hidden' in html, "header-quick-actions not hidden"
    assert 'id="course-context-card" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-5 hidden"' in html, "course-context-card not hidden"
    assert 'id="student-ramp-banner" class="bg-emerald-50/80 border border-emerald-200 rounded-xl p-3.5 shadow-2xs hidden"' in html, "student-ramp-banner not hidden"
    
    # Check enlarged emblem
    assert 'w-44 h-44 rounded-3xl object-cover' in html, "Enlarged emblem not found"
    assert 'w-12 h-12 rounded-2xl bg-slate-900' in html, "Enlarged lock badge not found"

    # Check preserved buttons
    assert 'id="btn-tab-student"' in html
    assert 'id="btn-tab-professor"' in html
    assert 'id="btn-mode-student"' in html
    assert 'id="btn-mode-dev"' in html
    assert 'id="btn-open-login"' in html
    assert 'id="btn-header-tma"' in html
    assert 'id="btn-header-reset"' in html

    # Check JS logic
    assert "if (!currentUser || !currentUser.token)" in html
    assert "navTabs.classList.add('hidden')" in html
    assert "modeSwitcher.classList.add('hidden')" in html
    assert "quickActions.classList.add('hidden')" in html
    assert "courseCard.classList.add('hidden')" in html
    assert "rampBanner.classList.add('hidden')" in html

    print("ALL VERIFICATIONS PASSED 100%!")

if __name__ == '__main__':
    verify()
