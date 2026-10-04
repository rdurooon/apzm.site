(() => {
  const token = document.querySelector('meta[name="csrf-token"]')?.content;
  if (!token) return;

  const originalFetch = window.fetch.bind(window);
  window.fetch = (input, init = {}) => {
    const inputUrl = input instanceof Request ? input.url : input;
    const url = new URL(inputUrl, window.location.href);
    const method = (init.method || (input instanceof Request ? input.method : "GET")).toUpperCase();

    if (url.origin === window.location.origin && !["GET", "HEAD", "OPTIONS"].includes(method)) {
      const headers = new Headers(input instanceof Request ? input.headers : undefined);
      new Headers(init.headers).forEach((value, name) => headers.set(name, value));
      headers.set("X-CSRF-Token", token);
      init = { ...init, headers };
    }

    return originalFetch(input, init);
  };
})();