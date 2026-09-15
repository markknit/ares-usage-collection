<?php
declare(strict_types=1);

require __DIR__ . '/upload_lib.php';
require __DIR__ . '/enrollment_lib.php';
require __DIR__ . '/enrollment_admin_lib.php';

const ARES_STAFF_SESSION_TIMEOUT_SECONDS = 900;

function ares_staff_escape(string $value): string
{
    return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function ares_staff_admin_key_configured(string $key): bool
{
    $key = trim($key);
    return strlen($key) >= 32 && !str_starts_with($key, 'REPLACE_');
}

function ares_staff_admin_key_matches(string $configured, string $provided): bool
{
    if (!ares_staff_admin_key_configured($configured)) {
        return false;
    }

    $provided = trim($provided);
    return $provided !== '' && hash_equals(trim($configured), $provided);
}

function ares_staff_session_expired(?int $lastActivity, int $now, int $timeout = ARES_STAFF_SESSION_TIMEOUT_SECONDS): bool
{
    if ($lastActivity === null || $lastActivity <= 0) {
        return false;
    }

    return ($now - $lastActivity) > $timeout;
}

function ares_staff_csrf_matches(string $expected, string $provided): bool
{
    return $expected !== '' && $provided !== '' && hash_equals($expected, $provided);
}

function ares_staff_cookie_path(string $scriptName): string
{
    $path = str_replace('\\', '/', dirname($scriptName));
    if ($path === '.' || $path === '/' || $path === '') {
        return '/';
    }

    return rtrim($path, '/') . '/';
}

function ares_staff_clear_session(string $cookiePath): void
{
    $_SESSION = [];
    if ((bool)ini_get('session.use_cookies')) {
        setcookie(session_name(), '', [
            'expires' => time() - 42000,
            'path' => $cookiePath,
            'secure' => true,
            'httponly' => true,
            'samesite' => 'Strict',
        ]);
    }
    session_destroy();
}

function ares_staff_error_message(string $error): string
{
    return match ($error) {
        'unknown-school' => 'That school is not available for enrollment.',
        'active-enrollment-code-exists' => 'An unused enrollment code already exists for this school. Because plaintext codes are not stored, ARES cannot display the earlier code again.',
        'invalid-school-registry' => 'The school registry is invalid.',
        'enrollment-secret-not-configured' => 'Enrollment code generation is not configured.',
        'enrollment-storage-unavailable' => 'Enrollment storage is unavailable.',
        'invalid-enrollment-state' => 'Enrollment state is invalid.',
        'enrollment-storage-write-failed' => 'The enrollment code could not be saved.',
        default => 'The enrollment code could not be generated.',
    };
}

function ares_staff_render_page(array $view): void
{
    $nonce = (string)$view['nonce'];
    $authorized = (bool)$view['authorized'];
    $loginError = (string)($view['login_error'] ?? '');
    $notice = (string)($view['notice'] ?? '');
    $error = (string)($view['error'] ?? '');
    $query = (string)($view['query'] ?? '');
    $matches = is_array($view['matches'] ?? null) ? $view['matches'] : [];
    $generated = is_array($view['generated'] ?? null) ? $view['generated'] : null;
    $rotateSchool = is_array($view['rotate_school'] ?? null) ? $view['rotate_school'] : null;
    $csrf = (string)($view['csrf'] ?? '');

    header('Content-Type: text/html; charset=utf-8');
    ?>
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>ARES Staff Enrollment Codes</title>
  <style nonce="<?= ares_staff_escape($nonce) ?>">
    :root { color-scheme: light; font-family: Arial, Helvetica, sans-serif; }
    * { box-sizing: border-box; }
    body { margin: 0; background: #f4f6f8; color: #1f2933; }
    header { background: #173f5f; color: white; padding: 18px 20px; }
    header .wrap { max-width: 920px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; gap: 16px; }
    header h1 { margin: 0; font-size: 1.45rem; }
    header p { margin: 4px 0 0; opacity: .9; }
    main { max-width: 920px; margin: 24px auto; padding: 0 16px 40px; }
    .card { background: white; border-radius: 12px; padding: 20px; margin-bottom: 18px; box-shadow: 0 2px 10px rgba(0,0,0,.07); }
    .card h2, .card h3 { margin-top: 0; }
    label { display: block; font-weight: 700; margin-bottom: 7px; }
    input[type="text"], input[type="password"] { width: 100%; padding: 12px 13px; border: 1px solid #aab7c4; border-radius: 8px; font-size: 1rem; }
    button { border: 0; border-radius: 8px; padding: 11px 16px; font-size: .98rem; font-weight: 700; cursor: pointer; background: #1769aa; color: white; }
    button.secondary { background: #52606d; }
    button.danger { background: #a13d2d; }
    .actions { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; margin-top: 12px; }
    .message { border-radius: 8px; padding: 13px 14px; margin-bottom: 18px; }
    .message.info { background: #e8f1f8; border-left: 4px solid #1769aa; }
    .message.warn { background: #fff4db; border-left: 4px solid #b7791f; }
    .message.error { background: #fdecea; border-left: 4px solid #b42318; }
    .message.after-code { margin-top: 16px; margin-bottom: 0; }
    .school { border-top: 1px solid #e5e9ed; padding: 16px 0; }
    .school:first-of-type { border-top: 0; }
    .school-name { font-size: 1.08rem; font-weight: 700; }
    .school-id { color: #52606d; font-family: Consolas, Monaco, monospace; margin-top: 3px; }
    .code-box { text-align: center; padding: 22px; border: 2px dashed #1769aa; border-radius: 10px; background: #f8fbfd; }
    .code { font-family: Consolas, Monaco, monospace; font-size: clamp(1.8rem, 6vw, 3rem); font-weight: 800; letter-spacing: .08em; margin: 10px 0 14px; }
    .small { color: #52606d; font-size: .9rem; }
    .top-actions form { margin: 0; }
    .inline { display: inline; }
    @media (max-width: 600px) { header .wrap { align-items: flex-start; flex-direction: column; } .top-actions { width: 100%; } }
  </style>
</head>
<body>
<header>
  <div class="wrap">
    <div>
      <h1>ARES Staff Enrollment Codes</h1>
      <p>Generate one-time teacher setup codes</p>
    </div>
    <?php if ($authorized): ?>
      <div class="top-actions">
        <form method="post">
          <input type="hidden" name="action" value="logout">
          <input type="hidden" name="csrf" value="<?= ares_staff_escape($csrf) ?>">
          <button class="secondary" type="submit">Sign out</button>
        </form>
      </div>
    <?php endif; ?>
  </div>
</header>
<main>
  <?php if (!$authorized): ?>
    <section class="card">
      <h2>Staff sign in</h2>
      <p>Enter the ARES enrollment administration key. The key is checked over HTTPS and is not stored in the browser by this page.</p>
      <?php if ($notice !== ''): ?><div class="message info"><?= ares_staff_escape($notice) ?></div><?php endif; ?>
      <?php if ($loginError !== ''): ?><div class="message error"><?= ares_staff_escape($loginError) ?></div><?php endif; ?>
      <form method="post" autocomplete="on">
        <input type="hidden" name="action" value="login">
        <label for="admin_key">Administration key</label>
        <input id="admin_key" name="admin_key" type="password" autocomplete="current-password" required autofocus>
        <div class="actions"><button type="submit">Continue</button></div>
      </form>
      <p class="small">For routine use, keep the administration key in the ARES password manager rather than in notes, email, or chat.</p>
    </section>
  <?php else: ?>
    <?php if ($notice !== ''): ?><div class="message info"><?= ares_staff_escape($notice) ?></div><?php endif; ?>
    <?php if ($error !== ''): ?><div class="message error"><?= ares_staff_escape($error) ?></div><?php endif; ?>

    <?php if ($generated !== null): ?>
      <section class="card">
        <h2>Enrollment code generated</h2>
        <div class="code-box">
          <div><?= ares_staff_escape((string)$generated['canonical_name']) ?></div>
          <div class="school-id"><?= ares_staff_escape((string)$generated['school_id']) ?></div>
          <div id="generated-code" class="code"><?= ares_staff_escape((string)$generated['enrollment_code']) ?></div>
          <button id="copy-code" type="button">Copy code</button>
        </div>
        <div class="message warn after-code">
          Give this code to the teacher now. It can be used once and the plaintext code is not stored by ARES, so it cannot be displayed again later.
        </div>
      </section>
    <?php endif; ?>

    <?php if ($rotateSchool !== null): ?>
      <section class="card">
        <h2>Unused code already exists</h2>
        <p>An unused code already exists for <strong><?= ares_staff_escape((string)$rotateSchool['canonical_name']) ?></strong>. The earlier plaintext code cannot be recovered.</p>
        <p>Only replace it if the old code is lost or should no longer work.</p>
        <form method="post">
          <input type="hidden" name="action" value="generate">
          <input type="hidden" name="csrf" value="<?= ares_staff_escape($csrf) ?>">
          <input type="hidden" name="school_id" value="<?= ares_staff_escape((string)$rotateSchool['school_id']) ?>">
          <input type="hidden" name="q" value="<?= ares_staff_escape($query) ?>">
          <input type="hidden" name="rotate" value="1">
          <button class="danger" type="submit">Replace unused code and generate new code</button>
        </form>
      </section>
    <?php endif; ?>

    <section class="card">
      <h2>Find a school</h2>
      <form method="get">
        <label for="q">School name</label>
        <input id="q" name="q" type="text" value="<?= ares_staff_escape($query) ?>" placeholder="Start typing the school name" minlength="2" required autofocus>
        <div class="actions"><button type="submit">Search</button></div>
      </form>
      <p class="small">Search uses the same canonical school registry as ARES Sync.</p>
    </section>

    <?php if ($query !== '' && strlen($query) < 2): ?>
      <div class="message warn">Enter at least two characters of the school name.</div>
    <?php elseif ($query !== '' && $matches === []): ?>
      <div class="message warn">No active school matched that search.</div>
    <?php elseif ($matches !== []): ?>
      <section class="card">
        <h2>Search results</h2>
        <?php foreach ($matches as $school): ?>
          <div class="school">
            <div class="school-name"><?= ares_staff_escape((string)$school['canonical_name']) ?></div>
            <div class="school-id"><?= ares_staff_escape((string)$school['school_id']) ?></div>
            <form method="post" class="actions">
              <input type="hidden" name="action" value="generate">
              <input type="hidden" name="csrf" value="<?= ares_staff_escape($csrf) ?>">
              <input type="hidden" name="school_id" value="<?= ares_staff_escape((string)$school['school_id']) ?>">
              <input type="hidden" name="q" value="<?= ares_staff_escape($query) ?>">
              <button type="submit">Generate one-time code</button>
            </form>
          </div>
        <?php endforeach; ?>
      </section>
    <?php endif; ?>

    <p class="small">For security, staff sessions expire after 15 minutes of inactivity. Sign out when finished.</p>
  <?php endif; ?>
</main>
<?php if ($generated !== null): ?>
<script nonce="<?= ares_staff_escape($nonce) ?>">
(() => {
  const button = document.getElementById('copy-code');
  const code = document.getElementById('generated-code');
  if (!button || !code || !navigator.clipboard) return;
  button.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(code.textContent.trim());
      button.textContent = 'Copied';
    } catch (_) {
      button.textContent = 'Select and copy the code above';
    }
  });
})();
</script>
<?php endif; ?>
</body>
</html>
<?php
}

function ares_staff_enrollment_main(): void
{
    header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0');
    header('Pragma: no-cache');
    header('X-Content-Type-Options: nosniff');
    header('Referrer-Policy: no-referrer');
    header('X-Frame-Options: DENY');

    $nonce = base64_encode(random_bytes(18));
    header("Content-Security-Policy: default-src 'none'; style-src 'nonce-{$nonce}'; script-src 'nonce-{$nonce}'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'");

    $configPath = __DIR__ . '/config.php';
    if (!is_file($configPath)) {
        http_response_code(503);
        ares_staff_render_page(['nonce' => $nonce, 'authorized' => false, 'login_error' => 'Enrollment administration is not configured.']);
        return;
    }

    $config = require $configPath;
    if (!is_array($config)) {
        http_response_code(503);
        ares_staff_render_page(['nonce' => $nonce, 'authorized' => false, 'login_error' => 'Enrollment administration configuration is invalid.']);
        return;
    }

    $requireHttps = array_key_exists('require_https', $config) ? (bool)$config['require_https'] : true;
    if ($requireHttps && !ares_is_https($_SERVER)) {
        http_response_code(400);
        ares_staff_render_page(['nonce' => $nonce, 'authorized' => false, 'login_error' => 'HTTPS is required for staff enrollment administration.']);
        return;
    }

    $adminKey = trim((string)($config['enrollment_admin_key'] ?? ''));
    if (!ares_staff_admin_key_configured($adminKey)) {
        http_response_code(503);
        ares_staff_render_page(['nonce' => $nonce, 'authorized' => false, 'login_error' => 'The enrollment administration key is not configured.']);
        return;
    }

    $scriptName = (string)($_SERVER['SCRIPT_NAME'] ?? '/monitor_upload/staff_enrollment.php');
    $cookiePath = ares_staff_cookie_path($scriptName);
    ini_set('session.use_strict_mode', '1');
    ini_set('session.use_only_cookies', '1');
    session_name('ARES_ENROLLMENT_ADMIN');
    session_set_cookie_params([
        'lifetime' => 0,
        'path' => $cookiePath,
        'secure' => true,
        'httponly' => true,
        'samesite' => 'Strict',
    ]);
    session_start();

    $now = time();
    $authorized = ($_SESSION['authorized'] ?? false) === true;
    $notice = '';
    if ($authorized && ares_staff_session_expired(isset($_SESSION['last_activity']) ? (int)$_SESSION['last_activity'] : null, $now)) {
        ares_staff_clear_session($cookiePath);
        session_name('ARES_ENROLLMENT_ADMIN');
        session_set_cookie_params([
            'lifetime' => 0,
            'path' => $cookiePath,
            'secure' => true,
            'httponly' => true,
            'samesite' => 'Strict',
        ]);
        session_start();
        $authorized = false;
        $notice = 'Your staff session expired. Sign in again to continue.';
    }

    $loginError = '';
    $error = '';
    $generated = null;
    $rotateSchool = null;
    $query = trim((string)($_GET['q'] ?? $_POST['q'] ?? ''));
    $method = strtoupper((string)($_SERVER['REQUEST_METHOD'] ?? 'GET'));
    $action = $method === 'POST' ? trim((string)($_POST['action'] ?? '')) : '';

    if ($method === 'POST' && $action === 'login') {
        $provided = (string)($_POST['admin_key'] ?? '');
        if (ares_staff_admin_key_matches($adminKey, $provided)) {
            session_regenerate_id(true);
            $_SESSION['authorized'] = true;
            $_SESSION['csrf'] = bin2hex(random_bytes(32));
            $_SESSION['last_activity'] = $now;
            header('Location: ' . basename($scriptName), true, 303);
            return;
        }

        usleep(350000);
        $loginError = 'Administration key not accepted.';
    }

    $authorized = ($_SESSION['authorized'] ?? false) === true;
    if ($authorized) {
        $_SESSION['last_activity'] = $now;
        if (empty($_SESSION['csrf']) || !is_string($_SESSION['csrf'])) {
            $_SESSION['csrf'] = bin2hex(random_bytes(32));
        }
    }
    $csrf = $authorized ? (string)$_SESSION['csrf'] : '';

    if ($method === 'POST' && $action !== '' && $action !== 'login') {
        if (!$authorized) {
            http_response_code(401);
            $loginError = 'Sign in before generating enrollment codes.';
        } elseif (!ares_staff_csrf_matches($csrf, (string)($_POST['csrf'] ?? ''))) {
            http_response_code(400);
            $error = 'The form expired or was not valid. Refresh the page and try again.';
        } elseif ($action === 'logout') {
            ares_staff_clear_session($cookiePath);
            header('Location: ' . basename($scriptName), true, 303);
            return;
        }
    }

    $matches = [];
    $registry = null;
    if ($authorized) {
        $registryPath = (string)($config['school_registry_path'] ?? (__DIR__ . '/data/schools.json'));
        $registry = ares_load_school_registry($registryPath);
        if ($registry === null) {
            http_response_code(503);
            $error = 'The canonical school registry is not available.';
        }
    }

    if ($authorized && $registry !== null && $method === 'POST' && $action === 'generate' && $error === '') {
        $schoolId = trim((string)($_POST['school_id'] ?? ''));
        $rotate = (string)($_POST['rotate'] ?? '') === '1';
        $statePath = (string)($config['enrollment_state_path'] ?? (__DIR__ . '/data/enrollment_state.json'));
        $secret = trim((string)($config['enrollment_secret'] ?? ''));

        $result = ares_generate_enrollment_code_for_school($statePath, $registry, $schoolId, $secret, $rotate);
        if (($result['ok'] ?? false) === true) {
            $generated = $result;
        } else {
            $resultError = (string)($result['error'] ?? 'enrollment-code-generation-failed');
            if ($resultError === 'active-enrollment-code-exists') {
                $rotateSchool = ares_find_school($registry, $schoolId);
            } else {
                $error = ares_staff_error_message($resultError);
            }
        }
    }

    if ($authorized && $registry !== null && strlen($query) >= 2) {
        $matches = ares_search_schools($registry, $query, 12);
    }

    ares_staff_render_page([
        'nonce' => $nonce,
        'authorized' => $authorized,
        'login_error' => $loginError,
        'notice' => $notice,
        'error' => $error,
        'query' => $query,
        'matches' => $matches,
        'generated' => $generated,
        'rotate_school' => $rotateSchool,
        'csrf' => $csrf,
    ]);
}

if (!defined('ARES_STAFF_ENROLLMENT_TESTING')) {
    ares_staff_enrollment_main();
}
