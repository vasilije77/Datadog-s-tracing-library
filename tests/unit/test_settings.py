from ddtrace.settings import Config, IntegrationConfig, HttpConfig

from ..base import BaseTestCase


class TestConfig(BaseTestCase):
    def test_environment_analytics_enabled(self):
        with self.override_env(dict(DD_ANALYTICS_ENABLED='True')):
            config = Config()
            self.assertTrue(config.analytics_enabled)

        with self.override_env(dict(DD_ANALYTICS_ENABLED='False')):
            config = Config()
            self.assertFalse(config.analytics_enabled)


class TestHttpConfig(BaseTestCase):

    def test_trace_headers(self):
        http_config = HttpConfig()
        http_config.trace_headers('some_header')
        assert http_config.header_is_traced('some_header')
        assert not http_config.header_is_traced('some_other_header')

    def test_trace_headers_whitelist_case_insensitive(self):
        http_config = HttpConfig()
        http_config.trace_headers('some_header')
        assert http_config.header_is_traced('sOmE_hEaDeR')
        assert not http_config.header_is_traced('some_other_header')

    def test_trace_multiple_headers(self):
        http_config = HttpConfig()
        http_config.trace_headers(['some_header_1', 'some_header_2'])
        assert http_config.header_is_traced('some_header_1')
        assert http_config.header_is_traced('some_header_2')
        assert not http_config.header_is_traced('some_header_3')

    def test_empty_entry_do_not_raise_exception(self):
        http_config = HttpConfig()
        http_config.trace_headers('')

        assert not http_config.header_is_traced('some_header_1')

    def test_none_entry_do_not_raise_exception(self):
        http_config = HttpConfig()
        http_config.trace_headers(None)
        assert not http_config.header_is_traced('some_header_1')

    def test_is_header_tracing_configured(self):
        http_config = HttpConfig()
        assert not http_config.is_header_tracing_configured
        http_config.trace_headers('some_header')
        assert http_config.is_header_tracing_configured

    def test_header_is_traced_case_insensitive(self):
        http_config = HttpConfig()
        http_config.trace_headers('sOmE_hEaDeR')
        assert http_config.header_is_traced('SoMe_HeAdEr')
        assert not http_config.header_is_traced('some_other_header')

    def test_header_is_traced_false_for_empty_header(self):
        http_config = HttpConfig()
        http_config.trace_headers('some_header')
        assert not http_config.header_is_traced('')

    def test_header_is_traced_false_for_none_header(self):
        http_config = HttpConfig()
        http_config.trace_headers('some_header')
        assert not http_config.header_is_traced(None)


class TestIntegrationConfig(BaseTestCase):
    def setUp(self):
        self.config = Config()
        self.integration_config = IntegrationConfig(self.config, 'test')

    def test_is_a_dict(self):
        assert isinstance(self.integration_config, dict)

    def test_allow_item_access(self):
        self.integration_config['setting'] = 'value'

        # Can be accessed both as item and attr accessor
        assert self.integration_config.setting == 'value'
        assert self.integration_config['setting'] == 'value'

    def test_allow_attr_access(self):
        self.integration_config.setting = 'value'

        # Can be accessed both as item and attr accessor
        assert self.integration_config.setting == 'value'
        assert self.integration_config['setting'] == 'value'

    def test_allow_both_access(self):
        self.integration_config.setting = 'value'
        assert self.integration_config['setting'] == 'value'
        assert self.integration_config.setting == 'value'

        self.integration_config['setting'] = 'new-value'
        assert self.integration_config.setting == 'new-value'
        assert self.integration_config['setting'] == 'new-value'

    def test_allow_configuring_http(self):
        self.integration_config.http.trace_headers('integration_header')
        assert self.integration_config.http.header_is_traced('integration_header')
        assert not self.integration_config.http.header_is_traced('other_header')

    def test_allow_exist_both_global_and_integration_config(self):
        self.config.trace_headers('global_header')
        assert self.integration_config.header_is_traced('global_header')

        self.integration_config.http.trace_headers('integration_header')
        assert self.integration_config.header_is_traced('integration_header')
        assert not self.integration_config.header_is_traced('global_header')
        assert not self.config.header_is_traced('integration_header')

    def test_environment_analytics_enabled(self):
        # default
        self.assertFalse(self.config.analytics_enabled)
        self.assertIsNone(self.config.foo.analytics_enabled)

        with self.override_env(dict(DD_ANALYTICS_ENABLED='True')):
            config = Config()
            self.assertTrue(config.analytics_enabled)
            self.assertIsNone(config.foo.analytics_enabled)

        with self.override_env(dict(DD_FOO_ANALYTICS_ENABLED='True')):
            config = Config()
            self.assertTrue(config.foo.analytics_enabled)

        with self.override_env(dict(DD_FOO_ANALYTICS_ENABLED='False')):
            config = Config()
            self.assertFalse(config.foo.analytics_enabled)
