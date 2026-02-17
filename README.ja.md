# ConoHa Python SDK

[ConoHa VPS v3 API](https://doc.conoha.jp/reference/api-vps3/) 用の Python SDK です。

[English README](README.md)

## 特徴

- ConoHa VPS v3 API を幅広くカバー（8サービス、100以上のエンドポイント）
- トークン認証の自動取得・自動更新
- トークンレスポンスからのサービスカタログ自動検出
- 遅延読み込みによるサービスクライアント
- 型付き例外階層によるエラーハンドリング

## 対応サービス

| サービス | 説明 |
|---------|------|
| **Identity** | クレデンシャル管理 |
| **Compute** | サーバー、プラン、キーペア、監視グラフ |
| **Volume** | ブロックストレージ、ボリュームタイプ、バックアップ |
| **Image** | VMイメージ、ISOイメージ、容量管理 |
| **Network** | セキュリティグループ/ルール、ネットワーク、サブネット、ポート |
| **Load Balancer** | ロードバランサー、リスナー、プール、メンバー、ヘルスモニター |
| **DNS** | ドメイン、DNSレコード |
| **Object Storage** | コンテナ、オブジェクト |

## インストール

```bash
pip install -r requirements.txt
```

パッケージとしてインストール：

```bash
pip install -e .
```

## クイックスタート

```python
from conoha import ConoHaClient

client = ConoHaClient(
    username="APIユーザー名",
    password="APIパスワード",
    tenant_id="テナントID",
)

# サーバー一覧を取得
servers = client.compute.list_servers_detail()
for server in servers:
    print(f"{server['id']}: {server['status']}")
```

## 使い方

### 認証

初回API呼び出し時に自動で認証が行われます。明示的に認証することも可能です：

```python
client = ConoHaClient(
    username="gncu12345678",
    password="your-password",
    tenant_id="0123456789abcdef",
)

# 明示的な認証（任意 - 自動で実行されます）
client.authenticate()
```

既存のトークンを使用する場合：

```python
client = ConoHaClient(
    token="既存のトークン",
    tenant_id="テナントID",
)
```

### Compute（サーバー管理）

```python
# サーバー一覧
servers = client.compute.list_servers()

# サーバー作成
server = client.compute.create_server(
    flavor_id="プランUUID",
    admin_pass="パスワード",
    volume_id="ブートボリュームUUID",
    instance_name_tag="my-server",
    key_name="my-keypair",
    security_groups=[{"name": "default"}],
)

# サーバー操作
client.compute.start_server("server-id")     # 起動
client.compute.stop_server("server-id")      # 停止
client.compute.reboot_server("server-id")    # 再起動

# プラン変更（リサイズ）
client.compute.resize_server("server-id", "new-flavor-id")
client.compute.confirm_resize("server-id")

# コンソールURL取得
console = client.compute.get_console_url("server-id", console_type="novnc")
print(console["url"])

# SSHキーペア
keypairs = client.compute.list_keypairs()
new_key = client.compute.create_keypair("my-key")

# 監視グラフ（CPU、ディスクI/O、トラフィック）
cpu_data = client.compute.get_cpu_graph("server-id")
```

### Volume（ブロックストレージ）

```python
# ボリューム一覧
volumes = client.volume.list_volumes_detail()

# ボリューム作成
volume = client.volume.create_volume(size=100, name="data-vol")

# ボリュームをイメージとして保存
client.volume.save_volume_as_image("volume-id", "my-image-name")

# バックアップ
backups = client.volume.list_backups_detail()
client.volume.enable_auto_backup("server-id")
```

### Image（イメージ管理）

```python
# イメージ一覧
images = client.image.list_images(visibility="private")

# ISOイメージのアップロード
iso = client.image.create_iso_image("my-distro.iso")
with open("my-distro.iso", "rb") as f:
    client.image.upload_iso_image(iso["id"], f)

# 容量管理
usage = client.image.get_image_usage()
client.image.update_image_quota(550)  # 550GB
```

### Network（ネットワーク）

```python
# セキュリティグループ
groups = client.network.list_security_groups()
new_sg = client.network.create_security_group("web-server")

# ルール追加: HTTP許可
client.network.create_security_group_rule(
    security_group_id=new_sg["id"],
    direction="ingress",
    ethertype="IPv4",
    protocol="tcp",
    port_range_min=80,
    port_range_max=80,
)

# ローカルネットワーク
network = client.network.create_network()
subnet = client.network.create_subnet(
    network_id=network["id"],
    cidr="10.0.0.0/24",
)

# 追加IPアドレスの割り当て
port = client.network.create_additional_ip_port(count=1)
```

### Load Balancer（ロードバランサー）

```python
# ロードバランサー作成
lb = client.load_balancer.create_load_balancer(
    name="my-lb",
    vip_subnet_id="subnet-id",
)

# リスナー作成
listener = client.load_balancer.create_listener(
    loadbalancer_id=lb["id"],
    protocol="TCP",
    protocol_port=80,
    name="http-listener",
)

# プール作成
pool = client.load_balancer.create_pool(
    listener_id=listener["id"],
    protocol="TCP",
    lb_algorithm="ROUND_ROBIN",
    name="web-pool",
)

# メンバー追加
client.load_balancer.create_member(
    pool_id=pool["id"],
    address="203.0.113.10",
    protocol_port=80,
)

# ヘルスモニター
client.load_balancer.create_health_monitor(
    pool_id=pool["id"],
    monitor_type="TCP",
    delay=30,
    timeout=10,
    max_retries=3,
)
```

### DNS

```python
# ドメイン登録
domain = client.dns.create_domain(
    name="example.com.",
    ttl=3600,
    email="admin@example.com",
)

# レコード追加
client.dns.create_record(
    domain_id=domain["uuid"],
    name="www.example.com.",
    record_type="A",
    data="203.0.113.10",
)

client.dns.create_record(
    domain_id=domain["uuid"],
    name="example.com.",
    record_type="MX",
    data="mail.example.com.",
    priority=10,
)
```

### Object Storage（オブジェクトストレージ）

```python
# 容量設定（最小100GB）
client.object_storage.set_account_quota(100)

# コンテナ操作
client.object_storage.create_container("my-bucket")
containers = client.object_storage.list_containers()

# オブジェクトのアップロード / ダウンロード
client.object_storage.upload_object(
    "my-bucket", "hello.txt", b"Hello, World!"
)
resp = client.object_storage.download_object("my-bucket", "hello.txt")
print(resp.content)

# 削除
client.object_storage.delete_object("my-bucket", "hello.txt")
client.object_storage.delete_container("my-bucket")
```

## エラーハンドリング

```python
from conoha.exceptions import (
    APIError,
    AuthenticationError,
    NotFoundError,
    BadRequestError,
    ForbiddenError,
    ConflictError,
    TokenExpiredError,
)

try:
    server = client.compute.get_server("nonexistent-id")
except NotFoundError:
    print("サーバーが見つかりません")
except AuthenticationError:
    print("認証情報が無効です")
except APIError as e:
    print(f"APIエラー {e.status_code}: {e}")
```

## 設定

| パラメータ | デフォルト値 | 説明 |
|-----------|-------------|------|
| `region` | `c3j1` | ConoHa リージョンコード |
| `timeout` | `30` | HTTPリクエストタイムアウト（秒） |

トークンは24時間有効で、期限切れ時に自動更新されます。

## 開発

### セットアップ

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
```

### テスト実行

```bash
# ユニットテスト
pytest tests/unit/

# カバレッジ付きユニットテスト
pytest tests/unit/ --cov=conoha --cov-report=term-missing

# 統合テスト（実際の認証情報が必要）
CONOHA_USERNAME=xxx CONOHA_PASSWORD=xxx CONOHA_TENANT_ID=xxx \
  pytest tests/integration/ --run-integration
```

## プロジェクト構成

```
conoha-python-sdk/
├── conoha/
│   ├── __init__.py          # パッケージエクスポート
│   ├── client.py            # メインクライアント（認証・サービス検出）
│   ├── config.py            # 定数・ベースURL
│   ├── exceptions.py        # 例外階層
│   ├── base.py              # ベースサービスクラス（HTTPヘルパー）
│   ├── identity.py          # Identity API
│   ├── compute.py           # Compute API
│   ├── volume.py            # Block Storage API
│   ├── image.py             # Image API
│   ├── network.py           # Network API
│   ├── loadbalancer.py      # Load Balancer API
│   ├── dns.py               # DNS API
│   └── object_storage.py    # Object Storage API
├── tests/
│   ├── unit/                # ユニットテスト（103テスト）
│   └── integration/         # 統合テスト
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

## ライセンス

MIT
