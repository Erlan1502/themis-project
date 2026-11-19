import os

def embed():
    with open('frontend/assets/emblem_b64.txt', 'r') as f:
        b64_uri = f.read().strip()

    # 1. Update frontend/index.html
    with open('frontend/index.html', 'r', encoding='utf-8') as f:
        idx = f.read()

    idx = idx.replace('assets/themis_emblem.png', b64_uri)

    if 'const THEMIS_EMBLEM_DATA' not in idx:
        idx = idx.replace(
            "let activeTopicId = 'week_09_deep_learning';",
            f"const THEMIS_EMBLEM_DATA = '{b64_uri}';\n    let activeTopicId = 'week_09_deep_learning';"
        )

    with open('frontend/index.html', 'w', encoding='utf-8') as f:
        f.write(idx)
    print("index.html updated successfully!")

    # 2. Update frontend/tma.html
    with open('frontend/tma.html', 'r', encoding='utf-8') as f:
        tma = f.read()

    tma = tma.replace('assets/themis_emblem.png', b64_uri)

    if 'const THEMIS_EMBLEM_DATA' not in tma:
        tma = tma.replace(
            "let currentStudentId =",
            f"const THEMIS_EMBLEM_DATA = '{b64_uri}';\n    let currentStudentId ="
        )

    with open('frontend/tma.html', 'w', encoding='utf-8') as f:
        f.write(tma)
    print("tma.html updated successfully!")

if __name__ == '__main__':
    embed()
