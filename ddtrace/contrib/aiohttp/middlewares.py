from ..asyncio import context_provider
from ...ext import AppTypes, http
from ...compat import stringify


class TraceMiddleware(object):
    """
    aiohttp Middleware class that will append a middleware coroutine to trace
    incoming traffic.
    """
    def __init__(self, app, tracer, service='aiohttp-web'):
        # safe-guard: don't add the middleware twice
        if getattr(app, '__datadog_middleware', False):
            return
        setattr(app, '__datadog_middleware', True)

        # keep the references
        self.app = app
        self._tracer = tracer
        self._service = service

        # the tracer must work with asynchronous Context propagation
        self._tracer.configure(context_provider=context_provider)

        # configure the current service
        self._tracer.set_service_info(
            service=service,
            app='aiohttp',
            app_type=AppTypes.web,
        )

        # add the async tracer middleware as a first middleware
        # and be sure that the on_prepare signal is the last one
        self._middleware = self.middleware_factory()
        self._on_prepare = self.signal_factory()
        self.app.middlewares.insert(0, self._middleware)
        self.app.on_response_prepare.append(self._on_prepare)

    def middleware_factory(self):
        """
        The middleware factory returns an aiohttp middleware that traces the handler execution.
        Because handlers are run in different tasks for each request, we attach the Context
        instance both to the Task and to the Request objects. In this way:
            * the Task may be used by the internal tracing
            * the Request remains the main Context carrier if it should be passed as argument
              to the tracer.trace() method
        """
        async def middleware(app, handler):
            async def attach_context(request):
                # trace the handler
                request_span = self._tracer.trace(
                    'aiohttp.request',
                    service=self._service,
                    span_type=http.TYPE,
                )

                # attach the context and the root span to the request
                request['__datadog_context'] = request_span.context
                request['__datadog_request_span'] = request_span
                try:
                    return await handler(request)
                except Exception:
                    request_span.set_traceback()
                    raise
            return attach_context
        return middleware

    def signal_factory(self):
        """
        The signal factory returns the on_prepare signal that is sent while the Response is
        being prepared. The signal is used to close the request span that is created during
        the trace middleware execution.
        """
        async def on_prepare(request, response):
            # safe-guard: discard if we don't have a request span
            request_span = request.get('__datadog_request_span', None)
            if not request_span:
                return

            # default resource name
            resource = stringify(response.status)

            if request.match_info.route.resource:
                # collect the resource name based on http resource type
                res_info = request.match_info.route.resource.get_info()

                if res_info.get('path'):
                    resource = res_info.get('path')
                elif res_info.get('formatter'):
                    resource = res_info.get('formatter')
                elif res_info.get('prefix'):
                    resource = res_info.get('prefix')

            request_span.resource = resource
            request_span.set_tag('http.method', request.method)
            request_span.set_tag('http.status_code', response.status)
            request_span.set_tag('http.url', request.path)
            request_span.finish()
        return on_prepare
