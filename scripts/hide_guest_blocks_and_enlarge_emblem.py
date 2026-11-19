import re

def modify_index():
    with open('frontend/index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Update Navigation Switcher container to have id="nav-tabs-container" and class="hidden ..."
    nav_tabs_old = '<!-- Navigation Switcher (Nanobanana Underline Tabs) -->\n      <div class="flex items-center space-x-6 text-sm h-full">'
    nav_tabs_new = '<!-- Navigation Switcher (Nanobanana Underline Tabs) -->\n      <div id="nav-tabs-container" class="hidden flex items-center space-x-6 text-sm h-full">'
    assert nav_tabs_old in html, "nav_tabs_old not found"
    html = html.replace(nav_tabs_old, nav_tabs_new)

    # 2. Update App Mode Switcher to have id="app-mode-switcher" and start hidden
    mode_old = '<!-- App Mode Switcher (Student / Developer) -->\n        <div class="hidden md:flex items-center space-x-1 bg-slate-100 p-1 rounded-lg border border-slate-200">'
    mode_new = '<!-- App Mode Switcher (Student / Developer) -->\n        <div id="app-mode-switcher" class="hidden items-center space-x-1 bg-slate-100 p-1 rounded-lg border border-slate-200">'
    assert mode_old in html, "mode_old not found"
    html = html.replace(mode_old, mode_new)

    # 3. Update Quick Action buttons to be wrapped in id="header-quick-actions" and hidden for guests
    quick_old = '''        <button onclick="openTmaQrModal()" class="hidden sm:flex px-2.5 py-1.5 text-xs font-medium rounded-lg bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 shadow-2xs transition items-center space-x-1 cursor-pointer" title="Telegram Mini App">
          <span>📱</span>
          <span>TMA</span>
        </button>
        <button onclick="resetDemoData()" class="hidden sm:flex px-2.5 py-1.5 text-xs font-medium rounded-lg bg-white hover:bg-slate-50 text-slate-600 border border-slate-200 shadow-2xs transition items-center space-x-1 cursor-pointer" title="Сбросить демо">
          <span>🔄</span>
          <span>Сброс</span>
        </button>'''

    quick_new = '''        <!-- Quick Demo Action Buttons (Hidden for Guests) -->
        <div id="header-quick-actions" class="hidden items-center space-x-1.5">
          <button id="btn-header-tma" onclick="openTmaQrModal()" class="px-2.5 py-1.5 text-xs font-medium rounded-lg bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 shadow-2xs transition flex items-center space-x-1 cursor-pointer" title="Telegram Mini App">
            <span>📱</span>
            <span>TMA</span>
          </button>
          <button id="btn-header-reset" onclick="resetDemoData()" class="px-2.5 py-1.5 text-xs font-medium rounded-lg bg-white hover:bg-slate-50 text-slate-600 border border-slate-200 shadow-2xs transition flex items-center space-x-1 cursor-pointer" title="Сбросить демо">
            <span>🔄</span>
            <span>Сброс</span>
          </button>
        </div>'''
    assert quick_old in html, "quick_old not found"
    html = html.replace(quick_old, quick_new)

    # 4. Update Course Context Card to have id="course-context-card" and start hidden
    course_old = '<!-- TOP SYLLABUS & COURSE CONTEXT CARD (Nanobanana Style) -->\n  <!-- =================================================================== -->\n  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-5">'
    course_new = '<!-- TOP SYLLABUS & COURSE CONTEXT CARD (Nanobanana Style) -->\n  <!-- =================================================================== -->\n  <div id="course-context-card" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-5 hidden">'
    assert course_old in html, "course_old not found"
    html = html.replace(course_old, course_new)

    # 5. Update Curb-Cut Banner to have id="student-ramp-banner" and start hidden
    ramp_old = '<!-- Curb-Cut Constitutional Banner (Nanobanana Image 3 style) -->\n      <div class="bg-emerald-50/80 border border-emerald-200 rounded-xl p-3.5 shadow-2xs">'
    ramp_new = '<!-- Curb-Cut Constitutional Banner (Nanobanana Image 3 style) -->\n      <div id="student-ramp-banner" class="bg-emerald-50/80 border border-emerald-200 rounded-xl p-3.5 shadow-2xs hidden">'
    assert ramp_old in html, "ramp_old not found"
    html = html.replace(ramp_old, ramp_new)

    # 6. Enlarge Themis Emblem with lock in student-guest-guard by 2.5x - 3x
    # Replace w-16 h-16 container and lock badge
    emblem_pat = re.compile(
        r'<div class="relative w-16 h-16 mx-auto mb-3\.5">\s*<img src="([^"]+)" alt="Themis Emblem" class="w-16 h-16 rounded-2xl object-cover border border-slate-200 shadow-sm" />\s*<div class="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-slate-900 text-white flex items-center justify-center text-xs shadow-md border-2 border-white">\s*🔒\s*</div>\s*</div>',
        re.DOTALL
    )
    
    m = emblem_pat.search(html)
    assert m is not None, "emblem pattern in student-guest-guard not matched"
    img_src = m.group(1)
    
    enlarged_emblem = f'''<div class="relative w-44 h-44 mx-auto mb-6">
          <img src="{img_src}" alt="Themis Emblem" class="w-44 h-44 rounded-3xl object-cover border-2 border-slate-200 shadow-md p-1.5 bg-white" />
          <div class="absolute -bottom-2 -right-2 w-12 h-12 rounded-2xl bg-slate-900 text-white flex items-center justify-center text-2xl shadow-xl border-3 border-white">
            🔒
          </div>
        </div>'''
    
    html = html[:m.start()] + enlarged_emblem + html[m.end():]

    # Also make student-guest-guard card slightly roomier with rounded-3xl and p-10
    html = html.replace(
        '<div id="student-guest-guard" class="bg-white border border-slate-200 rounded-2xl p-8 shadow-sm max-w-xl mx-auto text-center my-6 transition-all duration-300">',
        '<div id="student-guest-guard" class="bg-white border border-slate-200 rounded-3xl p-10 shadow-sm max-w-xl mx-auto text-center my-8 transition-all duration-300">'
    )

    # 7. Update updateNavigationTabsVisibility() in JS
    old_tabs_fn = '''    function updateNavigationTabsVisibility() {
      const btnStudent = document.getElementById('btn-tab-student');
      const btnProf = document.getElementById('btn-tab-professor');
      if (!btnStudent || !btnProf) return;

      // 1. В режиме "Разработчик" всегда показываем обе вкладки
      if (appMode === 'dev') {
        btnStudent.classList.remove('hidden');
        btnProf.classList.remove('hidden');
        return;
      }

      // 2. В обычном режиме — строгое ролевое разграничение:
      if (currentUser && currentUser.token) {
        if (currentUser.role === 'student') {
          // Студент не видит консоль преподавателя
          btnStudent.classList.remove('hidden');
          btnProf.classList.add('hidden');

          const vProf = document.getElementById('view-professor');
          if (vProf && !vProf.classList.contains('hidden')) {
            switchView('student');
          }
        } else if (currentUser.role === 'teacher') {
          // Преподаватель не видит цифровой пандус
          btnProf.classList.remove('hidden');
          btnStudent.classList.add('hidden');

          const vStudent = document.getElementById('view-student');
          if (vStudent && !vStudent.classList.contains('hidden')) {
            switchView('professor');
          }
        } else {
          btnStudent.classList.remove('hidden');
          btnProf.classList.remove('hidden');
        }
      } else {
        // Гость (не авторизован): открыты обе вкладки
        btnStudent.classList.remove('hidden');
        btnProf.classList.remove('hidden');
      }
    }'''

    new_tabs_fn = '''    function updateNavigationTabsVisibility() {
      const navTabs = document.getElementById('nav-tabs-container');
      const btnStudent = document.getElementById('btn-tab-student');
      const btnProf = document.getElementById('btn-tab-professor');
      if (!btnStudent || !btnProf) return;

      // Неавторизованный пользователь (гость): вкладки полностью скрыты
      if (!currentUser || !currentUser.token) {
        if (navTabs) navTabs.classList.add('hidden');
        btnStudent.classList.add('hidden');
        btnProf.classList.add('hidden');
        return;
      }

      // Авторизованный пользователь: контейнер вкладок показывается
      if (navTabs) navTabs.classList.remove('hidden');

      // 1. В режиме "Разработчик" всегда показываем обе вкладки
      if (appMode === 'dev') {
        btnStudent.classList.remove('hidden');
        btnProf.classList.remove('hidden');
        return;
      }

      // 2. В обычном режиме — строгое ролевое разграничение:
      if (currentUser.role === 'student') {
        // Студент не видит консоль преподавателя
        btnStudent.classList.remove('hidden');
        btnProf.classList.add('hidden');

        const vProf = document.getElementById('view-professor');
        if (vProf && !vProf.classList.contains('hidden')) {
          switchView('student');
        }
      } else if (currentUser.role === 'teacher') {
        // Преподаватель не видит цифровой пандус
        btnProf.classList.remove('hidden');
        btnStudent.classList.add('hidden');

        const vStudent = document.getElementById('view-student');
        if (vStudent && !vStudent.classList.contains('hidden')) {
          switchView('professor');
        }
      } else {
        btnStudent.classList.remove('hidden');
        btnProf.classList.remove('hidden');
      }
    }'''
    assert old_tabs_fn in html, "old_tabs_fn not found"
    html = html.replace(old_tabs_fn, new_tabs_fn)

    # 8. Update updateAuthUI() in JS
    old_auth_ui = '''    function updateAuthUI() {
      const btnOpen = document.getElementById('btn-open-login');
      const badge = document.getElementById('user-profile-badge');
      const nameEl = document.getElementById('badge-user-name');
      const roleEl = document.getElementById('badge-user-role');
      const iconEl = document.getElementById('badge-role-icon');
      const tgEl = document.getElementById('badge-tg-status');

      if (currentUser && currentUser.token) {
        if (btnOpen) btnOpen.classList.add('hidden');
        if (badge) badge.classList.remove('hidden');

        if (currentUser.role === 'teacher') {
          if (iconEl) iconEl.textContent = '👩‍🏫';
          if (nameEl) nameEl.textContent = currentUser.display_name || 'Белощицкая С.';
          if (roleEl) roleEl.textContent = 'Преподаватель';
          if (tgEl) tgEl.classList.add('hidden');
        } else {
          if (iconEl) iconEl.textContent = '👤';
          const rawName = currentUser.display_name || 'Студент К.';
          const cleanName = rawName.includes('(') ? rawName.split('(')[0].trim() : rawName;
          if (nameEl) nameEl.textContent = cleanName;
          if (roleEl) roleEl.textContent = '(ИИ-201)';
          if (tgEl) {
            tgEl.classList.remove('hidden');
            if (currentUser.is_telegram_linked) {
              tgEl.textContent = currentUser.telegram_username ? `TG: ${currentUser.telegram_username}` : 'TG: ✅';
              tgEl.className = 'px-1.5 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-300 border border-emerald-500/30';
            } else {
              tgEl.textContent = 'TG: ⏳';
              tgEl.className = 'px-1.5 py-0.5 rounded text-[10px] font-mono bg-amber-500/10 text-amber-300 border border-amber-500/30';
            }
          }
        }
      } else {
        if (btnOpen) btnOpen.classList.remove('hidden');
        if (badge) badge.classList.add('hidden');
      }

      // Обновляем видимость вкладок навигации по роли
      updateNavigationTabsVisibility();
    }'''

    new_auth_ui = '''    function updateAuthUI() {
      const btnOpen = document.getElementById('btn-open-login');
      const badge = document.getElementById('user-profile-badge');
      const nameEl = document.getElementById('badge-user-name');
      const roleEl = document.getElementById('badge-user-role');
      const iconEl = document.getElementById('badge-role-icon');
      const tgEl = document.getElementById('badge-tg-status');

      const navTabs = document.getElementById('nav-tabs-container');
      const modeSwitcher = document.getElementById('app-mode-switcher');
      const quickActions = document.getElementById('header-quick-actions');
      const courseCard = document.getElementById('course-context-card');
      const rampBanner = document.getElementById('student-ramp-banner');
      const guestGuard = document.getElementById('student-guest-guard');
      const authContent = document.getElementById('student-authorized-content');

      if (currentUser && currentUser.token) {
        if (btnOpen) btnOpen.classList.add('hidden');
        if (badge) badge.classList.remove('hidden');

        // Авторизованный пользователь: открываем доступ к общим блокам
        if (navTabs) navTabs.classList.remove('hidden');
        if (modeSwitcher) modeSwitcher.classList.remove('hidden');
        if (quickActions) quickActions.classList.remove('hidden');
        if (courseCard) courseCard.classList.remove('hidden');

        if (currentUser.role === 'teacher') {
          if (iconEl) iconEl.textContent = '👩‍🏫';
          if (nameEl) nameEl.textContent = currentUser.display_name || 'Белощицкая С.';
          if (roleEl) roleEl.textContent = 'Преподаватель';
          if (tgEl) tgEl.classList.add('hidden');
          if (rampBanner) rampBanner.classList.add('hidden');
          if (guestGuard) guestGuard.classList.add('hidden');
        } else {
          if (iconEl) iconEl.textContent = '👤';
          const rawName = currentUser.display_name || 'Студент К.';
          const cleanName = rawName.includes('(') ? rawName.split('(')[0].trim() : rawName;
          if (nameEl) nameEl.textContent = cleanName;
          if (roleEl) roleEl.textContent = '(ИИ-201)';
          if (rampBanner) rampBanner.classList.remove('hidden');
          if (guestGuard) guestGuard.classList.add('hidden');
          if (authContent) authContent.classList.remove('hidden');
          if (tgEl) {
            tgEl.classList.remove('hidden');
            if (currentUser.is_telegram_linked) {
              tgEl.textContent = currentUser.telegram_username ? `TG: ${currentUser.telegram_username}` : 'TG: ✅';
              tgEl.className = 'px-1.5 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-300 border border-emerald-500/30';
            } else {
              tgEl.textContent = 'TG: ⏳';
              tgEl.className = 'px-1.5 py-0.5 rounded text-[10px] font-mono bg-amber-500/10 text-amber-300 border border-amber-500/30';
            }
          }
        }
      } else {
        // НЕАВТОРИЗОВАННЫЙ ПОЛЬЗОВАТЕЛЬ (ГОСТЬ):
        if (btnOpen) btnOpen.classList.remove('hidden');
        if (badge) badge.classList.add('hidden');

        // Скрываем блоки, выделенные синим на скриншоте:
        if (navTabs) navTabs.classList.add('hidden');
        if (modeSwitcher) modeSwitcher.classList.add('hidden');
        if (quickActions) quickActions.classList.add('hidden');
        if (courseCard) courseCard.classList.add('hidden');
        if (rampBanner) rampBanner.classList.add('hidden');

        // Оставляем видимой только карточку авторизации
        if (guestGuard) guestGuard.classList.remove('hidden');
        if (authContent) authContent.classList.add('hidden');
      }

      // Обновляем видимость вкладок навигации по роли
      updateNavigationTabsVisibility();
    }'''
    assert old_auth_ui in html, "old_auth_ui not found"
    html = html.replace(old_auth_ui, new_auth_ui)

    # 9. Update renderTelegramBindingCard()
    old_tg_render = '''      // 1. Защита: Если пользователь НЕ авторизован — блокируем QR и сессию
      if (!currentUser || !currentUser.token) {
        if (qrPollingTimer) clearInterval(qrPollingTimer);
        if (qrCountdownTimer) clearInterval(qrCountdownTimer);
        if (guard) guard.classList.remove('hidden');
        if (authContent) authContent.classList.add('hidden');
        if (container) container.innerHTML = '';
        return;
      }'''

    new_tg_render = '''      // 1. Защита: Если пользователь НЕ авторизован — блокируем QR и сессию
      if (!currentUser || !currentUser.token) {
        if (qrPollingTimer) clearInterval(qrPollingTimer);
        if (qrCountdownTimer) clearInterval(qrCountdownTimer);
        if (guard) guard.classList.remove('hidden');
        if (authContent) authContent.classList.add('hidden');
        const courseCard = document.getElementById('course-context-card');
        const rampBanner = document.getElementById('student-ramp-banner');
        if (courseCard) courseCard.classList.add('hidden');
        if (rampBanner) rampBanner.classList.add('hidden');
        if (container) container.innerHTML = '';
        return;
      }'''
    assert old_tg_render in html, "old_tg_render not found"
    html = html.replace(old_tg_render, new_tg_render)

    # 10. In DOMContentLoaded, call updateAuthUI() at the very start
    old_dcl = 'document.addEventListener(\'DOMContentLoaded\', async () => {\n      updateModeUI();'
    new_dcl = 'document.addEventListener(\'DOMContentLoaded\', async () => {\n      updateAuthUI();\n      updateModeUI();'
    assert old_dcl in html, "old_dcl not found"
    html = html.replace(old_dcl, new_dcl)

    with open('frontend/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("SUCCESS: frontend/index.html updated cleanly!")

if __name__ == '__main__':
    modify_index()
