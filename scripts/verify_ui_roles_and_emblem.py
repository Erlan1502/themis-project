import os

def test_index_elements():
    index_path = 'frontend/index.html'
    assert os.path.exists(index_path), 'index.html not found'
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Check elements
    assert 'id="btn-tab-student"' in content, 'Missing id="btn-tab-student"'
    assert 'id="btn-tab-professor"' in content, 'Missing id="btn-tab-professor"'
    assert 'id="btn-mode-student"' in content, 'Missing id="btn-mode-student"'
    assert 'id="btn-mode-dev"' in content, 'Missing id="btn-mode-dev"'
    
    # 2. Check emblem integration
    assert 'data:image/png;base64,' in content, 'Missing embedded base64 in index.html'
    assert 'THEMIS_EMBLEM_DATA' in content, 'Missing THEMIS_EMBLEM_DATA'
    assert os.path.exists('frontend/assets/themis_emblem.png'), 'themis_emblem.png does not exist'
    assert os.path.exists('frontend/assets/themis_emblem.jfif'), 'themis_emblem.jfif does not exist'
    
    # 3. Check role-based function
    assert 'function updateNavigationTabsVisibility()' in content, 'Missing updateNavigationTabsVisibility()'
    assert "currentUser.role === 'student'" in content, "Missing student check"
    assert "currentUser.role === 'teacher'" in content, "Missing teacher check"
    assert "appMode === 'dev'" in content, "Missing dev mode check"

    # 4. Check TMA
    tma_path = 'frontend/tma.html'
    assert os.path.exists(tma_path), 'tma.html not found'
    with open(tma_path, 'r', encoding='utf-8') as f:
        tma_content = f.read()
    assert 'data:image/png;base64,' in tma_content, 'Missing embedded base64 in tma.html'

    print("All verification tests PASSED successfully!")

if __name__ == '__main__':
    test_index_elements()
