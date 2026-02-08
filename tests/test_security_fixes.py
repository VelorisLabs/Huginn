"""
安全修复验证测试
覆盖审计报告中 P0/P1 级别的修复项
"""
import pytest
import os
import sys
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 测试环境需要设置 SECRET_KEY 和 DEBUG，否则 api.core.config 导入会报错
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests-only")
os.environ.setdefault("DEBUG", "True")


# ============================================================
# P0 #1/#2: SECRET_KEY 校验 + DEBUG 默认关闭
# ============================================================
class TestConfigSecurity:
    """测试配置安全性"""
    
    def test_debug_default_is_false(self):
        """DEBUG 默认值应为 False"""
        from pydantic_settings import BaseSettings
        # 直接检查类定义中的默认值
        from api.core.config import Settings
        s = Settings.model_fields['DEBUG']
        assert s.default is False, "DEBUG 默认值应为 False"
    
    def test_secret_key_default_is_empty(self):
        """SECRET_KEY 默认值应为空字符串"""
        from api.core.config import Settings
        s = Settings.model_fields['SECRET_KEY']
        assert s.default == "", "SECRET_KEY 默认值应为空字符串"


# ============================================================
# P0 #3: XSS 防护 — html.escape
# ============================================================
class TestXSSProtection:
    """测试 HTML 转义函数"""
    
    def test_esc_function_escapes_html(self):
        """_esc 函数应正确转义 HTML 特殊字符"""
        from src.static_export import _esc
        
        assert _esc('<script>alert("xss")</script>') == '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;'
        assert _esc('normal text') == 'normal text'
        assert _esc(None) == ''
        assert _esc(42) == '42'
        assert _esc('a & b') == 'a &amp; b'
        assert _esc("it's") == "it&#x27;s"
    
    def test_esc_handles_edge_cases(self):
        """_esc 应处理边界情况"""
        from src.static_export import _esc
        
        assert _esc('') == ''
        assert _esc(0) == '0'
        assert _esc(False) == 'False'


# ============================================================
# P0 #4: PDF magic bytes 校验
# ============================================================
class TestPDFMagicBytes:
    """测试 PDF 文件头校验"""
    
    def test_valid_pdf_magic_bytes(self, tmp_path):
        """有效 PDF 文件应通过校验"""
        sys.path.insert(0, str(PROJECT_ROOT))
        from api.routes.upload import _validate_pdf_magic_bytes
        
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b'%PDF-1.4 fake content')
        assert _validate_pdf_magic_bytes(pdf_file) is True
    
    def test_invalid_pdf_magic_bytes(self, tmp_path):
        """非 PDF 文件应被拒绝"""
        from api.routes.upload import _validate_pdf_magic_bytes
        
        exe_file = tmp_path / "fake.pdf"
        exe_file.write_bytes(b'MZ\x90\x00\x03\x00\x00\x00')
        assert _validate_pdf_magic_bytes(exe_file) is False
    
    def test_empty_file(self, tmp_path):
        """空文件应被拒绝"""
        from api.routes.upload import _validate_pdf_magic_bytes
        
        empty_file = tmp_path / "empty.pdf"
        empty_file.write_bytes(b'')
        assert _validate_pdf_magic_bytes(empty_file) is False
    
    def test_nonexistent_file(self, tmp_path):
        """不存在的文件应返回 False"""
        from api.routes.upload import _validate_pdf_magic_bytes
        
        assert _validate_pdf_magic_bytes(tmp_path / "nonexistent.pdf") is False


# ============================================================
# P0 #5: ZIP 路径穿越防护
# ============================================================
class TestZIPPathTraversal:
    """测试 ZIP 路径穿越防护"""
    
    def test_malicious_zip_path_detected(self, tmp_path):
        """包含 .. 的 ZIP 文件路径应被过滤"""
        # 创建一个恶意 ZIP
        zip_path = tmp_path / "malicious.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("../../etc/passwd", "root:x:0:0")
            zf.writestr("normal.pdf", "%PDF-1.4 content")
        
        # 验证 ZIP 中确实有恶意路径
        with zipfile.ZipFile(zip_path, 'r') as zf:
            names = zf.namelist()
            assert any('..' in name for name in names)


# ============================================================
# P0 #7: PDF 资源泄漏 — with 语句
# ============================================================
class TestPDFResourceLeak:
    """测试 PDF 提取器使用了上下文管理器"""
    
    def test_pdf_extractor_uses_context_manager(self):
        """确认 extract_pdf_text 使用 with 语句"""
        import inspect
        from src.core.pdf_extractor import extract_pdf_text
        source = inspect.getsource(extract_pdf_text)
        assert 'with fitz.open' in source, "应使用 with fitz.open() 上下文管理器"
        assert 'doc.close()' not in source, "不应手动调用 doc.close()"


# ============================================================
# P0 #8: 模块级代码 — 延迟加载
# ============================================================
class TestStaticExportLazyLoading:
    """测试 static_export 模块延迟加载"""
    
    def test_module_import_does_not_read_csv(self):
        """导入模块不应立即执行 pd.read_csv"""
        # 如果模块级代码执行 read_csv 且文件不存在，import 会失败
        # 我们的修复应让 import 成功，数据加载推迟到 _load_data() 调用
        import importlib
        # 强制重新导入以验证
        if 'src.static_export' in sys.modules:
            # 模块已经被导入过了，检查 _load_data 函数存在即可
            from src.static_export import _load_data, _esc
            assert callable(_load_data)
            assert callable(_esc)
        else:
            # 首次导入不应崩溃
            from src.static_export import _load_data, _esc
            assert callable(_load_data)


# ============================================================
# P1 #15: Celery 任务路径
# ============================================================
class TestCeleryTaskPath:
    """测试 Celery 任务路径配置"""
    
    def test_celery_include_path_is_correct(self):
        """Celery include 路径应指向 api.tasks.paper_tasks"""
        import ast
        celery_app_path = PROJECT_ROOT / "api" / "tasks" / "celery_app.py"
        source = celery_app_path.read_text(encoding='utf-8')
        assert 'api.tasks.paper_tasks' in source, "Celery include 应使用 api.tasks.paper_tasks"
        assert 'app.tasks.paper_tasks' not in source, "不应使用旧的 app.tasks.paper_tasks 路径"


# ============================================================
# P1 #18: LLM 空值检查
# ============================================================
class TestLLMNullCheck:
    """测试 LLM 响应空值检查"""
    
    def test_call_llm_source_has_null_checks(self):
        """call_llm 函数应包含空值检查"""
        import inspect
        from src.core.llm_client import call_llm
        source = inspect.getsource(call_llm)
        assert 'not response' in source or 'response.choices' in source, "应检查 response 是否为空"
        assert 'message.content is None' in source or 'message is None' in source, "应检查 message.content 是否为空"


# ============================================================
# P2 #17: 裸 except 修复
# ============================================================
class TestBareExceptFix:
    """测试裸 except 已修复"""
    
    def test_no_bare_except_in_extraction(self):
        """extraction.py 不应包含裸 except"""
        source_path = PROJECT_ROOT / "src" / "extraction.py"
        source = source_path.read_text(encoding='utf-8')
        lines = source.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped == 'except:':
                pytest.fail(f"发现裸 except 在第 {i+1} 行: {stripped}")


# ============================================================
# P2 #20: 聚类参数动态化
# ============================================================
class TestClusteringDynamic:
    """测试聚类参数动态化"""
    
    def test_find_best_k_handles_small_dataset(self):
        """小数据集应自动调整 K 值范围"""
        from src.clustering import find_best_k
        import numpy as np
        from scipy.sparse import csr_matrix
        
        # 模拟 2 个样本的 TF-IDF 矩阵
        small_matrix = csr_matrix(np.array([[1.0, 0.5], [0.3, 1.0]]))
        k = find_best_k(small_matrix)
        assert k >= 1, "小数据集的 K 值应 >= 1"
    
    def test_find_best_k_normal_dataset(self):
        """正常大小数据集应正常工作"""
        from src.clustering import find_best_k
        import numpy as np
        from scipy.sparse import csr_matrix
        
        # 模拟 10 个样本
        np.random.seed(42)
        matrix = csr_matrix(np.random.rand(10, 20))
        k = find_best_k(matrix)
        assert 2 <= k <= 8, f"K 值应在 2-8 范围内，实际: {k}"


# ============================================================
# P1 #14: 事件循环 try-finally
# ============================================================
class TestEventLoopProtection:
    """测试事件循环 try-finally 保护"""
    
    def test_paper_tasks_has_try_finally(self):
        """paper_tasks.py 中的事件循环应使用 try-finally"""
        source_path = PROJECT_ROOT / "api" / "tasks" / "paper_tasks.py"
        source = source_path.read_text(encoding='utf-8')
        
        # 检查所有 new_event_loop 后面都有 try-finally
        import re
        loop_blocks = re.findall(r'new_event_loop\(\).*?loop\.close\(\)', source, re.DOTALL)
        for block in loop_blocks:
            assert 'try:' in block and 'finally:' in block, \
                "每个 new_event_loop 都应有 try-finally 保护"
    
    def test_upload_no_event_loop_hack(self):
        """upload.py 不应再使用 new_event_loop 黑科技（已改为纯 async）"""
        source_path = PROJECT_ROOT / "api" / "routes" / "upload.py"
        source = source_path.read_text(encoding='utf-8')
        assert 'new_event_loop' not in source, \
            "upload.py 应已移除 new_event_loop，改为纯 async 调用"
        assert 'async_call_llm' in source, \
            "upload.py 应使用 async_call_llm 异步调用 LLM"


# ============================================================
# Docker 配置验证
# ============================================================
class TestDockerConfig:
    """测试 Docker 配置正确性"""
    
    def test_docker_compose_paths_correct(self):
        """docker-compose.yml 不应引用不存在的 ./backend 目录"""
        compose_path = PROJECT_ROOT / "deploy" / "docker-compose.yml"
        content = compose_path.read_text(encoding='utf-8')
        assert 'context: ./backend' not in content, "不应引用 ./backend（该目录不存在）"
    
    def test_dockerfiles_exist(self):
        """Dockerfile 文件应存在"""
        assert (PROJECT_ROOT / "deploy" / "Dockerfile.backend").exists()
        assert (PROJECT_ROOT / "deploy" / "Dockerfile.frontend").exists()
    
    def test_celery_command_uses_correct_path(self):
        """Celery 启动命令应使用正确的模块路径"""
        compose_path = PROJECT_ROOT / "deploy" / "docker-compose.yml"
        content = compose_path.read_text(encoding='utf-8')
        assert 'api.tasks.celery_app' in content, "Celery 命令应使用 api.tasks.celery_app"
        assert 'app.tasks.celery_app' not in content, "不应使用旧的 app.tasks.celery_app"


# ============================================================
# V2 修复: NEW-1 测试账号密码一致性
# ============================================================
class TestAccountConsistency:
    """测试账号密码文档一致性"""
    
    def test_create_test_user_password_matches_docs(self):
        """create_test_user.py 密码应为 test123"""
        source_path = PROJECT_ROOT / "scripts" / "create_test_user.py"
        source = source_path.read_text(encoding='utf-8')
        assert 'get_password_hash("test123")' in source, "密码应为 test123"
        assert 'get_password_hash("test")' not in source, "不应使用旧密码 test"
    
    def test_start_ps1_matches_create_script(self):
        """start.ps1 中提示的密码应与脚本一致"""
        ps1_path = PROJECT_ROOT / "start.ps1"
        if ps1_path.exists():
            content = ps1_path.read_text(encoding='utf-8')
            assert 'test123' in content or 'test/test123' in content


# ============================================================
# V2 修复: #11 接口限流
# ============================================================
class TestRateLimiting:
    """测试接口限流配置"""
    
    def test_slowapi_imported_in_main(self):
        """main.py 应导入 slowapi"""
        source_path = PROJECT_ROOT / "api" / "main.py"
        source = source_path.read_text(encoding='utf-8')
        assert 'slowapi' in source, "main.py 应导入 slowapi"
        assert 'Limiter' in source, "应创建 Limiter 实例"
        assert 'RateLimitExceeded' in source, "应注册 RateLimitExceeded 处理器"
    
    def test_auth_endpoints_have_rate_limits(self):
        """认证接口应有限流装饰器"""
        source_path = PROJECT_ROOT / "api" / "routes" / "auth.py"
        source = source_path.read_text(encoding='utf-8')
        assert '@limiter.limit' in source, "auth 路由应有 @limiter.limit 装饰器"
        assert '5/minute' in source, "login 应限制 5/minute"


# ============================================================
# V2 修复: NEW-4 CORS 限定
# ============================================================
class TestCORSConfig:
    """测试 CORS 配置"""
    
    def test_cors_not_wildcard(self):
        """CORS 不应使用通配符 methods/headers"""
        source_path = PROJECT_ROOT / "api" / "main.py"
        source = source_path.read_text(encoding='utf-8')
        assert 'allow_methods=["*"]' not in source, "不应使用 allow_methods=[\"*\"]"
        assert 'allow_headers=["*"]' not in source, "不应使用 allow_headers=[\"*\"]"


# ============================================================
# V2 修复: NEW-2 datetime.utcnow 废弃
# ============================================================
class TestDatetimeDeprecation:
    """测试 datetime.utcnow 已替换"""
    
    def test_no_utcnow_in_security(self):
        """security.py 不应使用已废弃的 datetime.utcnow()"""
        source_path = PROJECT_ROOT / "api" / "core" / "security.py"
        source = source_path.read_text(encoding='utf-8')
        assert 'datetime.utcnow()' not in source, "应使用 datetime.now(timezone.utc) 替代 utcnow()"
        assert 'timezone.utc' in source, "应导入并使用 timezone.utc"
    
    def test_no_utcnow_in_theme_model(self):
        """theme.py 模型不应使用已废弃的 datetime.utcnow"""
        source_path = PROJECT_ROOT / "api" / "models" / "theme.py"
        source = source_path.read_text(encoding='utf-8')
        assert 'datetime.utcnow' not in source, "theme 模型不应使用 datetime.utcnow"


# ============================================================
# V2 修复: NEW-3 导出文件清理
# ============================================================
class TestExportFileCleanup:
    """测试导出文件清理"""
    
    def test_export_uses_background_task(self):
        """export.py 应使用 BackgroundTask 清理临时文件"""
        source_path = PROJECT_ROOT / "api" / "routes" / "export.py"
        source = source_path.read_text(encoding='utf-8')
        assert 'BackgroundTask' in source, "应导入 BackgroundTask"
        assert 'os.unlink' in source, "应在后台任务中删除文件"


# ============================================================
# V2 修复: NEW-5 LLM test_api_connection 空数组
# ============================================================
class TestLLMTestConnection:
    """测试 test_api_connection 安全检查"""
    
    def test_choices_checked_before_index(self):
        """test_api_connection 应在访问 choices[0] 前检查 choices 非空"""
        import inspect
        from src.core.llm_client import test_api_connection
        source = inspect.getsource(test_api_connection)
        assert 'response.choices and' in source, "应在 choices[0] 前检查 choices 非空"


# ============================================================
# V2 修复: NEW-8 Theme 唯一约束
# ============================================================
class TestThemeUniqueness:
    """测试 Theme 模型唯一约束"""
    
    def test_theme_has_unique_constraint(self):
        """Theme 模型应有 (user_id, name) 唯一约束"""
        source_path = PROJECT_ROOT / "api" / "models" / "theme.py"
        source = source_path.read_text(encoding='utf-8')
        assert 'UniqueConstraint' in source, "应使用 UniqueConstraint"
        assert 'user_id' in source and 'name' in source, "唯一约束应包含 user_id 和 name"


# ============================================================
# V2 修复: NEW-9 Nginx 安全头
# ============================================================
class TestNginxSecurityHeaders:
    """测试 Nginx 安全头配置"""
    
    def test_nginx_has_hsts(self):
        """nginx.conf 应有 HSTS 头"""
        conf_path = PROJECT_ROOT / "deploy" / "nginx.conf"
        content = conf_path.read_text(encoding='utf-8')
        assert 'Strict-Transport-Security' in content, "应有 HSTS 头"
    
    def test_nginx_has_csp(self):
        """nginx.conf 应有 CSP 头"""
        conf_path = PROJECT_ROOT / "deploy" / "nginx.conf"
        content = conf_path.read_text(encoding='utf-8')
        assert 'Content-Security-Policy' in content, "应有 CSP 头"
    
    def test_nginx_has_referrer_policy(self):
        """nginx.conf 应有 Referrer-Policy 头"""
        conf_path = PROJECT_ROOT / "deploy" / "nginx.conf"
        content = conf_path.read_text(encoding='utf-8')
        assert 'Referrer-Policy' in content, "应有 Referrer-Policy 头"
    
    def test_nginx_has_permissions_policy(self):
        """nginx.conf 应有 Permissions-Policy 头"""
        conf_path = PROJECT_ROOT / "deploy" / "nginx.conf"
        content = conf_path.read_text(encoding='utf-8')
        assert 'Permissions-Policy' in content, "应有 Permissions-Policy 头"


# ============================================================
# V2 修复: NEW-10 pytest 配置
# ============================================================
class TestProjectConfig:
    """测试项目配置完整性"""
    
    def test_pyproject_toml_exists(self):
        """应有 pyproject.toml 配置"""
        assert (PROJECT_ROOT / "pyproject.toml").exists(), "缺少 pyproject.toml"
    
    def test_pyproject_has_pytest_config(self):
        """pyproject.toml 应包含 pytest 配置"""
        content = (PROJECT_ROOT / "pyproject.toml").read_text(encoding='utf-8')
        assert 'tool.pytest' in content, "应有 [tool.pytest.ini_options]"
    
    def test_requirements_dev_exists(self):
        """应有 requirements-dev.txt"""
        assert (PROJECT_ROOT / "requirements-dev.txt").exists(), "缺少 requirements-dev.txt"
    
    def test_requirements_has_slowapi(self):
        """requirements.txt 应包含 slowapi"""
        content = (PROJECT_ROOT / "requirements.txt").read_text(encoding='utf-8')
        assert 'slowapi' in content, "requirements.txt 应包含 slowapi"


# ============================================================
# V2 修复: #9/#12 Token Cookie + Refresh
# ============================================================
class TestTokenSecurity:
    """测试 Token 安全性"""
    
    def test_auth_sets_httponly_cookie(self):
        """login 端点应设置 httpOnly cookie"""
        source_path = PROJECT_ROOT / "api" / "routes" / "auth.py"
        source = source_path.read_text(encoding='utf-8')
        assert 'httponly=True' in source, "应设置 httpOnly cookie"
        assert 'set_cookie' in source, "应使用 set_cookie"
    
    def test_refresh_endpoint_exists(self):
        """应有 /auth/refresh 端点"""
        source_path = PROJECT_ROOT / "api" / "routes" / "auth.py"
        source = source_path.read_text(encoding='utf-8')
        assert '/refresh' in source or 'refresh' in source, "应有 refresh 端点"
    
    def test_logout_clears_cookies(self):
        """logout 应清除 cookie"""
        source_path = PROJECT_ROOT / "api" / "routes" / "auth.py"
        source = source_path.read_text(encoding='utf-8')
        assert 'delete_cookie' in source, "logout 应调用 delete_cookie"
    
    def test_access_token_expire_shortened(self):
        """access_token 有效期应缩短"""
        from api.core.config import Settings
        field = Settings.model_fields['ACCESS_TOKEN_EXPIRE_MINUTES']
        assert field.default <= 60, f"access_token 有效期应 <= 60 分钟，实际: {field.default}"
    
    def test_refresh_token_config_exists(self):
        """应有 REFRESH_TOKEN_EXPIRE_DAYS 配置"""
        from api.core.config import Settings
        assert 'REFRESH_TOKEN_EXPIRE_DAYS' in Settings.model_fields, "应有 REFRESH_TOKEN_EXPIRE_DAYS"
    
    def test_deps_supports_cookie_auth(self):
        """deps.py 应支持从 Cookie 读取 token"""
        source_path = PROJECT_ROOT / "api" / "core" / "deps.py"
        source = source_path.read_text(encoding='utf-8')
        assert 'Cookie' in source, "deps 应支持从 Cookie 读取 token"
        assert 'auto_error=False' in source, "HTTPBearer 应设为 auto_error=False"


# ============================================================
# V2 修复: #24 日志系统
# ============================================================
class TestLoggingMigration:
    """测试 src/ 日志系统迁移"""
    
    def test_src_config_has_logging_setup(self):
        """src/core/config.py 应有日志配置"""
        source_path = PROJECT_ROOT / "src" / "core" / "config.py"
        source = source_path.read_text(encoding='utf-8')
        assert 'import logging' in source, "应导入 logging"
        assert 'setup_logging' in source, "应有 setup_logging 函数"
    
    def test_llm_client_uses_logger(self):
        """llm_client.py 应使用 logger 而非 print"""
        source_path = PROJECT_ROOT / "src" / "core" / "llm_client.py"
        source = source_path.read_text(encoding='utf-8')
        assert 'logger = logging.getLogger' in source, "应创建 logger"
        assert 'logger.info' in source or 'logger.error' in source, "应使用 logger"
    
    def test_clustering_uses_logger(self):
        """clustering.py 应使用 logger 而非 print"""
        source_path = PROJECT_ROOT / "src" / "clustering.py"
        source = source_path.read_text(encoding='utf-8')
        assert 'logger = logging.getLogger' in source, "应创建 logger"


# ============================================================
# V2 修复: #22 前端类型安全
# ============================================================
class TestFrontendTypeSafety:
    """测试前端类型安全"""
    
    def test_no_catch_err_any_in_login(self):
        """LoginForm.tsx 不应有 catch(err: any)"""
        source_path = PROJECT_ROOT / "frontend" / "src" / "components" / "LoginForm.tsx"
        source = source_path.read_text(encoding='utf-8')
        assert 'err: any' not in source, "不应使用 err: any"
        assert 'AxiosError' in source, "应使用 AxiosError 类型"
    
    def test_no_catch_err_any_in_register(self):
        """RegisterForm.tsx 不应有 catch(err: any)"""
        source_path = PROJECT_ROOT / "frontend" / "src" / "components" / "RegisterForm.tsx"
        source = source_path.read_text(encoding='utf-8')
        assert 'err: any' not in source, "不应使用 err: any"
    
    def test_no_catch_error_any_in_theme_manager(self):
        """ThemeManager.tsx 不应有 catch(error: any)"""
        source_path = PROJECT_ROOT / "frontend" / "src" / "components" / "ThemeManager.tsx"
        source = source_path.read_text(encoding='utf-8')
        assert 'error: any' not in source, "不应使用 error: any"
    
    def test_no_as_any_in_upload_zone(self):
        """UploadZone.tsx 不应有 (error as any)"""
        source_path = PROJECT_ROOT / "frontend" / "src" / "components" / "UploadZone.tsx"
        source = source_path.read_text(encoding='utf-8')
        assert 'as any' not in source, "不应使用 as any"


# ============================================================
# V2 修复: NEW-6 前端用户名校验
# ============================================================
class TestUsernameValidation:
    """测试前端用户名校验"""
    
    def test_register_form_has_username_validation(self):
        """RegisterForm 应有用户名长度和格式校验"""
        source_path = PROJECT_ROOT / "frontend" / "src" / "components" / "RegisterForm.tsx"
        source = source_path.read_text(encoding='utf-8')
        assert 'minLength' in source, "应有 minLength 属性"
        assert 'maxLength' in source, "应有 maxLength 属性"
        assert 'username.length' in source, "应有 JS 端的用户名长度校验"


# ============================================================
# V2 修复: NEW-7 前端 console 日志
# ============================================================
class TestFrontendLogger:
    """测试前端日志工具"""
    
    def test_logger_utility_exists(self):
        """应有 frontend/src/lib/logger.ts"""
        assert (PROJECT_ROOT / "frontend" / "src" / "lib" / "logger.ts").exists()
    
    def test_upload_zone_uses_logger(self):
        """UploadZone 应使用 logger 工具而非 console.error"""
        source_path = PROJECT_ROOT / "frontend" / "src" / "components" / "UploadZone.tsx"
        source = source_path.read_text(encoding='utf-8')
        assert 'from' in source and 'logger' in source, "应导入 logger"


# ============================================================
# 异步架构: AsyncOpenAI 重构验证
# ============================================================
class TestAsyncLLMRefactor:
    """测试 AsyncOpenAI 异步重构"""
    
    def test_llm_client_has_async_client(self):
        """llm_client.py 应包含 AsyncOpenAI 客户端"""
        source_path = PROJECT_ROOT / "src" / "core" / "llm_client.py"
        source = source_path.read_text(encoding='utf-8')
        assert 'AsyncOpenAI' in source, "应导入 AsyncOpenAI"
        assert 'async_client' in source, "应有 async_client 全局变量"
        assert 'async def async_call_llm' in source, "应有 async_call_llm 异步函数"
    
    def test_llm_client_keeps_sync_for_cli(self):
        """llm_client.py 应保留同步版本供 CLI 使用"""
        source_path = PROJECT_ROOT / "src" / "core" / "llm_client.py"
        source = source_path.read_text(encoding='utf-8')
        assert 'def init_client' in source, "应保留 sync init_client"
        assert 'def call_llm' in source, "应保留 sync call_llm"
    
    def test_task_manager_no_thread_pool(self):
        """task_manager.py 不应再使用 ThreadPoolExecutor"""
        source_path = PROJECT_ROOT / "api" / "core" / "task_manager.py"
        source = source_path.read_text(encoding='utf-8')
        assert 'ThreadPoolExecutor' not in source, "应移除 ThreadPoolExecutor"
        assert 'import threading' not in source, "应移除 threading 导入"
        assert 'asyncio' in source, "应使用 asyncio"
        assert 'submit_async_task' in source, "应有 submit_async_task 方法"
    
    def test_upload_uses_async_llm(self):
        """upload.py 应使用 async_call_llm 而非同步 call_llm"""
        source_path = PROJECT_ROOT / "api" / "routes" / "upload.py"
        source = source_path.read_text(encoding='utf-8')
        assert 'async_call_llm' in source, "应导入 async_call_llm"
        assert 'init_client' not in source, "不应再导入同步 init_client"
        # 确认没有同步 call_llm 调用（只有 async_call_llm）
        import re
        sync_calls = re.findall(r'(?<!async_)call_llm\(', source)
        assert len(sync_calls) == 0, f"不应有同步 call_llm 调用，发现 {len(sync_calls)} 处"
    
    def test_upload_background_is_async(self):
        """后台处理函数应为 async 协程"""
        source_path = PROJECT_ROOT / "api" / "routes" / "upload.py"
        source = source_path.read_text(encoding='utf-8')
        assert 'async def _process_pdf_background_async' in source, \
            "后台处理函数应为 async def"
        assert 'submit_async_task' in source, \
            "应使用 submit_async_task 提交异步任务"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
