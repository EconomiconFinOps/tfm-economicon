function handler(event) {
  var request = event.request;
  // Cache behavior is selected before this rewrite; the API origin is preserved.
  request.uri = request.uri === '/api' ? '/' : request.uri.replace(/^\/api\//, '/');
  return request;
}
