import urllib.request

def verify_live():
    with urllib.request.urlopen('http://localhost:8000/') as resp:
        html = resp.read().decode('utf-8')
        assert 'w-44 h-44 rounded-3xl object-cover' in html, 'Enlarged emblem not in served HTML'
        assert 'id="course-context-card" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-5 hidden"' in html
        assert 'id="student-ramp-banner" class="bg-emerald-50/80 border border-emerald-200 rounded-xl p-3.5 shadow-2xs hidden"' in html
        assert 'id="nav-tabs-container" class="hidden' in html
        assert 'id="app-mode-switcher" class="hidden' in html
        assert 'id="header-quick-actions" class="hidden' in html
        print("FastAPI is live and serving the updated HTML with hidden guest blocks and enlarged emblem!")

if __name__ == '__main__':
    verify_live()
