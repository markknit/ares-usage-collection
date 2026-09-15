<?php
declare(strict_types=1);

define('ARES_STAFF_ENROLLMENT_TESTING', true);
require __DIR__ . '/../central-monitoring/web-upload/staff_enrollment.php';

function staff_expect(bool $condition, string $message): void
{
    if (!$condition) {
        fwrite(STDERR, "FAIL: {$message}\n");
        exit(1);
    }
}

$validPassword = 'ares-staff-test';
staff_expect(ares_staff_password_configured($validPassword), 'configured shared password should be accepted');
staff_expect(!ares_staff_password_configured('short'), 'password shorter than six characters should be rejected');
staff_expect(!ares_staff_password_configured('REPLACE_WITH_SHARED_STAFF_PASSWORD'), 'placeholder staff password should be rejected');
staff_expect(ares_staff_password_matches($validPassword, $validPassword), 'matching shared password should pass');
staff_expect(!ares_staff_password_matches($validPassword, 'wrong-password'), 'wrong shared password should fail');
staff_expect(!ares_staff_password_matches('short', 'short'), 'invalid configured password should never authenticate');

$now = 2_000_000;
staff_expect(!ares_staff_session_expired(null, $now), 'new session should not be expired');
staff_expect(!ares_staff_session_expired($now - 900, $now), 'session at timeout boundary should remain valid');
staff_expect(ares_staff_session_expired($now - 901, $now), 'session beyond timeout should expire');

$csrf = str_repeat('c', 64);
staff_expect(ares_staff_csrf_matches($csrf, $csrf), 'matching CSRF token should pass');
staff_expect(!ares_staff_csrf_matches($csrf, ''), 'empty CSRF token should fail');
staff_expect(!ares_staff_csrf_matches($csrf, str_repeat('d', 64)), 'wrong CSRF token should fail');

staff_expect(ares_staff_cookie_path('/monitor_upload/staff_enrollment.php') === '/monitor_upload/', 'monitor upload cookie path should be scoped');
staff_expect(ares_staff_cookie_path('/staff_enrollment.php') === '/', 'root cookie path should remain root');
staff_expect(ares_staff_escape('<script>') === '&lt;script&gt;', 'HTML escaping should be enabled');
staff_expect(ares_staff_error_message('active-enrollment-code-exists') !== '', 'known errors should map to staff-safe text');

echo "ARES staff enrollment page tests passed\n";
