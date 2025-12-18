import sys
import pytest
from unittest.mock import patch, MagicMock
import cli

@pytest.fixture
def run_cli(capsys):
    """
    运行 CLI 命令并捕获输出的 Helper fixture。
    """
    def _run(args):
        # 模拟 sys.argv，第一个参数通常是脚本名
        with patch.object(sys, "argv", ["cli.py"] + args):
            try:
                cli.main()
            except SystemExit:
                pass # argparse 会触发 SystemExit，需捕获
        return capsys.readouterr()
    return _run

# ==========================================
# Server Tests
# ==========================================
class TestServerCommands:
    @patch("server.manager.server_start")
    def test_server_start(self, mock_start, run_cli):
        """[S-01] 启动服务器"""
        run_cli(["server", "start", "8080"])
        mock_start.assert_called_once_with(8080)

# ==========================================
# User Tests
# ==========================================
class TestUserCommands:
    @patch("logic.auth.user_register")
    def test_register_success(self, mock_reg, run_cli):
        """[U-01] 用户注册 (位置参数)"""
        mock_reg.return_value = 10086
        # 使用位置参数调用: user register <username> <password>
        out = run_cli(["user", "register", "alice", "secret123"])
        
        # 验证调用参数
        mock_reg.assert_called_once_with("alice", "secret123")
        # 验证输出
        assert "User registered. ID: 10086" in out.out

    @patch("client.store.save_local_token")
    @patch("logic.auth.user_login")
    def test_login_success(self, mock_login, mock_save, run_cli):
        """[U-02] 用户登录与 Token 保存 (位置参数)"""
        mock_login.return_value = "fake_token_xyz"
        # 使用位置参数调用: user login <username> <password>
        out = run_cli(["user", "login", "bob", "pass"])
        
        mock_login.assert_called_once_with("bob", "pass")
        mock_save.assert_called_once_with("fake_token_xyz")
        assert "Login successful." in out.out

    @patch("client.store.clear_local_token")
    def test_logout(self, mock_clear, run_cli):
        """[U-03] 用户登出"""
        out = run_cli(["user", "logout"])
        mock_clear.assert_called_once()
        assert "Logged out." in out.out

# ==========================================
# Post Tests
# ==========================================
@patch("client.store.load_local_token", return_value="mock_token_123")
class TestPostCommands:
    
    @patch("logic.post.post_create")
    def test_create(self, mock_create, mock_load, run_cli):
        """[P-01] 创建文章"""
        mock_create.return_value = "cid_999"
        out = run_cli(["post", "create"])
        
        mock_create.assert_called_once_with("mock_token_123")
        assert "Post created. CID: cid_999" in out.out

    @patch("logic.post.post_list")
    def test_list(self, mock_list, mock_load, run_cli):
        """[P-02] 列出文章"""
        mock_list.return_value = ["cid_1", "cid_2"]
        out = run_cli(["post", "list", "5"])
        
        mock_list.assert_called_once_with("mock_token_123", 5)
        assert "Posts: ['cid_1', 'cid_2']" in out.out

    @patch("logic.post.post_update")
    def test_update(self, mock_update, mock_load, run_cli):
        """[P-03] 更新文章"""
        mock_update.return_value = True
        # 测试转义字符处理
        out = run_cli(["post", "update", "cid_1", "context", "Line1\\nLine2"])
        
        mock_update.assert_called_once_with("mock_token_123", "cid_1", "context", "Line1\nLine2")
        assert "Success" in out.out

    @patch("logic.post.post_delete")
    def test_delete(self, mock_delete, mock_load, run_cli):
        """[P-04] 删除文章"""
        mock_delete.return_value = False # 模拟失败
        out = run_cli(["post", "delete", "cid_x"])
        
        mock_delete.assert_called_once_with("mock_token_123", "cid_x")
        assert "Failed" in out.out

    @patch("logic.post.post_get")
    def test_get(self, mock_get, mock_load, run_cli):
        """[P-05] 获取文章字段"""
        mock_get.return_value = "My Title"
        out = run_cli(["post", "get", "cid_1", "title"])
        
        mock_get.assert_called_once_with("mock_token_123", "cid_1", "title")
        assert "title: My Title" in out.out

    @patch("logic.post.post_search")
    def test_search(self, mock_search, mock_load, run_cli):
        """[P-06] 搜索文章"""
        mock_search.return_value = ["cid_found"]
        out = run_cli(["post", "search", "keyword"])
        
        mock_search.assert_called_once_with("mock_token_123", "keyword")
        assert "Results: ['cid_found']" in out.out

    def test_auth_error(self, mock_load, run_cli):
        """[P-07] 未登录错误处理"""
        mock_load.side_effect = PermissionError("No login")
        # 需要 patch 任意一个 post 方法来触发 load_local_token
        with patch("logic.post.post_list"): 
            out = run_cli(["post", "list"])
            assert "Error: Please login first." in out.out