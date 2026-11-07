// CloudFront viewer-request function (runtime cloudfront-js-2.0).
// Terraform fills in the host with templatefile() in cdn.tf.
//
// 1. Any other host name, such as the distribution's own *.cloudfront.net
//    name, is redirected to the canonical host, so each page has one address.
// 2. "/services" is redirected to "/services/", the address the site links to.
// 3. "/services/" is served from the object "services/index.html".
//
// Query strings are dropped on redirects: the site does not use them.
var HOST = "${host}";

function redirect(location) {
  return {
    statusCode: 301,
    statusDescription: "Moved Permanently",
    headers: { location: { value: location } },
  };
}

function handler(event) {
  var request = event.request;
  var host = request.headers.host ? request.headers.host.value.toLowerCase() : "";
  var uri = request.uri;

  if (host !== HOST) {
    return redirect("https://" + HOST + uri);
  }
  if (uri.endsWith("/")) {
    request.uri = uri + "index.html";
    return request;
  }
  // The last path segment has no dot, so it names a folder, not a file.
  if (uri.lastIndexOf(".") < uri.lastIndexOf("/")) {
    return redirect(uri + "/");
  }
  return request;
}
