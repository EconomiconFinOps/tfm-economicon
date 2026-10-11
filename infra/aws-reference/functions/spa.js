function handler(event) {
  var request = event.request;
  var leaf = request.uri.split('/').pop();
  // Only the static behavior uses this function; API errors never become index.html.
  if (request.uri.endsWith('/') || leaf.indexOf('.') === -1) {
    request.uri = '/index.html';
  }
  return request;
}
