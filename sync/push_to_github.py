# -*- coding: utf-8 -*-
"""YimMenuV2-zh-cn 构建包推送/轮询/下载工具（PAT 走 GitHub REST）。

用法:
    python push_to_github.py push  <PAT>          # 一次提交全部文件并触发构建
    python push_to_github.py docs  <PAT>          # 只更新 README（提交信息带 [skip ci]，不触发构建）
    python push_to_github.py poll  <PAT>          # 查看最新 workflow 运行状态
    python push_to_github.py dl    <PAT> <tag>    # 下载 Release 附件 YimMenuV2.dll 到桌面 Yim 目录
"""
import base64
import json
import os
import sys
import time
import urllib.request

OWNER, REPO = '3445006207', 'YimMenuV2-zh-cn'
# 自动定位脚本所在目录 —— 不要写死绝对路径，否则工作区搬移后即失效
LOCAL_DIR = os.path.dirname(os.path.abspath(__file__))
DEST_DIR = r'C:/Users/yesh/Desktop/Yim'

FILES = [
    ('README.md', 'README.md'),
    (r'translations_part_1.json', r'localization/translations_part_1.json'),
    (r'translations_part_2.json', r'localization/translations_part_2.json'),
    (r'translations_part_3.json', r'localization/translations_part_3.json'),
    (r'translations_part_4.json', r'localization/translations_part_4.json'),
    (r'translations_part_5.json', r'localization/translations_part_5.json'),
    (r'translations_part_6.json', r'localization/translations_part_6.json'),
    (r'apply.py', r'localization/apply.py'),
    (r'patch_font.py', r'localization/patch_font.py'),
    (r'localization/theme/Neon.hpp', r'localization/theme/Neon.hpp'),
    (r'localization/theme/Neon.cpp', r'localization/theme/Neon.cpp'),
    (r'localization/theme/DefaultStyle.cpp.inc', r'localization/theme/DefaultStyle.cpp.inc'),
    (r'build-zh-cn.yml', r'.github/workflows/build-zh-cn.yml'),
]

API = 'https://api.github.com'


def req(method, url, token, payload=None, accept='application/vnd.github+json', raw=False):
    data = json.dumps(payload).encode() if payload is not None else None
    r = urllib.request.Request(url, data=data, method=method, headers={
        'User-Agent': 'wb-agent',
        'Authorization': 'Bearer ' + token,
        'Accept': 'application/octet-stream' if raw else accept,
    })
    with urllib.request.urlopen(r, timeout=60) as resp:
        body = resp.read()
        return body if raw else (json.loads(body.decode()) if body else None)


def push_contents(token, files=None, message=None):
    """空仓库兜底：逐个文件走 Contents API（首个文件自动初始化 main）。
    工作流文件在 FILES 列表最后，最后一个提交才带工作流，确保只触发一次构建。"""
    files = FILES if files is None else files
    message = message or '添加 YimMenuV2 简体中文汉化构建包（工作流+脚本+定制词典）'
    for local, remote in files:
        content = open(os.path.join(LOCAL_DIR, local), 'rb').read()
        rpath = remote.replace('\\', '/')
        payload = {
            'message': message if len(files) == 1 else 'add ' + rpath,
            'content': base64.b64encode(content).decode(),
            'branch': 'main',
        }
        url = f'{API}/repos/{OWNER}/{REPO}/contents/' + rpath
        try:
            req('PUT', url, token, payload)
        except urllib.error.HTTPError as e:
            if e.code == 422:  # 文件已存在，取 sha 覆盖
                cur = req('GET', url + '?ref=main', token)
                payload['sha'] = cur['sha']
                req('PUT', url, token, payload)
            else:
                raise
        print('put ok:', rpath, len(content), 'bytes')
    print('PUSHED all files (contents API)')
    print('构建应已触发: https://github.com/%s/%s/actions' % (OWNER, REPO))


def push_docs(token):
    """只更新 README；提交信息带 [skip ci]，不会触发重构建。"""
    files = [(l, r) for l, r in FILES if r == 'README.md']
    push(token, files=files,
         message='docs: 更新 README（文件清单/词典条数/汉化原理）[skip ci]')


def push(token, files=None, message=None):
    files = FILES if files is None else files
    message = message or '添加 YimMenuV2 简体中文汉化构建包（工作流+脚本+定制词典）'
    base_sha = base_tree = None
    try:
        head = req('GET', f'{API}/repos/{OWNER}/{REPO}/git/ref/heads/main', token)
        base_sha = head['object']['sha']
        base_commit = req('GET', f'{API}/repos/{OWNER}/{REPO}/git/commits/{base_sha}', token)
        base_tree = base_commit['tree']['sha']
        print('base commit:', base_sha[:10])
    except urllib.error.HTTPError as e:
        print('repo is empty (%s), using contents API' % e.code)
        push_contents(token, files, message)
        return

    tree = []
    for local, remote in files:
        content = open(os.path.join(LOCAL_DIR, local), 'rb').read()
        blob = req('POST', f'{API}/repos/{OWNER}/{REPO}/git/blobs', token,
                   {'content': base64.b64encode(content).decode(), 'encoding': 'base64'})
        tree.append({'path': remote.replace('\\', '/'), 'mode': '100644',
                     'type': 'blob', 'sha': blob['sha']})
        print('blob ok:', remote.replace('\\', '/'), len(content), 'bytes')

    tree_payload = {'tree': tree} if base_tree is None else {'base_tree': base_tree, 'tree': tree}
    new_tree = req('POST', f'{API}/repos/{OWNER}/{REPO}/git/trees', token, tree_payload)
    commit_payload = {'message': message, 'tree': new_tree['sha']}
    if base_sha is not None:
        commit_payload['parents'] = [base_sha]
    commit = req('POST', f'{API}/repos/{OWNER}/{REPO}/git/commits', token, commit_payload)
    if base_sha is None:
        req('POST', f'{API}/repos/{OWNER}/{REPO}/git/refs', token,
            {'ref': 'refs/heads/main', 'sha': commit['sha']})
    else:
        req('PATCH', f'{API}/repos/{OWNER}/{REPO}/git/refs/heads/main', token,
            {'sha': commit['sha'], 'force': False})
    print('PUSHED commit:', commit['sha'])
    print('构建应已触发: https://github.com/%s/%s/actions' % (OWNER, REPO))


def poll(token, once=False):
    while True:
        runs = req('GET', f'{API}/repos/{OWNER}/{REPO}/actions/runs?per_page=5', token)
        print('--- runs @', time.strftime('%H:%M:%S'), '---')
        for r in runs.get('workflow_runs', []):
            print('%s | %s | %s | %s | jobs=%s' % (
                r['name'], r['head_branch'], r['status'], r['conclusion'], r['id']))
        if once or runs.get('workflow_runs'):
            for r in runs.get('workflow_runs', []):
                if r['status'] != 'completed':
                    return None
            return runs.get('workflow_runs', [])
        time.sleep(30)


def wait_done(token):
    deadline = time.time() + 60 * 40
    while time.time() < deadline:
        runs = req('GET', f'{API}/repos/{OWNER}/{REPO}/actions/runs?per_page=5', token)
        rs = runs.get('workflow_runs', [])
        if rs:
            active = [r for r in rs if r['status'] != 'completed']
            for r in rs:
                print('%s | %s | %s | %s' % (r['id'], r['head_branch'], r['status'], r['conclusion']))
            if not active:
                return rs
        else:
            print('no runs yet...')
        time.sleep(30)
    raise SystemExit('TIMEOUT waiting for build')


def download(token):
    rel = req('GET', f'{API}/repos/{OWNER}/{REPO}/releases/latest', token)
    print('latest release:', rel['tag_name'], rel['name'])
    for a in rel['assets']:
        print('asset:', a['name'], a['size'])
        if a['name'].lower() == 'yimmenuv2.dll':
            os.makedirs(DEST_DIR, exist_ok=True)
            dest = os.path.join(DEST_DIR, 'YimMenuV2.dll')
            data = req('GET', a['url'], token, raw=True)
            open(dest, 'wb').write(data)
            print('SAVED:', dest, len(data), 'bytes')


if __name__ == '__main__':
    cmd = sys.argv[1]
    token = sys.argv[2]
    if cmd == 'push':
        push(token)
    elif cmd == 'docs':
        push_docs(token)
    elif cmd == 'poll':
        poll(token)
    elif cmd == 'wait':
        rs = wait_done(token)
        bad = [r for r in rs if r['conclusion'] != 'success']
        print('DONE conclusion:', 'SUCCESS' if not bad else 'FAILED runs=%d' % len(bad))
    elif cmd == 'dl':
        download(token)
    else:
        sys.exit(__doc__)
