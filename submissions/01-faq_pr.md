## Question

I'm using Claude Code in GitHub Codespaces for isolation, but login fails with "localhost refused to connect." How do I fix it?

## Answer

### Claude Code OAuth Login in Codespaces — Workaround

Claude Code's OAuth login opens a browser tab pointing at  
`http://localhost:PORT/callback`.  
In GitHub Codespaces this often fails, because the browser reaches that URL
through Codespaces’ port‑forwarding proxy instead of talking to the listener directly.

### **Workaround**

1. Run `claude` and let it open the login link in your browser.
2. When the page fails to load, copy the full URL from the browser’s address bar  
   (e.g. `http://localhost:35251/oauth/callback?code=...`).
3. Open a second terminal tab **inside the Codespace** and run:

   ```bash
   curl "http://localhost:35251/oauth/callback?code=..."
   ```

4. Your original terminal logs in immediately.

This works because the `curl` command runs *inside* the Codespace, on the same machine as the OAuth listener,  
so it bypasses the port‑forwarding proxy entirely.

If this doesn't resolve your login error, check Anthropic’s [Troubleshoot installation and login](https://code.claude.com/docs/en/troubleshoot-install) page for other known causes.